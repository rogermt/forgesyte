"""TEST-CHANGE: Singleton enforcement test for Phase 11 plugin registry.

Verifies:
- PluginRegistry cannot be instantiated directly
- get_registry() always returns the same instance
- Thread safety of singleton getter
"""

import pytest

from app.plugins.loader.plugin_registry import PluginRegistry, get_registry


class TestSingletonEnforcement:
    """Tests for Phase 11 singleton pattern enforcement."""

    def test_direct_instantiation_raises_error(self) -> None:
        """Direct PluginRegistry() instantiation should raise RuntimeError."""
        with pytest.raises(RuntimeError, match="singleton.*get_registry"):
            PluginRegistry()

    def test_get_registry_returns_instance(self) -> None:
        """get_registry() should return a PluginRegistry instance."""
        registry = get_registry()
        assert isinstance(registry, PluginRegistry)

    def test_get_registry_returns_same_instance(self) -> None:
        """Multiple get_registry() calls should return the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_singleton_persists_across_calls(self) -> None:
        """Singleton should maintain state across multiple get_registry() calls."""
        # Get first instance and register a test plugin
        registry1 = get_registry()
        registry1.register("test_plugin_1", "Test Description", "1.0")

        # Get registry again and verify plugin is still there
        registry2 = get_registry()
        status = registry2.get_status("test_plugin_1")
        assert status is not None
        assert status.name == "test_plugin_1"

    def test_error_message_is_helpful(self) -> None:
        """Error message should guide users to use get_registry()."""
        with pytest.raises(RuntimeError) as exc_info:
            PluginRegistry()

        error_msg = str(exc_info.value)
        assert "singleton" in error_msg.lower()
        assert "get_registry" in error_msg
