"""Tests for ManifestCacheService."""

import time

from app.services.manifest_cache_service import ManifestCacheService


def test_cache_hit():
    """Test cache returns same manifest on second call."""
    cache = ManifestCacheService(ttl_seconds=300)

    manifest = {"id": "test", "name": "Test"}
    load_count = 0

    def loader(plugin_id):
        nonlocal load_count
        load_count += 1
        return manifest

    # First call: loads from disk
    result1 = cache.get("test-plugin", loader)
    assert result1 == manifest
    assert load_count == 1

    # Second call: returns from cache
    result2 = cache.get("test-plugin", loader)
    assert result2 == manifest
    assert load_count == 1  # No additional load


def test_cache_expiration():
    """Test cache expires after TTL."""
    cache = ManifestCacheService(ttl_seconds=1)

    manifest = {"id": "test", "name": "Test"}
    load_count = 0

    def loader(plugin_id):
        nonlocal load_count
        load_count += 1
        return manifest

    # First call
    cache.get("test-plugin", loader)
    assert load_count == 1

    # Second call within TTL
    cache.get("test-plugin", loader)
    assert load_count == 1

    # Wait for expiration
    time.sleep(1.1)

    # Third call after TTL: reloads
    cache.get("test-plugin", loader)
    assert load_count == 2


def test_cache_clear_single():
    """Test clearing single cache entry."""
    cache = ManifestCacheService()

    manifest = {"id": "test", "name": "Test"}
    load_count = 0

    def loader(plugin_id):
        nonlocal load_count
        load_count += 1
        return manifest

    # Load and cache
    cache.get("test-plugin", loader)
    assert load_count == 1

    # Clear specific entry
    cache.clear("test-plugin")

    # Next call reloads
    cache.get("test-plugin", loader)
    assert load_count == 2


def test_cache_clear_all():
    """Test clearing entire cache."""
    cache = ManifestCacheService()

    manifest = {"id": "test", "name": "Test"}
    load_count = 0

    def loader(plugin_id):
        nonlocal load_count
        load_count += 1
        return manifest

    # Load multiple
    cache.get("plugin-1", loader)
    cache.get("plugin-2", loader)
    assert load_count == 2

    # Clear all
    cache.clear()

    # Next calls reload
    cache.get("plugin-1", loader)
    cache.get("plugin-2", loader)
    assert load_count == 4


def test_cache_none_handling():
    """Test cache handles None manifests."""
    cache = ManifestCacheService()

    def loader(plugin_id):
        return None

    # First call returns None
    result1 = cache.get("missing-plugin", loader)
    assert result1 is None

    # Cache should not store None entries
