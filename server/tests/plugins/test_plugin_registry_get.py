"""Regression test for PluginRegistry.get() returning the plugin instance.

See: docs/releases/v0.9.3/MISSING_GET_IN_REGISTRY.md
"""

import pytest

from app.plugins.loader.plugin_registry import PluginRegistry


class DummyPlugin:
    """Test plugin with tools attribute."""

    tools: dict[str, dict] = {
        "tool_a": {},
        "tool_b": {},
    }


def test_get_returns_plugin_instance_not_metadata_or_class(monkeypatch):
    """
    Regression test:
    PluginRegistry.get(name) must return the actual plugin instance.

    If it returns:
        - PluginMetadata → tool list becomes lifecycle methods
        - Plugin class → tools attribute may not exist
        - Manifest wrapper → tools = ['on_load', 'on_unload', ...]
    """

    # Create a fresh registry instance
    registry = PluginRegistry._create_instance()
    registry._init_singleton()

    # Register plugin metadata + instance
    registry.register(
        name="dummy",
        description="Test plugin",
        version="1.0",
        instance=DummyPlugin(),  # <-- real instance
    )

    # Act
    plugin = registry.get("dummy")

    # Assert: must be the actual instance
    assert isinstance(
        plugin, DummyPlugin
    ), "PluginRegistry.get() must return the plugin instance"

    # Assert: tools must come from the instance, not manifest or metadata
    assert hasattr(plugin, "tools"), "Plugin instance must have a 'tools' attribute"

    assert set(plugin.tools.keys()) == {
        "tool_a",
        "tool_b",
    }, "PluginRegistry.get() returned wrong object; tools list incorrect"


def test_get_raises_keyerror_for_missing_plugin():
    """
    PluginRegistry.get(name) must raise KeyError for non-existent plugin.
    This prevents silent failures that could cause fallback to wrong objects.
    """
    registry = PluginRegistry._create_instance()
    registry._init_singleton()

    with pytest.raises(KeyError, match="Plugin instance for 'nonexistent' not found"):
        registry.get("nonexistent")


def test_get_raises_keyerror_for_plugin_without_instance():
    """
    PluginRegistry.get(name) must raise KeyError if plugin exists
    but has no instance (was registered without an instance).
    """
    registry = PluginRegistry._create_instance()
    registry._init_singleton()

    # Register plugin without instance
    registry.register(
        name="no_instance",
        description="Plugin without instance",
        version="1.0",
        instance=None,  # <-- no instance
    )

    with pytest.raises(KeyError, match="Plugin instance for 'no_instance' not found"):
        registry.get("no_instance")
