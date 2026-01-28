"""Regression test: Ensure PluginManager is completely removed."""

import os
import re

SOURCE_ROOT = "app"
FORBIDDEN_PATTERNS = [
    r"PluginManager",  # Class name itself
]


def test_no_pluginmanager_reference() -> None:
    """
    Regression test:
    Ensure the legacy PluginManager API is fully removed.

    All code must depend on PluginRegistry (and the PluginRegistry protocol)
    as the single canonical plugin API.
    """
    offending = []

    for root, _, files in os.walk(SOURCE_ROOT):
        for filename in files:
            if not filename.endswith((".py", ".pyi")):
                continue

            path = os.path.join(root, filename)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, content):
                    offending.append((path, pattern))

    if offending:
        formatted = "\n".join(
            f" - {path} (matched '{pattern}')" for path, pattern in offending
        )
        raise AssertionError("Legacy PluginManager references detected:\n" + formatted)
