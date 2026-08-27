from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg2://securekw:securekw@localhost:5432/secure_keyword",
        alias="DATABASE_URL",
    )
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    master_key: str = Field(alias="MASTER_KEY")

    storage_provider: str = Field(default="s3", alias="STORAGE_PROVIDER")
    minio_endpoint: str = Field(default="http://localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="secure-documents", alias="MINIO_BUCKET")
    minio_region: str = Field(default="us-east-1", alias="MINIO_REGION")
    local_storage_path: str = Field(default="./data/storage", alias="LOCAL_STORAGE_PATH")

    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    allowed_content_types: str = Field(
        default="text/plain,text/markdown,application/pdf,application/json",
        alias="ALLOWED_CONTENT_TYPES",
    )

    @field_validator("jwt_secret", "master_key")
    @classmethod
    def secrets_not_placeholders(cls, v: str) -> str:
        if not v or v.startswith("CHANGE_ME"):
            raise ValueError("Secret must be set to a non-placeholder value")
        if len(v) < 32:
            raise ValueError("Secret must be at least 32 characters")
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_content_type_list(self) -> List[str]:
        return [t.strip() for t in self.allowed_content_types.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
