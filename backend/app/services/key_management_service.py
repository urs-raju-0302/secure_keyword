"""Key management: DEK generation/wrapping, search keys, rotation, revocation.

Master key material is loaded from environment (local/dev). Production should
replace this with AWS KMS / Vault / HSM — this local env is NOT equivalent to an HSM.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.crypto.key_wrapping import unwrap_dek, unwrap_search_key, wrap_dek, wrap_search_key
from app.crypto.random import random_dek
from app.models import KeyStatus, KeyType, KeyVersion


class KeyManagementError(Exception):
    pass


def _decode_master_key(raw: str) -> bytes:
    """Accept urlsafe base64 or raw UTF-8 secret (>=32 chars)."""
    try:
        decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        if len(decoded) >= 32:
            return decoded
    except Exception:
        pass
    raw_bytes = raw.encode("utf-8")
    if len(raw_bytes) < 32:
        raise KeyManagementError("MASTER_KEY too short")
    return raw_bytes


class KeyManagementService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self._master = _decode_master_key(settings.master_key)

    def ensure_bootstrap_keys(self) -> None:
        """Create initial MASTER and SEARCH key versions if missing."""
        if not self._get_active(KeyType.MASTER):
            self._create_master_version(1)
        if not self._get_active(KeyType.SEARCH):
            self._create_search_version(1)

    def _get_active(self, key_type: KeyType) -> KeyVersion | None:
        return self.db.scalar(
            select(KeyVersion).where(
                KeyVersion.key_type == key_type,
                KeyVersion.status == KeyStatus.ACTIVE,
            )
        )

    def _create_master_version(self, version: int) -> KeyVersion:
        now = datetime.now(timezone.utc)
        row = KeyVersion(
            key_type=KeyType.MASTER,
            version=version,
            status=KeyStatus.ACTIVE,
            wrapped_key_material=None,
            activated_at=now,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def _create_search_version(self, version: int) -> KeyVersion:
        search_key = random_dek()
        wrapped = wrap_search_key(search_key, self._master, version)
        now = datetime.now(timezone.utc)
        row = KeyVersion(
            key_type=KeyType.SEARCH,
            version=version,
            status=KeyStatus.ACTIVE,
            wrapped_key_material=wrapped.wrapped_dek,
            activated_at=now,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def generate_document_key(self) -> bytes:
        return random_dek()

    def wrap_document_key(self, dek: bytes) -> tuple[bytes, bytes, int]:
        """Returns (packed_wrapped_dek = nonce||ciphertext, wrap_nonce, version)."""
        active = self._get_active(KeyType.MASTER)
        if not active:
            raise KeyManagementError("No active master key version")
        wrapped = wrap_dek(dek, self._master, active.version)
        packed = wrapped.wrap_nonce + wrapped.wrapped_dek
        return packed, wrapped.wrap_nonce, active.version

    def unwrap_document_key(self, packed_wrapped_dek: bytes, key_version: int) -> bytes:
        if len(packed_wrapped_dek) < 13:
            raise KeyManagementError("Invalid wrapped DEK")
        nonce, wrapped = packed_wrapped_dek[:12], packed_wrapped_dek[12:]
        return unwrap_dek(wrapped, nonce, self._master, key_version)

    def get_search_key(self, version: int | None = None) -> tuple[bytes, int]:
        if version is None:
            active = self._get_active(KeyType.SEARCH)
            if not active or not active.wrapped_key_material:
                raise KeyManagementError("No active search key")
            key = unwrap_search_key(active.wrapped_key_material, self._master, active.version)
            return key, active.version
        row = self.db.scalar(
            select(KeyVersion).where(
                KeyVersion.key_type == KeyType.SEARCH,
                KeyVersion.version == version,
            )
        )
        if not row or not row.wrapped_key_material:
            raise KeyManagementError("Search key version not found")
        if row.status == KeyStatus.REVOKED:
            raise KeyManagementError("Search key version revoked")
        key = unwrap_search_key(row.wrapped_key_material, self._master, row.version)
        return key, row.version

    def get_status(self) -> list[dict]:
        rows = self.db.scalars(select(KeyVersion).order_by(KeyVersion.key_type, KeyVersion.version)).all()
        return [
            {
                "key_type": r.key_type.value,
                "version": r.version,
                "status": r.status.value,
                "activated_at": r.activated_at.isoformat() if r.activated_at else None,
                "retired_at": r.retired_at.isoformat() if r.retired_at else None,
            }
            for r in rows
        ]

    def rotate_master_key(self) -> KeyVersion:
        """Activate a new master key *version* (same env MASTER_KEY, new HKDF version).

        Re-wrapping of existing DEKs is performed by the caller (KeyRotationService).
        """
        active = self._get_active(KeyType.MASTER)
        new_version = (active.version + 1) if active else 1
        if active:
            active.status = KeyStatus.RETIRED
            active.retired_at = datetime.now(timezone.utc)
        return self._create_master_version(new_version)

    def rotate_search_key(self) -> KeyVersion:
        """Create and activate a new search key. Old index must be reindexed separately."""
        active = self._get_active(KeyType.SEARCH)
        new_version = (active.version + 1) if active else 1
        # Keep old ACTIVE until reindex completes — create new as ACTIVE only after retire?
        # Policy: retire old immediately but allow unwrap of RETIRED for migration.
        if active:
            active.status = KeyStatus.RETIRED
            active.retired_at = datetime.now(timezone.utc)
        return self._create_search_version(new_version)

    def revoke_key(self, key_type: KeyType, version: int) -> KeyVersion:
        row = self.db.scalar(
            select(KeyVersion).where(KeyVersion.key_type == key_type, KeyVersion.version == version)
        )
        if not row:
            raise KeyManagementError("Key version not found")
        if row.status == KeyStatus.ACTIVE:
            raise KeyManagementError("Cannot revoke the active key; rotate first")
        row.status = KeyStatus.REVOKED
        row.retired_at = datetime.now(timezone.utc)
        self.db.flush()
        return row

    def rewrap_dek(self, packed_wrapped_dek: bytes, old_version: int, new_version: int) -> tuple[bytes, bytes]:
        dek = self.unwrap_document_key(packed_wrapped_dek, old_version)
        wrapped = wrap_dek(dek, self._master, new_version)
        packed = wrapped.wrap_nonce + wrapped.wrapped_dek
        return packed, wrapped.wrap_nonce
