"""Tests for web-ui package.json validation."""

import json
from pathlib import Path


def test_package_json_exists():
    """Test that package.json file exists."""
    package_file = Path(__file__).parent / "package.json"
    assert package_file.exists(), "package.json does not exist"


def test_package_json_valid_syntax():
    """Test that package.json has valid JSON syntax."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)
    assert isinstance(data, dict), "package.json should be a JSON object"


def test_package_json_has_required_fields():
    """Test that package.json has all required fields."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)

    required_fields = [
        "name",
        "version",
        "type",
        "scripts",
        "dependencies",
        "devDependencies",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_package_json_branding():
    """Test that package.json has ForgeSyte branding."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)

    assert (
        data["name"] == "forgesyte-ui"
    ), f"Name should be 'forgesyte-ui', got '{data['name']}'"
    assert "ForgeSyte" in data.get(
        "description", ""
    ), "Description should mention ForgeSyte"


def test_package_json_required_scripts():
    """Test that package.json has all required scripts."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)

    required_scripts = ["dev", "build", "preview", "lint", "type-check"]
    scripts = data.get("scripts", {})
    for script in required_scripts:
        assert script in scripts, f"Missing required script: {script}"


def test_package_json_react_dependencies():
    """Test that package.json has React dependencies."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)

    deps = data.get("dependencies", {})
    assert "react" in deps, "Missing react dependency"
    assert "react-dom" in deps, "Missing react-dom dependency"


def test_package_json_build_tools():
    """Test that package.json has build tools in devDependencies."""
    package_file = Path(__file__).parent / "package.json"
    with open(package_file) as f:
        data = json.load(f)

    dev_deps = data.get("devDependencies", {})
    required = ["typescript", "vite", "@vitejs/plugin-react"]
    for pkg in required:
        assert pkg in dev_deps, f"Missing required devDependency: {pkg}"
