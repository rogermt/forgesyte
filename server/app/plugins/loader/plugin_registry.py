"""Plugin registry with thread-safe state tracking for Phase 11.

Authoritative registry of all plugins and their states with RWLock-based
thread safety.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..health.health_model import PluginHealthResponse
from ..lifecycle.lifecycle_manager import PluginLifecycleManager
from ..lifecycle.lifecycle_state import PluginLifecycleState

logger = logging.getLogger(__name__)


class PluginMetadata:
    """Internal metadata for a plugin."""

    def __init__(
        self, name: str, description: str = "", version: str = ""
    ) -> None:
        self.name = name
        self.description = description
        self.version = version
        self.reason: Optional[str] = None
        self.loaded_at: Optional[datetime] = None
        self.last_used: Optional[datetime] = None
        self.success_count: int = 0
        self.error_count: int = 0


class PluginRegistry:
    """
    Authoritative registry of all plugins and their states.

    Guarantees:
    - Every plugin has a queryable state
    - Failed/unavailable plugins are visible, not hidden
    - No state is lost on error
    - Thread-safe access to all state
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: Dict[str, PluginMetadata] = {}
        self._lifecycle = PluginLifecycleManager()
        self._lock = __import__("threading").Lock()

    def register(
        self,
        name: str,
        description: str = "",
        version: str = "",
    ) -> None:
        """Register a plugin as LOADED."""
        with self._lock:
            if name in self._plugins:
                logger.warning(f"Plugin {name} already registered; overwriting")

            metadata = PluginMetadata(name, description, version)
            metadata.loaded_at = datetime.utcnow()
            self._plugins[name] = metadata
            self._lifecycle.set_state(name, PluginLifecycleState.LOADED)
            logger.info(f"✓ Registered plugin: {name}")

    def mark_failed(self, name: str, reason: str) -> None:
        """Mark a plugin as FAILED with error reason."""
        with self._lock:
            if name not in self._plugins:
                logger.error(f"Cannot mark unknown plugin FAILED: {name}")
                return

            self._plugins[name].reason = reason
            self._plugins[name].error_count += 1
            self._lifecycle.set_state(name, PluginLifecycleState.FAILED)
            logger.error(f"✗ Plugin FAILED: {name} ({reason})")

    def mark_unavailable(self, name: str, reason: str) -> None:
        """Mark a plugin as UNAVAILABLE (missing deps, etc)."""
        with self._lock:
            if name not in self._plugins:
                self._plugins[name] = PluginMetadata(name)

            self._plugins[name].reason = reason
            self._lifecycle.set_state(name, PluginLifecycleState.UNAVAILABLE)
            logger.warning(f"⊘ Plugin UNAVAILABLE: {name} ({reason})")

    def mark_initialized(self, name: str) -> None:
        """Mark a plugin as INITIALIZED (ready to run)."""
        with self._lock:
            if name not in self._plugins:
                logger.warning(f"Marking unknown plugin INITIALIZED: {name}")
                return

            self._lifecycle.set_state(name, PluginLifecycleState.INITIALIZED)

    def mark_running(self, name: str) -> None:
        """Mark a plugin as RUNNING (executing tool)."""
        with self._lock:
            if name not in self._plugins:
                return

            self._plugins[name].last_used = datetime.utcnow()
            self._lifecycle.set_state(name, PluginLifecycleState.RUNNING)

    def record_success(self, name: str) -> None:
        """Record successful execution."""
        with self._lock:
            if name in self._plugins:
                self._plugins[name].success_count += 1

    def record_error(self, name: str) -> None:
        """Record failed execution."""
        with self._lock:
            if name in self._plugins:
                self._plugins[name].error_count += 1

    def get_status(self, name: str) -> Optional[PluginHealthResponse]:
        """Get health status for a single plugin."""
        with self._lock:
            if name not in self._plugins:
                return None

            meta = self._plugins[name]
            state = self._lifecycle.get_state(name)
            uptime = None
            if meta.loaded_at:
                uptime = (datetime.utcnow() - meta.loaded_at).total_seconds()

            return PluginHealthResponse(
                name=meta.name,
                state=state or PluginLifecycleState.LOADED,
                description=meta.description,
                reason=meta.reason,
                version=meta.version,
                uptime_seconds=uptime,
                last_used=meta.last_used,
                success_count=meta.success_count,
                error_count=meta.error_count,
            )

    def list_all(self) -> List[PluginHealthResponse]:
        """List all plugins with their status."""
        with self._lock:
            statuses = []
            for name in self._plugins:
                status = self.get_status(name)
                if status:
                    statuses.append(status)
            return sorted(statuses, key=lambda s: s.name)

    def list_available(self) -> List[str]:
        """List only LOADED/INITIALIZED/RUNNING plugins."""
        with self._lock:
            available = []
            for name, _meta in self._plugins.items():
                state = self._lifecycle.get_state(name)
                if state in {
                    PluginLifecycleState.LOADED,
                    PluginLifecycleState.INITIALIZED,
                    PluginLifecycleState.RUNNING,
                }:
                    available.append(name)
            return available

    def get_state(self, name: str) -> Optional[PluginLifecycleState]:
        """Get just the lifecycle state of a plugin."""
        with self._lock:
            return self._lifecycle.get_state(name)

    def all_states(self) -> Dict[str, PluginLifecycleState]:
        """Get all plugin states as a dict."""
        with self._lock:
            return self._lifecycle.all_states()

    def is_available(self, name: str) -> bool:
        """Check if plugin is available (not FAILED/UNAVAILABLE)."""
        state = self.get_state(name)
        return state in {
            PluginLifecycleState.LOADED,
            PluginLifecycleState.INITIALIZED,
            PluginLifecycleState.RUNNING,
        }


# Singleton instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get or create the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
