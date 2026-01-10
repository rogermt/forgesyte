#!/usr/bin/env python3
"""Manual validation script for MCP adapter functionality.

This script verifies the MCP adapter implementation by:
1. Testing manifest generation with mock plugins
2. Verifying endpoint responses
3. Checking protocol compliance
4. Testing plugin discovery

Usage:
    python scripts/validate_mcp.py
    uv run scripts/validate_mcp.py
"""

import json

# Setup paths
import os
import sys
from typing import Optional
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp_adapter import (  # noqa: E402
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    build_gemini_extension_manifest,
)
from app.plugin_loader import PluginManager  # noqa: E402


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(
        self,
        name: str,
        description: str,
        inputs: Optional[list] = None,
        outputs: Optional[list] = None,
    ):
        self.name = name
        self.description = description
        self.inputs = inputs or ["image"]
        self.outputs = outputs or ["json"]

    def metadata(self) -> dict:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "version": "1.0.0",
        }


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"  ✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"  ✗ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"  → {message}")


def test_manifest_generation() -> bool:
    """Test manifest generation with mock plugins."""
    print_section("1. Testing Manifest Generation")

    # Create mock plugin manager with test plugins
    manager = Mock(spec=PluginManager)
    manager.list.return_value = {
        "ocr": MockPlugin(
            "ocr",
            "Optical Character Recognition",
            inputs=["image"],
            outputs=["text"],
        ).metadata(),
        "motion": MockPlugin(
            "motion",
            "Motion Detection",
            inputs=["image"],
            outputs=["json"],
        ).metadata(),
        "face_detect": MockPlugin(
            "face_detect",
            "Face Detection",
            inputs=["image"],
            outputs=["json"],
        ).metadata(),
    }

    adapter = MCPAdapter(plugin_manager=manager, base_url="http://localhost:8000")

    try:
        manifest = adapter.get_manifest()
        print_success("Manifest generated successfully")
    except Exception as e:
        print_error(f"Failed to generate manifest: {e}")
        return False

    # Verify structure
    if not all(key in manifest for key in ["server", "tools", "version"]):
        print_error("Manifest missing required top-level fields")
        return False
    print_success("Manifest has all required top-level fields")

    # Verify server info
    server = manifest["server"]
    if not all(key in server for key in ["name", "version", "mcp_version"]):
        print_error("Server info missing required fields")
        return False
    print_success("Server info has all required fields")

    if server["name"] != MCP_SERVER_NAME:
        print_error(f"Server name mismatch: {server['name']} != {MCP_SERVER_NAME}")
        return False
    print_success(f"Server name correct: {server['name']}")

    if server["mcp_version"] != MCP_PROTOCOL_VERSION:
        print_error(
            f"MCP version mismatch: {server['mcp_version']} != "
            f"{MCP_PROTOCOL_VERSION}"
        )
        return False
    print_success(f"MCP protocol version correct: {server['mcp_version']}")

    # Verify tools
    if not isinstance(manifest["tools"], list):
        print_error("Tools field is not a list")
        return False
    print_success(f"Tools field is a list with {len(manifest['tools'])} items")

    if len(manifest["tools"]) != 3:
        print_error(f"Expected 3 tools, got {len(manifest['tools'])}")
        return False
    print_success("All plugins converted to tools")

    # Verify each tool
    for tool in manifest["tools"]:
        required_fields = [
            "id",
            "title",
            "description",
            "inputs",
            "outputs",
            "invoke_endpoint",
        ]
        if not all(field in tool for field in required_fields):
            print_error(f"Tool {tool.get('id')} missing required fields")
            return False

        if not tool["id"].startswith("vision."):
            print_error(f"Tool ID doesn't start with 'vision.': {tool['id']}")
            return False

        if "plugin=" not in tool["invoke_endpoint"]:
            print_error(
                f"Invoke endpoint missing plugin parameter: "
                f"{tool['invoke_endpoint']}"
            )
            return False

    print_success("All tools have correct structure")

    # Test JSON serialization
    try:
        json_str = json.dumps(manifest)
        print_success(f"Manifest is JSON serializable ({len(json_str)} bytes)")
    except Exception as e:
        print_error(f"Failed to serialize manifest to JSON: {e}")
        return False

    return True


