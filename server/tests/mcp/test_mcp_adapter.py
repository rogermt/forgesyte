"""Tests for MCP adapter functionality."""

import logging
import os
import sys
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import MCPAdapter, MCPServerInfo, MCPToolSchema  # noqa: E402
from app.models import MCPManifest, MCPTool  # noqa: E402
from app.plugin_loader import PluginRegistry  # noqa: E402


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
        manager = Mock(spec=PluginRegistry)
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
        # Note: title field in metadata is not in PluginMetadata schema
        # so it defaults to name
        assert tool["title"] == "ocr"
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

    def test_build_manifest_uses_name_for_title_fallback(
        self, adapter, mock_plugin_manager
    ):
        """Test manifest uses name if title field not in schema."""
        metadata = {
            "name": "plugin_name",
            "description": "Description",
        }
        mock_plugin_manager.list.return_value = {"plugin": metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        # Title defaults to name when not provided
        assert tool["title"] == "plugin_name"

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

    def test_plugin_metadata_with_required_fields_only(
        self, adapter, mock_plugin_manager
    ):
        """Test handling plugin metadata with only required fields."""
        metadata = {
            "name": "minimal",
            "description": "Minimal plugin",
            # All other fields are optional and will use defaults
        }
        mock_plugin_manager.list.return_value = {"minimal": metadata}

        # Should not raise error
        manifest = adapter.get_manifest()
        assert len(manifest["tools"]) == 1
        # Should use defaults for inputs/outputs
        tool = manifest["tools"][0]
        assert tool["inputs"] == ["image"]
        assert tool["outputs"] == ["json"]


class TestMCPAdapterValidation:
    """Test metadata validation in MCPAdapter."""

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

    def test_valid_metadata_passes_validation(self, adapter, mock_plugin_manager):
        """Test that valid metadata passes validation."""
        metadata = {
            "name": "test_plugin",
            "description": "Test plugin",
            "version": "1.0.0",
            "inputs": ["image"],
            "outputs": ["json"],
            "permissions": [],
        }
        mock_plugin_manager.list.return_value = {"test": metadata}

        manifest = adapter.get_manifest()

        # Should include the plugin in manifest
        assert len(manifest["tools"]) == 1
        assert manifest["tools"][0]["id"] == "vision.test"

    def test_invalid_metadata_skipped_with_logging(
        self, adapter, mock_plugin_manager, caplog
    ):
        """Test that invalid metadata is skipped and logged."""
        invalid_metadata = {
            "name": "",  # Empty name - invalid
            "description": "Test",
        }
        mock_plugin_manager.list.return_value = {"invalid": invalid_metadata}

        with caplog.at_level(logging.ERROR):
            manifest = adapter.get_manifest()

        # Should skip invalid plugin
        assert len(manifest["tools"]) == 0
        # Should log error
        assert "Invalid plugin metadata" in caplog.text

        # Verify context data in log record
        error_record = next(
            r for r in caplog.records if r.message == "Invalid plugin metadata"
        )
        assert error_record.plugin_name == "invalid"

    def test_multiple_plugins_partial_invalid(self, adapter, mock_plugin_manager):
        """Test handling mix of valid and invalid plugins."""
        valid_metadata = {
            "name": "valid_plugin",
            "description": "Valid",
        }
        invalid_metadata = {
            "name": "",  # Invalid
            "description": "Invalid",
        }
        mock_plugin_manager.list.return_value = {
            "valid": valid_metadata,
            "invalid": invalid_metadata,
        }

        manifest = adapter.get_manifest()

        # Should only include valid plugin
        assert len(manifest["tools"]) == 1
        assert manifest["tools"][0]["id"] == "vision.valid"

    def test_missing_required_name_field(self, adapter, mock_plugin_manager):
        """Test plugin missing required name field."""
        metadata = {
            "description": "Missing name",
        }
        mock_plugin_manager.list.return_value = {"noname": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin with missing required fields
        assert len(manifest["tools"]) == 0

    def test_missing_required_description_field(self, adapter, mock_plugin_manager):
        """Test plugin missing required description field."""
        metadata = {
            "name": "test",
            # Missing description
        }
        mock_plugin_manager.list.return_value = {"nodesc": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin with missing required fields
        assert len(manifest["tools"]) == 0

    def test_empty_description_rejected(self, adapter, mock_plugin_manager):
        """Test that empty description is rejected."""
        metadata = {
            "name": "test",
            "description": "",  # Empty - invalid
        }
        mock_plugin_manager.list.return_value = {"empty_desc": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin
        assert len(manifest["tools"]) == 0

    def test_invalid_inputs_type(self, adapter, mock_plugin_manager):
        """Test that non-list inputs are rejected."""
        metadata = {
            "name": "test",
            "description": "Test",
            "inputs": "image",  # Should be list
        }
        mock_plugin_manager.list.return_value = {"bad_inputs": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin
        assert len(manifest["tools"]) == 0

    def test_invalid_outputs_type(self, adapter, mock_plugin_manager):
        """Test that non-list outputs are rejected."""
        metadata = {
            "name": "test",
            "description": "Test",
            "outputs": "json",  # Should be list
        }
        mock_plugin_manager.list.return_value = {"bad_outputs": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin
        assert len(manifest["tools"]) == 0

    def test_invalid_permissions_type(self, adapter, mock_plugin_manager):
        """Test that non-list permissions are rejected."""
        metadata = {
            "name": "test",
            "description": "Test",
            "permissions": "read:files",  # Should be list
        }
        mock_plugin_manager.list.return_value = {"bad_perms": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin
        assert len(manifest["tools"]) == 0

    def test_config_schema_must_be_dict(self, adapter, mock_plugin_manager):
        """Test that config_schema must be dict or None."""
        metadata = {
            "name": "test",
            "description": "Test",
            "config_schema": "invalid",  # Should be dict or None
        }
        mock_plugin_manager.list.return_value = {"bad_schema": metadata}

        manifest = adapter.get_manifest()

        # Should skip plugin
        assert len(manifest["tools"]) == 0

    def test_validated_metadata_preserves_fields(self, adapter, mock_plugin_manager):
        """Test that validated metadata preserves all fields."""
        metadata = {
            "name": "advanced",
            "description": "Advanced plugin",
            "version": "2.0.0",
            "inputs": ["image", "config"],
            "outputs": ["results", "confidence"],
            "permissions": ["read:files", "write:results"],
            "config_schema": {"key": {"type": "string"}},
        }
        mock_plugin_manager.list.return_value = {"adv": metadata}

        manifest = adapter.get_manifest()

        tool = manifest["tools"][0]
        # Fields should be preserved after validation
        assert tool["inputs"] == ["image", "config"]
        assert tool["outputs"] == ["results", "confidence"]
        assert tool["permissions"] == ["read:files", "write:results"]
