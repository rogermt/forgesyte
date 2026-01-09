"""Tests for TypeScript configuration files."""

import json
from pathlib import Path


def test_tsconfig_json_exists():
    """Test that tsconfig.json exists."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    assert tsconfig.exists(), "tsconfig.json does not exist"


def test_tsconfig_json_valid():
    """Test that tsconfig.json has valid JSON syntax."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)
    assert isinstance(data, dict), "tsconfig.json should be a JSON object"


def test_tsconfig_json_compiler_options():
    """Test that tsconfig.json has required compiler options."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    options = data.get("compilerOptions", {})
    required = ["target", "lib", "module", "jsx", "strict", "noUnusedLocals"]
    for opt in required:
        assert opt in options, f"Missing compiler option: {opt}"

    # Verify strict mode enabled
    assert options.get("strict") is True, "Strict mode should be true"
    assert options.get("noUnusedLocals") is True, "noUnusedLocals should be true"
    assert (
        options.get("noUnusedParameters") is True
    ), "noUnusedParameters should be true"


def test_tsconfig_node_json_exists():
    """Test that tsconfig.node.json exists."""
    tsconfig_node = Path(__file__).parent / "tsconfig.node.json"
    assert tsconfig_node.exists(), "tsconfig.node.json does not exist"


def test_tsconfig_node_json_valid():
    """Test that tsconfig.node.json has valid JSON syntax."""
    tsconfig_node = Path(__file__).parent / "tsconfig.node.json"
    with open(tsconfig_node) as f:
        data = json.load(f)
    assert isinstance(data, dict), "tsconfig.node.json should be a JSON object"
    assert "compilerOptions" in data, "Missing compilerOptions"
    assert "include" in data, "Missing include"
