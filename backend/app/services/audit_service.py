"""Structured audit logging — never log secrets or plaintext content."""

from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def hash_ip(ip: str | None) -> str | None:
        if not ip:
            return None
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()

    def record_event(
        self,
        *,
        action: str,
        success: bool,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        # Strip any accidental sensitive keys
        safe_meta = None
        if metadata:
            blocked = {"password", "token", "dek", "master_key", "search_key", "jwt", "plaintext"}
            safe_meta = {k: v for k, v in metadata.items() if k.lower() not in blocked}

        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            ip_hash=self.hash_ip(ip),
            metadata_json=safe_meta,
        )
        self.db.add(entry)
        self.db.flush()
        return entry
