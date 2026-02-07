#!/usr/bin/env python3
"""
Execution Governance Mechanical Scanner

Checks for execution governance violations using efficient pattern matching.
"""

import re
import sys

# Define paths
import os

SERVER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"
)

# Patterns to detect actual code calls (not comments/docstrings)
DIRECT_PLUGIN_RUN = re.compile(
    r'^\s*(?!#)(?!.*["\'])(?:[a-zA-Z_][a-zA-Z0-9_.]*\s*=\s*)?plugin\.run\s*\('
)
FORBIDDEN_LIFECYCLE = re.compile(r"LifecycleState\.(SUCCESS|ERROR)")

# Tool name contract patterns (Issue #164)
FORBIDDEN_TOOL_NAME_PATTERNS = [
    r'args\.get\s*\(\s*["\']tool_name["\']\s*,\s*["\']default["\']\s*\)',  # args.get("tool_name", "default")
    r'tool_name\s*=\s*["\']default["\']',  # tool_name = "default"
    r'tool_name\s*or\s*["\']default["\']',  # tool_name or "default"
]
FORBIDDEN_TOOL_NAME = re.compile("|".join(FORBIDDEN_TOOL_NAME_PATTERNS), re.IGNORECASE)


def check_file(path: str) -> list[str]:
    """Check a single file for violations."""
    violations: list[str] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        return violations

    for i, line in enumerate(lines, 1):
        # Skip comments and docstrings (lines with only quotes)
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if '"""' in stripped or "'''" in stripped:
            continue

        # Check for direct plugin.run() calls
        if DIRECT_PLUGIN_RUN.search(line):
            violations.append(f"Direct plugin.run() in {path}:{i}")

        # Check for forbidden lifecycle states
        if "LifecycleState.SUCCESS" in line or "LifecycleState.ERROR" in line:
            violations.append(f"Forbidden LifecycleState in {path}:{i}")

        # Check for tool_name contract violations (Issue #164)
        if FORBIDDEN_TOOL_NAME.search(line):
            violations.append(
                f"Tool name contract violation (hardcoded 'default') in {path}:{i}"
            )

    return violations


def main() -> int:
    """Run all checks and return exit code."""
    print("=" * 60)
    print("Execution Governance Scanner")
    print("=" * 60)
    print()

    all_violations = []
    files_checked = 0

    print("[1/2] Scanning for violations...")

    # Walk server/app directory (excluding tests)
    for root, dirs, files in os.walk(SERVER_DIR):
        # Skip test directories
        if "/tests/" in root:
            continue
        # Skip __pycache__
        if "__pycache__" in root:
            continue
        # Skip .pyc files
        if root.endswith(".pyc"):
            continue

        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                violations = check_file(path)
                if violations:
                    all_violations.extend(violations)
                files_checked += 1

    print(f"   Checked {files_checked} files")

    if all_violations:
        print(f"   ❌ Found {len(all_violations)} violations:")
        for v in all_violations[:10]:
            print(f"      - {v}")
        if len(all_violations) > 10:
            print(f"      ... and {len(all_violations) - 10} more")
    else:
        print("   ✅ No violations found")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if all_violations:
        print(f"❌ FAILED - {len(all_violations)} violation(s) found")
        return 1
    else:
        print("✅ PASSED - All execution governance rules satisfied")
        return 0


if __name__ == "__main__":
    sys.exit(main())
