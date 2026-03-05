"""S3/MinIO storage implementation for Phase 11 (v0.11.0)."""

import tempfile
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.services.storage.base import StorageService


class S3StorageService(StorageService):
    """S3-compatible storage for shared job processing."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
    ) -> None:
        self.bucket = bucket_name
        self._bucket_verified = False  # Track bucket verification state (Issue #247)

        # FIX: Force Path Style addressing for IP-based MinIO URLs (Tailscale)
        # FIX: Force s3v4 signature for modern MinIO compatibility
        s3_config = Config(s3={"addressing_style": "path"}, signature_version="s3v4")

        # Build client arguments
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region_name,
            "config": s3_config,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self.client = boto3.client(**client_kwargs)
        # REMOVED: No longer calls head_bucket on init (Issue #247)

    def _ensure_bucket(self) -> None:
        """Lazily verify/create bucket on first use (Issue #247)."""
        if self._bucket_verified:
            return

        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            # Check for 404 (Not Found)
            error_code = str(e.response.get("Error", {}).get("Code", ""))
            if error_code == "404":
                self.client.create_bucket(Bucket=self.bucket)
            else:
                raise

        self._bucket_verified = True

    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        """Upload file-like object to S3."""
        self._ensure_bucket()  # Lazy bucket verification (Issue #247)
        src.seek(0)
        self.client.upload_fileobj(src, self.bucket, dest_path)
        return dest_path

    def load_file(self, path: str) -> Path:
        """Download file from S3 to a local temp file.
        Preserves suffix so OpenCV knows it is an .mp4.
        """
        self._ensure_bucket()  # Lazy bucket verification (Issue #247)

        suffix = Path(path).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = Path(tmp.name)

        try:
            self.client.download_fileobj(self.bucket, path, tmp)
            tmp.close()
            return tmp_path
        except ClientError as e:
            # Clean up temp file on error (Issue #246)
            tmp.close()
            if tmp_path.exists():
                tmp_path.unlink()

            error_code = str(e.response.get("Error", {}).get("Code", ""))
            # S3 returns '404' for HeadObject, 'NoSuchKey' for GetObject
            if error_code in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"File not found in S3: {path}") from e
            raise
        except Exception:
            # Clean up on any other exception (Issue #246)
            tmp.close()
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def delete_file(self, path: str) -> None:
        """Delete a stored file, if it exists."""
        self._ensure_bucket()  # Lazy bucket verification (Issue #247)
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            path: Path relative to storage root

        Returns:
            True if file exists, False otherwise
        """
        self._ensure_bucket()  # Lazy bucket verification (Issue #247)
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError as e:
            error_code = str(e.response.get("Error", {}).get("Code", ""))
            # S3 returns '404' for head_object, 'NoSuchKey' for get_object (Issue #248)
            if error_code in ("404", "NoSuchKey"):
                return False
            raise  # Re-raise permission/network/service errors
