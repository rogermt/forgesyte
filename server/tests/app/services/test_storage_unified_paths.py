"""Test unified storage paths for v0.9.2.

Tests that:
1. LocalStorageService uses data/jobs as BASE_DIR
2. Storage paths are relative under data/jobs/
3. Image jobs use image/input/ and image/output/
4. Video jobs use video/input/ and video/output/
"""

from io import BytesIO
from pathlib import Path

import pytest

from app.services.storage.local_storage import LocalStorageService


def test_storage_base_dir_is_jobs():
    """Test that BASE_DIR points to data/jobs."""
    from app.services.storage.local_storage import BASE_DIR
    
    assert BASE_DIR.name == "jobs"
    assert BASE_DIR.parent.name == "data"


def test_storage_save_and_load_relative_path():
    """Test that save_file returns relative path."""
    storage = LocalStorageService()

    # Save a file
    test_data = b"test data"
    relative_path = storage.save_file(BytesIO(test_data), "test/file.txt")

    # Verify returned path is relative
    assert not Path(relative_path).is_absolute()
    assert relative_path == "test/file.txt"

    # Verify file can be loaded
    loaded_path = storage.load_file(relative_path)
    assert loaded_path.exists()

    # Verify content
    with open(loaded_path, "rb") as f:
        content = f.read()
    assert content == test_data


def test_storage_image_paths():
    """Test that image jobs use image/ subdirectory."""
    storage = LocalStorageService()

    # Save an image input file
    image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    input_path = storage.save_file(BytesIO(image_data), "image/input/test.png")

    assert input_path == "image/input/test.png"
    assert not Path(input_path).is_absolute()

    # Verify file exists under data/jobs/image/input/
    loaded_path = storage.load_file(input_path)
    assert "image/input" in str(loaded_path)
    assert loaded_path.exists()

    # Save an image output file
    output_data = b'{"results": {}}'
    output_path = storage.save_file(BytesIO(output_data), "image/output/test.json")

    assert output_path == "image/output/test.json"
    assert "image/output" in str(storage.load_file(output_path))


def test_storage_video_paths():
    """Test that video jobs use video/ subdirectory."""
    storage = LocalStorageService()

    # Save a video input file
    video_data = b"ftyp" + b"\x00" * 100
    input_path = storage.save_file(BytesIO(video_data), "video/input/test.mp4")

    assert input_path == "video/input/test.mp4"
    assert not Path(input_path).is_absolute()

    # Verify file exists under data/jobs/video/input/
    loaded_path = storage.load_file(input_path)
    assert "video/input" in str(loaded_path)
    assert loaded_path.exists()

    # Save a video output file
    output_data = b'{"results": {}}'
    output_path = storage.save_file(BytesIO(output_data), "video/output/test.json")

    assert output_path == "video/output/test.json"
    assert "video/output" in str(storage.load_file(output_path))


def test_storage_creates_subdirectories():
    """Test that storage creates subdirectories as needed."""
    storage = LocalStorageService()

    # Save to a deeply nested path
    test_data = b"test data"
    nested_path = "image/input/deeply/nested/file.txt"
    relative_path = storage.save_file(BytesIO(test_data), nested_path)

    assert relative_path == nested_path

    # Verify all directories were created
    loaded_path = storage.load_file(nested_path)
    assert loaded_path.exists()
    assert loaded_path.parent.name == "nested"
    assert loaded_path.parent.parent.name == "deeply"


def test_storage_delete_file():
    """Test that delete_file removes files."""
    storage = LocalStorageService()

    # Save a file
    test_data = b"test data"
    relative_path = storage.save_file(BytesIO(test_data), "test/delete_me.txt")

    # Verify file exists
    loaded_path = storage.load_file(relative_path)
    assert loaded_path.exists()

    # Delete the file
    storage.delete_file(relative_path)

    # Verify file no longer exists
    with pytest.raises(FileNotFoundError):
        storage.load_file(relative_path)


def test_storage_delete_nonexistent_file():
    """Test that delete_file handles nonexistent files gracefully."""
    storage = LocalStorageService()

    # Try to delete a file that doesn't exist
    # Should not raise an exception
    storage.delete_file("nonexistent/file.txt")


def test_storage_paths_are_relative():
    """Test that all storage operations use relative paths."""
    storage = LocalStorageService()

    # Save multiple files
    paths = [
        "image/input/test1.png",
        "image/output/test1.json",
        "video/input/test1.mp4",
        "video/output/test1.json",
    ]

    for path in paths:
        test_data = b"test data"
        relative_path = storage.save_file(BytesIO(test_data), path)

        # Verify path is relative
        assert not Path(relative_path).is_absolute()
        assert relative_path == path

        # Verify can be loaded
        loaded_path = storage.load_file(relative_path)
        assert loaded_path.exists()