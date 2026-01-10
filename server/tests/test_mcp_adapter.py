"""Tests for MCP adapter functionality."""

import os
import sys
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp_adapter import MCPAdapter, MCPServerInfo, MCPToolSchema  # noqa: E402
from app.models import MCPManifest, MCPTool  # noqa: E402
from app.plugin_loader import PluginManager  # noqa: E402


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

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Mock analyze method."""
        return {"result": "test"}

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass


class TestMCPServerInfo:
    """Test MCPServerInfo Pydantic model."""

    def test_mcp_server_info_valid(self):
        """Test creating valid MCPServerInfo."""
        info = MCPServerInfo(
            name="forgesyte",
            version="0.1.0",
            mcp_version="1.0.0",
        )
        assert info.name == "forgesyte"
        assert info.version == "0.1.0"
        assert info.mcp_version == "1.0.0"

    def test_mcp_server_info_required_fields(self):
        """Test MCPServerInfo requires all fields."""
        with pytest.raises(ValidationError):
            MCPServerInfo()  # type: ignore

    def test_mcp_server_info_model_dump(self):
        """Test MCPServerInfo serialization."""
        info = MCPServerInfo(
            name="forgesyte",
            version="0.1.0",
            mcp_version="1.0.0",
        )
        dumped = info.model_dump()
        assert dumped["name"] == "forgesyte"
        assert dumped["version"] == "0.1.0"
        assert dumped["mcp_version"] == "1.0.0"


class TestMCPToolSchema:
    """Test MCPToolSchema validation."""

    def test_mcp_tool_schema_valid(self):
        """Test creating valid MCPToolSchema."""
        schema = MCPToolSchema(
            id="vision.ocr",
            title="OCR Plugin",
            description="Extract text from images",
            inputs=["image"],
            outputs=["text"],
            invoke_endpoint="/v1/analyze?plugin=ocr",
        )
        assert schema.id == "vision.ocr"
        assert schema.title == "OCR Plugin"

    def test_mcp_tool_schema_required_fields(self):
        """Test MCPToolSchema requires all fields."""
        with pytest.raises(ValidationError):
            MCPToolSchema(id="vision.ocr")  # type: ignore

    def test_mcp_tool_schema_empty_inputs_valid(self):
        """Test MCPToolSchema allows empty inputs."""
        schema = MCPToolSchema(
            id="vision.list_plugins",
            title="List Plugins",
            description="List available plugins",
            inputs=[],
            outputs=["json"],
            invoke_endpoint="/v1/plugins",
        )
        assert schema.inputs == []


class TestMCPAdapter:
    """Test MCPAdapter functionality."""

    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager."""
        manager = Mock(spec=PluginManager)
        return manager

    @pytest.fixture
    def adapter(self, mock_plugin_manager):
        """Create MCPAdapter instance."""
        return MCPAdapter(
            plugin_manager=mock_plugin_manager, base_url="http://localhost:8000"
        )

    def test_adapter_initialization(self, adapter, mock_plugin_manager):
        """Test MCPAdapter initialization."""
        assert adapter.plugin_manager == mock_plugin_manager
        assert adapter.base_url == "http://localhost:8000"

    def test_adapter_strips_trailing_slash(self, mock_plugin_manager):
        """Test adapter strips trailing slash from base_url."""
        adapter = MCPAdapter(
            plugin_manager=mock_plugin_manager, base_url="http://localhost:8000/"
        )
        assert adapter.base_url == "http://localhost:8000"

    def test_build_manifest_empty_plugins(self, adapter, mock_plugin_manager):
        """Test building manifest with no plugins."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert isinstance(manifest, dict)
        assert manifest["server"]["name"] == "forgesyte"
        assert manifest["server"]["version"] == "0.1.0"
        assert manifest["tools"] == []

    def test_build_manifest_single_plugin(self, adapter, mock_plugin_manager):
        """Test building manifest with single plugin."""
        mock_plugin = MockPlugin(
            name="ocr", title="OCR Plugin", description="Extracts text from images"
        )
        mock_plugin_manager.list.return_value = {"ocr": mock_plugin.metadata()}

        manifest = adapter.get_manifest()

        assert len(manifest["tools"]) == 1
        tool = manifest["tools"][0]
        assert tool["id"] == "vision.ocr"
        assert tool["title"] == "OCR Plugin"
        assert tool["invoke_endpoint"] == "http://localhost:8000/v1/analyze?plugin=ocr"

    def test_build_manifest_multiple_plugins(self, adapter, mock_plugin_manager):
        """Test building manifest with multiple plugins."""
        plugin1 = MockPlugin(name="ocr", description="OCR Plugin")
        plugin2 = MockPlugin(name="detector", description="Object Detector")

        mock_plugin_manager.list.return_value = {
            "ocr": plugin1.metadata(),
            "detector": plugin2.metadata(),
        }

        manifest = adapter.get_manifest()

        assert len(manifest["tools"]) == 2
        tool_ids = [tool["id"] for tool in manifest["tools"]]
        assert "vision.ocr" in tool_ids
        assert "vision.detector" in tool_ids

    def test_build_manifest_preserves_plugin_metadata(
        self, adapter, mock_plugin_manager
    ):
        """Test manifest preserves plugin metadata."""
        custom_metadata = {
            "name": "custom_plugin",
            "description": "Custom analysis plugin",
            "inputs": ["image", "options"],
            "outputs": ["json", "metadata"],
            "version": "2.0.0",
        }
        mock_plugin_manager.list.return_value = {"custom": custom_metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["inputs"] == ["image", "options"]
        assert tool["outputs"] == ["json", "metadata"]

    def test_build_manifest_default_inputs_outputs(self, adapter, mock_plugin_manager):
        """Test manifest uses defaults for missing inputs/outputs."""
        minimal_metadata = {
            "name": "minimal",
            "description": "Minimal plugin",
        }
        mock_plugin_manager.list.return_value = {"minimal": minimal_metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["inputs"] == ["image"]
        assert tool["outputs"] == ["json"]

    def test_build_manifest_uses_title_field_if_present(
        self, adapter, mock_plugin_manager
    ):
        """Test manifest uses title field if present."""
        metadata = {
            "name": "plugin_name",
            "title": "Plugin Display Name",
            "description": "Description",
        }
        mock_plugin_manager.list.return_value = {"plugin": metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["title"] == "Plugin Display Name"

    def test_build_manifest_fallback_to_name_for_title(
        self, adapter, mock_plugin_manager
    ):
        """Test manifest falls back to name if title not present."""
        metadata = {
            "name": "plugin_name",
            "description": "Description",
        }
        mock_plugin_manager.list.return_value = {"plugin": metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["title"] == "plugin_name"

    def test_build_manifest_plugin_with_permissions(self, adapter, mock_plugin_manager):
        """Test manifest includes plugin permissions."""
        metadata = {
            "name": "secure_plugin",
            "description": "Secure plugin",
            "inputs": ["image"],
            "outputs": ["json"],
            "permissions": ["read:files", "write:results"],
        }
        mock_plugin_manager.list.return_value = {"secure": metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["permissions"] == ["read:files", "write:results"]

    def test_manifest_structure_valid(self, adapter, mock_plugin_manager):
        """Test generated manifest matches MCPManifest schema."""
        mock_plugin_manager.list.return_value = {}
        manifest_dict = adapter.get_manifest()

        # Should not raise ValidationError
        manifest = MCPManifest(**manifest_dict)
        assert isinstance(manifest, MCPManifest)

    def test_manifest_includes_server_metadata(self, adapter, mock_plugin_manager):
        """Test manifest includes server metadata."""
        mock_plugin_manager.list.return_value = {}

        manifest = adapter.get_manifest()

        assert "server" in manifest
        assert manifest["server"]["name"] == "forgesyte"
        assert "version" in manifest["server"]

    def test_build_tools_creates_valid_tools(self, adapter, mock_plugin_manager):
        """Test _build_tools creates valid MCPTool instances."""
        metadata = {
            "name": "test",
            "description": "Test plugin",
            "inputs": ["image"],
            "outputs": ["json"],
        }
        mock_plugin_manager.list.return_value = {"test": metadata}

        tools = adapter._build_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert isinstance(tool, MCPTool)
        assert tool.id == "vision.test"

    def test_invoke_endpoint_format(self, adapter, mock_plugin_manager):
        """Test invoke endpoint follows correct format."""
        mock_plugin_manager.list.return_value = {
            "ocr": {"name": "ocr", "description": "OCR"}
        }

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["invoke_endpoint"].startswith(
            "http://localhost:8000/v1/analyze?plugin="
        )
        assert "ocr" in tool["invoke_endpoint"]

    def test_manifest_consistency(self, adapter, mock_plugin_manager):
        """Test manifest is consistent across multiple calls."""
        metadata = {"ocr": {"name": "ocr", "description": "OCR"}}
        mock_plugin_manager.list.return_value = metadata

        manifest1 = adapter.get_manifest()
        manifest2 = adapter.get_manifest()

        assert manifest1 == manifest2

    def test_adapter_with_empty_base_url(self, mock_plugin_manager):
        """Test adapter with empty base_url."""
        adapter = MCPAdapter(plugin_manager=mock_plugin_manager, base_url="")
        adapter.plugin_manager.list.return_value = {
            "test": {"name": "test", "description": "Test"}
        }

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        assert tool["invoke_endpoint"] == "/v1/analyze?plugin=test"

    def test_plugin_metadata_missing_optional_fields(
        self, adapter, mock_plugin_manager
    ):
        """Test handling plugin metadata with missing optional fields."""
        metadata = {
            "name": "minimal",
            # description is optional
            "inputs": ["image"],
        }
        mock_plugin_manager.list.return_value = {"minimal": metadata}

        # Should not raise error
        manifest = adapter.get_manifest()
        assert len(manifest["tools"]) == 1
