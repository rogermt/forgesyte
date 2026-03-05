"""Tests for S3StorageService and Storage Factory."""

import os
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

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
from app.settings import AppSettings


@pytest.fixture
def s3_env():
    """Set up environment variables for S3 storage."""
    with patch.dict(
        os.environ,
        {
            "FORGESYTE_STORAGE_BACKEND": "s3",
            "S3_BUCKET_NAME": "test-bucket",
            "S3_ENDPOINT_URL": "",  # Empty for moto
            "S3_ACCESS_KEY": "testing",
            "S3_SECRET_KEY": "testing",
        },
    ):
        # Create fresh AppSettings instance to pick up env vars
        yield AppSettings()


@pytest.fixture
def local_env():
    """Set up environment variables for local storage."""
    with patch.dict(os.environ, {"FORGESYTE_STORAGE_BACKEND": "local"}):
        # Create fresh AppSettings instance to pick up env vars
        yield AppSettings()


@pytest.fixture
def s3_storage():
    """Fixture for S3StorageService with mocked S3."""
    with mock_aws():
        # Create bucket first so S3StorageService doesn't fail on head_bucket
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")

        storage = S3StorageService(
            bucket_name="test-bucket",
            endpoint_url=None,  # None for moto to use default
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

    def test_load_file_nosuchkey_error(self, s3_storage):
        """Test that NoSuchKey also raises FileNotFoundError (for MinIO compatibility)."""
        from botocore.exceptions import ClientError

        # Mock download_fileobj to raise NoSuchKey
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        }
        with patch.object(
            s3_storage.client,
            "download_fileobj",
            side_effect=ClientError(error_response, "GetObject"),
        ):
            with pytest.raises(FileNotFoundError) as excinfo:
                s3_storage.load_file("missing.mp4")
            assert "File not found in S3" in str(excinfo.value)

    def test_s3_client_config(self, s3_storage):
        """Test that S3 client is configured with path-style addressing and s3v4."""
        # This test is expected to fail initially as these are not yet set
        config = s3_storage.client.meta.config
        assert config.s3.get("addressing_style") == "path"
        assert config.signature_version == "s3v4"

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
        storage = get_storage_service(local_env)
        assert isinstance(storage, LocalStorageService)

    @mock_aws
    def test_get_storage_service_s3(self, s3_env):
        """Test factory returns S3StorageService when configured."""
        # Moto needs bucket to exist
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")

        storage = get_storage_service(s3_env)
        assert isinstance(storage, S3StorageService)
        assert storage.bucket == "test-bucket"


