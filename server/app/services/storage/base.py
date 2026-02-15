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
