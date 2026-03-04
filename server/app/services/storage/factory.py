"""Storage service factory for dependency injection."""

import os
from functools import lru_cache

from app.services.storage.base import StorageService
from app.services.storage.local_storage import LocalStorageService
from app.services.storage.s3_storage import S3StorageService

@lru_cache()
def get_storage_service() -> StorageService:
    """Returns the configured storage backend (Singleton)."""
    backend = os.getenv("FORGESYTE_STORAGE_BACKEND", "local").lower()

    if backend == "s3":
        return S3StorageService(
            bucket_name=os.getenv("S3_BUCKET_NAME", "forgesyte-jobs"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL", ""),
            access_key=os.getenv("S3_ACCESS_KEY", ""),
            secret_key=os.getenv("S3_SECRET_KEY", "")
        )

    return LocalStorageService()
