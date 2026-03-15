#!/usr/bin/env python3
"""
Pipeline Validator (plugin-agnostic, abstract tool types).

Validates:
- node/edge structure
- no cycles
- reachability from entry_nodes
- sinks are output_nodes
- type compatibility via input_types/output_types on nodes
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = ROOT / "app" / "pipelines"


def detect_cycle(nodes: List[dict], edges: List[dict]) -> bool:
    graph: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        graph[e["from_node"]].append(e["to_node"])

    visited: Set[str] = set()
    stack: Set[str] = set()

    def dfs(nid: str) -> bool:
        if nid in stack:
            return True
        if nid in visited:
            return False
        visited.add(nid)
        stack.add(nid)
        for nxt in graph.get(nid, []):
            if dfs(nxt):
                return True
        stack.remove(nid)
        return False

    return any(dfs(n["id"]) for n in nodes)


def validate_pipeline_file(path: Path) -> List[str]:
    with path.open() as f:
        data: Dict[str, Any] = json.load(f)

    pid = data.get("id", path.stem)
    errors: List[str] = []

    nodes: List[dict] = data.get("nodes", [])
    edges: List[dict] = data.get("edges", [])
    entry_nodes: List[str] = data.get("entry_nodes", [])
    output_nodes: List[str] = data.get("output_nodes", [])

    if not nodes:
        return [f"{pid}: pipeline has no nodes"]

    node_ids = [n["id"] for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{pid}: node IDs must be unique")

    node_set = set(node_ids)

    # Edge references
    for e in edges:
        if e["from_node"] not in node_set:
            errors.append(f"{pid}: edge from unknown node '{e['from_node']}'")
        if e["to_node"] not in node_set:
            errors.append(f"{pid}: edge to unknown node '{e['to_node']}'")

    # Entry/output nodes exist
    for nid in entry_nodes:
        if nid not in node_set:
            errors.append(f"{pid}: entry node '{nid}' not in nodes")
    for nid in output_nodes:
        if nid not in node_set:
            errors.append(f"{pid}: output node '{nid}' not in nodes")

    # Cycle detection
    if detect_cycle(nodes, edges):
        errors.append(f"{pid}: pipeline graph contains a cycle")

    # Reachability
    graph: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        graph[e["from_node"]].append(e["to_node"])

    reachable: Set[str] = set()

    def dfs_reach(nid: str):
        if nid in reachable:
            return
        reachable.add(nid)
        for nxt in graph.get(nid, []):
            dfs_reach(nxt)

    for nid in entry_nodes:
        dfs_reach(nid)

    unreachable = node_set - reachable
    if unreachable:
        errors.append(f"{pid}: unreachable nodes: {sorted(unreachable)}")

    # Sinks must be output nodes
    sinks = {nid for nid in node_set if not graph.get(nid)}
    non_output_sinks = sinks - set(output_nodes)
    if non_output_sinks:
        errors.append(
            f"{pid}: nodes with no outgoing edges must be output nodes: {sorted(non_output_sinks)}"
        )

    # Type compatibility (abstract)
    node_map = {n["id"]: n for n in nodes}

    for n in nodes:
        if "input_types" not in n or "output_types" not in n:
            errors.append(
                f"{pid}: node '{n['id']}' must define input_types and output_types"
            )

    for e in edges:
        src = node_map[e["from_node"]]
        dst = node_map[e["to_node"]]

        src_out = set(src.get("output_types", []))
        dst_in = set(dst.get("input_types", []))

        if src_out and dst_in and not (src_out & dst_in):
            errors.append(
                f"{pid}: type mismatch {e['from_node']}→{e['to_node']}: "
                f"src outputs={sorted(src_out)}, dst inputs={sorted(dst_in)}"
            )

    return errors


def main():
    pipeline_files = sorted(PIPELINES_DIR.glob("*.json"))

    if not pipeline_files:
        print("⚠️ No pipeline files found in app/pipelines/")
        sys.exit(0)

    all_errors: List[str] = []
    for pf in pipeline_files:
        all_errors.extend(validate_pipeline_file(pf))

    if all_errors:
        print("❌ Pipeline validation failed:")
        for e in all_errors:
            print(" -", e)
        sys.exit(1)

    print("✅ All pipelines valid.")


if __name__ == "__main__":
    main()
