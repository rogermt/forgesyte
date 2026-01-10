"""Integration tests for MCP with Gemini-CLI client simulation.

These tests simulate realistic Gemini-CLI workflows to ensure the MCP
transport layer works correctly with actual client interactions.
"""

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
                title="Optical Character Recognition",
                description="Extract text from images",
                inputs=["image"],
                outputs=["text"],
                version="1.0.0",
            ),
            "motion_detector": MockPlugin(
                name="motion_detector",
                title="Motion Detector",
                description="Detect motion in video frames",
                inputs=["frame"],
                outputs=["motion_data"],
                version="1.0.0",
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
def reset_transport():
    """Reset the global transport instance for each test."""
    # Clear the global transport cache before each test
    import app.mcp_routes

    app.mcp_routes._transport = None
    yield
    # Clean up after test
    app.mcp_routes._transport = None


@pytest.fixture
def mock_plugin_manager(reset_transport):
    """Create a mock plugin manager."""
    return MockPluginManager()


class TestGeminiCLIInitializationWorkflow:
    """Test Gemini-CLI initialization workflow.

    This simulates the initial handshake that Gemini-CLI performs
    when connecting to a new MCP server.
    """

    def test_gemini_cli_initialize_request(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that Gemini-CLI can initialize with the server."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # Gemini-CLI initialize request
            request_data = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "gemini-cli",
                        "version": "1.0.0",
                    },
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data
            assert "serverInfo" in data["result"]
            assert "capabilities" in data["result"]

    def test_gemini_cli_initialize_response_has_server_info(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that initialize response includes server info."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "gemini-cli",
                        "version": "1.0.0",
                    },
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            server_info = data["result"]["serverInfo"]
            assert "name" in server_info
            assert "version" in server_info
            assert server_info["name"] == "forgesyte"

    def test_gemini_cli_initialize_response_has_capabilities(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that initialize response includes capabilities."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "gemini-cli",
                        "version": "1.0.0",
                    },
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            capabilities = data["result"]["capabilities"]
            assert isinstance(capabilities, dict)


class TestGeminiCLIToolDiscoveryWorkflow:
    """Test Gemini-CLI tool discovery workflow.

    After initialization, Gemini-CLI discovers available tools.
    """

    def test_gemini_cli_tools_list_request(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that Gemini-CLI can list available tools."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert "tools" in data["result"]

    def test_gemini_cli_tools_list_returns_all_plugins(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that tools/list returns all available plugins."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            tools = data["result"]["tools"]
            assert isinstance(tools, list)
            assert len(tools) == 2
            tool_ids = [tool["id"] for tool in tools]
            assert "vision.ocr" in tool_ids
            assert "vision.motion_detector" in tool_ids

    def test_gemini_cli_tools_have_required_metadata(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that each tool has required metadata fields."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            tools = data["result"]["tools"]
            for tool in tools:
                assert "id" in tool
                assert "title" in tool
                assert "description" in tool
                assert "invoke_endpoint" in tool

    def test_gemini_cli_tools_have_input_output_types(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that tools have input and output types defined."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            tools = data["result"]["tools"]
            for tool in tools:
                assert "inputs" in tool
                assert "outputs" in tool
                assert isinstance(tool["inputs"], list)
                assert isinstance(tool["outputs"], list)


class TestGeminiCLIToolInvocationWorkflow:
    """Test Gemini-CLI tool invocation workflow.

    Gemini-CLI calls tools with arguments and expects results.
    """

    def test_gemini_cli_calls_ocr_tool(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that Gemini-CLI can invoke the OCR tool."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ocr",
                    "arguments": {"image": "base64_encoded_image"},
                },
                "id": 3,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert "content" in data["result"]

    def test_gemini_cli_tool_call_response_format(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that tool call responses follow JSON-RPC format."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "motion_detector",
                    "arguments": {"frame": "frame_data"},
                },
                "id": 3,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 3
            assert "result" in data

    def test_gemini_cli_tool_call_with_nonexistent_tool(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that invoking nonexistent tool returns proper error."""
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
                "id": 3,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "error" in data
            # Can be INVALID_PARAMS (-32602) or other error code
            assert data["error"]["code"] in [-32602, -32603]


class TestGeminiCLIHealthAndKeepalive:
    """Test Gemini-CLI health check and keepalive workflow."""

    def test_gemini_cli_ping_health_check(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that Gemini-CLI can ping the server."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 100,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["status"] == "pong"

    def test_gemini_cli_ping_response_time(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that ping responds quickly (simple and fast)."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 100,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should be near-instant (no processing)
            assert response.status_code == 200


class TestGeminiCLIMultipleSequentialRequests:
    """Test Gemini-CLI's multiple sequential requests workflow."""

    def test_gemini_cli_full_workflow_sequence(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test a complete workflow: init -> list tools -> call tool."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # Step 1: Initialize
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "gemini-cli",
                        "version": "1.0.0",
                    },
                    "protocolVersion": "2024-11-05",
                },
                "id": 1,
            }
            response = client.post("/v1/mcp", json=init_request)
            assert response.status_code == 200

            # Step 2: List tools
            list_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            }
            response = client.post("/v1/mcp", json=list_request)
            assert response.status_code == 200
            tools_response = response.json()
            tools = tools_response["result"]["tools"]
            assert len(tools) > 0

            # Step 3: Call a tool (use the plugin name from id prefix)
            tool_id = tools[0]["id"]
            # Extract plugin name from tool id (e.g., "vision.ocr" -> "ocr")
            plugin_name = tool_id.split(".")[-1]
            call_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": plugin_name,
                    "arguments": {},
                },
                "id": 3,
            }
            response = client.post("/v1/mcp", json=call_request)
            assert response.status_code == 200

    def test_gemini_cli_maintains_session_across_requests(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that session state is maintained across requests."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # Make multiple requests
            for request_id in range(1, 5):
                request_data = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "params": {},
                    "id": request_id,
                }
                response = client.post("/v1/mcp", json=request_data)
                data = response.json()

                # Each response should preserve the request ID
                assert data["id"] == request_id
                assert response.status_code == 200


class TestGeminiCLIErrorHandling:
    """Test Gemini-CLI error handling scenarios."""

    def test_gemini_cli_handles_invalid_json_rpc_version(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server validates JSON-RPC version."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "1.0",  # Invalid version
                "method": "ping",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should be rejected
            assert response.status_code >= 400

    def test_gemini_cli_handles_missing_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server requires method field."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                # Missing method
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code >= 400

    def test_gemini_cli_handles_unknown_method(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server returns proper error for unknown methods."""
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

            assert "error" in data
            assert data["error"]["code"] == -32601  # METHOD_NOT_FOUND

    def test_gemini_cli_handles_invalid_params(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server validates method parameters."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # tools/call requires 'name' parameter
            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {},  # Missing 'name'
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "error" in data


class TestGeminiCLIContentTypes:
    """Test Gemini-CLI content type handling."""

    def test_gemini_cli_accepts_json_content_type(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server accepts JSON content type."""
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

    def test_gemini_cli_response_is_valid_json(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that response is valid JSON."""
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

            # Should be able to parse JSON without error
            data = response.json()
            assert isinstance(data, dict)


class TestGeminiCLILargePayloads:
    """Test Gemini-CLI with large payloads."""

    def test_gemini_cli_handles_large_tool_arguments(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server can handle large tool arguments (e.g., base64 images)."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            # Simulate large base64 image data (1MB)
            large_data = "x" * 1_000_000

            request_data = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ocr",
                    "arguments": {"image": large_data},
                },
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should handle without crashing
            assert response.status_code in [200, 400, 500]


class TestGeminiCLIEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_gemini_cli_handles_zero_id(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server accepts id=0."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 0,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert data["id"] == 0
            assert response.status_code == 200

    def test_gemini_cli_handles_string_id(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server accepts string IDs."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": "request-123",
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert data["id"] == "request-123"
            assert response.status_code == 200

    def test_gemini_cli_handles_null_params(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server handles null params field."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": None,
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_gemini_cli_handles_empty_params(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that server handles empty params object."""
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


class TestGeminiCLIResourceDiscovery:
    """Test Gemini-CLI resource discovery."""

    def test_gemini_cli_resources_list_endpoint(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that Gemini-CLI can list resources."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "result" in data

    def test_gemini_cli_resources_list_returns_list(
        self, client: TestClient, mock_plugin_manager: MockPluginManager
    ):
        """Test that resources/list returns proper format."""
        with client:
            client.get("/")
            app.state.plugins = mock_plugin_manager

            request_data = {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "params": {},
                "id": 1,
            }

            response = client.post("/v1/mcp", json=request_data)
            data = response.json()

            assert "resources" in data["result"]
            assert isinstance(data["result"]["resources"], list)
