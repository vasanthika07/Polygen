from abc import ABC, abstractmethod
from typing import Optional

class StorageService(ABC):
    """Abstract interface defining required storage operations for 3D assets and textures."""

    @abstractmethod
    def save_file(self, category: str, filename: str, content: bytes) -> str:
        """Saves file content under the designated category and returns storage reference/path."""
        pass

    @abstractmethod
    def get_file_path(self, category: str, filename: str) -> str:
        """Returns the local or absolute path to the file."""
        pass

    @abstractmethod
    def get_file_bytes(self, category: str, filename: str) -> bytes:
        """Reads and returns file bytes."""
        pass

    @abstractmethod
    def delete_file(self, category: str, filename: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    def exists(self, category: str, filename: str) -> bool:
        """Checks if file exists in storage."""
        pass

    @abstractmethod
    def get_download_url(self, category: str, filename: str, expires_in: int = 3600) -> str:
        """Returns an authorized direct download URL or route reference."""
        pass

