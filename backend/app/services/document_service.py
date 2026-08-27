from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.crypto.hmac_search import generate_search_token
from app.models import Document, SearchIndexEntry, User
from app.security.authorization import can_delete_document, can_read_document
from app.services.audit_service import AuditService
from app.services.encryption_service import EncryptionError, EncryptionService
from app.services.key_management_service import KeyManagementService
from app.services.keyword_service import extract_keywords
from app.storage.base import StorageProvider


class DocumentService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        kms: KeyManagementService,
        encryption: EncryptionService,
        storage: StorageProvider,
        audit: AuditService,
    ) -> None:
        self.db = db
        self.settings = settings
        self.kms = kms
        self.encryption = encryption
        self.storage = storage
        self.audit = audit

    def upload(
        self,
        user: User,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        ip: str | None = None,
    ) -> Document:
        if len(data) == 0:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file")
        if len(data) > self.settings.max_upload_bytes:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
        if content_type not in self.settings.allowed_content_type_list:
            # Also allow octet-stream for text demos if filename ends with .txt
            if not (content_type == "application/octet-stream" and filename.lower().endswith((".txt", ".md", ".json"))):
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Content type not allowed")

        # Sanitize filename (no path components)
        safe_name = filename.replace("\\", "/").split("/")[-1][:512] or "document.txt"

        dek = self.kms.generate_document_key()
        aad = safe_name.encode("utf-8")
        encrypted = self.encryption.encrypt(data, dek, associated_data=aad)
        packed_wrapped, _nonce, dek_version = self.kms.wrap_document_key(dek)

        search_key, search_version = self.kms.get_search_key()
        keywords = extract_keywords(data, content_type)
        tokens = {generate_search_token(search_key, kw) for kw in keywords}

        storage_key = f"{user.id}/{uuid.uuid4()}.bin"
        self.storage.put_object(storage_key, encrypted.ciphertext, content_type="application/octet-stream")

        doc = Document(
            owner_id=user.id,
            original_filename=safe_name,
            content_type=content_type,
            size_bytes=len(data),
            storage_key=storage_key,
            wrapped_dek=packed_wrapped,
            dek_key_version=dek_version,
            encryption_algorithm="AES-256-GCM",
            encryption_nonce=encrypted.nonce,
        )
        self.db.add(doc)
        self.db.flush()

        for token in tokens:
            self.db.add(
                SearchIndexEntry(
                    document_id=doc.id,
                    keyword_token=token,
                    search_key_version=search_version,
                )
            )

        self.audit.record_event(
            action="DOCUMENT_UPLOAD",
            success=True,
            user_id=user.id,
            resource_type="document",
            resource_id=str(doc.id),
            ip=ip,
            metadata={"size_bytes": len(data), "keyword_count": len(tokens)},
        )
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_documents(self, user: User) -> list[Document]:
        q = select(Document).order_by(Document.created_at.desc())
        if user.role.value != "ADMIN":
            q = q.where(Document.owner_id == user.id)
        return list(self.db.scalars(q).all())

    def get_document(self, user: User, document_id: UUID) -> Document:
        doc = self.db.get(Document, document_id)
        if not doc or not can_read_document(user, doc):
            self.audit.record_event(
                action="AUTHORIZATION_FAILURE",
                success=False,
                user_id=user.id,
                resource_type="document",
                resource_id=str(document_id),
            )
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        return doc

    def download(self, user: User, document_id: UUID, *, ip: str | None = None) -> tuple[Document, bytes]:
        doc = self.get_document(user, document_id)
        try:
            dek = self.kms.unwrap_document_key(doc.wrapped_dek, doc.dek_key_version)
            ciphertext = self.storage.get_object(doc.storage_key)
            plaintext = self.encryption.decrypt(
                ciphertext,
                dek,
                doc.encryption_nonce,
                associated_data=doc.original_filename.encode("utf-8"),
            )
        except (EncryptionError, Exception):
            self.audit.record_event(
                action="DECRYPTION_FAILURE",
                success=False,
                user_id=user.id,
                resource_type="document",
                resource_id=str(document_id),
                ip=ip,
            )
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unable to decrypt document")

        self.audit.record_event(
            action="DOCUMENT_DOWNLOAD",
            success=True,
            user_id=user.id,
            resource_type="document",
            resource_id=str(document_id),
            ip=ip,
        )
        return doc, plaintext

    def delete(self, user: User, document_id: UUID, *, ip: str | None = None) -> None:
        doc = self.db.get(Document, document_id)
        if not doc or not can_delete_document(user, doc):
            self.audit.record_event(
                action="AUTHORIZATION_FAILURE",
                success=False,
                user_id=user.id,
                resource_type="document",
                resource_id=str(document_id),
            )
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        try:
            self.storage.delete_object(doc.storage_key)
        except Exception:
            pass
        self.db.delete(doc)
        self.audit.record_event(
            action="DOCUMENT_DELETE",
            success=True,
            user_id=user.id,
            resource_type="document",
            resource_id=str(document_id),
            ip=ip,
        )
        self.db.commit()
