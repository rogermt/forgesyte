"""Test that all plugin tools return JSON-safe output."""

import json
from importlib.metadata import entry_points


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
            if key == "image_bytes":
                # OCR plugin needs actual bytes
                dummy[key] = b""
            else:
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


def test_all_tools_return_json_safe_output():
    """Ensure every plugin tool returns JSON-serializable output."""
    eps = entry_points(group="forgesyte.plugins")

    for ep in eps:
        try:
            plugin_class = ep.load()
        except ImportError:
            # Skip plugins with missing dependencies (e.g., cv2, torch)
            continue

        plugin = plugin_class()
        plugin.on_load()

        for tool_name, tool_def in plugin.tools.items():
            # Build dummy input matching schema types
            input_schema = tool_def["input_schema"]
            dummy_input = build_dummy_input(input_schema)

            # Call tool via run_tool (plugin contract)
            output = plugin.run_tool(tool_name, dummy_input)

            # Check if output is JSON-safe
            output_dict = (
                output.model_dump()
                if hasattr(output, "model_dump")
                else output.dict() if hasattr(output, "dict") else output
            )

            assert is_json_safe(output_dict), (
                f"Tool '{tool_name}' in plugin '{plugin.name}' "
                f"returned non-JSON-safe output"
            )