def test_empty_plugins() -> bool:
    """Test manifest with no plugins."""
    print_section("2. Testing Manifest with Empty Plugin List")

    manager = Mock(spec=PluginManager)
    manager.list.return_value = {}

    adapter = MCPAdapter(plugin_manager=manager, base_url="http://localhost:8000")

    try:
        manifest = adapter.get_manifest()
        print_success("Manifest generated successfully with no plugins")
    except Exception as e:
        print_error(f"Failed to generate manifest: {e}")
        return False

    if manifest["tools"] != []:
        print_error(f"Expected empty tools list, got {manifest['tools']}")
        return False
    print_success("Tools list is empty as expected")

    if manifest["server"]["name"] != MCP_SERVER_NAME:
        print_error("Server info missing even with no plugins")
        return False
    print_success("Server info present even with no plugins")

    return True


def test_tool_invocation() -> bool:
    """Test tool invocation handling."""
    print_section("3. Testing Tool Invocation")

    manager = Mock(spec=PluginManager)
    adapter = MCPAdapter(plugin_manager=manager, base_url="http://localhost:8000")

    try:
        result = adapter.invoke_tool("vision.ocr", {"image_path": "test.jpg"})
        print_success("invoke_tool() executed successfully")
    except Exception as e:
        print_error(f"invoke_tool() failed: {e}")
        return False

    required_fields = ["tool_id", "status", "message"]
    if not all(field in result for field in required_fields):
        print_error(f"Invocation result missing required fields: {result}")
        return False
    print_success("Invocation result has all required fields")

    if result["tool_id"] != "vision.ocr":
        print_error(f"Tool ID mismatch: {result['tool_id']}")
        return False
    print_success(f"Tool ID correct: {result['tool_id']}")

    if result["status"] != "use_http":
        print_error(f"Status should be 'use_http', got {result['status']}")
        return False
    print_success(f"Status correct: {result['status']}")

    return True


def test_base_url_handling() -> bool:
    """Test base URL handling in endpoints."""
    print_section("4. Testing Base URL Handling")

    manager = Mock(spec=PluginManager)
    plugin = MockPlugin("test", "Test Plugin")
    manager.list.return_value = {"test": plugin.metadata()}

    # Test with trailing slash
    adapter = MCPAdapter(plugin_manager=manager, base_url="http://localhost:8000/")
    manifest = adapter.get_manifest()
    if "http://localhost:8000//" in manifest["tools"][0]["invoke_endpoint"]:
        print_error("Double slash in invoke endpoint (trailing slash not stripped)")
        return False
    print_success("Trailing slash correctly stripped from base URL")

    # Test with no base URL
    adapter = MCPAdapter(plugin_manager=manager, base_url="")
    manifest = adapter.get_manifest()
    if not manifest["tools"][0]["invoke_endpoint"].startswith("/v1/analyze"):
        print_error("Invoke endpoint should start with /v1/analyze for empty base URL")
        return False
    print_success("Empty base URL handled correctly")

    # Test with HTTPS
    adapter = MCPAdapter(plugin_manager=manager, base_url="https://api.example.com")
    manifest = adapter.get_manifest()
    if not manifest["tools"][0]["invoke_endpoint"].startswith("https://"):
        print_error("HTTPS URL not preserved in invoke endpoint")
        return False
    print_success("HTTPS URL preserved in invoke endpoint")

    return True


