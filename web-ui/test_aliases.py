"""Tests for path aliases in tsconfig."""

import json
from pathlib import Path


def test_tsconfig_has_paths():
    """Test that tsconfig.json has path aliases."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    assert "compilerOptions" in data, "Missing compilerOptions"
    options = data["compilerOptions"]
    assert "paths" in options, "Missing paths in compilerOptions"


def test_tsconfig_has_base_url():
    """Test that tsconfig.json has baseUrl."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    options = data["compilerOptions"]
    assert "baseUrl" in options, "Missing baseUrl in compilerOptions"
    assert options["baseUrl"] == ".", "baseUrl should be '.'"


def test_tsconfig_has_component_alias():
    """Test that path aliases include @/components."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    paths = data["compilerOptions"].get("paths", {})
    assert (
        "@/components/*" in paths or "@/components" in paths
    ), "Should have @/components alias"


def test_tsconfig_has_hooks_alias():
    """Test that path aliases include @/hooks."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    paths = data["compilerOptions"].get("paths", {})
    assert "@/hooks/*" in paths or "@/hooks" in paths, "Should have @/hooks alias"


def test_tsconfig_has_api_alias():
    """Test that path aliases include @/api."""
    tsconfig = Path(__file__).parent / "tsconfig.json"
    with open(tsconfig) as f:
        data = json.load(f)

    paths = data["compilerOptions"].get("paths", {})
    assert "@/api/*" in paths or "@/api" in paths, "Should have @/api alias"
