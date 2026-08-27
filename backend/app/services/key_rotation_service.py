"""Key rotation and search-index rekeying."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.crypto.hmac_search import generate_search_token
from app.models import Document, KeyType, SearchIndexEntry, User
from app.services.audit_service import AuditService
from app.services.encryption_service import EncryptionService
from app.services.key_management_service import KeyManagementService
from app.services.keyword_service import extract_keywords
from app.storage.base import StorageProvider


class KeyRotationService:
    def __init__(
        self,
        db: Session,
        kms: KeyManagementService,
        encryption: EncryptionService,
        storage: StorageProvider,
        audit: AuditService,
    ) -> None:
        self.db = db
        self.kms = kms
        self.encryption = encryption
        self.storage = storage
        self.audit = audit

    def rotate_search_and_reindex(self, admin: User, *, ip: str | None = None) -> dict:
        old_key, old_version = self.kms.get_search_key()
        new_row = self.kms.rotate_search_key()
        new_key, new_version = self.kms.get_search_key()

        documents = list(self.db.scalars(select(Document)).all())
        reindexed = 0
        for doc in documents:
            try:
                dek = self.kms.unwrap_document_key(doc.wrapped_dek, doc.dek_key_version)
                ciphertext = self.storage.get_object(doc.storage_key)
                plaintext = self.encryption.decrypt(
                    ciphertext,
                    dek,
                    doc.encryption_nonce,
                    associated_data=doc.original_filename.encode("utf-8"),
                )
            except Exception:
                continue

            keywords = extract_keywords(plaintext, doc.content_type)
            tokens = {generate_search_token(new_key, kw) for kw in keywords}

            # Remove old-version entries for this document
            self.db.execute(
                delete(SearchIndexEntry).where(
                    SearchIndexEntry.document_id == doc.id,
                    SearchIndexEntry.search_key_version == old_version,
                )
            )
            for token in tokens:
                self.db.add(
                    SearchIndexEntry(
                        document_id=doc.id,
                        keyword_token=token,
                        search_key_version=new_version,
                    )
                )
            reindexed += 1

        self.audit.record_event(
            action="KEY_ROTATION",
            success=True,
            user_id=admin.id,
            resource_type="search_key",
            resource_id=str(new_version),
            ip=ip,
            metadata={
                "old_version": old_version,
                "new_version": new_version,
                "documents_reindexed": reindexed,
            },
        )
        self.db.commit()
        return {
            "old_search_key_version": old_version,
            "new_search_key_version": new_version,
            "documents_reindexed": reindexed,
        }

    def rotate_master_and_rewrap(self, admin: User, *, ip: str | None = None) -> dict:
        old_active = next(
            (k for k in self.kms.get_status() if k["key_type"] == "MASTER" and k["status"] == "ACTIVE"),
            None,
        )
        old_version = old_active["version"] if old_active else 1
        new_row = self.kms.rotate_master_key()
        new_version = new_row.version

        documents = list(self.db.scalars(select(Document)).all())
        rewrapped = 0
        for doc in documents:
            try:
                packed, _nonce = self.kms.rewrap_dek(doc.wrapped_dek, doc.dek_key_version, new_version)
                doc.wrapped_dek = packed
                doc.dek_key_version = new_version
                # Nonce for document ciphertext unchanged; wrap nonce is inside packed
                rewrapped += 1
            except Exception:
                continue

        self.audit.record_event(
            action="KEY_ROTATION",
            success=True,
            user_id=admin.id,
            resource_type="master_key",
            resource_id=str(new_version),
            ip=ip,
            metadata={"old_version": old_version, "new_version": new_version, "documents_rewrapped": rewrapped},
        )
        self.db.commit()
        return {
            "old_master_key_version": old_version,
            "new_master_key_version": new_version,
            "documents_rewrapped": rewrapped,
        }

    def reindex_only(self, admin: User, *, ip: str | None = None) -> dict:
        """Rebuild index for the currently active search key without rotating."""
        search_key, version = self.kms.get_search_key()
        documents = list(self.db.scalars(select(Document)).all())
        count = 0
        for doc in documents:
            try:
                dek = self.kms.unwrap_document_key(doc.wrapped_dek, doc.dek_key_version)
                ciphertext = self.storage.get_object(doc.storage_key)
                plaintext = self.encryption.decrypt(
                    ciphertext,
                    dek,
                    doc.encryption_nonce,
                    associated_data=doc.original_filename.encode("utf-8"),
                )
            except Exception:
                continue
            keywords = extract_keywords(plaintext, doc.content_type)
            tokens = {generate_search_token(search_key, kw) for kw in keywords}
            self.db.execute(
                delete(SearchIndexEntry).where(
                    SearchIndexEntry.document_id == doc.id,
                    SearchIndexEntry.search_key_version == version,
                )
            )
            for token in tokens:
                self.db.add(
                    SearchIndexEntry(
                        document_id=doc.id,
                        keyword_token=token,
                        search_key_version=version,
                    )
                )
            count += 1

        self.audit.record_event(
            action="KEY_REINDEX",
            success=True,
            user_id=admin.id,
            ip=ip,
            metadata={"search_key_version": version, "documents": count},
        )
        self.db.commit()
        return {"search_key_version": version, "documents_reindexed": count}
