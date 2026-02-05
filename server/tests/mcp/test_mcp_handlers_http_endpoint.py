"""Tests for MCP HTTP POST /mcp endpoint."""

import os
import sys
from typing import Dict, Optional

import pytest
from fastapi.testclient import TestClient

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402


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
        self.tools = {
            "default": {
                "handler": "analyze_image",
                "description": self.description,
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        }

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

    def analyze_image(self, image_bytes: bytes, options: dict) -> dict:
        """Analyze image bytes and return results."""
        return {
            "text": "mock result",
            "confidence": 0.95,
            "blocks": [],
        }

    def run_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a tool by name."""
        if tool_name == "default":
            return self.analyze_image(args["image"], args.get("options", {}))
        raise ValueError(f"Unknown tool: {tool_name}")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass


class MockPluginManager:
    """Mock plugin manager for testing."""

    def __init__(self, plugins: Optional[Dict[str, MockPlugin]] = None):
        self.plugins = plugins or {
            "test_tool": MockPlugin(
                name="test_tool",
                title="Test Tool",
                description="A test tool",
                inputs=["text"],
                outputs=["text"],
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


class TestMCPHTTPEndpoint:
    """Tests for POST /mcp endpoint."""

    def test_mcp_endpoint_accepts_valid_request(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp accepts valid JSON-RPC request."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_mcp_endpoint_returns_json_rpc_response(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp returns proper JSON-RPC response."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            # Valid JSON-RPC response fields
            assert "jsonrpc" in data
            assert data["jsonrpc"] == "2.0"
            assert "id" in data
            assert data["id"] == 1

    def test_mcp_endpoint_handles_successful_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp successfully handles ping method."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            # Should have result for successful call
            assert "result" in data
            assert "error" not in data
            assert data["result"]["status"] == "pong"

    def test_mcp_endpoint_handles_initialize_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp handles initialize method."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "result" in data
            assert "serverInfo" in data["result"]
            assert "capabilities" in data["result"]

    def test_mcp_endpoint_handles_tools_list_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp handles tools/list method."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "result" in data
            assert "tools" in data["result"]
            assert isinstance(data["result"]["tools"], list)

    def test_mcp_endpoint_handles_invalid_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp returns error for unknown method."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "unknown_method",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            # Should have error for unknown method
            assert "error" in data
            assert data["error"]["code"] == -32601  # METHOD_NOT_FOUND
            assert "result" not in data

    def test_mcp_endpoint_handles_missing_params(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp handles missing required params."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {},  # Missing 'name' parameter
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            # Should have error for invalid params
            assert "error" in data
            assert data["error"]["code"] == -32602  # INVALID_PARAMS

    def test_mcp_endpoint_handles_malformed_json(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp handles malformed JSON."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            response = client.post("/v1/mcp", content="{invalid json")

            # Should return 400 or JSON-RPC parse error
            assert response.status_code >= 400

    def test_mcp_endpoint_handles_notification(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp handles notification (request without id)."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                # No 'id' field = notification
            }

            response = client.post("/v1/mcp", json=request_data)

            # Notification responses can be 200 with no response body
            # or 204 No Content
            assert response.status_code in [200, 204]

    def test_mcp_endpoint_preserves_request_id(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp preserves request ID in response."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            for test_id in [1, 2, "test-string-id", 999]:
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "params": {},
                    "id": test_id,
                }

                response = client.post("/v1/mcp", json=request_data)
                data = response.json()

                assert data["id"] == test_id

    def test_mcp_endpoint_tools_call_with_valid_tool(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp can call a valid tool."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "test_tool",
                    "arguments": {"image": "test_data"},
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "result" in data
            assert "content" in data["result"]

    def test_mcp_endpoint_tools_call_with_invalid_tool(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp returns error for nonexistent tool."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {},
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "error" in data

    def test_mcp_endpoint_returns_http_200_for_valid_request(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp returns HTTP 200 for valid requests."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200

    def test_mcp_endpoint_requires_jsonrpc_field(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp validates jsonrpc field."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                # Missing 'jsonrpc' field
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should return error
            assert response.status_code >= 400

    def test_mcp_endpoint_requires_method_field(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp validates method field."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                # Missing 'method' field
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should return error
            assert response.status_code >= 400

    def test_mcp_endpoint_session_isolation(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that separate requests don't share state."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # Make first request
            request_data_1 = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }
            response_1 = client.post("/v1/mcp", json=request_data_1)
            data_1 = response_1.json()

            # Make second request with different ID
            request_data_2 = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 2,
            }
            response_2 = client.post("/v1/mcp", json=request_data_2)
            data_2 = response_2.json()

            # IDs should be preserved independently
            assert data_1["id"] == 1
            assert data_2["id"] == 2

    def test_mcp_endpoint_content_type_json(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that /v1/mcp accepts application/json content type."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post(
                "/v1/mcp",
                json=request_data,
                headers={"Content-Type": "application/json"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/json")
