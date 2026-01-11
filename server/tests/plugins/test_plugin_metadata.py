"""Tests for enhanced PluginMetadata schema and validation."""

import os
import sys

import pytest
from pydantic import ValidationError

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import PluginMetadata  # noqa: E402


class TestPluginMetadataBasics:
    """Test basic PluginMetadata model functionality."""

    def test_minimal_valid_metadata(self):
        """Test creating metadata with only required fields."""
        metadata = PluginMetadata(
            name="test_plugin",
            description="Test plugin description",
        )
        assert metadata.name == "test_plugin"
        assert metadata.description == "Test plugin description"
        assert metadata.version == "1.0.0"  # Default version

    def test_full_valid_metadata(self):
        """Test creating metadata with all fields."""
        metadata = PluginMetadata(
            name="advanced_plugin",
            description="Advanced analysis tool",
            version="2.5.1",
            inputs=["image", "config"],
            outputs=["json", "metadata"],
            permissions=["read:files", "write:results"],
            config_schema={"sensitivity": {"type": "float", "default": 0.8}},
        )
        assert metadata.name == "advanced_plugin"
        assert metadata.version == "2.5.1"
        assert len(metadata.inputs) == 2
        assert len(metadata.outputs) == 2
        assert len(metadata.permissions) == 2

    def test_name_required(self):
        """Test that name field is required."""
        with pytest.raises(ValidationError) as exc_info:
            PluginMetadata(description="Test")  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "name" for error in errors)

    def test_description_required(self):
        """Test that description field is required."""
        with pytest.raises(ValidationError) as exc_info:
            PluginMetadata(name="test")  # type: ignore
        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "description" for error in errors)

    def test_default_version(self):
        """Test default version value."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.version == "1.0.0"

    def test_default_inputs(self):
        """Test default inputs value."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.inputs == ["image"]

    def test_default_outputs(self):
        """Test default outputs value."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.outputs == ["json"]

    def test_default_permissions(self):
        """Test default permissions value."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.permissions == []

    def test_default_config_schema(self):
        """Test default config_schema value."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.config_schema is None


class TestPluginMetadataNameValidation:
    """Test name field validation."""

    def test_name_non_empty(self):
        """Test that name cannot be empty string."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="", description="Test")

    def test_name_valid_with_underscores(self):
        """Test that name can contain underscores."""
        metadata = PluginMetadata(name="my_plugin_name", description="Test")
        assert metadata.name == "my_plugin_name"

    def test_name_valid_with_hyphens(self):
        """Test that name can contain hyphens."""
        metadata = PluginMetadata(name="my-plugin-name", description="Test")
        assert metadata.name == "my-plugin-name"

    def test_name_valid_with_numbers(self):
        """Test that name can contain numbers."""
        metadata = PluginMetadata(name="plugin2024", description="Test")
        assert metadata.name == "plugin2024"

    def test_name_preserves_case(self):
        """Test that name preserves case."""
        metadata = PluginMetadata(name="MyPlugin", description="Test")
        assert metadata.name == "MyPlugin"


class TestPluginMetadataVersionValidation:
    """Test version field validation and semantics."""

    def test_version_valid_semver(self):
        """Test valid semantic version."""
        metadata = PluginMetadata(name="test", description="Test", version="1.2.3")
        assert metadata.version == "1.2.3"

    def test_version_two_component(self):
        """Test version with two components."""
        metadata = PluginMetadata(name="test", description="Test", version="2.0")
        assert metadata.version == "2.0"

    def test_version_with_prerelease(self):
        """Test version with prerelease suffix."""
        metadata = PluginMetadata(
            name="test", description="Test", version="1.0.0-alpha"
        )
        assert metadata.version == "1.0.0-alpha"

    def test_version_with_build_metadata(self):
        """Test version with build metadata."""
        metadata = PluginMetadata(
            name="test", description="Test", version="1.0.0+build.123"
        )
        assert metadata.version == "1.0.0+build.123"


class TestPluginMetadataInputsOutputs:
    """Test inputs and outputs field validation."""

    def test_inputs_list_type(self):
        """Test that inputs must be a list."""
        with pytest.raises(ValidationError):
            PluginMetadata(
                name="test", description="Test", inputs="image"  # type: ignore
            )

    def test_outputs_list_type(self):
        """Test that outputs must be a list."""
        with pytest.raises(ValidationError):
            PluginMetadata(
                name="test", description="Test", outputs="json"  # type: ignore
            )

    def test_inputs_empty_list_valid(self):
        """Test that inputs can be empty list."""
        metadata = PluginMetadata(name="test", description="Test", inputs=[])
        assert metadata.inputs == []

    def test_outputs_empty_list_valid(self):
        """Test that outputs can be empty list."""
        metadata = PluginMetadata(name="test", description="Test", outputs=[])
        assert metadata.outputs == []

    def test_inputs_multiple_types(self):
        """Test inputs with multiple types."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            inputs=["image", "config", "metadata"],
        )
        assert len(metadata.inputs) == 3
        assert "image" in metadata.inputs
        assert "config" in metadata.inputs

    def test_outputs_multiple_types(self):
        """Test outputs with multiple types."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            outputs=["json", "text", "regions"],
        )
        assert len(metadata.outputs) == 3
        assert "json" in metadata.outputs
        assert "text" in metadata.outputs


