"""Manifest caching service with TTL support.

Designed for FastAPI dependency injection and thread-safe operation.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ManifestCacheService:
    """Simple in-memory TTL-based cache for plugin manifests.

    Thread-safe cache designed for plugin manifest storage. Each cached manifest
    has an independent TTL (time-to-live). Expired entries are lazily removed
    on access.

    Typical usage:
        # Create service (60s TTL)
        cache = ManifestCacheService(ttl_seconds=60)

        # Store manifest
        cache.set("yolo-tracker", manifest_dict)

        # Retrieve manifest
        manifest = cache.get("yolo-tracker")

        # Use as FastAPI dependency
        @app.get("/manifest")
        def get_manifest(
            cache: ManifestCacheService = Depends(ManifestCacheService.dep),
        ):
            return cache.get("plugin-id")
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        """Initialize cache service.

        Args:
            ttl_seconds: Time-to-live for cached manifests (default 60 seconds).
                        Each entry's TTL is measured from when it was set.
        """
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Dict[str, Any], float]] = {}
        self._lock = threading.RLock()
        logger.debug(f"Initialized ManifestCacheService with TTL={ttl_seconds}s")

    def set(self, plugin_id: str, manifest: Dict[str, Any]) -> None:
        """Store manifest in cache with TTL.

        Args:
            plugin_id: Unique identifier for the plugin
            manifest: Manifest dictionary (must be JSON-serializable)

        Raises:
            TypeError: If manifest is not a dictionary
        """
        if not isinstance(manifest, dict):
            raise TypeError(f"manifest must be dict, got {type(manifest)}")

        with self._lock:
            self._cache[plugin_id] = (manifest, time.time())
            logger.debug(f"Cached manifest for '{plugin_id}' (TTL={self.ttl_seconds}s)")

    def get(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve manifest from cache if valid and not expired.

        Expired entries are removed from cache on access (lazy cleanup).

        Args:
            plugin_id: Plugin identifier

        Returns:
            Manifest dictionary if found and not expired, None otherwise
        """
        with self._lock:
            if plugin_id not in self._cache:
                return None

            manifest, created_at = self._cache[plugin_id]
            age = time.time() - created_at

            if age > self.ttl_seconds:
                # Expired, remove and return None
                del self._cache[plugin_id]
                logger.debug(
                    f"Cache expired for '{plugin_id}' (age={age:.1f}s, "
                    f"ttl={self.ttl_seconds}s)"
                )
                return None

            logger.debug(
                f"Cache hit for '{plugin_id}' (age={age:.1f}s, "
                f"ttl={self.ttl_seconds}s)"
            )
            return manifest

    def clear(self, plugin_id: Optional[str] = None) -> None:
        """Clear cache entry or entire cache.

        Args:
            plugin_id: Specific plugin to remove, or None to clear all entries
        """
        with self._lock:
            if plugin_id is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared entire manifest cache ({count} entries)")
            else:
                if plugin_id in self._cache:
                    del self._cache[plugin_id]
                    logger.info(f"Cleared cache entry for '{plugin_id}'")

    def _cache_size(self) -> int:
        """Get current number of cached entries (for testing).

        Returns:
            Number of entries currently in cache
        """
        with self._lock:
            return len(self._cache)

    @classmethod
    def dep(cls) -> "ManifestCacheService":
        """FastAPI dependency injection classmethod.

        Returns:
            New ManifestCacheService instance with default TTL (60s)

        Usage:
            @app.get("/manifest")
            async def get_manifest(
                cache: ManifestCacheService = Depends(ManifestCacheService.dep),
            ):
                return cache.get("plugin-id")
        """
        return cls(ttl_seconds=60)

    def __repr__(self) -> str:
        """String representation for debugging."""
        with self._lock:
            return (
                f"ManifestCacheService("
                f"entries={len(self._cache)}, ttl={self.ttl_seconds}s)"
            )
