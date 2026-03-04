"""S3/MinIO storage implementation for Phase 11 (v0.11.0)."""

import os
import tempfile
from pathlib import Path
from typing import BinaryIO

import boto3
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
        
        # Build client arguments
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region_name,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            
        self.client = boto3.client(**client_kwargs)

        # Ensure bucket exists on startup
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            # 404: bucket doesn't exist. 
            # 403: Forbidden, but often means bucket exists or we don't have head permission.
            # In moto, if bucket doesn't exist, it might throw 404.
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", 404):
                self.client.create_bucket(Bucket=self.bucket)
            elif error_code in ("403", 403):
                # If 403, we might not have permission to head but maybe can use it?
                # For this implementation, we assume we want to create it if it doesn't exist.
                # But head_bucket returning 403 usually means it exists but we can't head it.
                pass
            else:
                raise

    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        """Upload file-like object to S3."""
        src.seek(0)
        self.client.upload_fileobj(src, self.bucket, dest_path)
        return dest_path

    def load_file(self, path: str) -> Path:
        """Download file from S3 to a local temp file.
        Preserves suffix so OpenCV knows it is an .mp4.
        """
        try:
            suffix = Path(path).suffix
            # Use delete=False so we can return the Path object to the file after closing.
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            
            self.client.download_fileobj(self.bucket, path, tmp)
            tmp.close()
            
            return Path(tmp.name)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", 404):
                raise FileNotFoundError(f"File not found in S3: {path}") from e
            raise

    def delete_file(self, path: str) -> None:
        """Delete a stored file, if it exists."""
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False
