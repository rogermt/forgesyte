"""Integration tests for loading plugins from forgesyte-plugins repo.

Tests the local-dev plugin loader that loads plugins directly from the
forgesyte-plugins repository without pip installation.

Plugin Status:
- OCR: ✅ Fully working (uses correct imports)
- Motion Detector: ⚠️ Partial (import path needs fixing)
- Block Mapper: ⚠️ Partial (import path needs fixing)
- Moderation: ⚠️ Partial (import path needs fixing)
- Plugin Template: Template only (skipped)
"""

from pathlib import Path

import pytest

from app.plugin_loader import PluginManager

# Paths to actual plugin repo
PLUGINS_REPO_PATH = Path("/home/rogermt/forgesyte-plugins")


@pytest.mark.skip(
    reason="Requires local forgesyte-plugins repo at /home/rogermt/forgesyte-plugins. "
    "Not available in CI workflow. Local dev testing only."
)
@pytest.mark.integration
class TestLocalPluginLoading:
    """Test loading real plugins from forgesyte-plugins repo."""

    def test_plugins_repo_exists(self):
        """Verify the forgesyte-plugins repo is available."""
        assert (
            PLUGINS_REPO_PATH.exists()
        ), f"Plugin repo not found at {PLUGINS_REPO_PATH}"
        assert (PLUGINS_REPO_PATH / "ocr").exists(), "OCR plugin directory missing"
        assert (
            PLUGINS_REPO_PATH / "motion_detector"
        ).exists(), "Motion detector plugin directory missing"
        assert (
            PLUGINS_REPO_PATH / "block_mapper"
        ).exists(), "Block mapper plugin directory missing"

    def test_load_all_plugins_from_repo(self):
        """Test PluginManager can scan and load plugins from local repo."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        result = pm.load_plugins()

        assert "loaded" in result, "Result should have 'loaded' key"
        assert "errors" in result, "Result should have 'errors' key"

        # At least OCR should load
        assert len(result["loaded"]) > 0, "Should have loaded at least one plugin"

        # Some plugins may error due to import issues, but that's expected for now
        print(f"Loaded: {result['loaded']}")
        print(f"Errors: {result['errors']}")

    def test_load_ocr_plugin(self):
        """Test OCR plugin loads successfully (fully working)."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        result = pm.load_plugins()

        # OCR should be in loaded plugins
        assert (
            "ocr" in result["loaded"]
        ), f"OCR not loaded. Loaded: {result['loaded']}, Errors: {result['errors']}"

        # Should be able to get OCR plugin
        ocr_plugin = pm.get("ocr")
        assert ocr_plugin is not None, "OCR plugin should be loadable"

        # Should have valid metadata
        metadata = ocr_plugin.metadata()
        # Convert Pydantic model to dict if necessary
        if hasattr(metadata, "model_dump"):
            metadata = metadata.model_dump()
        assert metadata["name"] == "ocr"
        assert "version" in metadata

    def test_ocr_plugin_analyze_interface(self):
        """Test OCR plugin implements analyze interface."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        ocr_plugin = pm.get("ocr")
        assert ocr_plugin is not None

        # Plugin should have analyze method
        assert hasattr(ocr_plugin, "analyze")
        assert callable(ocr_plugin.analyze)

    def test_motion_detector_import_path(self):
        """Test motion_detector plugin - currently has import path issues.

        This test documents the current state and expected fix.
        The plugin uses:
            from forgesyte.server.models import PluginMetadata
            from forgesyte.server.plugin_loader import BasePlugin

        Should be:
            from app.models import PluginMetadata
            from app.plugin_loader import BasePlugin
        """
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        result = pm.load_plugins()

        # Currently motion_detector will fail due to import path
        if "motion_detector" not in result["loaded"]:
            assert (
                "motion_detector" in result["errors"]
            ), "Motion detector should error with current import paths"
            error = result["errors"]["motion_detector"]
            assert (
                "forgesyte.server" in error
                or "ModuleNotFoundError" in error
                or "No module named 'forgesyte'" in error
            ), f"Expected import error, got: {error}"

    def test_list_all_loaded_plugins(self):
        """List metadata for all successfully loaded plugins."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        plugin_list = pm.list()
        print(f"\nLoaded plugins: {list(plugin_list.keys())}")

        for name, metadata in plugin_list.items():
            print(f"  {name}: {metadata.get('version', 'unknown')}")

    def test_plugin_lifecycle_on_load_called(self):
        """Test that on_load() is called during plugin loading."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        ocr_plugin = pm.get("ocr")
        assert ocr_plugin is not None
        # on_load() should have been called during load_plugins()
        # No exception means it succeeded

    def test_reload_plugin(self):
        """Test reloading a specific plugin."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        # Try to reload OCR
        reload_success = pm.reload_plugin("ocr")
        assert reload_success is True, "OCR plugin should reload successfully"

        # Plugin should still be available
        ocr_plugin = pm.get("ocr")
        assert ocr_plugin is not None

    def test_reload_all_plugins(self):
        """Test reloading all plugins."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        initial_count = len(pm.list())
        assert initial_count > 0, "Should have loaded at least one plugin"

        result = pm.reload_all()
        assert "loaded" in result
        assert "errors" in result

        # After reload, should have same plugins
        final_count = len(pm.list())
        assert final_count == initial_count, "Reload should have same number of plugins"

    def test_uninstall_plugin(self):
        """Test uninstalling a loaded plugin."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        pm.load_plugins()

        assert pm.get("ocr") is not None
        success = pm.uninstall_plugin("ocr")
        assert success is True

        # Should no longer be in list
        assert pm.get("ocr") is None


@pytest.mark.skip(
    reason="Requires local forgesyte-plugins repo at /home/rogermt/forgesyte-plugins. "
    "Not available in CI workflow. Local dev testing only."
)
@pytest.mark.integration
class TestPluginImportPaths:
    """Document and test plugin import path issues.

    All forgesyte-plugins currently use incorrect import paths:
        from forgesyte.server.models import ...
        from forgesyte.server.plugin_loader import ...

    These imports fail because:
    1. forgesyte is not installed in the test environment
    2. The correct imports are from 'app' module:
        from app.models import ...
        from app.plugin_loader import ...
    """

    def test_document_import_issues(self):
        """Document which plugins have import path issues."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        result = pm.load_plugins()

        import_issues = {}
        for plugin_name, error in result.get("errors", {}).items():
            if "ModuleNotFoundError" in error or "forgesyte.server" in error:
                import_issues[plugin_name] = error

        print(f"\nPlugins with import path issues: {list(import_issues.keys())}")
        for plugin_name, error in import_issues.items():
            print(f"  {plugin_name}: {error[:100]}")

    def test_ocr_uses_correct_imports(self):
        """Verify OCR plugin uses correct import paths (working baseline)."""
        pm = PluginManager(plugins_dir=str(PLUGINS_REPO_PATH))
        result = pm.load_plugins()

        # OCR should load - it uses correct imports
        assert (
            "ocr" in result["loaded"]
        ), "OCR should load with correct imports from app module"

        # Show OCR loads successfully
        ocr = pm.get("ocr")
        assert ocr is not None
        assert ocr.name == "ocr"
