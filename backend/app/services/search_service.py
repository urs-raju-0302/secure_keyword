from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto.hmac_search import generate_search_token
from app.models import Document, SearchIndexEntry, User
from app.security.authorization import can_search_document
from app.services.audit_service import AuditService
from app.services.key_management_service import KeyManagementService
from app.services.keyword_service import normalize_keyword


class SearchService:
    def __init__(
        self,
        db: Session,
        kms: KeyManagementService,
        audit: AuditService,
    ) -> None:
        self.db = db
        self.kms = kms
        self.audit = audit

    def search(self, user: User, keyword: str, *, ip: str | None = None) -> list[Document]:
        normalized = normalize_keyword(keyword)
        if not normalized:
            return []

        search_key, version = self.kms.get_search_key()
        token = generate_search_token(search_key, normalized)

        # Cloud/index layer only sees the opaque token — not the plaintext keyword
        rows = self.db.scalars(
            select(SearchIndexEntry).where(
                SearchIndexEntry.keyword_token == token,
                SearchIndexEntry.search_key_version == version,
            )
        ).all()

        doc_ids = {r.document_id for r in rows}
        if not doc_ids:
            self.audit.record_event(
                action="SEARCH",
                success=True,
                user_id=user.id,
                ip=ip,
                metadata={"result_count": 0, "token_prefix": token[:8]},
            )
            return []

        documents = list(self.db.scalars(select(Document).where(Document.id.in_(doc_ids))).all())

        # Defense-in-depth: authorization after token matching
        authorized = [d for d in documents if can_search_document(user, d.owner_id)]

        self.audit.record_event(
            action="SEARCH",
            success=True,
            user_id=user.id,
            ip=ip,
            metadata={
                "result_count": len(authorized),
                "matched_before_authz": len(documents),
                "token_prefix": token[:8],
            },
        )
        return authorized

    def find_document_ids(self, token: str, version: int) -> list[UUID]:
        rows = self.db.scalars(
            select(SearchIndexEntry.document_id).where(
                SearchIndexEntry.keyword_token == token,
                SearchIndexEntry.search_key_version == version,
            )
        ).all()
        return list(rows)
