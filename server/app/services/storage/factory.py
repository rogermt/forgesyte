"""Storage service factory for dependency injection."""

import logging
from typing import TYPE_CHECKING

from app.services.storage.base import StorageService
from app.services.storage.local_storage import LocalStorageService
from app.services.storage.s3_storage import S3StorageService

if TYPE_CHECKING:
    from app.settings import AppSettings

logger = logging.getLogger(__name__)

# Cache to track if we've already logged initialization
_logged_backends = set()


def get_storage_service(settings: "AppSettings") -> StorageService:
    """Returns the configured storage backend based on settings.

    Args:
        settings: AppSettings instance with storage configuration

    Returns:
        StorageService instance (S3 or Local)

    Note:
        Logs the backend selection only on first call to avoid log spam.
    """
    backend = settings.storage_backend.lower()

    # Log only once per backend type
    if backend not in _logged_backends:
        _logged_backends.add(backend)

        if backend == "s3":
            endpoint = settings.s3_endpoint_url or None
            logger.info(f"Storage Backend: S3 (MinIO) enabled at {endpoint}")
        else:
            logger.info("Storage Backend: Local Filesystem")

    if backend == "s3":
        # Handle empty string by converting to None
        endpoint = settings.s3_endpoint_url or None

        return S3StorageService(
            bucket_name=settings.s3_bucket_name,
            endpoint_url=endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
        )

    return LocalStorageService()