class TestPluginMetadataPermissions:
    """Test permissions field validation."""

    def test_permissions_list_type(self):
        """Test that permissions must be a list."""
        with pytest.raises(ValidationError):
            PluginMetadata(
                name="test",
                description="Test",
                permissions="read:files",  # type: ignore
            )

    def test_permissions_empty_list_valid(self):
        """Test that permissions can be empty list."""
        metadata = PluginMetadata(name="test", description="Test", permissions=[])
        assert metadata.permissions == []

    def test_permissions_multiple(self):
        """Test multiple permissions."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            permissions=["read:files", "write:results", "execute:model"],
        )
        assert len(metadata.permissions) == 3
        assert "read:files" in metadata.permissions

    def test_permissions_format_with_colon(self):
        """Test permission format with colon separator."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            permissions=["read:files", "write:results"],
        )
        assert all(":" in p for p in metadata.permissions)

    def test_common_permission_types(self):
        """Test common permission types."""
        common_perms = [
            "read:files",
            "write:results",
            "execute:model",
            "network:external",
            "gpu:access",
        ]
        metadata = PluginMetadata(
            name="test", description="Test", permissions=common_perms
        )
        assert metadata.permissions == common_perms


class TestPluginMetadataConfigSchema:
    """Test config_schema field validation."""

    def test_config_schema_none_default(self):
        """Test that config_schema defaults to None."""
        metadata = PluginMetadata(name="test", description="Test")
        assert metadata.config_schema is None

    def test_config_schema_dict_type(self):
        """Test that config_schema must be dict if provided."""
        with pytest.raises(ValidationError):
            PluginMetadata(
                name="test",
                description="Test",
                config_schema="invalid",  # type: ignore
            )

    def test_config_schema_simple(self):
        """Test simple config_schema."""
        schema = {"sensitivity": {"type": "float", "default": 0.8}}
        metadata = PluginMetadata(name="test", description="Test", config_schema=schema)
        assert metadata.config_schema == schema

    def test_config_schema_complex(self):
        """Test complex config_schema with multiple fields."""
        schema = {
            "sensitivity": {
                "type": "float",
                "default": 0.8,
                "min": 0.0,
                "max": 1.0,
                "description": "Detection sensitivity",
            },
            "categories": {
                "type": "array",
                "default": ["nsfw", "violence"],
                "description": "Categories to check",
            },
            "mode": {
                "type": "string",
                "default": "fast",
                "enum": ["fast", "accurate"],
                "description": "Analysis mode",
            },
        }
        metadata = PluginMetadata(name="test", description="Test", config_schema=schema)
        assert len(metadata.config_schema) == 3
        assert "sensitivity" in metadata.config_schema

    def test_config_schema_empty_dict_valid(self):
        """Test that empty config_schema dict is valid."""
        metadata = PluginMetadata(name="test", description="Test", config_schema={})
        assert metadata.config_schema == {}


class TestPluginMetadataFromDict:
    """Test creating PluginMetadata from dictionaries."""

    def test_from_plugin_metadata_dict(self):
        """Test creating from typical plugin metadata dict."""
        plugin_dict = {
            "name": "ocr",
            "version": "1.0.0",
            "description": "Optical Character Recognition",
            "inputs": ["image"],
            "outputs": ["text", "confidence"],
            "permissions": ["read:files"],
        }
        metadata = PluginMetadata(**plugin_dict)
        assert metadata.name == "ocr"
        assert len(metadata.outputs) == 2

    def test_from_minimal_dict(self):
        """Test creating from minimal dict."""
        plugin_dict = {
            "name": "simple",
            "description": "Simple plugin",
        }
        metadata = PluginMetadata(**plugin_dict)
        assert metadata.name == "simple"
        assert metadata.version == "1.0.0"

    def test_from_complex_dict(self):
        """Test creating from complex dict with all fields."""
        plugin_dict = {
            "name": "moderation",
            "version": "1.0.0",
            "description": "Content moderation",
            "inputs": ["image"],
            "outputs": ["safe", "categories", "confidence"],
            "permissions": ["moderation"],
            "config_schema": {
                "sensitivity": {
                    "type": "string",
                    "default": "medium",
                    "enum": ["low", "medium", "high"],
                    "description": "Detection sensitivity level",
                },
                "categories": {
                    "type": "array",
                    "default": ["nsfw", "violence"],
                    "description": "Categories to check",
                },
            },
        }
        metadata = PluginMetadata(**plugin_dict)
        assert metadata.name == "moderation"
        assert len(metadata.outputs) == 3
        assert metadata.config_schema is not None


