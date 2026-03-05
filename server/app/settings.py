"""Application configuration and settings management.

This module defines the AppSettings class for loading configuration from
environment variables and .env files. It's kept separate from main.py
to avoid circular imports.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    title: str = "ForgeSyte"
    description: str = (
        "ForgeSyte: A modular AI-vision MCP server engineered for developers"
    )
    version: str = "0.1.0"
    api_prefix: str = "/v1"

    # Storage backend configuration
    storage_backend: str = Field(default="local", alias="FORGESYTE_STORAGE_BACKEND")
    s3_endpoint_url: str = Field(default="", alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(default="", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="", alias="S3_SECRET_KEY")
    s3_bucket_name: str = Field(default="forgesyte-jobs", alias="S3_BUCKET_NAME")

    # CORS configuration
    cors_origins: List[str] = ["*"]
    cors_origins_raw: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", populate_by_name=True
    )


# Global settings instance
settings = AppSettings()
