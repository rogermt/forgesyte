"""Plugin registry with thread-safe state tracking for Phase 11.

Authoritative registry of all plugins and their states with RWLock-based
thread safety. Enforces singleton pattern to prevent registry divergence.
"""

import logging
import threading
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from ..health.health_model import PluginHealthResponse
from ..lifecycle.lifecycle_manager import PluginLifecycleManager
from ..lifecycle.lifecycle_state import PluginLifecycleState

logger = logging.getLogger(__name__)


class RWLock:
    """
    Reader-Writer Lock for Phase 11 thread safety.

    Allows multiple concurrent readers or single writer.
    Preferred over simple Lock for 10-50 req/sec load.
    """

    def __init__(self) -> None:
        self._read_lock = RLock()
        self._write_lock = RLock()
        self._readers = 0

    def acquire_read(self) -> None:
        """Acquire read lock (multiple readers allowed)."""
        with self._read_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self) -> None:
        """Release read lock."""
        with self._read_lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self) -> None:
        """Acquire write lock (exclusive access)."""
        self._write_lock.acquire()

    def release_write(self) -> None:
        """Release write lock."""
        self._write_lock.release()

    def __enter__(self) -> "RWLock":
        """Context manager for write lock."""
        self.acquire_write()
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self.release_write()


class PluginMetadata:
    """Internal metadata for a plugin."""

    def __init__(self, name: str, description: str = "", version: str = "") -> None:
        self.name = name
        self.description = description
        self.version = version
        self.reason: Optional[str] = None
        self.loaded_at: Optional[datetime] = None
        self.last_used: Optional[datetime] = None
        self.success_count: int = 0
        self.error_count: int = 0
        self._execution_times: list = []  # Track last 10 execution times (in ms)
        self._max_execution_times: int = 10  # Keep last 10 for averaging

    @property
    def last_execution_time_ms(self) -> Optional[float]:
        """Get the last execution time in milliseconds."""
        if self._execution_times:
            return self._execution_times[-1]
        return None

    @property
    def avg_execution_time_ms(self) -> Optional[float]:
        """Get the average execution time from last 10 runs."""
        if not self._execution_times:
            return None
        return sum(self._execution_times) / len(self._execution_times)

    def record_execution_time(self, time_ms: float) -> None:
        """Record an execution time for metrics tracking."""
        self._execution_times.append(time_ms)
        # Keep only the last N execution times
        if len(self._execution_times) > self._max_execution_times:
            self._execution_times.pop(0)

    def metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }


