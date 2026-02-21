"""Test plugin manifest input canonicalization for v0.9.2.

Tests that:
1. Manifests with 'inputs' field are preserved
2. Manifests with 'input_types' field are canonicalized to 'inputs'
3. Manifests without either field get empty 'inputs' list
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.plugin_management_service import PluginManagementService


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(self, name: str, manifest_path: Path):
        self.name = name
        self._manifest_path = manifest_path

    def __class__(self):
        """Mock class for module path."""

        class MockClass:
            __module__ = f"test_plugins.{self.name}"

        return MockClass


def test_manifest_with_inputs_preserved(plugin_service):
    """Test that manifests with 'inputs' field are preserved."""
    with TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir) / "test_plugin"
        plugin_dir.mkdir()

        # Create manifest with 'inputs' field
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "tools": {
                "extract_text": {
                    "description": "Extract text",
                    "inputs": ["image_bytes", "detections"],
                    "output_types": ["text"],
                }
            },
        }

        manifest_path = plugin_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        # Create mock plugin
        plugin = MockPlugin("test_plugin", plugin_dir)

        # Mock registry to return our plugin
        class MockRegistry:
            def get(self, plugin_id):
                return plugin if plugin_id == "test_plugin" else None

        service = PluginManagementService(MockRegistry())
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        assert result["tools"]["extract_text"]["inputs"] == [
            "image_bytes",
            "detections",
        ]


def test_manifest_with_input_types_canonicalized(plugin_service):
    """Test that manifests with 'input_types' are canonicalized to 'inputs'."""
    with TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir) / "test_plugin"
        plugin_dir.mkdir()

        # Create manifest with 'input_types' field (legacy format)
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "tools": {
                "extract_text": {
                    "description": "Extract text",
                    "input_types": ["image_bytes", "detections"],  # Legacy field
                    "output_types": ["text"],
                }
            },
        }

        manifest_path = plugin_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        # Create mock plugin
        plugin = MockPlugin("test_plugin", plugin_dir)

        # Mock registry to return our plugin
        class MockRegistry:
            def get(self, plugin_id):
                return plugin if plugin_id == "test_plugin" else None

        service = PluginManagementService(MockRegistry())
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        # Both 'inputs' and 'input_types' should exist
        assert "inputs" in result["tools"]["extract_text"]
        assert result["tools"]["extract_text"]["inputs"] == [
            "image_bytes",
            "detections",
        ]
        assert result["tools"]["extract_text"]["input_types"] == [
            "image_bytes",
            "detections",
        ]


def test_manifest_without_inputs_gets_empty_list(plugin_service):
    """Test that manifests without 'inputs' or 'input_types' get empty 'inputs' list."""
    with TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir) / "test_plugin"
        plugin_dir.mkdir()

        # Create manifest without input specification
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "tools": {
                "simple_tool": {
                    "description": "Simple tool without input specification",
                    "output_types": ["text"],
                }
            },
        }

        manifest_path = plugin_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        # Create mock plugin
        plugin = MockPlugin("test_plugin", plugin_dir)

        # Mock registry to return our plugin
        class MockRegistry:
            def get(self, plugin_id):
                return plugin if plugin_id == "test_plugin" else None

        service = PluginManagementService(MockRegistry())
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        assert "inputs" in result["tools"]["simple_tool"]
        assert result["tools"]["simple_tool"]["inputs"] == []


def test_real_ocr_manifest_canonicalization(plugin_service):
    """Test that the real OCR plugin manifest is properly canonicalized."""
    manifest = plugin_service.get_plugin_manifest("ocr")
    assert manifest is not None
    assert "tools" in manifest

    # Check that extract_text tool has canonicalized inputs
    extract_text = manifest["tools"].get("extract_text")
    if extract_text:
        assert "inputs" in extract_text
        # Should have image_bytes at minimum
        assert "image_bytes" in extract_text["inputs"]


def test_real_yolo_manifest_canonicalization(plugin_service):
    """Test that the real YOLO plugin manifest is properly canonicalized."""
    manifest = plugin_service.get_plugin_manifest("yolo")
    assert manifest is not None
    assert "tools" in manifest

    # Check that detect_objects tool has canonicalized inputs
    detect_objects = manifest["tools"].get("detect_objects")
    if detect_objects:
        assert "inputs" in detect_objects
        # Should have image_bytes
        assert "image_bytes" in detect_objects["inputs"]
