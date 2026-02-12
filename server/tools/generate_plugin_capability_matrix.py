#!/usr/bin/env python3
"""Phase 14 Plugin Capability Matrix Generator.

This script generates a Markdown table documenting all plugins, tools,
and their declared input/output types and capabilities.

Usage:
    python tools/generate_plugin_capability_matrix.py

Output:
    docs/phase_14_plugin_capability_matrix.md
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / ".." / "plugins"
OUT = ROOT / ".." / "docs" / "phase_14_plugin_capability_matrix.md"


def main():
    """Generate the plugin capability matrix."""
    rows = []

    for manifest_path in sorted(PLUGINS_DIR.glob("*/manifest.json")):
        plugin_id = manifest_path.parent.name
        with manifest_path.open() as f:
            data = json.load(f)

        for tool_id, tool in data.get("tools", {}).items():
            rows.append(
                {
                    "plugin": plugin_id,
                    "tool": tool_id,
                    "input_types": ", ".join(tool.get("input_types", [])),
                    "output_types": ", ".join(tool.get("output_types", [])),
                    "capabilities": ", ".join(tool.get("capabilities", [])),
                }
            )

    lines = []
    lines.append("# Phase 14 Plugin Capability Matrix\n")
    lines.append("| Plugin | Tool | Input Types | Output Types | Capabilities |")
    lines.append("|--------|------|-------------|--------------|--------------|")

    for r in sorted(rows, key=lambda x: (x["plugin"], x["tool"])):
        lines.append(
            f"| `{r['plugin']}` | `{r['tool']}` | {r['input_types']} | {r['output_types']} | {r['capabilities']} |"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"✅ Wrote capability matrix to {OUT}")


if __name__ == "__main__":
    main()
