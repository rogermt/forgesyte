"""Test PluginRegistry update_execution_metrics (Phase 12 TDD).

Tests verify:
- Metrics are updated on successful execution
- Metrics are updated on failed execution
- Unknown plugin is handled gracefully
- Lifecycle states are set correctly (INITIALIZED/FAILED)
- Execution times are recorded
"""

from app.plugins.lifecycle.lifecycle_state import PluginLifecycleState
from app.plugins.loader.plugin_registry import PluginRegistry, get_registry


class FakeRWLock:
    """Fake RWLock for testing without threading."""

    def __init__(self):
        self._readers = 0

    def acquire_read(self):
        pass

    def release_read(self):
        pass

    def acquire_write(self):
        pass

    def release_write(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestUpdateExecutionMetrics:
    """Tests for update_execution_metrics method."""

    def test_updates_metrics_on_success(self):
        """Successful execution should increment success_count and set INITIALIZED state."""
        # Create a fresh registry instance for testing
        registry = object.__new__(PluginRegistry)
        registry._initialized = True
        registry._plugins = {}
        registry._plugin_instances = {}
        registry._rwlock = FakeRWLock()

        # Create a mock lifecycle manager
        class MockLifecycleManager:
            def __init__(self):
                self._states = {}

            def set_state(self, name, state):
                self._states[name] = state

            def get_state(self, name):
                return self._states.get(name)

        registry._lifecycle = MockLifecycleManager()

        # Register a plugin
        from app.plugins.loader.plugin_registry import PluginMetadata

        registry._plugins["test_plugin"] = PluginMetadata(
            name="test_plugin", description="Test plugin", version="1.0.0"
        )

        # Call update_execution_metrics with success
        registry.update_execution_metrics(
            plugin_name="test_plugin",
            state="INITIALIZED",
            elapsed_ms=150,
            had_error=False,
        )

        # Verify metrics were updated
        metadata = registry._plugins["test_plugin"]
        assert metadata.success_count == 1
        assert metadata.error_count == 0
        assert metadata.last_execution_time_ms == 150

        # Verify lifecycle state
        assert (
            registry._lifecycle.get_state("test_plugin")
            == PluginLifecycleState.INITIALIZED
        )

    def test_updates_metrics_on_error(self):
        """Failed execution should increment error_count and set FAILED state."""
        registry = object.__new__(PluginRegistry)
        registry._initialized = True
        registry._plugins = {}
        registry._plugin_instances = {}
        registry._rwlock = FakeRWLock()

        class MockLifecycleManager:
            def __init__(self):
                self._states = {}

            def set_state(self, name, state):
                self._states[name] = state

            def get_state(self, name):
                return self._states.get(name)

        registry._lifecycle = MockLifecycleManager()

        from app.plugins.loader.plugin_registry import PluginMetadata

        registry._plugins["failing_plugin"] = PluginMetadata(
            name="failing_plugin", description="Failing plugin", version="1.0.0"
        )

        # Call update_execution_metrics with error
        registry.update_execution_metrics(
            plugin_name="failing_plugin",
            state="FAILED",
            elapsed_ms=50,
            had_error=True,
        )

        # Verify metrics were updated
        metadata = registry._plugins["failing_plugin"]
        assert metadata.success_count == 0
        assert metadata.error_count == 1

        # Verify lifecycle state
        assert (
            registry._lifecycle.get_state("failing_plugin")
            == PluginLifecycleState.FAILED
        )

    def test_handles_unknown_plugin_gracefully(self):
        """Unknown plugin should be handled gracefully without raising."""
        registry = object.__new__(PluginRegistry)
        registry._initialized = True
        registry._plugins = {}
        registry._plugin_instances = {}
        registry._rwlock = FakeRWLock()

        class MockLifecycleManager:
            def __init__(self):
                self._states = {}

            def set_state(self, name, state):
                self._states[name] = state

        registry._lifecycle = MockLifecycleManager()

        # Should not raise
        registry.update_execution_metrics(
            plugin_name="unknown_plugin",
            state="INITIALIZED",
            elapsed_ms=100,
            had_error=False,
        )

    def test_records_execution_time(self):
        """Execution time should be recorded in the plugin metadata."""
        registry = object.__new__(PluginRegistry)
        registry._initialized = True
        registry._plugins = {}
        registry._plugin_instances = {}
        registry._rwlock = FakeRWLock()

        class MockLifecycleManager:
            def __init__(self):
                self._states = {}

            def set_state(self, name, state):
                self._states[name] = state

        registry._lifecycle = MockLifecycleManager()

        from app.plugins.loader.plugin_registry import PluginMetadata

        registry._plugins["timed_plugin"] = PluginMetadata(
            name="timed_plugin", description="Timed plugin", version="1.0.0"
        )

        # Record multiple executions
        registry.update_execution_metrics(
            plugin_name="timed_plugin",
            state="INITIALIZED",
            elapsed_ms=100,
            had_error=False,
        )
        registry.update_execution_metrics(
            plugin_name="timed_plugin",
            state="INITIALIZED",
            elapsed_ms=200,
            had_error=False,
        )

        metadata = registry._plugins["timed_plugin"]

        # Verify execution times are tracked
        assert metadata.last_execution_time_ms == 200
        assert metadata.success_count == 2

    def test_uses_valid_lifecycle_states_only(self):
        """Should use only INITIALIZED (success) or FAILED (error) states."""
        registry = object.__new__(PluginRegistry)
        registry._initialized = True
        registry._plugins = {}
        registry._plugin_instances = {}
        registry._rwlock = FakeRWLock()

        class MockLifecycleManager:
            def __init__(self):
                self._states = {}

            def set_state(self, name, state):
                self._states[name] = state

            def get_state(self, name):
                return self._states.get(name)

        registry._lifecycle = MockLifecycleManager()

        from app.plugins.loader.plugin_registry import PluginMetadata

        registry._plugins["state_test_plugin"] = PluginMetadata(
            name="state_test_plugin", description="State test plugin", version="1.0.0"
        )

        # Success case - should set INITIALIZED
        registry.update_execution_metrics(
            plugin_name="state_test_plugin",
            state="INITIALIZED",
            elapsed_ms=100,
            had_error=False,
        )
        assert (
            registry._lifecycle.get_state("state_test_plugin")
            == PluginLifecycleState.INITIALIZED
        )

        # Error case - should set FAILED
        registry.update_execution_metrics(
            plugin_name="state_test_plugin",
            state="FAILED",
            elapsed_ms=50,
            had_error=True,
        )
        assert (
            registry._lifecycle.get_state("state_test_plugin")
            == PluginLifecycleState.FAILED
        )


class TestRegistryIntegration:
    """Integration tests for registry metrics with singleton pattern."""

    def test_get_registry_returns_singleton(self):
        """Verify get_registry returns a valid singleton instance."""
        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, PluginRegistry)

    def test_registry_has_update_execution_metrics_method(self):
        """Verify the registry instance has the update_execution_metrics method."""
        registry = get_registry()
        assert hasattr(registry, "update_execution_metrics")
        assert callable(registry.update_execution_metrics)
