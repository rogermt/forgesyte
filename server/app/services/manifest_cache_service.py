"""Manifest caching service with TTL support."""

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ManifestCacheEntry:
    """Single cached manifest with TTL."""

    def __init__(self, manifest: Dict[str, Any], ttl_seconds: int = 300):
        """Initialize cache entry.

        Args:
            manifest: Manifest dictionary
            ttl_seconds: Time-to-live (default 5 minutes)
        """
        self.manifest = manifest
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        age = time.time() - self.created_at
        return age > self.ttl_seconds

    def __repr__(self) -> str:
        age = time.time() - self.created_at
        return f"CacheEntry(age={age:.1f}s, ttl={self.ttl_seconds}s)"


class ManifestCacheService:
    """Cache plugin manifests with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache service.

        Args:
            ttl_seconds: Default TTL for cached manifests (default 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, ManifestCacheEntry] = {}
        self._lock = threading.RLock()
        logger.info(f"Initialized ManifestCacheService (TTL={ttl_seconds}s)")

    def get(
        self,
        plugin_id: str,
        loader_func: Callable[[str], Optional[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """Get manifest from cache or load from disk.

        Args:
            plugin_id: Plugin ID
            loader_func: Callable that loads manifest from disk
                        Signature: (plugin_id: str) -> Optional[Dict[str, Any]]

        Returns:
            Manifest dict or None if not found
        """
        with self._lock:
            # Check cache
            if plugin_id in self._cache:
                entry = self._cache[plugin_id]
                if not entry.is_expired():
                    logger.debug(f"Cache hit for manifest '{plugin_id}' ({entry})")
                    return entry.manifest
                else:
                    # Expired, remove from cache
                    logger.debug(f"Cache expired for manifest '{plugin_id}', reloading")
                    del self._cache[plugin_id]

            # Cache miss or expired, load from disk
            logger.debug(f"Loading manifest '{plugin_id}' from disk")
            manifest = loader_func(plugin_id)

            if manifest:
                # Cache the result
                entry = ManifestCacheEntry(manifest, self.ttl_seconds)
                self._cache[plugin_id] = entry
                logger.debug(f"Cached manifest '{plugin_id}' ({entry})")

            return manifest

    def clear(self, plugin_id: Optional[str] = None) -> None:
        """Clear cache entry or entire cache.

        Args:
            plugin_id: Specific plugin to clear, or None to clear all
        """
        with self._lock:
            if plugin_id:
                if plugin_id in self._cache:
                    del self._cache[plugin_id]
                    logger.info(f"Cleared cache for plugin '{plugin_id}'")
            else:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared entire manifest cache ({count} entries)")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            expired = sum(1 for entry in self._cache.values() if entry.is_expired())
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired,
                "ttl_seconds": self.ttl_seconds,
            }

    def __repr__(self) -> str:
        stats = self.stats()
        return (
            f"ManifestCacheService("
            f"entries={stats['total_entries']}, "
            f"ttl={stats['ttl_seconds']}s)"
        )
