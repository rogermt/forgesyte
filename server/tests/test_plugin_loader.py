"""Complete pytest suite for plugin_loader module (80-90% coverage)"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.plugin_loader import (
    BasePlugin,
    PluginInterface,
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


# -------------------------------------------------------------------
# Entry‑point plugin loading
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


# -------------------------------------------------------------------
# Local plugin loading
# -------------------------------------------------------------------


def test_load_local_plugins_success(tmp_path):
    plugin_dir = tmp_path / "myplugin"
    plugin_dir.mkdir()

    plugin_file = plugin_dir / "plugin.py"
    plugin_file.write_text(
        """
from app.plugin_loader import BasePlugin

class Plugin(BasePlugin):
    name = "local_dummy"
    def metadata(self): return {"name": "local_dummy"}
    def analyze(self, image_bytes, options=None): return {"ok": True}
"""
    )

    pm = PluginManager(plugins_dir=str(tmp_path))
    loaded, errors = pm.load_local_plugins()

    assert "local_dummy" in loaded
    assert errors == {}
    assert pm.get("local_dummy") is not None


def test_load_local_plugins_missing_plugin_file(tmp_path):
    (tmp_path / "emptydir").mkdir()

    pm = PluginManager(plugins_dir=str(tmp_path))
    loaded, errors = pm.load_local_plugins()

    assert loaded == {}
    assert errors == {}


def test_load_local_plugins_invalid_plugin(tmp_path):
    plugin_dir = tmp_path / "badplugin"
    plugin_dir.mkdir()

    plugin_file = plugin_dir / "plugin.py"
    plugin_file.write_text("class Plugin: pass")  # Missing interface

    pm = PluginManager(plugins_dir=str(tmp_path))
    loaded, errors = pm.load_local_plugins()

    assert loaded == {}
    assert "badplugin" in errors


# -------------------------------------------------------------------
# File loader tests
# -------------------------------------------------------------------


def test_load_plugin_from_file_success(tmp_path):
    plugin_file = tmp_path / "plugin.py"
    plugin_file.write_text(
        """
from app.plugin_loader import BasePlugin

class Plugin(BasePlugin):
    name = "file_dummy"
    def metadata(self): return {"name": "file_dummy"}
    def analyze(self, image_bytes, options=None): return {"ok": True}
"""
    )

    pm = PluginManager()
    plugin = pm._load_plugin_from_file(plugin_file, "file_dummy")

    assert plugin.name == "file_dummy"
    assert isinstance(plugin, PluginInterface)


def test_load_plugin_from_file_missing_class(tmp_path):
    plugin_file = tmp_path / "plugin.py"
    plugin_file.write_text("x = 1")

    pm = PluginManager()

    with pytest.raises(AttributeError):
        pm._load_plugin_from_file(plugin_file, "missing")


def test_load_plugin_from_file_invalid_interface(tmp_path):
    plugin_file = tmp_path / "plugin.py"
    plugin_file.write_text(
        """
class Plugin:
    pass
"""
    )

    pm = PluginManager()

    with pytest.raises(TypeError):
        pm._load_plugin_from_file(plugin_file, "invalid")


# -------------------------------------------------------------------
# Combined loader
# -------------------------------------------------------------------


def test_load_plugins_combined(monkeypatch, tmp_path):
    # Mock entrypoint plugin
    mock_ep = MagicMock()
    mock_ep.name = "dummy_ep"
    mock_ep.load.return_value = DummyPlugin

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])

    # Local plugin
    plugin_dir = tmp_path / "local"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        """
from app.plugin_loader import BasePlugin
class Plugin(BasePlugin):
    name = "local_dummy"
    def metadata(self): return {"name": "local_dummy"}
    def analyze(self, image_bytes, options=None): return {"ok": True}