def test_gemini_extension_manifest() -> bool:
    """Test Gemini extension manifest generation."""
    print_section("5. Testing Gemini Extension Manifest")

    try:
        manifest = build_gemini_extension_manifest("http://localhost:8000")
        print_success("Gemini manifest generated successfully")
    except Exception as e:
        print_error(f"Failed to generate Gemini manifest: {e}")
        return False

    required_fields = ["name", "version", "description", "mcp", "commands"]
    if not all(field in manifest for field in required_fields):
        print_error("Gemini manifest missing required fields")
        return False
    print_success("Gemini manifest has all required fields")

    if manifest["name"] != "vision-mcp":
        print_error(f"Manifest name should be 'vision-mcp', got {manifest['name']}")
        return False
    print_success(f"Manifest name correct: {manifest['name']}")

    if "manifest_url" not in manifest["mcp"]:
        print_error("MCP section missing manifest_url")
        return False
    print_success("MCP section has manifest_url")

    if manifest["mcp"]["transport"] != "http":
        print_error(f"Transport should be 'http', got {manifest['mcp']['transport']}")
        return False
    print_success(f"Transport correct: {manifest['mcp']['transport']}")

    if not isinstance(manifest["commands"], list) or len(manifest["commands"]) == 0:
        print_error("Commands field is not a non-empty list")
        return False
    print_success(f"Commands list has {len(manifest['commands'])} items")

    # Check for required commands
    command_names = [cmd["name"] for cmd in manifest["commands"]]
    if "vision-analyze" not in command_names:
        print_error("Missing 'vision-analyze' command")
        return False
    print_success("'vision-analyze' command present")

    if "vision-stream" not in command_names:
        print_error("Missing 'vision-stream' command")
        return False
    print_success("'vision-stream' command present")

    # Test custom parameters
    custom_manifest = build_gemini_extension_manifest(
        "http://localhost:8000", name="custom-mcp", version="2.0.0"
    )
    if custom_manifest["name"] != "custom-mcp":
        print_error("Custom name not applied")
        return False
    if custom_manifest["version"] != "2.0.0":
        print_error("Custom version not applied")
        return False
    print_success("Custom parameters applied correctly")

    # Test JSON serialization
    try:
        json_str = json.dumps(custom_manifest)
        print_success(f"Gemini manifest is JSON serializable ({len(json_str)} bytes)")
    except Exception as e:
        print_error(f"Failed to serialize manifest: {e}")
        return False

    return True


def test_protocol_compliance() -> bool:
    """Test MCP protocol compliance."""
    print_section("6. Testing MCP Protocol Compliance")

    manager = Mock(spec=PluginManager)
    plugin = MockPlugin(
        "test",
        "Test",
        inputs=["image", "video"],
        outputs=["json", "text"],
    )
    manager.list.return_value = {"test": plugin.metadata()}

    adapter = MCPAdapter(plugin_manager=manager, base_url="http://localhost:8000")
    manifest = adapter.get_manifest()
    tool = manifest["tools"][0]

    # Check tool ID format
    if not tool["id"].startswith("vision."):
        print_error("Tool ID doesn't follow vision.* format")
        return False
    print_success(f"Tool ID format correct: {tool['id']}")

    # Check that inputs/outputs are preserved
    if tool["inputs"] != ["image", "video"]:
        print_error(f"Inputs not preserved: {tool['inputs']}")
        return False
    print_success("Plugin inputs preserved in tool")

    if tool["outputs"] != ["json", "text"]:
        print_error(f"Outputs not preserved: {tool['outputs']}")
        return False
    print_success("Plugin outputs preserved in tool")

    # Check manifest version format
    if manifest["version"] != "1.0":
        print_error(f"Manifest version should be '1.0', got {manifest['version']}")
        return False
    print_success(f"Manifest version format correct: {manifest['version']}")

    # Check server version
    if manifest["server"]["version"] != MCP_SERVER_VERSION:
        print_error(f"Server version mismatch: {manifest['server']['version']}")
        return False
    print_success(f"Server version correct: {manifest['server']['version']}")

    return True


def main() -> int:
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print("  MCP Adapter Manual Testing Script")
    print("=" * 70)
    print(f"  Server: {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    print(f"  MCP Protocol: v{MCP_PROTOCOL_VERSION}")

    tests = [
        ("Manifest Generation", test_manifest_generation),
        ("Empty Plugin List", test_empty_plugins),
        ("Tool Invocation", test_tool_invocation),
        ("Base URL Handling", test_base_url_handling),
        ("Gemini Extension Manifest", test_gemini_extension_manifest),
        ("Protocol Compliance", test_protocol_compliance),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((name, False))

    # Print summary
    print_section("Test Summary")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {name}: {status}")

    print(f"\n  Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
