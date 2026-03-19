"""Local filesystem storage implementation."""

from pathlib import Path
from typing import BinaryIO

from app.services.storage.base import StorageService

# Absolute path to data/jobs directory (v0.9.2 unified storage)
# __file__ is .../server/app/services/storage/local_storage.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "jobs"


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
            Relative path where file was saved (for storage in DB)
        """
        full_path = BASE_DIR / dest_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(src.read())

        # Return relative path only (not full path)
        return dest_path

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

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            path: Path relative to storage root

        Returns:
            True if file exists, False otherwise
        """
        full_path = BASE_DIR / path
        return full_path.exists()

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a URL for local file access.

        Issue #350: Artifact Pattern - lazy loading video results.

        For local storage, returns an internal API endpoint URL.
        The actual file serving is handled by the /v1/jobs/{id}/result endpoint.

        Args:
            path: Path relative to storage root
            expires_in: URL expiration time in seconds (ignored for local)

        Returns:
            API endpoint URL for fetching the file

        Raises:
            FileNotFoundError: If file does not exist
        """
        full_path = BASE_DIR / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        # For local storage, return the stream endpoint URL
        # The job_id is extracted from the path (e.g., video/output/{job_id}.json)
        # This is a simplified approach - the actual endpoint handles the fetch
        return f"/v1/jobs/result?path={path}"
