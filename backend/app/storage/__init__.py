from functools import lru_cache

from app.config import get_settings
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider
from app.storage.s3 import S3CompatibleStorageProvider


@lru_cache
def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.storage_provider.lower() == "local":
        return LocalStorageProvider(settings.local_storage_path)
    return S3CompatibleStorageProvider(
        endpoint_url=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        region=settings.minio_region,
    )
