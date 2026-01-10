"""Integration tests for MCP API endpoints."""

import os
import sys
from typing import Dict, Optional

import pytest
from fastapi.testclient import TestClient

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402
from app.mcp_adapter import (  # noqa: E402
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
)


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(
        self,
        name: str = "test_plugin",
        description: str = "Test plugin",
        title: Optional[str] = None,
        inputs: Optional[list] = None,
        outputs: Optional[list] = None,
        version: str = "1.0.0",
    ):
        self.name = name
        self.description = description
        self.title = title
        self.inputs = inputs or ["image"]
        self.outputs = outputs or ["json"]
        self.version = version

    def metadata(self) -> dict:
        """Return plugin metadata."""
        meta = {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "version": self.version,
        }
        if self.title:
            meta["title"] = self.title
        return meta

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass


class MockPluginManager:
    """Mock plugin manager for testing."""

    def __init__(self, plugins: Optional[Dict[str, MockPlugin]] = None):
        self.plugins = plugins or {
            "ocr": MockPlugin(
                name="ocr",
                title="OCR Engine",
                description="Optical Character Recognition",
                inputs=["image"],
                outputs=["text"],
            ),
            "motion": MockPlugin(
                name="motion",
                title="Motion Detector",
                description="Detect motion in video frames",
                inputs=["image"],
                outputs=["json"],
            ),
        }

    def list(self) -> Dict[str, dict]:
        """List all plugins with their metadata."""
        return {name: plugin.metadata() for name, plugin in self.plugins.items()}

    def get(self, name: str) -> Optional[MockPlugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_plugin_manager():
    """Create a mock plugin manager."""
    return MockPluginManager()


def test_mcp_manifest_endpoint_returns_valid_json(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that /v1/mcp-manifest returns valid JSON."""
    # Set up the app with mock plugin manager
    with client:
        client.get("/")  # Trigger app startup
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


def test_mcp_manifest_contains_tools(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that manifest contains tools from plugins."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert len(data["tools"]) == 2  # ocr and motion


def test_mcp_manifest_contains_server_info(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that manifest contains server information."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        assert "server" in data
        server = data["server"]
        assert server["name"] == MCP_SERVER_NAME
        assert server["version"] == MCP_SERVER_VERSION
        assert server["mcp_version"] == MCP_PROTOCOL_VERSION


def test_mcp_manifest_tool_structure(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that tools in manifest have correct structure."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        tools = data["tools"]
        ocr_tool = next((t for t in tools if t["id"] == "vision.ocr"), None)

        assert ocr_tool is not None
        # Title defaults to plugin name in schema
        assert ocr_tool["title"] == "ocr"
        assert ocr_tool["description"] == "Optical Character Recognition"
        assert "inputs" in ocr_tool
        assert "outputs" in ocr_tool
        assert "invoke_endpoint" in ocr_tool


def test_mcp_manifest_version_field(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that manifest has version field."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        assert "version" in data
        assert data["version"] == "1.0"


def test_mcp_version_endpoint_returns_valid_json(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that /v1/mcp-version returns valid JSON."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-version")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


def test_mcp_version_contains_protocol_version(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that version endpoint returns MCP protocol version."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-version")
        data = response.json()

        assert "mcp_version" in data
        assert data["mcp_version"] == MCP_PROTOCOL_VERSION


def test_mcp_version_contains_server_version(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that version endpoint returns server version."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-version")
        data = response.json()

        assert "server_version" in data
        assert data["server_version"] == MCP_SERVER_VERSION


def test_mcp_version_contains_server_name(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that version endpoint returns server name."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-version")
        data = response.json()

        assert "server_name" in data
        assert data["server_name"] == MCP_SERVER_NAME


def test_mcp_version_response_structure(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test the complete structure of version endpoint response."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-version")
        data = response.json()

        # Should have all three version fields
        assert "server_name" in data
        assert "server_version" in data
        assert "mcp_version" in data

        # Values should be strings
        assert isinstance(data["server_name"], str)
        assert isinstance(data["server_version"], str)
        assert isinstance(data["mcp_version"], str)


def test_mcp_manifest_with_empty_plugins(client: TestClient):
    """Test manifest endpoint with no plugins loaded."""

    # Create a mock manager with no plugins
    class EmptyPluginManager:
        def __init__(self):
            self.plugins = {}

        def list(self):
            return {}

    empty_manager = EmptyPluginManager()

    with client:
        client.get("/")
        app.state.plugins = empty_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        # Should still return valid manifest with empty tools list
        assert response.status_code == 200
        assert "server" in data
        assert "tools" in data
        assert len(data["tools"]) == 0


def test_mcp_version_with_empty_plugins(client: TestClient):
    """Test version endpoint works even with no plugins loaded."""

    # Create a mock manager with no plugins
    class EmptyPluginManager:
        def __init__(self):
            self.plugins = {}

        def list(self):
            return {}

    empty_manager = EmptyPluginManager()

    with client:
        client.get("/")
        app.state.plugins = empty_manager

        response = client.get("/v1/mcp-version")
        data = response.json()

        # Should return version info regardless of plugins
        assert response.status_code == 200
        assert data["mcp_version"] == MCP_PROTOCOL_VERSION
        assert data["server_version"] == MCP_SERVER_VERSION


def test_mcp_manifest_invoke_endpoint_includes_base_url(
    client: TestClient, mock_plugin_manager: MockPluginManager
):
    """Test that tools have invoke_endpoint with base URL."""
    with client:
        client.get("/")
        app.state.plugins = mock_plugin_manager

        response = client.get("/v1/mcp-manifest")
        data = response.json()

        tools = data["tools"]
        assert len(tools) > 0

        for tool in tools:
            assert "invoke_endpoint" in tool
            # Endpoint should contain plugin parameter
            assert "plugin=" in tool["invoke_endpoint"]
            assert "/v1/analyze" in tool["invoke_endpoint"]
