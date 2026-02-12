#!/usr/bin/env python3
"""Phase 14 Plugin Metadata Validator (CI-Ready).

This validator ensures that every plugin manifest contains the required
Phase 14 metadata fields:
- input_types
- output_types
- capabilities

Usage:
    python tools/validate_plugins.py

Exit codes:
    0 - All plugins valid
    1 - Validation failed
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"

REQUIRED_FIELDS = ["input_types", "output_types", "capabilities"]


def validate_manifest(path: Path):
    """Validate a single plugin manifest.

    Args:
        path: Path to manifest.json file

    Returns:
        List of error messages (empty if valid)
    """
    with path.open() as f:
        data = json.load(f)

    errors = []

    for tool_name, tool in data.get("tools", {}).items():
        for field in REQUIRED_FIELDS:
            if field not in tool:
                errors.append(f"{path}: tool '{tool_name}' missing '{field}'")

            elif not isinstance(tool[field], list):
                errors.append(f"{path}: tool '{tool_name}' field '{field}' must be a list")

            elif not tool[field]:
                errors.append(f"{path}: tool '{tool_name}' field '{field}' cannot be empty")

    return errors


def main():
    """Main validation entry point."""
    manifests = list(PLUGINS_DIR.glob("*/manifest.json"))
    all_errors = []

    for manifest in manifests:
        all_errors.extend(validate_manifest(manifest))

    if all_errors:
        print("❌ Plugin metadata validation failed:")
        for err in all_errors:
            print(" -", err)
        sys.exit(1)

    print("✅ All plugin manifests valid.")


if __name__ == "__main__":
    main()