class PluginRegistry:
    """
    Authoritative registry of all plugins and their states (Phase 11 singleton).

    Guarantees:
    - Every plugin has a queryable state
    - Failed/unavailable plugins are visible, not hidden
    - No state is lost on error
    - Thread-safe access to all state
    - Singleton: Only one instance can exist (prevents registry divergence)
    """

    _instance: Optional["PluginRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PluginRegistry":
        """Enforce singleton pattern (Phase 11).

        Raises:
            RuntimeError: If direct instantiation attempted. Use get_registry() instead.
        """
        raise RuntimeError(
            "PluginRegistry is a singleton (Phase 11). Use get_registry() instead."
        )

    @classmethod
    def _create_instance(cls) -> "PluginRegistry":
        """Internal factory for singleton creation. Called by get_registry()."""
        obj = object.__new__(cls)
        return obj

    def _init_singleton(self) -> None:
        """Initialize singleton instance (called by get_registry after creation)."""
        if not hasattr(self, "_initialized"):
            self._plugins: Dict[str, PluginMetadata] = {}
            self._plugin_instances: Dict[str, Any] = {}
            self._lifecycle = PluginLifecycleManager()
            self._rwlock = RWLock()
            self._initialized = True

    def register(
        self,
        name: str,
        description: str = "",
        version: str = "",
        instance: Optional[Any] = None,
    ) -> None:
        """Register a plugin as LOADED."""
        with self._rwlock:
            if name in self._plugins:
                logger.warning(f"Plugin {name} already registered; overwriting")

            metadata = PluginMetadata(name, description, version)
            metadata.loaded_at = datetime.now(timezone.utc)
            self._plugins[name] = metadata
            if instance is not None:
                self._plugin_instances[name] = instance
            self._lifecycle.set_state(name, PluginLifecycleState.LOADED)
            logger.info(f"✓ Registered plugin: {name}")

    def set_plugin_instance(self, name: str, instance: Any) -> None:
        """Store a plugin instance."""
        with self._rwlock:
            self._plugin_instances[name] = instance

    def get_plugin_instance(self, name: str) -> Optional[Any]:
        """Retrieve a plugin instance by name."""
        self._rwlock.acquire_read()
        try:
            return self._plugin_instances.get(name)
        finally:
            self._rwlock.release_read()

    def mark_failed(self, name: str, reason: str) -> None:
        """Mark a plugin as FAILED with error reason."""
        with self._rwlock:
            if name not in self._plugins:
                logger.error(f"Cannot mark unknown plugin FAILED: {name}")
                return

            self._plugins[name].reason = reason
            self._plugins[name].error_count += 1
            self._lifecycle.set_state(name, PluginLifecycleState.FAILED)
            logger.error(f"✗ Plugin FAILED: {name} ({reason})")

    def mark_unavailable(self, name: str, reason: str) -> None:
        """Mark a plugin as UNAVAILABLE (missing deps, etc)."""
        with self._rwlock:
            if name not in self._plugins:
                self._plugins[name] = PluginMetadata(name)

            self._plugins[name].reason = reason
            self._lifecycle.set_state(name, PluginLifecycleState.UNAVAILABLE)
            logger.warning(f"⊘ Plugin UNAVAILABLE: {name} ({reason})")

    def mark_initialized(self, name: str) -> None:
        """Mark a plugin as INITIALIZED (ready to run)."""
        with self._rwlock:
            if name not in self._plugins:
                logger.warning(f"Marking unknown plugin INITIALIZED: {name}")
                return

            self._lifecycle.set_state(name, PluginLifecycleState.INITIALIZED)

    def mark_running(self, name: str) -> None:
        """Mark a plugin as RUNNING (executing tool)."""
        with self._rwlock:
            if name not in self._plugins:
                return

            self._plugins[name].last_used = datetime.now(timezone.utc)
            self._lifecycle.set_state(name, PluginLifecycleState.RUNNING)

    def record_success(
        self, name: str, execution_time_ms: Optional[float] = None
    ) -> None:
        """Record successful execution."""
        with self._rwlock:
            if name in self._plugins:
                self._plugins[name].success_count += 1
                if execution_time_ms is not None:
                    self._plugins[name].record_execution_time(execution_time_ms)

    def record_error(
        self, name: str, execution_time_ms: Optional[float] = None
    ) -> None:
        """Record failed execution."""
        with self._rwlock:
            if name in self._plugins:
                self._plugins[name].error_count += 1
                if execution_time_ms is not None:
                    self._plugins[name].record_execution_time(execution_time_ms)

    def get_status(self, name: str) -> Optional[PluginHealthResponse]:
        """Get health status for a single plugin."""
        self._rwlock.acquire_read()
        try:
            if name not in self._plugins:
                return None

            meta = self._plugins[name]
            state = self._lifecycle.get_state(name)
            uptime = None
            if meta.loaded_at:
                uptime = (datetime.now(timezone.utc) - meta.loaded_at).total_seconds()

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
                last_execution_time_ms=meta.last_execution_time_ms,
                avg_execution_time_ms=meta.avg_execution_time_ms,
            )
        finally:
            self._rwlock.release_read()

    def list_all(self) -> List[PluginHealthResponse]:
        """List all plugins with their status."""
        self._rwlock.acquire_read()
        try:
            statuses = []
            for name in self._plugins:
                status = self.get_status(name)
                if status:
                    statuses.append(status)
            return sorted(statuses, key=lambda s: s.name)
        finally:
            self._rwlock.release_read()

    def list_available(self) -> List[str]:
        """List only LOADED/INITIALIZED/RUNNING plugins."""
        self._rwlock.acquire_read()
        try:
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
        finally:
            self._rwlock.release_read()

    def get_state(self, name: str) -> Optional[PluginLifecycleState]:
        """Get just the lifecycle state of a plugin."""
        self._rwlock.acquire_read()
        try:
            return self._lifecycle.get_state(name)
        finally:
            self._rwlock.release_read()

    def all_states(self) -> Dict[str, PluginLifecycleState]:
        """Get all plugin states as a dict."""
        self._rwlock.acquire_read()
        try:
            return self._lifecycle.all_states()
        finally:
            self._rwlock.release_read()

    def is_available(self, name: str) -> bool:
        """Check if plugin is available (not FAILED/UNAVAILABLE)."""
        state = self.get_state(name)
        return state in {
            PluginLifecycleState.LOADED,
            PluginLifecycleState.INITIALIZED,
            PluginLifecycleState.RUNNING,
        }

    def update_execution_metrics(
        self,
        plugin_name: str,
        state: str,
        elapsed_ms: int,
        had_error: bool,
    ) -> None:
        """Update metrics and lifecycle state after each execution (Phase 12).

        Args:
            plugin_name: Name of the plugin that executed
            state: Lifecycle state (INITIALIZED for success, FAILED for error)
            elapsed_ms: Execution time in milliseconds
            had_error: True if execution had an error

        Note:
            Uses ONLY valid lifecycle states: INITIALIZED, FAILED
            Metrics fields are updated atomically with state change.
        """
        with self._rwlock:
            if plugin_name not in self._plugins:
                logger.warning(
                    f"update_execution_metrics called for unknown plugin: {plugin_name}"
                )
                return

            metadata = self._plugins[plugin_name]

            # Update counts
            if had_error:
                metadata.error_count += 1
            else:
                metadata.success_count += 1

            # Track execution time
            metadata.record_execution_time(elapsed_ms)

            # Update lifecycle state based on success/error
            if had_error:
                self._lifecycle.set_state(plugin_name, PluginLifecycleState.FAILED)
            else:
                self._lifecycle.set_state(plugin_name, PluginLifecycleState.INITIALIZED)

            logger.debug(
                f"Updated metrics for {plugin_name}: state={state}, "
                f"elapsed_ms={elapsed_ms}, had_error={had_error}"
            )


def get_registry() -> PluginRegistry:
    """Get or create the global plugin registry (Phase 11 singleton).

    Thread-safe singleton getter. Always returns the same instance.
    Do NOT instantiate PluginRegistry() directly; use this function.

    Returns:
        The global PluginRegistry singleton instance

    Raises:
        RuntimeError: Never (singleton creation is safe)
    """
    if PluginRegistry._instance is None:
        with PluginRegistry._lock:
            if PluginRegistry._instance is None:
                # Create instance via factory (bypasses __new__ check)
                PluginRegistry._instance = PluginRegistry._create_instance()
                # Initialize the singleton
                PluginRegistry._instance._init_singleton()
    return PluginRegistry._instance
