import os
import shutil
from typing import Dict
from app.config import settings
from app.services.storage.base import StorageService

class LocalStorageService(StorageService):
    """Local filesystem implementation of the storage service."""

    def __init__(self):
        self.category_dirs: Dict[str, str] = {
            "raw_meshes": settings.STORAGE_RAW_DIR,
            "processed_meshes": settings.STORAGE_PROCESSED_DIR,
            "textures": settings.STORAGE_TEXTURES_DIR,
            "exports": settings.STORAGE_EXPORTS_DIR,
            "thumbnails": settings.STORAGE_THUMBNAILS_DIR,
        }
        for d in self.category_dirs.values():
            os.makedirs(d, exist_ok=True)

    def _resolve_dir(self, category: str) -> str:
        target_dir = self.category_dirs.get(category)
        if not target_dir:
            target_dir = os.path.join(settings.STORAGE_DIR, category)
            os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def save_file(self, category: str, filename: str, content: bytes) -> str:
        dir_path = self._resolve_dir(category)
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    def get_file_path(self, category: str, filename: str) -> str:
        dir_path = self._resolve_dir(category)
        return os.path.join(dir_path, filename)

    def get_file_bytes(self, category: str, filename: str) -> bytes:
        path = self.get_file_path(category, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            return f.read()

    def delete_file(self, category: str, filename: str) -> bool:
        path = self.get_file_path(category, filename)
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True
            except OSError:
                return False
        return False

    def exists(self, category: str, filename: str) -> bool:
        return os.path.exists(self.get_file_path(category, filename))

    def get_download_url(self, category: str, filename: str, expires_in: int = 3600) -> str:
        # Local storage serves through FastAPI endpoints
        return f"/api/assets/{filename}/download"

