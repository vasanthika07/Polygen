from app.config import settings
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorageService

_storage_instance = None

def get_storage_service() -> StorageService:
    """Returns the singleton instance of the configured storage service."""
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_BACKEND == "s3":
            from app.services.storage.s3 import S3StorageService
            _storage_instance = S3StorageService()
        else:
            _storage_instance = LocalStorageService()
    return _storage_instance

storage_service = get_storage_service()

__all__ = ["StorageService", "LocalStorageService", "get_storage_service", "storage_service"]

