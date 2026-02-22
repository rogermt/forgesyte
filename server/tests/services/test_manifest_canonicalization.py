"""Test plugin manifest input canonicalization for v0.9.2.

Tests that:
1. Manifests with 'inputs' field are preserved
2. Manifests with 'input_types' field are canonicalized to 'inputs'
3. Manifests without either field get empty 'inputs' list
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest

from app.services.plugin_management_service import PluginManagementService


class MockPluginWithManifest:
    """Mock plugin that has __class__.__module__ pointing to a module with manifest."""

    def __init__(self, module_name: str):
        self._module_name = module_name
        self.tools = {"analyze": {"input_schema": {"image_bytes": {"type": "bytes"}}}}

    @property
    def __class__(self):
        """Mock class for module path."""

        class MockClass:
            __module__ = self._module_name

        return MockClass


class MockRegistry:
    """Mock registry that returns plugins by ID."""

    def __init__(self, plugins: dict):
        self._plugins = plugins

    def get(self, plugin_id: str):
        return self._plugins.get(plugin_id)

    def list(self):
        return self._plugins


@pytest.fixture
def temp_module_setup():
    """Create temporary module with manifest file."""
    with TemporaryDirectory() as tmpdir:
        # Create a mock module directory
        module_dir = Path(tmpdir) / "test_plugin_module"
        module_dir.mkdir()

        # Create __init__.py to make it a module
        (module_dir / "__init__.py").write_text("")

        yield tmpdir, module_dir


def test_manifest_with_inputs_preserved(temp_module_setup):
    """Test that manifests with 'inputs' field are preserved."""
    tmpdir, module_dir = temp_module_setup

    # Create manifest with 'inputs' field
    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "tools": [
            {
                "id": "analyze",
                "description": "Extract text",
                "inputs": ["image_bytes", "detections"],
                "output_types": ["text"],
            }
        ],
    }

    manifest_path = module_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Create mock plugin that points to this module
    mock_plugin = MockPluginWithManifest("test_plugin_module")

    # Mock sys.modules to include our test module
    import sys

    old_module = sys.modules.get("test_plugin_module")
    mock_module = MagicMock()
    mock_module.__file__ = str(module_dir / "__init__.py")
    sys.modules["test_plugin_module"] = mock_module

    try:
        registry = MockRegistry({"test_plugin": mock_plugin})
        service = PluginManagementService(registry)
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        # Find the analyze tool
        tools = result.get("tools", [])
        analyze = next((t for t in tools if t.get("id") == "analyze"), None)
        assert analyze is not None
        assert analyze["inputs"] == ["image_bytes", "detections"]
    finally:
        if old_module is not None:
            sys.modules["test_plugin_module"] = old_module
        else:
            sys.modules.pop("test_plugin_module", None)


def test_manifest_with_input_types_canonicalized(temp_module_setup):
    """Test that manifests with 'input_types' are canonicalized to 'inputs'."""
    tmpdir, module_dir = temp_module_setup

    # Create manifest with 'input_types' field (legacy format)
    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "tools": [
            {
                "id": "analyze",
                "description": "Extract text",
                "input_types": ["image_bytes", "detections"],  # Legacy field
                "output_types": ["text"],
            }
        ],
    }

    manifest_path = module_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Create mock plugin that points to this module
    mock_plugin = MockPluginWithManifest("test_plugin_module")

    # Mock sys.modules to include our test module
    import sys

    old_module = sys.modules.get("test_plugin_module")
    mock_module = MagicMock()
    mock_module.__file__ = str(module_dir / "__init__.py")
    sys.modules["test_plugin_module"] = mock_module

    try:
        registry = MockRegistry({"test_plugin": mock_plugin})
        service = PluginManagementService(registry)
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        # Find the analyze tool
        tools = result.get("tools", [])
        analyze = next((t for t in tools if t.get("id") == "analyze"), None)
        assert analyze is not None
        # 'inputs' should be canonicalized from 'input_types'
        assert "inputs" in analyze
        assert analyze["inputs"] == ["image_bytes", "detections"]
    finally:
        if old_module is not None:
            sys.modules["test_plugin_module"] = old_module
        else:
            sys.modules.pop("test_plugin_module", None)


def test_manifest_without_inputs_gets_empty_list(temp_module_setup):
    """Test that manifests without 'inputs' or 'input_types' get empty 'inputs' list."""
    tmpdir, module_dir = temp_module_setup

    # Create manifest without input specification
    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "tools": [
            {
                "id": "simple_tool",
                "description": "Simple tool without input specification",
                "output_types": ["text"],
            }
        ],
    }

    manifest_path = module_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Create mock plugin that points to this module
    mock_plugin = MockPluginWithManifest("test_plugin_module")

    # Mock sys.modules to include our test module
    import sys

    old_module = sys.modules.get("test_plugin_module")
    mock_module = MagicMock()
    mock_module.__file__ = str(module_dir / "__init__.py")
    sys.modules["test_plugin_module"] = mock_module

    try:
        registry = MockRegistry({"test_plugin": mock_plugin})
        service = PluginManagementService(registry)
        result = service.get_plugin_manifest("test_plugin")

        assert result is not None
        # Find the simple_tool
        tools = result.get("tools", [])
        simple_tool = next((t for t in tools if t.get("id") == "simple_tool"), None)
        assert simple_tool is not None
        # Should have empty inputs list
        assert "inputs" in simple_tool
        assert simple_tool["inputs"] == []
    finally:
        if old_module is not None:
            sys.modules["test_plugin_module"] = old_module
        else:
            sys.modules.pop("test_plugin_module", None)


def test_real_ocr_manifest_canonicalization(app_with_plugins):
    """Test that the real OCR plugin manifest is properly canonicalized."""
    plugin_service = app_with_plugins.state.plugin_service
    manifest = plugin_service.get_plugin_manifest("ocr")

    # If OCR plugin is not installed, skip this test
    if manifest is None:
        pytest.skip("OCR plugin not installed")

    assert manifest is not None
    assert "tools" in manifest

    # Check that analyze tool has canonicalized inputs
    tools = manifest.get("tools", [])
    analyze = next((t for t in tools if t.get("id") == "analyze"), None)
    if analyze:
        assert "inputs" in analyze
        # Should have image_bytes at minimum
        assert "image_bytes" in analyze["inputs"]


def test_real_yolo_manifest_canonicalization(app_with_plugins):
    """Test that the real YOLO plugin manifest is properly canonicalized."""
    plugin_service = app_with_plugins.state.plugin_service
    manifest = plugin_service.get_plugin_manifest("yolo")

    # If YOLO plugin is not installed, skip this test
    if manifest is None:
        pytest.skip("YOLO plugin not installed")

    assert manifest is not None
    assert "tools" in manifest

    # Check that detect_objects tool has canonicalized inputs
    tools = manifest.get("tools", [])
    detect_objects = next((t for t in tools if t.get("id") == "detect_objects"), None)
    if detect_objects:
        assert "inputs" in detect_objects
        # Should have image_bytes
        assert "image_bytes" in detect_objects["inputs"]