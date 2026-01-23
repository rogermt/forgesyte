# Backend: ManifestCacheService

**File:** `forgesyte/server/app/services/manifest_cache_service.py` (NEW)  
**Purpose:** Cache plugin manifests with TTL to avoid repeated file I/O  
**Status:** Ready to implement  

---

## Overview

Caches manifest.json files in memory with configurable TTL. When a manifest is requested, return from cache if valid; otherwise read from disk and cache.

**Benefits:**
- Zero file I/O for repeated manifest requests
- Automatic invalidation on timeout
- Thread-safe (uses locks)
- Easy to clear on plugin reload

---

## Implementation

**Location:** `forgesyte/server/app/services/manifest_cache_service.py` (NEW FILE)

```python
"""Manifest caching service with TTL support."""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

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

    def get(self, plugin_id: str, loader_func: callable) -> Optional[Dict[str, Any]]:
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
                    logger.debug(
                        f"Cache hit for manifest '{plugin_id}' ({entry})"
                    )
                    return entry.manifest
                else:
                    # Expired, remove from cache
                    logger.debug(
                        f"Cache expired for manifest '{plugin_id}', reloading"
                    )
                    del self._cache[plugin_id]

            # Cache miss or expired, load from disk
            logger.debug(f"Loading manifest '{plugin_id}' from disk")
            manifest = loader_func(plugin_id)

            if manifest:
                # Cache the result
                entry = ManifestCacheEntry(manifest, self.ttl_seconds)
                self._cache[plugin_id] = entry
                logger.debug(
                    f"Cached manifest '{plugin_id}' ({entry})"
                )

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
            expired = sum(
                1 for entry in self._cache.values()
                if entry.is_expired()
            )
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
```

---

## Integration with Plugin Management Service

**Location:** `forgesyte/server/app/services/plugin_management_service.py` (UPDATE)

Add to `__init__` method:
```python
from .manifest_cache_service import ManifestCacheService

def __init__(self):
    # ... existing code ...
    self.manifest_cache = ManifestCacheService(ttl_seconds=300)
```

Update `get_plugin_manifest` method to use cache:
```python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get plugin manifest (with caching)."""
    # Use cache service
    return self.manifest_cache.get(
        plugin_id,
        loader_func=self._load_manifest_from_disk
    )

def _load_manifest_from_disk(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Load manifest from disk (called by cache service)."""
    plugin = self.get_plugin(plugin_id)
    if not plugin:
        return None
    
    try:
        import json
        import sys
        from pathlib import Path
        
        plugin_module_name = plugin.__class__.__module__
        plugin_module = sys.modules.get(plugin_module_name)
        if not plugin_module or not hasattr(plugin_module, '__file__'):
            return None
        
        plugin_dir = Path(plugin_module.__file__).parent
        manifest_path = plugin_dir / "manifest.json"
        
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading manifest for '{plugin_id}': {e}")
        return None
```

Clear cache on plugin reload:
```python
async def reload_plugin(self, plugin_id: str) -> None:
    """Reload plugin and clear its cached manifest."""
    # ... existing reload code ...
    self.manifest_cache.clear(plugin_id)  # Clear cache entry
```

---

## Testing

**Location:** `forgesyte/server/tests/services/test_manifest_cache_service.py` (NEW FILE)

```python
"""Tests for ManifestCacheService."""

import time
import pytest
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
    result1 = cache.get("test-plugin", loader)
    assert load_count == 1
    
    # Second call within TTL
    result2 = cache.get("test-plugin", loader)
    assert load_count == 1
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Third call after TTL: reloads
    result3 = cache.get("test-plugin", loader)
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
    
    # Cache should not store None entries (or store them briefly)
    # This is by design: None means "not found", not "found empty"
```

**Run tests:**
```bash
cd forgesyte/server
uv run pytest tests/services/test_manifest_cache_service.py -v
```

---

## Usage Example

```python
# In PluginManagementService
class PluginManagementService:
    def __init__(self):
        self.manifest_cache = ManifestCacheService(ttl_seconds=300)
    
    def get_plugin_manifest(self, plugin_id: str):
        return self.manifest_cache.get(
            plugin_id,
            loader_func=self._load_manifest_from_disk
        )
    
    async def reload_plugin(self, plugin_id: str):
        # ... reload code ...
        self.manifest_cache.clear(plugin_id)  # Invalidate cache
```

---

## Performance

- **Cache hit:** O(1) dict lookup, <1ms
- **Cache miss:** File I/O, ~5-10ms per manifest
- **Memory:** ~1KB per cached manifest (negligible)

---

## Related Files

- [BACKEND_MANIFEST_ENDPOINT.md](./BACKEND_MANIFEST_ENDPOINT.md) — Uses this service
- [TESTS_BACKEND_CPU.md](./TESTS_BACKEND_CPU.md) — Integration tests
