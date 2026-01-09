"""
Test suite for WU-09: Vite config path aliases.

Ensures vite.config.ts has resolve.alias configured to mirror tsconfig.json paths:
- @/*: src/*
- @/components/*: src/components/*
- @/hooks/*: src/hooks/*
- @/api/*: src/api/*
"""

import json
import re
import subprocess
from pathlib import Path

# Get web-ui directory
WEB_UI_DIR = Path(__file__).parent


def test_vite_config_exists():
    """Verify vite.config.ts exists and is readable."""
    vite_path = WEB_UI_DIR / "vite.config.ts"
    with open(vite_path, "r") as f:
        content = f.read()
    assert len(content) > 0, "vite.config.ts is empty"


def test_vite_config_has_import():
    """Verify vite config imports defineConfig."""
    vite_path = WEB_UI_DIR / "vite.config.ts"
    with open(vite_path, "r") as f:
        content = f.read()
    assert "defineConfig" in content, "Missing defineConfig import"
    assert "import" in content, "No imports found"


def test_vite_config_has_resolve_alias():
    """Verify vite config defines resolve.alias object."""
    vite_path = WEB_UI_DIR / "vite.config.ts"
    with open(vite_path, "r") as f:
        content = f.read()
    assert "resolve:" in content or "resolve" in content, "Missing resolve config"
    assert "alias:" in content or "alias" in content, "Missing alias config"


def test_vite_aliases_mirror_tsconfig():
    """Verify all tsconfig base paths are mirrored in vite.config."""
    vite_path = WEB_UI_DIR / "vite.config.ts"
    tsconfig_path = WEB_UI_DIR / "tsconfig.json"

    with open(vite_path, "r") as f:
        vite_content = f.read()

    with open(tsconfig_path, "r") as f:
        tsconfig = json.load(f)

    required_paths = tsconfig.get("compilerOptions", {}).get("paths", {})
    assert required_paths, "No paths found in tsconfig.json"

    # Extract base aliases (without wildcards) from tsconfig
    # @/* -> @ , @/components/* -> @/components, etc.
    base_aliases = set()
    for alias in required_paths.keys():
        base = alias.rstrip("/*")  # Remove trailing /* from wildcard
        base_aliases.add(base)

    # Check each base alias is mentioned in vite config
    for alias in base_aliases:
        assert alias in vite_content, f"Missing alias {alias} in vite.config.ts"


def test_vite_path_resolving_works():
    """Verify TypeScript can resolve paths through vite config."""
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=str(WEB_UI_DIR),
        capture_output=True,
        text=True,
    )

    # Should not have path resolution errors
    assert (
        "Cannot find module" not in result.stderr or "@/" not in result.stderr
    ), f"Path resolution error detected: {result.stderr}"


def test_vite_config_syntax_valid():
    """Verify vite.config.ts has valid TypeScript syntax."""
    result = subprocess.run(
        ["npx", "tsc", "--noEmit", "vite.config.ts"],
        cwd=str(WEB_UI_DIR),
        capture_output=True,
        text=True,
    )

    assert (
        result.returncode == 0 or "vite.config.ts" not in result.stderr
    ), f"TypeScript error in vite.config.ts: {result.stderr}"


def test_all_required_aliases_present():
    """Verify all required base aliases are in vite config."""
    vite_path = WEB_UI_DIR / "vite.config.ts"
    with open(vite_path, "r") as f:
        content = f.read()

    # Vite uses base aliases without wildcards
    required_aliases = ["@", "@/components", "@/hooks", "@/api"]

    for alias in required_aliases:
        # Look for the alias in quotes (single or double)
        pattern = f"[\"']({re.escape(alias)})[\"']"
        matches = re.findall(pattern, content)
        assert len(matches) > 0, f"Missing required alias {alias} in vite.config.ts"
