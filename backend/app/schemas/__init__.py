from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    encryption_algorithm: str
    dek_key_version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=256)


class SearchResponse(BaseModel):
    keyword_normalized_length: int
    result_count: int
    documents: list[DocumentResponse]
    note: str = (
        "Search used an HMAC-SHA-256 token; plaintext keyword was not stored in the index. "
        "Deterministic tokens leak equality of repeated queries."
    )


class KeyStatusResponse(BaseModel):
    keys: list[dict]


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    success: bool
    created_at: datetime
    metadata_json: dict | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
