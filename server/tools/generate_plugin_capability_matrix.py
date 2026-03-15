#!/usr/bin/env python3
"""
Generate Plugin Capability Matrix.

Reads manifests from forgesyte-plugins and writes:
docs/plugin_capability_matrix_generated.md
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / ".." / "forgesyte-plugins" / "plugins"
OUTFILE = ROOT / ".." / "docs" / "plugin_capability_matrix_generated.md"


def load_plugins():
    plugins = {}
    for manifest_path in PLUGINS_DIR.glob("*/manifest.json"):
        plugin_id = manifest_path.parent.name
        with manifest_path.open() as f:
            data = json.load(f)
        plugins[plugin_id] = data.get("tools", {})
    return plugins


def generate_matrix(plugins):
    """Generate flat table format with Plugin column."""
    lines = []
    lines.append("# Plugin Capability Matrix\n")

    if not plugins:
        lines.append("_No plugins found._\n")
        return "".join(lines)

    lines.append("| Plugin | Tool | Input Types | Output Types | Capabilities |")
    lines.append("|--------|------|-------------|--------------|--------------|")

    for plugin_id in sorted(plugins.keys()):
        tools = plugins[plugin_id]
        for tool_id, meta in sorted(tools.items()):
            input_types = ", ".join(meta.get("input_types", []))
            output_types = ", ".join(meta.get("output_types", []))
            capabilities = ", ".join(meta.get("capabilities", []))
            lines.append(
                f"| `{plugin_id}` | `{tool_id}` | "
                f"{input_types} | {output_types} | {capabilities} |"
            )

    return "\n".join(lines) + "\n"


def main():
    if not PLUGINS_DIR.exists():
        print(f"Plugins directory not found: {PLUGINS_DIR}")
        print("Skipping capability matrix generation.")
        return

    plugins = load_plugins()
    if not plugins:
        print("No plugins found. Skipping generation.")
        return

    content = generate_matrix(plugins)
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(content)
    print(f"Generated {OUTFILE}")


if __name__ == "__main__":
    main()
