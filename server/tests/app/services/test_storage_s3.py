"""Tests for S3StorageService and Storage Factory."""

import os
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

# Set dummy AWS credentials for all tests in this module before any boto3 client is created
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from app.services.storage.factory import get_storage_service
from app.services.storage.local_storage import LocalStorageService
from app.services.storage.s3_storage import S3StorageService


@pytest.fixture
def s3_env():
    """Set up environment variables for S3 storage."""
    with patch.dict(os.environ, {
        "FORGESYTE_STORAGE_BACKEND": "s3",
        "S3_BUCKET_NAME": "test-bucket",
        "S3_ENDPOINT_URL": "",  # Empty for moto
        "S3_ACCESS_KEY": "testing",
        "S3_SECRET_KEY": "testing",
    }):
        # Clear lru_cache for get_storage_service
        get_storage_service.cache_clear()
        yield
        get_storage_service.cache_clear()


@pytest.fixture
def local_env():
    """Set up environment variables for local storage."""
    with patch.dict(os.environ, {"FORGESYTE_STORAGE_BACKEND": "local"}):
        get_storage_service.cache_clear()
        yield
        get_storage_service.cache_clear()


@pytest.fixture
def s3_storage():
    """Fixture for S3StorageService with mocked S3."""
    with mock_aws():
        # Create bucket first so S3StorageService doesn't fail on head_bucket
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        
        storage = S3StorageService(
            bucket_name="test-bucket",
            endpoint_url=None, # None for moto to use default
            access_key="testing",
            secret_key="testing",
        )
        yield storage


class TestS3StorageService:
    def test_save_file(self, s3_storage):
        """Test saving a file to S3."""
        contents = b"test video data"
        src = BytesIO(contents)
        dest_path = "test_videos/video1.mp4"

        result = s3_storage.save_file(src, dest_path)

        assert result == dest_path
        assert s3_storage.file_exists(dest_path)

    def test_load_file(self, s3_storage):
        """Test loading a file from S3."""
        contents = b"test video data"
        src = BytesIO(contents)
        dest_path = "test_videos/video2.mp4"
        s3_storage.save_file(src, dest_path)

        local_path = s3_storage.load_file(dest_path)

        assert isinstance(local_path, Path)
        assert local_path.exists()
        assert local_path.suffix == ".mp4"
        assert local_path.read_bytes() == contents
        
        # Cleanup temp file
        if local_path.exists():
            local_path.unlink()

    def test_load_nonexistent_file(self, s3_storage):
        """Test loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            s3_storage.load_file("nonexistent.mp4")

    def test_delete_file(self, s3_storage):
        """Test deleting a file from S3."""
        contents = b"test data"
        src = BytesIO(contents)
        dest_path = "delete_me.txt"
        s3_storage.save_file(src, dest_path)
        assert s3_storage.file_exists(dest_path)

        s3_storage.delete_file(dest_path)

        assert not s3_storage.file_exists(dest_path)

    def test_file_exists(self, s3_storage):
        """Test file_exists method."""
        contents = b"test data"
        src = BytesIO(contents)
        dest_path = "exists.txt"
        
        assert not s3_storage.file_exists(dest_path)
        
        s3_storage.save_file(src, dest_path)
        
        assert s3_storage.file_exists(dest_path)


class TestStorageFactory:
    def test_get_storage_service_local(self, local_env):
        """Test factory returns LocalStorageService by default or when configured."""
        storage = get_storage_service()
        assert isinstance(storage, LocalStorageService)

    @mock_aws
    def test_get_storage_service_s3(self, s3_env):
        """Test factory returns S3StorageService when configured."""
        # Moto needs bucket to exist
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        
        storage = get_storage_service()
        assert isinstance(storage, S3StorageService)
        assert storage.bucket == "test-bucket"
