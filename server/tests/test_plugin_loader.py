"""Complete pytest suite for plugin_loader module (entry-point plugins only)"""

import asyncio
from unittest.mock import MagicMock

from app.plugin_loader import (
    BasePlugin,
    PluginManager,
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


class DummyPlugin(BasePlugin):
    name = "dummy"

    def metadata(self):
        return {"name": "dummy", "version": "1.0.0"}

    def analyze(self, image_bytes: bytes, options=None):
        return {"ok": True, "len": len(image_bytes)}


class InvalidPlugin:
    """Does not implement PluginInterface"""

    pass


# -------------------------------------------------------------------
# BasePlugin Tests
# -------------------------------------------------------------------


def test_baseplugin_async_analysis():
    plugin = DummyPlugin()

    result = asyncio.run(plugin.analyze_async(b"12345"))
    assert result["ok"] is True
    assert result["len"] == 5


def test_baseplugin_on_load_and_unload():
    plugin = DummyPlugin()
    plugin.on_load()
    plugin.on_unload()  # Should not raise


def test_baseplugin_validate_image_valid():
    plugin = DummyPlugin()
    # PNG header + padding
    png_data = b"\x89PNG" + b"\x00" * 100
    assert plugin.validate_image(png_data) is True


def test_baseplugin_validate_image_invalid():
    plugin = DummyPlugin()
    assert plugin.validate_image(b"not an image") is False
    assert plugin.validate_image(b"") is False
    assert plugin.validate_image(b"short") is False


# -------------------------------------------------------------------
# Entry-point plugin loading
# -------------------------------------------------------------------


def test_load_entrypoint_plugins_success(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr(
        "app.plugin_loader.entry_points",
        lambda group: [mock_ep] if group == "forgesyte.plugins" else [],
    )

    pm = PluginManager()
    loaded, errors = pm.load_entrypoint_plugins()

    assert "dummy" in loaded
    assert errors == {}
    assert pm.get("dummy") is not None


def test_load_entrypoint_plugins_invalid_plugin(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "invalid_ep"
    mock_ep.load.return_value = InvalidPlugin  # Not PluginInterface

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    loaded, errors = pm.load_entrypoint_plugins()

    assert loaded == {}
    assert "invalid_ep" in errors


def test_load_entrypoint_plugins_exception(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "failing_ep"
    mock_ep.load.side_effect = ImportError("Module not found")

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    loaded, errors = pm.load_entrypoint_plugins()

    assert loaded == {}
    assert "failing_ep" in errors


def test_load_plugins_returns_correct_structure(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    result = pm.load_plugins()

    assert "loaded" in result
    assert "errors" in result
    assert "dummy" in result["loaded"]
    assert result["errors"] == {}


# -------------------------------------------------------------------
# Utility methods
# -------------------------------------------------------------------


def test_plugin_manager_get_and_list(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_entrypoint_plugins()

    assert pm.get("dummy") is not None
    assert "dummy" in pm.list()


def test_plugin_manager_get_nonexistent():
    pm = PluginManager()
    assert pm.get("nonexistent") is None


def test_plugin_manager_contains_operator():
    """Test that PluginManager supports the 'in' operator."""
    pm = PluginManager()
    mock_plugin = MagicMock()
    mock_plugin.name = "test_plugin"
    pm.plugins["test_plugin"] = mock_plugin

    assert "test_plugin" in pm
    assert "nonexistent" not in pm


def test_plugin_manager_list_empty():
    pm = PluginManager()
    assert pm.list() == {}


def test_plugin_manager_list_with_pydantic_metadata(monkeypatch):
    """Test list() handles Pydantic model metadata."""
    mock_ep = MagicMock()
    mock_ep.name = "pydantic_ep"

    class PydanticPlugin(BasePlugin):
        name = "pydantic_test"

        def metadata(self):
            mock_model = MagicMock()
            mock_model.model_dump.return_value = {"name": "pydantic_test"}
            return mock_model

        def analyze(self, image_bytes, options=None):
            return {}

    mock_ep.load.return_value = PydanticPlugin
    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    result = pm.list()
    assert "pydantic_test" in result
    assert result["pydantic_test"]["name"] == "pydantic_test"


# -------------------------------------------------------------------
# Reload operations
# -------------------------------------------------------------------


def test_reload_plugin_existing(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    assert "dummy" in pm
    result = pm.reload_plugin("dummy")
    assert result is True
    assert "dummy" not in pm  # Removed, needs reload_all to rediscover


def test_reload_plugin_nonexistent():
    pm = PluginManager()
    result = pm.reload_plugin("nonexistent")
    assert result is False


def test_reload_all(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    result = pm.reload_all()
    assert "loaded" in result
    assert "errors" in result
    assert "dummy" in result["loaded"]


def test_reload_all_handles_unload_exception(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    # Make on_unload raise an exception
    pm.plugins["dummy"].on_unload = MagicMock(side_effect=Exception("Unload failed"))

    # Should not raise, should log warning and continue
    result = pm.reload_all()
    assert "loaded" in result


# -------------------------------------------------------------------
# Uninstall operations
# -------------------------------------------------------------------


def test_uninstall_plugin_existing(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    assert "dummy" in pm
    result = pm.uninstall_plugin("dummy")
    assert result is True
    assert "dummy" not in pm


def test_uninstall_plugin_nonexistent():
    pm = PluginManager()
    result = pm.uninstall_plugin("nonexistent_plugin")
    assert result is False


def test_uninstall_plugin_handles_exception(monkeypatch):
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    pm = PluginManager()
    pm.load_plugins()

    # Make on_unload raise an exception
    pm.plugins["dummy"].on_unload = MagicMock(side_effect=Exception("Unload failed"))

    # Should not raise, should log warning and still remove
    result = pm.uninstall_plugin("dummy")
    assert result is True
    assert "dummy" not in pm


# -------------------------------------------------------------------
# Edge cases
# -------------------------------------------------------------------


def test_plugin_manager_initialization():
    """Test basic initialization."""
    pm = PluginManager()
    assert pm.plugins == {}


def test_load_plugins_no_entrypoints(monkeypatch):
    """Test loading when no entry-points are registered."""
    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [])

    pm = PluginManager()
    result = pm.load_plugins()

    assert result["loaded"] == {}
    assert result["errors"] == {}