class TestS3TempFileCleanup:
    """Tests for temp file cleanup on failed downloads (Issue #246)."""

    def test_temp_file_cleaned_on_network_error(self, s3_storage):
        """Test that temp file is cleaned up when download fails with network error."""
        from botocore.exceptions import ClientError

        # Mock a network error (not 404/NoSuchKey)
        error_response = {
            "Error": {
                "Code": "ConnectionTimeout",
                "Message": "Connection timed out",
            }
        }

        temp_files_before = set(Path("/tmp").glob("tmp*.mp4"))

        with patch.object(
            s3_storage.client,
            "download_fileobj",
            side_effect=ClientError(error_response, "GetObject"),
        ):
            with pytest.raises(ClientError):
                s3_storage.load_file("test.mp4")

        temp_files_after = set(Path("/tmp").glob("tmp*.mp4"))

        # No new temp files should exist
        assert temp_files_after == temp_files_before

    def test_temp_file_cleaned_on_generic_exception(self, s3_storage):
        """Test that temp file is cleaned up on any exception."""
        temp_files_before = set(Path("/tmp").glob("tmp*.mp4"))

        with patch.object(
            s3_storage.client,
            "download_fileobj",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with pytest.raises(RuntimeError):
                s3_storage.load_file("test.mp4")

        temp_files_after = set(Path("/tmp").glob("tmp*.mp4"))
        assert temp_files_after == temp_files_before


class TestS3LazyBucketInit:
    """Tests for lazy bucket initialization (Issue #247)."""

    def test_init_does_not_call_head_bucket(self):
        """Test that __init__ does not perform network I/O."""
        with patch("boto3.client") as mock_boto_client:
            mock_client = MagicMock()
            mock_boto_client.return_value = mock_client

            # Construct S3StorageService
            S3StorageService(
                bucket_name="test-bucket",
                endpoint_url="http://localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
            )

            # head_bucket should NOT have been called during __init__
            mock_client.head_bucket.assert_not_called()
            mock_client.create_bucket.assert_not_called()

    def test_bucket_created_on_first_save(self):
        """Test that bucket is verified/created on first operation."""
        from botocore.exceptions import ClientError

        with patch("boto3.client") as mock_boto_client:
            mock_client = MagicMock()
            mock_boto_client.return_value = mock_client

            # Simulate bucket not existing
            error_response = {"Error": {"Code": "404"}}
            mock_client.head_bucket.side_effect = ClientError(
                error_response, "HeadBucket"
            )

            storage = S3StorageService(
                bucket_name="test-bucket",
                endpoint_url="http://localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
            )

            # First save should trigger bucket verification
            storage.save_file(BytesIO(b"test"), "test.txt")

            # Now head_bucket should have been called
            mock_client.head_bucket.assert_called_once()
            mock_client.create_bucket.assert_called_once_with(Bucket="test-bucket")

    def test_bucket_not_reverified_after_first_success(self):
        """Test that bucket is only verified once per service instance."""
        with patch("boto3.client") as mock_boto_client:
            mock_client = MagicMock()
            mock_boto_client.return_value = mock_client

            storage = S3StorageService(
                bucket_name="test-bucket",
                endpoint_url="http://localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
            )

            # Multiple saves
            storage.save_file(BytesIO(b"test1"), "test1.txt")
            storage.save_file(BytesIO(b"test2"), "test2.txt")
            storage.save_file(BytesIO(b"test3"), "test3.txt")

            # head_bucket should only be called once
            mock_client.head_bucket.assert_called_once()


class TestFileExistsErrorHandling:
    """Tests for file_exists error handling (Issue #248)."""

    def test_file_exists_returns_false_for_404(self, s3_storage):
        """Test that file_exists returns False for 404 error."""
        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "404", "Message": "Not Found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        }

        with patch.object(
            s3_storage.client,
            "head_object",
            side_effect=ClientError(error_response, "HeadObject"),
        ):
            assert s3_storage.file_exists("nonexistent.txt") is False

    def test_file_exists_returns_false_for_nosuchkey(self, s3_storage):
        """Test that file_exists returns False for NoSuchKey error."""
        from botocore.exceptions import ClientError

        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist",
            },
            "ResponseMetadata": {"HTTPStatusCode": 404},
        }

        with patch.object(
            s3_storage.client,
            "head_object",
            side_effect=ClientError(error_response, "HeadObject"),
        ):
            assert s3_storage.file_exists("nonexistent.txt") is False

    def test_file_exists_reraises_permission_error(self, s3_storage):
        """Test that file_exists re-raises permission denied errors."""
        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "403", "Message": "Forbidden"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        }

        with patch.object(
            s3_storage.client,
            "head_object",
            side_effect=ClientError(error_response, "HeadObject"),
        ):
            with pytest.raises(ClientError):
                s3_storage.file_exists("protected.txt")

    def test_file_exists_reraises_network_error(self, s3_storage):
        """Test that file_exists re-raises network/service errors."""
        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"},
            "ResponseMetadata": {"HTTPStatusCode": 503},
        }

        with patch.object(
            s3_storage.client,
            "head_object",
            side_effect=ClientError(error_response, "HeadObject"),
        ):
            with pytest.raises(ClientError):
                s3_storage.file_exists("any.txt")
