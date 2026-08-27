from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import client_ip, get_current_user, get_document_service
from app.db import get_db
from app.schemas import DocumentResponse, MessageResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    svc: DocumentService = Depends(get_document_service),
):
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    doc = svc.upload(
        user,
        filename=file.filename or "document.txt",
        content_type=content_type,
        data=data,
        ip=client_ip(request),
    )
    return doc


@router.get("", response_model=list[DocumentResponse])
def list_documents(user=Depends(get_current_user), svc: DocumentService = Depends(get_document_service)):
    return svc.list_documents(user)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    user=Depends(get_current_user),
    svc: DocumentService = Depends(get_document_service),
):
    return svc.get_document(user, document_id)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: UUID,
    request: Request,
    user=Depends(get_current_user),
    svc: DocumentService = Depends(get_document_service),
):
    svc.delete(user, document_id, ip=client_ip(request))
    return MessageResponse(message="Deleted")


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    request: Request,
    user=Depends(get_current_user),
    svc: DocumentService = Depends(get_document_service),
    db: Session = Depends(get_db),
):
    doc, plaintext = svc.download(user, document_id, ip=client_ip(request))
    db.commit()
    return Response(
        content=plaintext,
        media_type=doc.content_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )
