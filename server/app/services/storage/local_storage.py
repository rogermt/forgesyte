"""Local filesystem storage implementation."""

from pathlib import Path
from typing import BinaryIO

from app.services.storage.base import StorageService

BASE_DIR = Path("./data/video_jobs")


class LocalStorageService(StorageService):
    """Local filesystem storage for Phase 16 job processing."""

    def __init__(self) -> None:
        """Initialize local storage, creating base directory if needed."""
        BASE_DIR.mkdir(parents=True, exist_ok=True)

    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        """Save a file-like object to local filesystem.

        Args:
            src: File-like object (BinaryIO) to save
            dest_path: Destination path relative to storage root

        Returns:
            Full path where file was saved
        """
        full_path = BASE_DIR / dest_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(src.read())

        return str(full_path)

    def load_file(self, path: str) -> Path:
        """Return a local filesystem path to the stored file.

        Args:
            path: Path relative to storage root

        Returns:
            Local filesystem Path object

        Raises:
            FileNotFoundError: If file does not exist
        """
        full_path = BASE_DIR / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path

    def delete_file(self, path: str) -> None:
        """Delete a stored file, if it exists.

        Args:
            path: Path relative to storage root
        """
        full_path = BASE_DIR / path
        if full_path.exists():
            full_path.unlink()
