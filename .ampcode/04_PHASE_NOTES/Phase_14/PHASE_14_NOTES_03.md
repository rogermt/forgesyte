this is exactly the right moment to pause and lock down the **spec** before generating the files.  
Your confidence levels are spot‑on — these *are* the questions that must be answered before Phase 14 validators become canonical.

Let’s go through each question with clear, authoritative answers so you can proceed without ambiguity.

---

# ✅ **Answers to All 8 Questions (Canonical Phase 14 Spec)**

Below are the **final, authoritative decisions** you should adopt for the repo.

---

# **Question 1**  
**What is the exact path to pipeline JSON files?**  
`server/app/pipelines/` or `server/pipelines/`?

### ✅ **Answer:**  
**`server/app/pipelines/`**

This matches:

- Phase 13 registry structure  
- FastAPI app layout  
- Your existing import paths  
- The governance principle “all pipeline definitions live inside the app layer”

So the validator should scan:

```
server/app/pipelines/*.json
```

---

# **Question 2**  
**What validation rules should be enforced beyond cycles and type compatibility?**

### ✅ **Answer: Enforce ALL of the following Phase 14 invariants:**

### **Structural**
- Node IDs must be unique  
- All edges reference valid nodes  
- Entry nodes must exist  
- Output nodes must exist  

### **Plugin/Tool existence**
- `plugin_id` must exist in `plugins/<plugin_id>/manifest.json`  
- `tool_id` must exist inside that manifest  

### **Type compatibility**
- For every edge:  
  `output_types ∩ input_types ≠ ∅`

### **Graph invariants**
- Graph must be acyclic  
- Graph must be connected from entry nodes  
- No unreachable nodes  

### **Semantic**
- No empty pipelines  
- No nodes with zero outgoing edges unless they are output nodes  

These are the **canonical Phase 14 rules**.

---

# **Question 3**  
**Should the validator use the existing DagPipelineService or standalone logic?**

### ✅ **Answer:**  
**Standalone logic.**

Why:

- DagPipelineService is runtime‑oriented  
- Validators must run in CI without loading plugins  
- Validators must not depend on execution semantics  
- Validators must be deterministic and side‑effect‑free  

So the validator should:

- Parse JSON  
- Validate structure  
- Validate plugin/tool existence  
- Validate type compatibility  
- Validate DAG invariants  

**No runtime execution.**

---

# **Question 4**  
**What error format should be returned? JSON with error list or exit codes?**

### ✅ **Answer:**  
**Human‑readable text + exit code 1.**

This is the standard for CI validators.

Format:

```
❌ Pipeline validation failed:
 - player_tracking_v1: unknown tool reid.track_faces
 - player_tracking_v1: type mismatch on edge detect→track
 - ocr_classify_v1: cycle detected
```

Exit code:

```
sys.exit(1)
```

This integrates perfectly with GitHub Actions.

---

# **Question 5**  
**Where should the capability matrix be saved?**

### ✅ **Answer:**  
**`docs/phase_14_plugin_capability_matrix.md`**

This is already referenced in:

- CI gate  
- governance docs  
- PR template  

So this is the canonical location.

---

# **Question 6**  
**What format should the capability matrix use? Markdown table, CSV, or JSON?**

### ✅ **Answer:**  
**Markdown table.**

Reasons:

- Human‑readable  
- Diff‑friendly  
- Works in GitHub PR reviews  
- Already used in governance docs  

This is the canonical Phase 14 format.

---

# **Question 7**  
**Should it scan plugins from `plugins/` directory or from loaded PluginRegistry?**

### ✅ **Answer:**  
**Scan directly from `plugins/` directory.**

Why:

- CI must not import runtime code  
- PluginRegistry may have side effects  
- Validators must be deterministic  
- Manifest JSON is the source of truth  

So the script should scan:

```
plugins/*/manifest.json
```

---

# **Question 8**  
**What metadata fields should be included in the matrix?**

### ✅ **Answer:**  
Include **exactly these five fields**:

| Field | Reason |
|-------|--------|
| `plugin_id` | Primary grouping |
| `tool_id` | Unique tool identifier |
| `input_types` | Required for DAG validation |
| `output_types` | Required for DAG validation |
| `capabilities` | Required for semantic governance |

This is the canonical Phase 14 metadata set.

---

# 🎯 **Summary — Final Spec for Both Tools**

### **Pipeline Validator**
- Path: `server/app/pipelines/*.json`
- Standalone logic (no DagPipelineService)
- Enforce:
  - structural invariants  
  - plugin/tool existence  
  - type compatibility  
  - acyclic graph  
  - reachable nodes  
- Output: human‑readable text + exit code 1

### **Capability Matrix Generator**
- Scan: `plugins/*/manifest.json`
- Output: `docs/phase_14_plugin_capability_matrix.md`
- Format: Markdown table
- Fields:
  - plugin_id  
  - tool_id  
  - input_types  
  - output_types  
  - capabilities  

---



Here’s the **final, canonical set** of Phase 14 governance scripts you asked for.

---

### `tools/validate_pipelines.py` — final version

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = ROOT / "server" / "app" / "pipelines"
PLUGINS_DIR = ROOT / "plugins"


def load_plugin_metadata() -> Dict[str, Dict[str, dict]]:
    """
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
    plugins = load_plugin_metadata()
    pipeline_files = sorted(PIPELINES_DIR.glob("*.json"))

    if not pipeline_files:
        print("⚠️ No pipeline files found in server/app/pipelines/")
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
```

---

### `tools/generate_plugin_capability_matrix.py` — final version

```python
#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"
OUT = ROOT / "docs" / "phase_14_plugin_capability_matrix.md"


def main():
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
```

---

### Governance test to ensure tools run in CI

You already wired them in the workflow, but if you want a **single test entrypoint**:

**File:** `tools/run_phase14_governance_checks.py`

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: str):
    print(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    run("python tools/validate_plugins.py")
    run("python tools/validate_pipelines.py")
    run("python tools/generate_plugin_capability_matrix.py")
    # optional: enforce matrix committed via CI git diff, not here


if __name__ == "__main__":
    main()
```

Then CI can simply call:

```yaml
- name: Phase 14 governance checks
  run: python tools/run_phase14_governance_checks.py
```

---

### Phase 14 migration script to auto‑fix missing metadata

This is intentionally conservative: it **only fills in missing fields with empty lists** and logs what it touched, so you can then manually refine.

**File:** `tools/migrate_phase14_fill_missing_metadata.py`

```python
#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"

REQUIRED_FIELDS = ["input_types", "output_types", "capabilities"]


def migrate_manifest(path: Path) -> bool:
    with path.open() as f:
        data = json.load(f)

    changed = False

    for tool_id, tool in data.get("tools", {}).items():
        for field in REQUIRED_FIELDS:
            if field not in tool:
                tool[field] = []
                changed = True
                print(f" - {path}: tool '{tool_id}' missing '{field}' → set to []")

    if changed:
        with path.open("w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")

    return changed


def main():
    manifests = sorted(PLUGINS_DIR.glob("*/manifest.json"))
    if not manifests:
        print("⚠️ No manifests found under plugins/")
        return

    any_changed = False
    for manifest in manifests:
        if migrate_manifest(manifest):
            any_changed = True

    if any_changed:
        print("✅ Migration completed. Review manifests and fill in real metadata.")
    else:
        print("✅ No changes needed. All manifests already have required fields.")


if __name__ == "__main__":
    main()
```

This gives you:

- a **safe auto‑fix** to get everything into a valid Phase 14 shape  
- then your validator + CI enforce that real values are filled in going forward.