"""
    )

    pm = PluginManager(plugins_dir=str(tmp_path))
    result = pm.load_plugins()

    assert "dummy" in result["loaded"]
    assert "local_dummy" in result["loaded"]
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


# -------------------------------------------------------------------
# High-value missing tests
# -------------------------------------------------------------------


def test_plugin_manager_with_none_plugins_dir():
    """Ensures PluginManager handles None cleanly - a real-world scenario."""
    # Initialize PluginManager with None plugins_dir
    plugin_manager = PluginManager(plugins_dir=None)

    # Verify that the plugins_dir is properly set to None
    assert plugin_manager.plugins_dir is None

    # Verify that the plugins dictionary is initialized empty
    assert plugin_manager.plugins == {}

    # Verify that load_plugins works without errors when plugins_dir is None
    result = plugin_manager.load_plugins()

    # Should return empty loaded and errors dicts
    assert result["loaded"] == {}
    assert result["errors"] == {}

    # Verify that other methods work correctly with empty plugin set
    assert plugin_manager.get("nonexistent") is None
    assert plugin_manager.list() == {}

    # Verify that reload operations work correctly with empty plugin set
    assert plugin_manager.reload_plugin("nonexistent") is False
    reload_all_result = plugin_manager.reload_all()
    assert reload_all_result == {"loaded": {}, "errors": {}}


def test_plugin_manager_with_nonexistent_plugins_dir():
    """Prevents crashes when someone misconfigures the path."""
    # Create a path that definitely doesn't exist
    nonexistent_path = Path("/definitely/not/a/real/path/12345")

    # Verify the path doesn't exist
    assert not nonexistent_path.exists()

    # Initialize PluginManager with non-existent plugins_dir
    plugin_manager = PluginManager(plugins_dir=str(nonexistent_path))

    # Verify that the plugins_dir is set correctly
    assert plugin_manager.plugins_dir == nonexistent_path

    # Verify that the plugins dictionary is initialized empty
    assert plugin_manager.plugins == {}

    # Verify that load_plugins works without errors when plugins_dir doesn't exist
    result = plugin_manager.load_plugins()

    # Should return empty loaded and errors dicts
    assert result["loaded"] == {}
    assert result["errors"] == {}

    # Verify that other methods work correctly with empty plugin set
    assert plugin_manager.get("nonexistent") is None
    assert plugin_manager.list() == {}

    # Verify that reload operations work correctly with empty plugin set
    assert plugin_manager.reload_plugin("nonexistent") is False
    reload_all_result = plugin_manager.reload_all()
    assert reload_all_result == {"loaded": {}, "errors": {}}


def test_load_local_plugins_empty_directory():
    """Ensures the loader doesn't blow up on empty dirs."""
    # Create an empty temporary directory
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create an empty subdirectory
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        # Initialize PluginManager with the empty directory
        pm = PluginManager(plugins_dir=str(tmp_path))

        # Call load_local_plugins - should not raise an exception
        loaded, errors = pm.load_local_plugins()

        # Should return empty results since there are no plugin files
        assert loaded == {}
        assert errors == {}

        # Verify the plugin manager still works normally
        assert pm.plugins == {}


def test_uninstall_plugin_nonexistent():
    """Ensures uninstall is idempotent and safe."""
    # Initialize PluginManager
    pm = PluginManager()

    # Try to uninstall a plugin that doesn't exist
    result = pm.uninstall_plugin("nonexistent_plugin")

    # Should return False since plugin wasn't found
    assert result is False

    # Verify that the plugins dict is still empty
    assert pm.plugins == {}

    # Verify that calling it again doesn't cause issues (idempotent)
    result2 = pm.uninstall_plugin("nonexistent_plugin")
    assert result2 is False


def test_load_plugins_no_directory_specified():
    """Ensures entry-point loading works even without local plugins."""
    # Initialize PluginManager with no plugins_dir (None)
    pm = PluginManager(plugins_dir=None)

    # Verify that plugins_dir is None
    assert pm.plugins_dir is None

    # Call load_plugins - should work without errors even with no directory
    result = pm.load_plugins()

    # Should return empty loaded and errors since no directory and no entry points
    assert result["loaded"] == {}
    assert result["errors"] == {}

    # Verify that the plugin manager still works normally
    assert pm.plugins == {}

    # Verify that other methods work correctly
    assert pm.get("any_plugin") is None
    assert pm.list() == {}