class TestPluginMetadataSerialization:
    """Test serialization of PluginMetadata."""

    def test_model_dump(self):
        """Test model_dump serialization."""
        metadata = PluginMetadata(
            name="test",
            description="Test plugin",
            version="1.0.0",
            inputs=["image"],
            outputs=["json"],
        )
        dumped = metadata.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["name"] == "test"
        assert dumped["version"] == "1.0.0"

    def test_model_dump_exclude_none(self):
        """Test model_dump with exclude_none."""
        metadata = PluginMetadata(name="test", description="Test", config_schema=None)
        dumped = metadata.model_dump(exclude_none=True)
        # config_schema should be excluded
        assert "config_schema" not in dumped

    def test_model_dump_with_config_schema(self):
        """Test model_dump includes config_schema when present."""
        schema = {"key": {"type": "string"}}
        metadata = PluginMetadata(name="test", description="Test", config_schema=schema)
        dumped = metadata.model_dump()
        assert dumped["config_schema"] == schema

    def test_model_dump_exclude_defaults(self):
        """Test model_dump_exclude_defaults."""
        metadata = PluginMetadata(name="test", description="Test")
        dumped = metadata.model_dump(exclude_defaults=False)
        # All defaults should be included
        assert "version" in dumped
        assert "inputs" in dumped
        assert "outputs" in dumped


class TestPluginMetadataEdgeCases:
    """Test edge cases and special scenarios."""

    def test_name_with_special_chars_valid(self):
        """Test name with allowed special characters."""
        metadata = PluginMetadata(name="plugin_v2-pro", description="Test")
        assert metadata.name == "plugin_v2-pro"

    def test_description_empty_invalid(self):
        """Test that description cannot be empty."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="test", description="")

    def test_description_long_text(self):
        """Test description with long text."""
        long_description = "This is a comprehensive plugin description " * 10
        metadata = PluginMetadata(name="test", description=long_description)
        assert metadata.description == long_description

    def test_inputs_with_spaces(self):
        """Test inputs with spaces (should be allowed)."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            inputs=["image data", "config params"],
        )
        assert "image data" in metadata.inputs

    def test_large_number_of_inputs(self):
        """Test with many inputs."""
        many_inputs = [f"input_{i}" for i in range(50)]
        metadata = PluginMetadata(name="test", description="Test", inputs=many_inputs)
        assert len(metadata.inputs) == 50

    def test_large_config_schema(self):
        """Test with large config_schema."""
        schema = {
            f"param_{i}": {"type": "string", "default": f"value_{i}"} for i in range(20)
        }
        metadata = PluginMetadata(name="test", description="Test", config_schema=schema)
        assert len(metadata.config_schema) == 20


class TestPluginMetadataValidationMessages:
    """Test validation error messages."""

    def test_missing_name_error_message(self):
        """Test error message when name is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PluginMetadata(description="Test")  # type: ignore
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_description_error_message(self):
        """Test error message when description is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PluginMetadata(name="test")  # type: ignore
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_invalid_type_error_message(self):
        """Test error message for invalid field type."""
        with pytest.raises(ValidationError):
            PluginMetadata(
                name="test",
                description="Test",
                inputs={"invalid": "type"},  # type: ignore
            )


class TestPluginMetadataRealWorldExamples:
    """Test with real-world plugin metadata examples."""

    def test_ocr_plugin_metadata(self):
        """Test with OCR plugin metadata structure."""
        metadata = PluginMetadata(
            name="ocr",
            version="1.0.0",
            description="Extract text from images",
            inputs=["image"],
            outputs=["text", "confidence"],
            permissions=["read:files"],
            config_schema={
                "language": {
                    "type": "string",
                    "default": "eng",
                    "description": "OCR language",
                }
            },
        )
        assert metadata.name == "ocr"
        assert "text" in metadata.outputs

    def test_motion_detector_metadata(self):
        """Test with motion detector plugin metadata."""
        metadata = PluginMetadata(
            name="motion_detector",
            version="1.0.0",
            description="Detect motion between frames",
            inputs=["image"],
            outputs=["motion_detected", "motion_score", "regions"],
            permissions=[],
            config_schema={
                "threshold": {
                    "type": "float",
                    "default": 25.0,
                    "min": 1.0,
                    "max": 100.0,
                },
                "min_area": {
                    "type": "float",
                    "default": 0.01,
                    "min": 0.001,
                    "max": 0.5,
                },
                "blur_size": {
                    "type": "integer",
                    "default": 5,
                },
                "reset_baseline": {
                    "type": "boolean",
                    "default": False,
                },
            },
        )
        assert metadata.name == "motion_detector"
        assert len(metadata.outputs) == 3
        assert len(metadata.config_schema) == 4

    def test_moderation_plugin_metadata(self):
        """Test with content moderation plugin metadata."""
        metadata = PluginMetadata(
            name="moderation",
            version="1.0.0",
            description="Detect unsafe or inappropriate content",
            inputs=["image"],
            outputs=["safe", "categories", "confidence"],
            permissions=["moderation"],
            config_schema={
                "sensitivity": {
                    "type": "string",
                    "default": "medium",
                    "enum": ["low", "medium", "high"],
                    "description": "Detection sensitivity level",
                },
                "categories": {
                    "type": "array",
                    "default": ["nsfw", "violence", "hate"],
                    "description": "Categories to check",
                },
            },
        )
        assert metadata.name == "moderation"
        assert "moderation" in metadata.permissions
