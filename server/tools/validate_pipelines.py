#!/usr/bin/env python3
"""Phase 14 Pipeline Validator (Graph + Type Invariants).

This validator ensures that every pipeline definition in Phase 14 is:
- structurally valid
- acyclic
- type-compatible
- referencing real plugins and tools
- safe for DAG execution

Usage:
    python tools/validate_pipelines.py

Exit codes:
    0 - All pipelines valid
    1 - Validation failed
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = ROOT / "app" / "pipelines"
PLUGINS_DIR = ROOT / ".." / "plugins"


def load_plugin_metadata() -> Dict[str, Dict[str, dict]]:
    """Load plugin metadata from manifests.

    Returns:
        { plugin_id: { tool_id: {input_types, output_types, capabilities} } }
    """
    result: Dict[str, Dict[str, dict]] = {}

    for manifest_path in PLUGINS_DIR.glob("*/manifest.json"):
        plugin_id = manifest_path.parent.name
        with manifest_path.open() as f:
            data = json.load(f)

        tools = {}
        for tool_id, tool in data.get("tools", {}).items():
            tools[tool_id] = {
                "input_types": tool.get("input_types", []),
                "output_types": tool.get("output_types", []),
                "capabilities": tool.get("capabilities", []),
            }
        result[plugin_id] = tools

    return result


def detect_cycle(nodes: List[dict], edges: List[dict]) -> bool:
    """Detect if the graph contains a cycle using DFS.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        True if cycle detected, False otherwise
    """
    graph = {n["id"]: [] for n in nodes}
    for e in edges:
        graph[e["from_node"]].append(e["to_node"])

    visited: Set[str] = set()
    stack: Set[str] = set()

    def dfs(node_id: str) -> bool:
        if node_id in stack:
            return True
        if node_id in visited:
            return False
        visited.add(node_id)
        stack.add(node_id)
        for nxt in graph.get(node_id, []):
            if dfs(nxt):
                return True
        stack.remove(node_id)
        return False

    return any(dfs(n["id"]) for n in nodes)


def validate_pipeline_file(path: Path, plugins: Dict[str, Dict[str, dict]]) -> List[str]:
    """Validate a single pipeline file.

    Args:
        path: Path to pipeline JSON file
        plugins: Plugin metadata dictionary

    Returns:
        List of error messages (empty if valid)
    """
    with path.open() as f:
        data = json.load(f)

    pid = data.get("id", path.stem)
    errors: List[str] = []

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    entry_nodes = data.get("entry_nodes", [])
    output_nodes = data.get("output_nodes", [])

    if not nodes:
        errors.append(f"{pid}: pipeline has no nodes")
        return errors

    node_ids = [n["id"] for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{pid}: node IDs must be unique")

    node_id_set = set(node_ids)

    # edges reference valid nodes
    for e in edges:
        if e["from_node"] not in node_id_set:
            errors.append(f"{pid}: edge from unknown node '{e['from_node']}'")
        if e["to_node"] not in node_id_set:
            errors.append(f"{pid}: edge to unknown node '{e['to_node']}'")

    # entry/output nodes exist
    for nid in entry_nodes:
        if nid not in node_id_set:
            errors.append(f"{pid}: entry node '{nid}' not in nodes")
    for nid in output_nodes:
        if nid not in node_id_set:
            errors.append(f"{pid}: output node '{nid}' not in nodes")

    # no cycles
    if detect_cycle(nodes, edges):
        errors.append(f"{pid}: pipeline graph contains a cycle")

    # no unreachable nodes (from entry nodes)
    reachable: Set[str] = set()

    graph = {n["id"]: [] for n in nodes}
    for e in edges:
        graph[e["from_node"]].append(e["to_node"])

    def dfs_reach(nid: str):
        if nid in reachable:
            return
        reachable.add(nid)
        for nxt in graph.get(nid, []):
            dfs_reach(nxt)

    for nid in entry_nodes:
        dfs_reach(nid)

    unreachable = node_id_set - reachable
    if unreachable:
        errors.append(f"{pid}: unreachable nodes: {sorted(unreachable)}")

    # nodes with no outgoing edges must be output nodes
    sinks = {n["id"] for n in nodes if not graph.get(n["id"])}
    non_output_sinks = sinks - set(output_nodes)
    if non_output_sinks:
        errors.append(
            f"{pid}: nodes with no outgoing edges must be output nodes, found: {sorted(non_output_sinks)}"
        )

    # plugin/tool existence + type compatibility
    node_map = {n["id"]: n for n in nodes}

    for e in edges:
        src = node_map[e["from_node"]]
        dst = node_map[e["to_node"]]

        src_plugin = src["plugin_id"]
        src_tool = src["tool_id"]
        dst_plugin = dst["plugin_id"]
        dst_tool = dst["tool_id"]

        src_meta = plugins.get(src_plugin, {}).get(src_tool)
        dst_meta = plugins.get(dst_plugin, {}).get(dst_tool)

        if not src_meta:
            errors.append(
                f"{pid}: unknown source tool {src_plugin}.{src_tool} on edge {e['from_node']}→{e['to_node']}"
            )
            continue

        if not dst_meta:
            errors.append(
                f"{pid}: unknown target tool {dst_plugin}.{dst_tool} on edge {e['from_node']}→{e['to_node']}"
            )
            continue

        src_out = set(src_meta["output_types"])
        dst_in = set(dst_meta["input_types"])

        if not src_out & dst_in:
            errors.append(
                f"{pid}: type mismatch on edge {e['from_node']}→{e['to_node']}: "
                f"src {src_plugin}.{src_tool} outputs={sorted(src_out)}, "
                f"dst {dst_plugin}.{dst_tool} inputs={sorted(dst_in)}"
            )

    return errors


def main():
    """Main validation entry point."""
    plugins = load_plugin_metadata()
    pipeline_files = sorted(PIPELINES_DIR.glob("*.json"))

    if not pipeline_files:
        print("⚠️ No pipeline files found in app/pipelines/")
        sys.exit(0)

    all_errors: List[str] = []
    for pf in pipeline_files:
        all_errors.extend(validate_pipeline_file(pf, plugins))

    if all_errors:
        print("❌ Pipeline validation failed:")
        for e in all_errors:
            print(" -", e)
        sys.exit(1)

    print("✅ All pipelines valid.")


if __name__ == "__main__":
    main()