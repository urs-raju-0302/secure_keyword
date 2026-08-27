from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import client_ip, get_current_user, get_search_service
from app.db import get_db
from app.schemas import DocumentResponse, SearchRequest, SearchResponse
from app.services.keyword_service import normalize_keyword
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search(
    body: SearchRequest,
    request: Request,
    user=Depends(get_current_user),
    svc: SearchService = Depends(get_search_service),
    db: Session = Depends(get_db),
):
    docs = svc.search(user, body.keyword, ip=client_ip(request))
    db.commit()
    normalized = normalize_keyword(body.keyword)
    return SearchResponse(
        keyword_normalized_length=len(normalized),
        result_count=len(docs),
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )
