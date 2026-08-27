from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    client_ip,
    get_current_user,
    get_kms,
    get_rotation_service,
    require_admin,
)
from app.db import get_db
from app.models import AuditLog, KeyType
from app.schemas import AuditLogResponse, KeyStatusResponse, MessageResponse
from app.services.key_management_service import KeyManagementError, KeyManagementService
from app.services.key_rotation_service import KeyRotationService
from fastapi import HTTPException, status

router = APIRouter(prefix="/keys", tags=["Key Management"])


@router.get("/status", response_model=KeyStatusResponse)
def key_status(
    _admin=Depends(require_admin),
    kms: KeyManagementService = Depends(get_kms),
):
    return KeyStatusResponse(keys=kms.get_status())


@router.post("/rotate/search")
def rotate_search(
    request: Request,
    admin=Depends(require_admin),
    rotation: KeyRotationService = Depends(get_rotation_service),
):
    result = rotation.rotate_search_and_reindex(admin, ip=client_ip(request))
    return result


@router.post("/rotate/master")
def rotate_master(
    request: Request,
    admin=Depends(require_admin),
    rotation: KeyRotationService = Depends(get_rotation_service),
):
    result = rotation.rotate_master_and_rewrap(admin, ip=client_ip(request))
    return result


@router.post("/reindex")
def reindex(
    request: Request,
    admin=Depends(require_admin),
    rotation: KeyRotationService = Depends(get_rotation_service),
):
    return rotation.reindex_only(admin, ip=client_ip(request))


@router.post("/revoke/{key_type}/{version}", response_model=MessageResponse)
def revoke(
    key_type: str,
    version: int,
    request: Request,
    admin=Depends(require_admin),
    kms: KeyManagementService = Depends(get_kms),
    db: Session = Depends(get_db),
):
    try:
        kt = KeyType(key_type.upper())
        kms.revoke_key(kt, version)
        db.commit()
    except (ValueError, KeyManagementError) as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return MessageResponse(message="Key version revoked")


audit_router = APIRouter(prefix="/audit", tags=["Audit"])


@audit_router.get("", response_model=list[AuditLogResponse])
def list_audit(
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    limit = min(max(limit, 1), 500)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return list(rows)


@audit_router.get("/me", response_model=list[AuditLogResponse])
def my_audit(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    limit = min(max(limit, 1), 200)
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return list(rows)
