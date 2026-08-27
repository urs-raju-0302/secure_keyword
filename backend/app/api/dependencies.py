from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import User, UserRole
from app.security.jwt import TokenError, decode_access_token
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.encryption_service import EncryptionService
from app.services.key_management_service import KeyManagementService
from app.services.key_rotation_service import KeyRotationService
from app.services.search_service import SearchService
from app.storage import get_storage_provider

bearer_scheme = HTTPBearer(auto_error=False)


def get_audit(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


def get_kms(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> KeyManagementService:
    kms = KeyManagementService(db, settings)
    kms.ensure_bootstrap_keys()
    return kms


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    audit: AuditService = Depends(get_audit),
) -> AuthService:
    return AuthService(db, settings, audit)


def get_document_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    kms: KeyManagementService = Depends(get_kms),
    audit: AuditService = Depends(get_audit),
) -> DocumentService:
    return DocumentService(db, settings, kms, EncryptionService(), get_storage_provider(), audit)


def get_search_service(
    db: Session = Depends(get_db),
    kms: KeyManagementService = Depends(get_kms),
    audit: AuditService = Depends(get_audit),
) -> SearchService:
    return SearchService(db, kms, audit)


def get_rotation_service(
    db: Session = Depends(get_db),
    kms: KeyManagementService = Depends(get_kms),
    audit: AuditService = Depends(get_audit),
) -> KeyRotationService:
    return KeyRotationService(db, kms, EncryptionService(), get_storage_provider(), audit)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    audit: AuditService = Depends(get_audit),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (TokenError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        audit.record_event(action="AUTHORIZATION_FAILURE", success=False, metadata={"reason": "inactive_or_missing"})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
    return user


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
