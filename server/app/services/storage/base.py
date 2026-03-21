"""Abstract storage service interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageService(ABC):
    """Abstract storage interface for Phase 16 job processing."""

    @abstractmethod
    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        """Save a file-like object to storage.

        Args:
            src: File-like object (BinaryIO) to save
            dest_path: Destination path relative to storage root

        Returns:
            Full path where file was saved
        """
        raise NotImplementedError

    @abstractmethod
    def load_file(self, path: str) -> Path:
        """Return a local filesystem path to the stored file.

        Args:
            path: Path relative to storage root

        Returns:
            Local filesystem Path object

        Raises:
            FileNotFoundError: If file does not exist
        """
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete a stored file, if it exists.

        Args:
            path: Path relative to storage root
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            path: Path relative to storage root

        Returns:
            True if file exists, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a signed URL for direct access to a stored file.

        Issue #350: Artifact Pattern - lazy loading video results.

        Args:
            path: Path relative to storage root
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed URL that can be used to fetch the file directly

        Raises:
            FileNotFoundError: If file does not exist
        """
        raise NotImplementedError
