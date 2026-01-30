"""Unit tests for ManifestCacheService (TDD)."""

import threading
import time
from typing import Any, Dict

from app.services.manifest_cache import ManifestCacheService


class TestManifestCacheService:
    """Test ManifestCacheService with TTL-based caching."""

    def test_get_returns_none_for_unknown_plugin(self) -> None:
        """Test get() returns None for plugin not in cache."""
        cache = ManifestCacheService(ttl_seconds=60)
        result = cache.get("unknown-plugin")
        assert result is None

    def test_set_and_get_stores_and_retrieves_manifest(self) -> None:
        """Test set() stores manifest and get() retrieves it."""
        cache = ManifestCacheService(ttl_seconds=60)
        manifest: Dict[str, Any] = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "tools": [],
        }

        cache.set("test-plugin", manifest)
        result = cache.get("test-plugin")

        assert result == manifest
        assert result is not None

    def test_ttl_cache_hit_before_expiry(self) -> None:
        """Test cache returns manifest before TTL expires."""
        cache = ManifestCacheService(ttl_seconds=2)
        manifest: Dict[str, Any] = {"id": "plugin", "data": "test"}

        cache.set("plugin", manifest)
        # Access within TTL
        result1 = cache.get("plugin")
        time.sleep(0.5)
        result2 = cache.get("plugin")

        assert result1 == manifest
        assert result2 == manifest

    def test_ttl_cache_miss_after_expiry(self) -> None:
        """Test cache returns None after TTL expires."""
        cache = ManifestCacheService(ttl_seconds=1)
        manifest: Dict[str, Any] = {"id": "plugin", "data": "test"}

        cache.set("plugin", manifest)
        # Wait for expiration (with buffer for system time variation)
        time.sleep(1.2)

        result = cache.get("plugin")
        assert result is None

    def test_multiple_plugins_independent_ttl(self) -> None:
        """Test multiple plugins have independent TTL."""
        cache = ManifestCacheService(ttl_seconds=1)
        manifest1: Dict[str, Any] = {"id": "plugin1"}
        manifest2: Dict[str, Any] = {"id": "plugin2"}

        cache.set("plugin1", manifest1)
        time.sleep(0.5)
        cache.set("plugin2", manifest2)
        time.sleep(0.7)  # plugin1 expired, plugin2 still valid

        assert cache.get("plugin1") is None
        assert cache.get("plugin2") == manifest2

    def test_overwrite_existing_manifest(self) -> None:
        """Test set() overwrites existing manifest."""
        cache = ManifestCacheService(ttl_seconds=60)
        manifest1: Dict[str, Any] = {"id": "plugin", "version": "1.0"}
        manifest2: Dict[str, Any] = {"id": "plugin", "version": "2.0"}

        cache.set("plugin", manifest1)
        assert cache.get("plugin") == manifest1

        cache.set("plugin", manifest2)
        assert cache.get("plugin") == manifest2

    def test_dep_classmethod_returns_instance(self) -> None:
        """Test dep() classmethod returns ManifestCacheService instance."""
        service = ManifestCacheService.dep()
        assert isinstance(service, ManifestCacheService)

    def test_concurrent_gets_and_sets(self) -> None:
        """Test concurrent access doesn't corrupt cache (thread-safe)."""
        cache = ManifestCacheService(ttl_seconds=60)
        results: list = []
        errors: list = []

        def set_manifest(plugin_id: str, version: int) -> None:
            try:
                manifest = {
                    "id": plugin_id,
                    "version": version,
                }
                cache.set(plugin_id, manifest)
            except Exception as e:
                errors.append(e)

        def get_manifest(plugin_id: str) -> None:
            try:
                result = cache.get(plugin_id)
                if result:
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Spawn multiple threads
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=set_manifest, args=(f"plugin-{i}", i))
            t2 = threading.Thread(target=get_manifest, args=(f"plugin-{i}",))
            threads.extend([t1, t2])

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrency errors: {errors}"
        assert len(results) > 0

    def test_get_after_expiry_removes_from_cache(self) -> None:
        """Test expired entry is removed from cache on access."""
        cache = ManifestCacheService(ttl_seconds=1)
        manifest: Dict[str, Any] = {"id": "plugin"}

        cache.set("plugin", manifest)
        assert cache._cache_size() == 1

        time.sleep(1.1)
        result = cache.get("plugin")

        assert result is None
        # Entry should be cleaned up (removed from internal dict)
        assert cache._cache_size() == 0

    def test_clear_single_entry(self) -> None:
        """Test clear() removes specific plugin from cache."""
        cache = ManifestCacheService(ttl_seconds=60)
        manifest1 = {"id": "plugin1"}
        manifest2 = {"id": "plugin2"}

        cache.set("plugin1", manifest1)
        cache.set("plugin2", manifest2)

        cache.clear("plugin1")

        assert cache.get("plugin1") is None
        assert cache.get("plugin2") == manifest2

    def test_clear_all_entries(self) -> None:
        """Test clear(None) removes all entries from cache."""
        cache = ManifestCacheService(ttl_seconds=60)
        cache.set("plugin1", {"id": "plugin1"})
        cache.set("plugin2", {"id": "plugin2"})
        cache.set("plugin3", {"id": "plugin3"})

        cache.clear()

        assert cache.get("plugin1") is None
        assert cache.get("plugin2") is None
        assert cache.get("plugin3") is None
        assert cache._cache_size() == 0

    def test_cache_size_reports_entries(self) -> None:
        """Test _cache_size() reports number of cached entries."""
        cache = ManifestCacheService(ttl_seconds=60)
        assert cache._cache_size() == 0

        cache.set("plugin1", {"id": "1"})
        assert cache._cache_size() == 1

        cache.set("plugin2", {"id": "2"})
        assert cache._cache_size() == 2

        cache.clear("plugin1")
        assert cache._cache_size() == 1
