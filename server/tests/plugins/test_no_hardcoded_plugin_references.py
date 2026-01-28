"""Regression test: Ensure no hardcoded plugin references exist."""

import os
import re

FORBIDDEN_PATTERNS = [
    r"ocr ",  # trailing space is intentional
    r"yolo ",  # trailing space is intentional
    r"yolo-tracker",
    r"forgesyte-yolo-tracker",
    r"ocr_plugin",
    r"motion_detector",
    r"OCRPlugin",
    r"MotionDetectorPlugin",
]

SOURCE_ROOT = "app"


def test_no_hardcoded_plugin_references() -> None:
    """
    Regression test:
    Ensures no hardcoded plugin references exist anywhere in the codebase.

    This enforces the architectural invariant that plugins must ONLY be
    discovered via entry points and NEVER imported or referenced directly.
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
        raise AssertionError("Hardcoded plugin references detected:\n" + formatted)
