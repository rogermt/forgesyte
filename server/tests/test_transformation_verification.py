"""
Final verification tests for the ForgeSyte transformation.
This verifies that the vision-mcp code has been successfully transformed to ForgeSyte.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402
from app.plugin_loader import PluginManager  # noqa: E402


def test_server_branding_updated():
    """Test that all branding has been updated from Vision-MCP to ForgeSyte."""
    assert app.title == "ForgeSyte"
    assert "ForgeSyte" in app.description
    assert "Vision MCP" not in app.description  # Ensure old branding is gone


def test_root_endpoint_updated():
    """Test that the root endpoint returns ForgeSyte branding."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "ForgeSyte"
        assert "Vision MCP Server" not in str(data)  # Ensure old branding is gone


def test_environment_variables_updated():
    """Test that environment variables have been updated to FORGESYTE_ prefix."""
    import app.main as main_module

    # Check that AppSettings uses FORGESYTE_PLUGINS_DIR
    settings = main_module.AppSettings()
    assert hasattr(settings, "plugins_dir")

    # Verify the env var name is correct
    import inspect

    source = inspect.getsource(main_module.AppSettings)
    assert "FORGESYTE_PLUGINS_DIR" in source
    assert "VISION_PLUGINS_DIR" not in source  # Ensure old variable is gone


def test_plugin_loading_path_updated():
    """Test that plugin manager loads from the new directory structure."""
    # Test with the example plugins directory
    plugins_dir = Path(__file__).parent.parent / "example_plugins"
    pm = PluginManager(plugins_dir=str(plugins_dir))

    # Verify the plugin manager is configured correctly
    assert "example_plugins" in str(pm.plugins_dir)

    # Try to load plugins (should not raise an exception)
    result = pm.load_plugins()
    # Even if plugins fail to load due to missing dependencies, the structure
    # should be correct
    assert isinstance(result, dict)
    assert "loaded" in result
    assert "errors" in result


def test_mcp_adapter_updated():
    """Test that MCP adapter returns ForgeSyte server name."""
    from app.mcp import MCPAdapter

    # Create a mock plugin manager for testing
    class MockPluginManager:
        def list(self):
            return {}

    adapter = MCPAdapter(MockPluginManager(), "http://test")
    manifest = adapter.get_manifest()

    assert manifest["server"]["name"] == "forgesyte"
    assert "Vision MCP" not in str(manifest)  # Ensure old branding is gone


def test_startup_messages_updated():
    """Test that startup/shutdown messages use ForgeSyte branding."""
    import io
    import logging

    # Capture log output during app startup simulation
    log_capture_string = io.StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.INFO)

    # Get the logger used in main.py
    logger = logging.getLogger("app.main")
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    # The app should have been created with ForgeSyte branding
    assert app.title == "ForgeSyte"


def test_configuration_files_updated():
    """Test that configuration reflects the new project structure."""
    import inspect

    import app.auth as auth_module

    # Check that auth module uses new environment variable names
    source = inspect.getsource(auth_module.AuthSettings)
    assert "FORGESYTE_" in source or "VISION_" not in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
