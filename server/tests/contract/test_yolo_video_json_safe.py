"""Test YOLO video tool for JSON-safe output compliance."""

import json
import os
from importlib.metadata import entry_points

import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS, reason="Set RUN_MODEL_TESTS=1 to run (requires YOLO models)"
)


def is_json_safe(value):
    try:
        json.dumps(value)
        return True
    except Exception:
        return False


def build_dummy_input(input_schema):
    """Build dummy input matching schema types."""
    dummy = {}
    for key, prop_schema in input_schema.get("properties", {}).items():
        prop_type = prop_schema.get("type", "string")
        if prop_type == "string":
            dummy[key] = ""
        elif prop_type == "object":
            dummy[key] = {}
        elif prop_type == "array":
            dummy[key] = []
        elif prop_type == "integer":
            dummy[key] = 0
        elif prop_type == "number":
            dummy[key] = 0.0
        elif prop_type == "boolean":
            dummy[key] = False
        else:
            dummy[key] = ""
    return dummy


def test_yolo_video_tool_returns_json_safe_output():
    """Verify YOLO video tool returns JSON-safe output."""
    eps = entry_points(group="forgesyte.plugins")
    yolo_eps = [ep for ep in eps if ep.name == "yolo-tracker"]
    assert yolo_eps, "YOLO entrypoint not found"

    try:
        plugin_class = yolo_eps[0].load()
    except ImportError:
        pytest.skip("YOLO plugin dependencies not available")

    plugin = plugin_class()
    plugin.on_load()

    # Find video tool
    video_tool = None
    for tool_name, tool_def in plugin.tools.items():
        if "video" in tool_name:
            video_tool = (tool_name, tool_def)
            break

    if not video_tool:
        pytest.skip("No video tool found in YOLO plugin (video tools not yet integrated)")

    tool_name, tool_def = video_tool
    input_schema = tool_def["input_schema"]
    dummy_input = build_dummy_input(input_schema)

    output = plugin.run_tool(tool_name, dummy_input)

    output_dict = (
        output.model_dump()
        if hasattr(output, "model_dump")
        else output.dict() if hasattr(output, "dict") else output
    )

    assert is_json_safe(output_dict), "YOLO video tool returned non-JSON-safe output"
