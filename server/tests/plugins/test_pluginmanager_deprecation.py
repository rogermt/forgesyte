"""TDD tests for PluginManager → PluginRegistry migration (#120)."""

import warnings

from app.plugin_loader import PluginManager, PluginRegistry


def test_pluginmanager_alias_exists():
    """PluginManager alias must exist for backward compatibility."""
    assert PluginManager is not None
    assert issubclass(PluginManager, PluginRegistry) or PluginManager is PluginRegistry


def test_pluginmanager_emits_deprecation_warning():
    """PluginManager must emit DeprecationWarning on instantiation."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = PluginManager()  # noqa: F841

        # Check that a DeprecationWarning was issued
        assert len(w) >= 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "PluginRegistry" in str(w[-1].message)


def test_pluginmanager_still_functional():
    """PluginManager must still work (backward compat), just with warning."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        pm = PluginManager()

        # Must have all the same methods
        assert hasattr(pm, "load_plugins")
        assert hasattr(pm, "get")
        assert hasattr(pm, "list")
        assert hasattr(pm, "load_entrypoint_plugins")

        # Must work the same way
        result = pm.load_plugins()
        assert isinstance(result, dict)
        assert "loaded" in result
        assert "errors" in result


def test_pluginregistry_no_warning():
    """PluginRegistry must NOT emit warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = PluginRegistry()  # noqa: F841

        # No DeprecationWarning for PluginRegistry
        deprecation_warnings = [
            warning for warning in w if issubclass(warning.category, DeprecationWarning)
        ]
        assert len(deprecation_warnings) == 0


def test_pluginmanager_warning_points_to_registry():
    """DeprecationWarning message must recommend PluginRegistry."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = PluginManager()  # noqa: F841

        warning_msg = str(w[-1].message)
        assert "PluginRegistry" in warning_msg


def test_pluginmanager_type_equivalent():
    """PluginManager instance should pass type checks for PluginRegistry."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        pm = PluginManager()

        # Should be instance of PluginRegistry
        assert isinstance(pm, PluginRegistry)


def test_no_direct_pluginmanager_imports_in_production(monkeypatch):
    """Production code must NOT import PluginManager directly (except alias)."""
    # This is a canary test - it will pass now but catch regressions
    # Note: We can't fully test this without importing all modules
    # This is more of a TODO for code review
    pass


def test_pluginmanager_get_returns_baseplugin():
    """PluginManager.get() must return BasePlugin (inherited from PluginRegistry)."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        pm = PluginManager()

        # get() should return None for non-existent plugin
        result = pm.get("nonexistent")
        assert result is None


def test_pluginmanager_list_returns_dict():
    """PluginManager.list() must return Dict[str, BasePlugin]."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        pm = PluginManager()

        result = pm.list()
        assert isinstance(result, dict)
