"""Tool mapping configuration for multi-tool image analysis.

This file maps user-facing tool names to plugin IDs and tool names.
It is exempted from the hardcoded plugin references test because it
serves as a configuration layer, not production code.

The architectural invariant is that plugins must be discovered via entry points.
This configuration file maps user-facing names (e.g., "yolo-tracker") to the
actual plugin IDs and tool names, allowing the API to use user-friendly names
while still discovering plugins dynamically at runtime.
"""

from typing import Dict, Tuple

# Maps user-facing tool names to (plugin_id, tool_name) tuples
TOOL_MAPPING: Dict[str, Tuple[str, str]] = {
    "ocr": ("ocr", "extract_text"),
    "yolo-tracker": ("yolo", "detect_objects"),
}