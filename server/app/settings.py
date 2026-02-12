"""Phase 14 Settings - Configuration layer for ForgeSyte server."""

import os
from functools import lru_cache
from typing import List


class Settings:
    """Configuration settings for the ForgeSyte server.

    This class provides a centralized configuration system that reads from
    environment variables and provides safe defaults for local development.
    """

    # -----------------------------
    # Core API configuration
    # -----------------------------
    api_prefix: str = "/v1"

    # -----------------------------
    # CORS configuration
    # -----------------------------
    cors_origins_raw: str = os.getenv("FORGESYTE_CORS_ORIGINS", "")
    cors_origins: List[str] = []

    # -----------------------------
    # Logging configuration
    # -----------------------------
    log_level: str = os.getenv("FORGESYTE_LOG_LEVEL", "INFO")
    log_file: str = os.getenv("FORGESYTE_LOG_FILE", "forgesyte.log")

    # -----------------------------
    # WebSocket configuration
    # -----------------------------
    ws_enabled: bool = os.getenv("FORGESYTE_WS_ENABLED", "true").lower() == "true"

    def __init__(self):
        """Initialize settings and parse CORS origins."""
        if self.cors_origins_raw:
            self.cors_origins = [
                origin.strip()
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]
        else:
            # Safe defaults for local dev
            self.cors_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached Settings instance.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()
