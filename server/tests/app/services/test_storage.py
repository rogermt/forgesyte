"""Tests for StorageService implementations."""

from io import BytesIO
from pathlib import Path

import pytest

from app.services.storage.local_storage import LocalStorageService


@pytest.mark.unit
def test_local_storage_save_file():
    """Test saving a file to local storage."""
    storage = LocalStorageService()
    contents = b"test video data"
    src = BytesIO(contents)

    result = storage.save_file(src, "test_videos/video1.mp4")

    assert result is not None
    assert "video1.mp4" in result
    assert Path(result).exists()
    assert Path(result).read_bytes() == contents


@pytest.mark.unit
def test_local_storage_load_file():
    """Test loading a file from local storage."""
    storage = LocalStorageService()
    contents = b"test video data"
    src = BytesIO(contents)
    storage.save_file(src, "test_videos/video2.mp4")

    path = storage.load_file("test_videos/video2.mp4")

    assert path.exists()
    assert path.read_bytes() == contents


@pytest.mark.unit
def test_local_storage_load_nonexistent_file():
    """Test loading a nonexistent file raises error."""
    storage = LocalStorageService()

    with pytest.raises(FileNotFoundError):
        storage.load_file("nonexistent/video.mp4")


@pytest.mark.unit
def test_local_storage_delete_file():
    """Test deleting a file from local storage."""
    storage = LocalStorageService()
    contents = b"test video data"
    src = BytesIO(contents)
    saved_path = storage.save_file(src, "test_videos/video3.mp4")

    storage.delete_file("test_videos/video3.mp4")

    assert not Path(saved_path).exists()


@pytest.mark.unit
def test_local_storage_delete_nonexistent_file():
    """Test deleting a nonexistent file doesn't raise error."""
    storage = LocalStorageService()

    # Should not raise
    storage.delete_file("nonexistent/video.mp4")


@pytest.mark.unit
def test_local_storage_creates_directories():
    """Test that local storage creates parent directories."""
    storage = LocalStorageService()
    contents = b"test video data"
    src = BytesIO(contents)

    result = storage.save_file(src, "deeply/nested/path/video.mp4")

    assert Path(result).exists()
    assert Path(result).parent.exists()
