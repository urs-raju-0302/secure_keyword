from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import RefreshToken, User, UserRole
from app.security.jwt import create_access_token
from app.security.password import hash_password, needs_rehash, verify_password
from app.services.audit_service import AuditService


class AuthError(Exception):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)
        self.message = message


class AuthService:
    def __init__(self, db: Session, settings: Settings, audit: AuditService) -> None:
        self.db = db
        self.settings = settings
        self.audit = audit

    def register(self, email: str, password: str, *, ip: str | None = None) -> User:
        existing = self.db.scalar(select(User).where(User.email == email.lower()))
        if existing:
            self.audit.record_event(action="REGISTER_FAILURE", success=False, ip=ip, metadata={"reason": "email_taken"})
            raise AuthError("Registration failed")
        if len(password) < 10:
            raise AuthError("Password must be at least 10 characters")
        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()
        self.audit.record_event(
            action="REGISTER_SUCCESS",
            success=True,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip=ip,
        )
        return user

    def login(self, email: str, password: str, *, ip: str | None = None) -> tuple[User, str, str]:
        user = self.db.scalar(select(User).where(User.email == email.lower().strip()))
        # Constant-ish failure message — do not reveal whether email exists
        if not user or not user.is_active or not verify_password(user.password_hash, password):
            self.audit.record_event(action="LOGIN_FAILURE", success=False, ip=ip, metadata={"email_domain": email.split("@")[-1] if "@" in email else None})
            raise AuthError("Invalid credentials")
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        access = create_access_token(user_id=user.id, role=user.role.value, email=user.email)
        refresh = self._issue_refresh_token(user.id)
        self.audit.record_event(
            action="LOGIN_SUCCESS",
            success=True,
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip=ip,
        )
        return user, access, refresh

    def _hash_refresh(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _issue_refresh_token(self, user_id: UUID) -> str:
        raw = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days)
        row = RefreshToken(
            user_id=user_id,
            token_hash=self._hash_refresh(raw),
            expires_at=expires,
            revoked=False,
        )
        self.db.add(row)
        self.db.flush()
        return raw

    def refresh(self, refresh_token: str, *, ip: str | None = None) -> tuple[str, str]:
        token_hash = self._hash_refresh(refresh_token)
        row = self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        now = datetime.now(timezone.utc)
        expires_at = row.expires_at if row else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not row or row.revoked or (expires_at is not None and expires_at < now):
            self.audit.record_event(action="TOKEN_REFRESH_FAILURE", success=False, ip=ip)
            raise AuthError("Invalid refresh token")
        user = self.db.get(User, row.user_id)
        if not user or not user.is_active:
            raise AuthError("Invalid refresh token")
        # Rotate: revoke old, issue new
        row.revoked = True
        new_refresh = self._issue_refresh_token(user.id)
        access = create_access_token(user_id=user.id, role=user.role.value, email=user.email)
        self.audit.record_event(
            action="TOKEN_REFRESH_SUCCESS",
            success=True,
            user_id=user.id,
            ip=ip,
        )
        return access, new_refresh

    def logout(self, refresh_token: str | None, user_id: UUID | None, *, ip: str | None = None) -> None:
        if refresh_token:
            token_hash = self._hash_refresh(refresh_token)
            row = self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
            if row:
                row.revoked = True
        self.audit.record_event(action="LOGOUT", success=True, user_id=user_id, ip=ip)

    def get_user(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)
