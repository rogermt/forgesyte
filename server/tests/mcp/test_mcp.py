"""Comprehensive MCP testing - unit tests and protocol validation."""

import json
import os
import sys
from typing import Optional
from unittest.mock import Mock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import (  # noqa: E402
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    build_gemini_extension_manifest,
)
from app.models_pydantic import MCPManifest  # noqa: E402
from app.plugin_loader import PluginRegistry  # noqa: E402


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(
        self,
        name: str = "test_plugin",
        description: str = "Test plugin",
        inputs: Optional[list] = None,
        outputs: Optional[list] = None,
        version: str = "1.0.0",
    ):
        self.name = name
        self.description = description
        self.inputs = inputs or ["image"]
        self.outputs = outputs or ["json"]
        self.version = version

    def metadata(self) -> dict:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "version": self.version,
        }


class TestMCPProtocolValidation:
    """Test MCP protocol compliance and manifest validation."""

    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager."""
        manager = Mock(spec=PluginRegistry)
        return manager

    @pytest.fixture
    def adapter(self, mock_plugin_manager):
        """Create MCPAdapter instance."""
        return MCPAdapter(
            plugin_manager=mock_plugin_manager, base_url="http://localhost:8000"
        )

    def test_manifest_json_structure_valid(self, adapter, mock_plugin_manager):
        """Test manifest can be serialized to valid JSON."""
        plugin = MockPlugin(name="ocr", description="OCR Plugin")
        mock_plugin_manager.list.return_value = {"ocr": plugin.metadata()}

        manifest = adapter.get_manifest()

        # Should be JSON-serializable
        json_str = json.dumps(manifest)
        assert isinstance(json_str, str)

        # Should parse back correctly
        parsed = json.loads(json_str)
        assert parsed["server"]["name"] == MCP_SERVER_NAME

    def test_manifest_has_all_required_fields(self, adapter, mock_plugin_manager):
        """Test manifest has all required top-level fields."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert "server" in manifest
        assert "tools" in manifest
        assert "version" in manifest

    def test_server_info_has_all_required_fields(self, adapter, mock_plugin_manager):
        """Test server info in manifest has all required fields."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()
        server = manifest["server"]

        assert "name" in server
        assert "version" in server
        assert "mcp_version" in server

    def test_tool_has_all_required_fields(self, adapter, mock_plugin_manager):
        """Test each tool in manifest has all required fields."""
        plugin = MockPlugin(name="test", description="Test")
        mock_plugin_manager.list.return_value = {"test": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert "id" in tool
        assert "title" in tool
        assert "description" in tool
        assert "inputs" in tool
        assert "outputs" in tool
        assert "invoke_endpoint" in tool

    def test_tool_id_format_correct(self, adapter, mock_plugin_manager):
        """Test tool IDs follow vision.{plugin_name} format."""
        plugins = {
            "ocr": MockPlugin(name="ocr", description="OCR"),
            "motion": MockPlugin(name="motion", description="Motion"),
            "face_detect": MockPlugin(name="face_detect", description="Face"),
        }
        mock_plugin_manager.list.return_value = {
            name: plugin.metadata() for name, plugin in plugins.items()
        }

        manifest = adapter.get_manifest()

        for tool in manifest["tools"]:
            assert tool["id"].startswith("vision.")
            assert len(tool["id"]) > len("vision.")

    def test_mcp_version_matches_constant(self, adapter, mock_plugin_manager):
        """Test manifest uses correct MCP protocol version."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert manifest["server"]["mcp_version"] == MCP_PROTOCOL_VERSION

    def test_server_name_matches_constant(self, adapter, mock_plugin_manager):
        """Test manifest uses correct server name."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert manifest["server"]["name"] == MCP_SERVER_NAME

    def test_server_version_matches_constant(self, adapter, mock_plugin_manager):
        """Test manifest uses correct server version."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert manifest["server"]["version"] == MCP_SERVER_VERSION

    def test_manifest_version_format(self, adapter, mock_plugin_manager):
        """Test manifest version field is properly formatted."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert manifest["version"] == "1.0"
        assert isinstance(manifest["version"], str)

    def test_manifest_tools_is_list(self, adapter, mock_plugin_manager):
        """Test tools field is always a list."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert isinstance(manifest["tools"], list)

    def test_inputs_outputs_are_lists(self, adapter, mock_plugin_manager):
        """Test tool inputs and outputs are lists."""
        plugin = MockPlugin(
            name="test", description="Test", inputs=["a", "b"], outputs=["c"]
        )
        mock_plugin_manager.list.return_value = {"test": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert isinstance(tool["inputs"], list)
        assert isinstance(tool["outputs"], list)

    def test_invoke_endpoint_includes_plugin_name(self, adapter, mock_plugin_manager):
        """Test invoke endpoint includes the plugin name as parameter."""
        plugin = MockPlugin(name="custom_plugin", description="Custom")
        mock_plugin_manager.list.return_value = {"custom_plugin": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert "plugin=custom_plugin" in tool["invoke_endpoint"]


class TestMCPAdapterToolInvocation:
    """Test tool invocation handling."""

    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager."""
        manager = Mock(spec=PluginRegistry)
        return manager

    @pytest.fixture
    def adapter(self, mock_plugin_manager):
        """Create MCPAdapter instance."""
        return MCPAdapter(
            plugin_manager=mock_plugin_manager, base_url="http://localhost:8000"
        )

    def test_invoke_tool_returns_dict(self, adapter):
        """Test invoke_tool returns a dictionary."""
        result = adapter.invoke_tool("vision.ocr", {})

        assert isinstance(result, dict)

    def test_invoke_tool_includes_tool_id(self, adapter):
        """Test invoke_tool returns the tool_id in response."""
        tool_id = "vision.motion"
        result = adapter.invoke_tool(tool_id, {})

        assert "tool_id" in result
        assert result["tool_id"] == tool_id

    def test_invoke_tool_includes_status(self, adapter):
        """Test invoke_tool includes status field."""
        result = adapter.invoke_tool("vision.test", {})

        assert "status" in result
        assert result["status"] == "use_http"

    def test_invoke_tool_includes_message(self, adapter):
        """Test invoke_tool includes helpful message."""
        result = adapter.invoke_tool("vision.test", {})

        assert "message" in result
        assert "HTTP" in result["message"]

    def test_invoke_tool_accepts_params(self, adapter):
        """Test invoke_tool accepts parameters."""
        params = {"image_path": "test.jpg", "options": {"mode": "fast"}}

        # Should not raise an error
        result = adapter.invoke_tool("vision.ocr", params)
        assert isinstance(result, dict)

    def test_invoke_tool_with_empty_params(self, adapter):
        """Test invoke_tool works with empty parameters."""
        result = adapter.invoke_tool("vision.test", {})

        assert isinstance(result, dict)


class TestGeminiExtensionManifest:
    """Test Gemini extension manifest generation."""

    def test_gemini_manifest_structure(self):
        """Test Gemini manifest has correct structure."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert "name" in manifest
        assert "version" in manifest
        assert "description" in manifest
        assert "mcp" in manifest
        assert "commands" in manifest

    def test_gemini_manifest_name_field(self):
        """Test manifest name field."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert manifest["name"] == "vision-mcp"

    def test_gemini_manifest_version_field(self):
        """Test manifest version field."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert manifest["version"] == "0.1.0"

    def test_gemini_manifest_mcp_section(self):
        """Test manifest MCP section."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")
        mcp = manifest["mcp"]

        assert "manifest_url" in mcp
        assert "transport" in mcp
        assert mcp["transport"] == "http"

    def test_gemini_manifest_url_includes_server_url(self):
        """Test manifest URL includes the provided server URL."""
        server_url = "https://my-server.com"
        manifest = build_gemini_extension_manifest(server_url)

        assert server_url in manifest["mcp"]["manifest_url"]

    def test_gemini_manifest_commands_list(self):
        """Test manifest includes commands list."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert isinstance(manifest["commands"], list)
        assert len(manifest["commands"]) > 0

    def test_gemini_manifest_command_structure(self):
        """Test each command in manifest has required fields."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        for command in manifest["commands"]:
            assert "name" in command
            assert "description" in command
            assert "usage" in command

    def test_gemini_manifest_includes_vision_analyze(self):
        """Test manifest includes vision-analyze command."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")
        command_names = [cmd["name"] for cmd in manifest["commands"]]

        assert "vision-analyze" in command_names

    def test_gemini_manifest_includes_vision_stream(self):
        """Test manifest includes vision-stream command."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")
        command_names = [cmd["name"] for cmd in manifest["commands"]]

        assert "vision-stream" in command_names

    def test_gemini_manifest_requirements(self):
        """Test manifest includes requirements."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert "requirements" in manifest
        assert "python" in manifest["requirements"]

    def test_gemini_manifest_install_info(self):
        """Test manifest includes installation info."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        assert "install" in manifest
        assert "type" in manifest["install"]
        assert "package" in manifest["install"]

    def test_gemini_manifest_custom_name(self):
        """Test manifest accepts custom name."""
        custom_name = "my-vision-mcp"
        manifest = build_gemini_extension_manifest(
            "http://localhost:8000", name=custom_name
        )

        assert manifest["name"] == custom_name

    def test_gemini_manifest_custom_version(self):
        """Test manifest accepts custom version."""
        custom_version = "2.0.0"
        manifest = build_gemini_extension_manifest(
            "http://localhost:8000", version=custom_version
        )

        assert manifest["version"] == custom_version

    def test_gemini_manifest_json_serializable(self):
        """Test manifest can be serialized to JSON."""
        manifest = build_gemini_extension_manifest("http://localhost:8000")

        # Should not raise an error
        json_str = json.dumps(manifest)
        assert isinstance(json_str, str)

        # Should parse back correctly
        parsed = json.loads(json_str)
        assert parsed["name"] == "vision-mcp"


class TestMCPAdapterEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager."""
        manager = Mock(spec=PluginRegistry)
        return manager

    @pytest.fixture
    def adapter(self, mock_plugin_manager):
        """Create MCPAdapter instance."""
        return MCPAdapter(
            plugin_manager=mock_plugin_manager, base_url="http://localhost:8000"
        )

    def test_adapter_with_special_characters_in_plugin_name(
        self, adapter, mock_plugin_manager
    ):
        """Test adapter handles plugin names with underscores."""
        plugin = MockPlugin(name="ocr_v2_enhanced", description="Enhanced OCR")
        mock_plugin_manager.list.return_value = {"ocr_v2_enhanced": plugin.metadata()}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["id"] == "vision.ocr_v2_enhanced"

    def test_adapter_with_long_plugin_name(self, adapter, mock_plugin_manager):
        """Test adapter handles long plugin names."""
        long_name = "very_long_plugin_name_with_many_components"
        plugin = MockPlugin(name=long_name, description="Long named plugin")
        mock_plugin_manager.list.return_value = {long_name: plugin.metadata()}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["id"] == f"vision.{long_name}"

    def test_manifest_with_many_plugins(self, adapter, mock_plugin_manager):
        """Test adapter handles many plugins."""
        plugins = {
            f"plugin_{i}": MockPlugin(name=f"plugin_{i}", description=f"Plugin {i}")
            for i in range(20)
        }
        mock_plugin_manager.list.return_value = {
            name: plugin.metadata() for name, plugin in plugins.items()
        }

        manifest = adapter.get_manifest()

        assert len(manifest["tools"]) == 20

    def test_manifest_with_plugin_complex_inputs_outputs(
        self, adapter, mock_plugin_manager
    ):
        """Test adapter preserves complex input/output lists."""
        inputs = ["image", "video", "config", "metadata"]
        outputs = ["results", "confidence", "metadata", "debug_info"]
        plugin = MockPlugin(
            name="complex", description="Complex plugin", inputs=inputs, outputs=outputs
        )
        mock_plugin_manager.list.return_value = {"complex": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert tool["inputs"] == inputs
        assert tool["outputs"] == outputs

    def test_invoke_endpoint_with_no_base_url(self, mock_plugin_manager):
        """Test invoke endpoint works with no base URL."""
        adapter = MCPAdapter(plugin_manager=mock_plugin_manager, base_url="")
        plugin = MockPlugin(name="test", description="Test")
        mock_plugin_manager.list.return_value = {"test": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert tool["invoke_endpoint"].startswith("/v1/analyze")

    def test_invoke_endpoint_with_https_url(self, mock_plugin_manager):
        """Test invoke endpoint works with HTTPS URLs."""
        adapter = MCPAdapter(
            plugin_manager=mock_plugin_manager,
            base_url="https://api.example.com:443",
        )
        plugin = MockPlugin(name="test", description="Test")
        mock_plugin_manager.list.return_value = {"test": plugin.metadata()}

        manifest = adapter.get_manifest()
        tool = manifest["tools"][0]

        assert "https://api.example.com:443" in tool["invoke_endpoint"]

    def test_mcp_model_validation_with_pydantic(self, adapter, mock_plugin_manager):
        """Test MCPManifest Pydantic model validates correctly."""
        mock_plugin_manager.list.return_value = {}

        # Should create valid manifest that passes Pydantic validation
        manifest = adapter.get_manifest()
        validated = MCPManifest(**manifest)

        assert validated.server["name"] == MCP_SERVER_NAME
        assert isinstance(validated.tools, list)
