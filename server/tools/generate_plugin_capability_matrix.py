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
    lines = []
    lines.append("# Plugin Capability Matrix (Generated)\n")
    lines.append("This file is auto-generated. Do not edit manually.\n")

    for plugin_id, tools in sorted(plugins.items()):
        lines.append(f"## {plugin_id}\n")

        if not tools:
            lines.append("_No tools defined._\n")
            continue

        lines.append("| Tool | Input Types | Output Types | Capabilities |")
        lines.append("|------|-------------|--------------|--------------|")

        for tool_id, meta in sorted(tools.items()):
            lines.append(
                f"| `{tool_id}` | "
                f"{', '.join(meta.get('input_types', []))} | "
                f"{', '.join(meta.get('output_types', []))} | "
                f"{', '.join(meta.get('capabilities', []))} |"
            )

        lines.append("")

    return "\n".join(lines)


def main():
    plugins = load_plugins()
    content = generate_matrix(plugins)
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(content)
    print(f"Generated {OUTFILE}")


if __name__ == "__main__":
    main()
