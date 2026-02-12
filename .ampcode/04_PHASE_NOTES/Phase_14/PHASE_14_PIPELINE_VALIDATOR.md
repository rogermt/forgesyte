Absolutely, Roger — here is the **complete Phase 14 configuration system**, all in one place, clean, production‑ready, and aligned with the governance style you’ve been enforcing across the project.

This gives you:

- **Full `settings.py` / `config.py` system**  
- **Backend + frontend `.env` templates**  
- **A CORS diagnostic endpoint**  
- **A Phase 14 environment sanity‑check script**  

Everything is deterministic, explicit, and future‑proof.

Let’s build this properly.

---

# ⭐ 1. Phase 14 `settings.py` / `config.py` System  
This is the canonical configuration layer for the backend.

Create:

```
server/app/settings.py
```

```python
import os
from functools import lru_cache
from typing import List


class Settings:
    # -----------------------------
    # Core API configuration
    # -----------------------------
    api_prefix: str = "/v1"

    # -----------------------------
    # CORS configuration
    # -----------------------------
    cors_origins_raw: str = os.getenv("FORGESYTE_CORS_ORIGINS", "")
    cors_origins: List[str] = []

    # -----------------------------
    # Logging configuration
    # -----------------------------
    log_level: str = os.getenv("FORGESYTE_LOG_LEVEL", "INFO")
    log_file: str = os.getenv("FORGESYTE_LOG_FILE", "forgesyte.log")

    # -----------------------------
    # WebSocket configuration
    # -----------------------------
    ws_enabled: bool = os.getenv("FORGESYTE_WS_ENABLED", "true").lower() == "true"

    def __init__(self):
        if self.cors_origins_raw:
            self.cors_origins = [
                origin.strip()
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]
        else:
            # Safe defaults for local dev
            self.cors_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

# ⭐ 2. Integrate settings into `main.py`

Modify:

```
server/app/main.py
```

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import get_settings

settings = get_settings()

app = FastAPI()

# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Diagnostic endpoint
# -----------------------------
@app.get("/v1/debug/cors")
def debug_cors():
    return {
        "allowed_origins": settings.cors_origins,
        "raw_env": settings.cors_origins_raw,
    }
```

This gives you a **live endpoint** to confirm CORS config.

---

# ⭐ 3. Backend `.env` Template (Phase 14)

Create:

```
server/.env
```

```env
# -----------------------------
# Backend API configuration
# -----------------------------
FORGESYTE_LOG_LEVEL=INFO
FORGESYTE_LOG_FILE=/kaggle/working/forgesyte/server/forgesyte.log

# -----------------------------
# CORS configuration
# -----------------------------
# Add all allowed frontend origins here
FORGESYTE_CORS_ORIGINS=http://localhost:3000,https://forgetunnel.loca.lt

# -----------------------------
# WebSocket configuration
# -----------------------------
FORGESYTE_WS_ENABLED=true
```

This is the **canonical** way to configure CORS for tunnels, local dev, or production.

---

# ⭐ 4. Frontend `.env` Template (Phase 14)

Create:

```
web-ui/.env.local
```

```env
# REST API base URL
VITE_API_URL=https://forgetunnel.loca.lt/v1

# WebSocket URL
VITE_WS_URL=wss://forgetunnel.loca.lt/v1/stream
```

This ensures:

- REST → correct backend  
- WS → correct backend  
- No more localhost mismatches  

---

# ⭐ 5. CORS Diagnostic Endpoint (already added above)

You now have:

```
GET /v1/debug/cors
```

Example output:

```json
{
  "allowed_origins": [
    "http://localhost:3000",
    "https://forgetunnel.loca.lt"
  ],
  "raw_env": "http://localhost:3000,https://forgetunnel.loca.lt"
}
```

This is invaluable for debugging tunnels.

---

# ⭐ 6. Phase 14 Environment Sanity‑Check Script  
This script verifies:

- REST connectivity  
- WS connectivity  
- CORS headers  
- API prefix correctness  
- Plugin listing endpoint  

Create:

```
scripts/env_check.py
```

```python
import asyncio
import json
import websockets
import requests

API_URL = "https://forgetunnel.loca.lt/v1"
WS_URL = "wss://forgetunnel.loca.lt/v1/stream"


def check_rest():
    print("🔍 Checking REST API:", API_URL)

    try:
        r = requests.options(f"{API_URL}/plugins")
        print("OPTIONS /plugins:", r.status_code)
        print("CORS headers:", r.headers.get("Access-Control-Allow-Origin"))

        r = requests.get(f"{API_URL}/plugins")
        print("GET /plugins:", r.status_code)
        print("Response:", r.json())
    except Exception as e:
        print("❌ REST check failed:", e)


async def check_ws():
    print("\n🔍 Checking WebSocket:", WS_URL)

    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            msg = await ws.recv()
            print("WS response:", msg)
    except Exception as e:
        print("❌ WS check failed:", e)


if __name__ == "__main__":
    check_rest()
    asyncio.run(check_ws())
```

Run it with:

```
python scripts/env_check.py
```

This gives you a **single command** to verify:

- CORS  
- REST  
- WS  
- Plugin endpoint  
- Tunnel connectivity  

---

# ⭐ 7. Summary

You now have:

### ✔ Full Phase 14 `settings.py` / `config.py`  
### ✔ Backend `.env` template  
### ✔ Frontend `.env.local` template  
### ✔ CORS diagnostic endpoint  
### ✔ Environment sanity‑check script  

This is the **canonical Phase 14 configuration system** — explicit, deterministic, and ready for tunnels, local dev, and production.

---

Roger, here you go — the **full Phase 14 governance pack** you asked for.  
This is the kind of material you’d drop straight into `docs/` and treat as canonical.  
It’s crisp, enforceable, and aligned with the deterministic, governance‑driven engineering culture you’ve been building.

I’ll give you:

1. **Phase 14 Config Governance Doc**  
2. **Phase 14 Deployment Checklist**  
3. **Phase 14 Plugin Metadata Validator (CI‑ready)**  

All in one place, clean and authoritative.

---

# **📘 Phase 14 Configuration Governance Document**  
`docs/governance/phase_14_config_governance.md`

---

## **1. Purpose**

Phase 14 introduces cross‑plugin DAG pipelines, remote tunnels, WebSockets, and multi‑origin UI environments.  
This requires a **formal configuration governance model** to ensure:

- deterministic behavior  
- reproducible environments  
- explicit configuration boundaries  
- safe cross‑origin communication  
- predictable plugin and pipeline loading  

This document defines the **canonical configuration system** for the backend and frontend.

---

## **2. Configuration Principles**

### **2.1 Explicit > Implicit**
No configuration is inferred.  
All environment‑dependent behavior must be explicitly declared.

### **2.2 Deterministic Startup**
The backend must behave identically across:

- local dev  
- tunnels  
- staging  
- production  

### **2.3 Single Source of Truth**
All configuration values must originate from:

```
server/app/settings.py
```

No scattered environment reads.

### **2.4 Safe Defaults**
If a value is missing:

- local dev defaults apply  
- never silently degrade security  
- never silently disable features  

### **2.5 Observability of Configuration**
The system must expose:

```
/v1/debug/cors
/v1/debug/config
```

for runtime introspection.

---

## **3. Configuration Structure**

### **3.1 Backend**

```
server/app/settings.py
server/.env
```

### **3.2 Frontend**

```
web-ui/.env.local
```

### **3.3 Required Environment Variables**

| Variable | Purpose | Required | Example |
|---------|----------|----------|---------|
| `FORGESYTE_CORS_ORIGINS` | Allowed UI origins | Yes | `http://localhost:3000,https://forgetunnel.loca.lt` |
| `FORGESYTE_LOG_LEVEL` | Logging level | No | `INFO` |
| `FORGESYTE_LOG_FILE` | Log file path | No | `/kaggle/.../forgesyte.log` |
| `FORGESYTE_WS_ENABLED` | Enable WebSockets | No | `true` |

### **3.4 Frontend Variables**

| Variable | Purpose | Example |
|---------|----------|---------|
| `VITE_API_URL` | REST base URL | `https://forgetunnel.loca.lt/v1` |
| `VITE_WS_URL` | WebSocket URL | `wss://forgetunnel.loca.lt/v1/stream` |

---

## **4. CORS Governance**

### **4.1 Allowed Origins Must Be Explicit**
Wildcards like `https://*.loca.lt` are **not allowed**.

### **4.2 Tunnel Domains Must Be Listed**
Every tunnel domain must be explicitly added to:

```
FORGESYTE_CORS_ORIGINS
```

### **4.3 CORS Must Be Validated at Runtime**
The endpoint:

```
GET /v1/debug/cors
```

must always reflect the active configuration.

---

## **5. WebSocket Governance**

### **5.1 WS and REST Must Use the Same Origin Set**
If REST allows an origin, WS handshake must allow it too.

### **5.2 WS Must Be Explicitly Enabled**
`FORGESYTE_WS_ENABLED=false` must disable WS endpoints cleanly.

---

## **6. Plugin & Pipeline Governance**

### **6.1 Plugin Metadata Must Be Validated at Startup**
Every plugin must declare:

- `input_types`
- `output_types`
- `capabilities`

### **6.2 Pipeline Definitions Must Be Validated**
Validation includes:

- acyclic graph  
- known plugins  
- known tools  
- type compatibility  

---

## **7. Configuration Drift Prevention**

- All config values must be logged at startup.  
- CI must validate plugin metadata.  
- CI must validate pipeline definitions.  
- CI must validate `.env` templates.  

---

# **📦 Phase 14 Deployment Checklist**  
`docs/deployment/phase_14_deployment_checklist.md`

---

## **1. Pre‑Deployment**

### **1.1 Backend Environment**
- [ ] `.env` file exists  
- [ ] `FORGESYTE_CORS_ORIGINS` set  
- [ ] `FORGESYTE_LOG_LEVEL` set  
- [ ] `FORGESYTE_WS_ENABLED` set  
- [ ] `uvicorn` log level configured  

### **1.2 Frontend Environment**
- [ ] `VITE_API_URL` set  
- [ ] `VITE_WS_URL` set  
- [ ] UI builds successfully  

### **1.3 Plugin Validation**
- [ ] All plugin manifests contain metadata  
- [ ] All tools return dict outputs  
- [ ] All tools accept dict payloads  
- [ ] Plugin metadata validator passes  

### **1.4 Pipeline Validation**
- [ ] All pipelines load  
- [ ] All pipelines pass DAG validation  
- [ ] No cycles  
- [ ] All plugin/tool references valid  

---

## **2. Deployment**

### **2.1 Backend**
- [ ] Start FastAPI  
- [ ] Confirm `/v1/debug/cors`  
- [ ] Confirm `/v1/plugins`  
- [ ] Confirm `/v1/pipelines`  

### **2.2 Frontend**
- [ ] Confirm UI loads  
- [ ] Confirm plugin list loads  
- [ ] Confirm pipeline selector loads  

### **2.3 WebSocket**
- [ ] Confirm WS handshake  
- [ ] Confirm WS frame processing  
- [ ] Confirm WS pipeline execution  

---

## **3. Post‑Deployment**

- [ ] Check logs for errors  
- [ ] Check DuckDB ingestion  
- [ ] Run environment sanity script  
- [ ] Validate MP4 upload (Phase 15 readiness)  

---

# **🧪 Phase 14 Plugin Metadata Validator (CI‑Ready)**  
`tools/validate_plugins.py`

---

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"

REQUIRED_FIELDS = ["input_types", "output_types", "capabilities"]


def validate_manifest(path: Path):
    with path.open() as f:
        data = json.load(f)

    errors = []

    for tool_name, tool in data.get("tools", {}).items():
        for field in REQUIRED_FIELDS:
            if field not in tool:
                errors.append(f"{path}: tool '{tool_name}' missing '{field}'")

            elif not isinstance(tool[field], list):
                errors.append(f"{path}: tool '{tool_name}' field '{field}' must be a list")

            elif not tool[field]:
                errors.append(f"{path}: tool '{tool_name}' field '{field}' cannot be empty")

    return errors


def main():
    manifests = list(PLUGINS_DIR.glob("*/manifest.json"))
    all_errors = []

    for manifest in manifests:
        all_errors.extend(validate_manifest(manifest))

    if all_errors:
        print("❌ Plugin metadata validation failed:")
        for err in all_errors:
            print(" -", err)
        sys.exit(1)

    print("✅ All plugin manifests valid.")


if __name__ == "__main__":
    main()
```

---

# **🎯 Summary**

You now have:

### ✔ Phase 14 Config Governance Doc  
### ✔ Phase 14 Deployment Checklist  
### ✔ Phase 14 Plugin Metadata Validator (CI‑ready)  

This is the complete governance package for Phase 14 — deterministic, explicit, and ready for real‑world deployment.

Absolutely, Roger — here are the **two artifacts** you asked for, delivered cleanly and without code‑execution tooling:  

- **A Phase 14 Pipeline Validator** (graph + type invariants)  
- **A Phase 14 Plugin Capability Matrix** (auditable at a glance)

Both are written as **drop‑in docs** you can commit directly into `docs/` or `tools/`.

I’ll keep them crisp, deterministic, and aligned with your governance style.

---

# **🔥 Phase 14 Pipeline Validator (Graph + Type Invariants)**  
`docs/governance/phase_14_pipeline_validator.md`

---

## **Purpose**

This validator ensures that every pipeline definition in Phase 14 is:

- structurally valid  
- acyclic  
- type‑compatible  
- referencing real plugins and tools  
- safe for DAG execution  

This prevents runtime failures and enforces deterministic pipeline behavior.

---

## **Validation Rules**

### **1. Structural Integrity**

Each pipeline must satisfy:

- All `nodes[]` have unique IDs  
- All `edges[]` reference valid node IDs  
- All `entry_nodes[]` exist in `nodes[]`  
- All `output_nodes[]` exist in `nodes[]`  

**Failure example:**  
```
edge from_node="n5" but no node "n5" exists
```

---

### **2. Acyclic Graph**

Pipelines must be **DAGs**.  
Cycles are forbidden.

**Failure example:**  
```
Cycle detected: n1 → n2 → n3 → n1
```

---

### **3. Plugin + Tool Existence**

Each node must reference a real plugin and tool:

```
plugin_id: must exist in plugin registry
tool_id: must exist in plugin manifest
```

**Failure example:**  
```
Unknown tool: plugin "ocr" has no tool "segment_text"
```

---

### **4. Type Compatibility (Phase 14 Core Rule)**

For each edge:

```
A.output_types ∩ B.input_types ≠ ∅
```

This ensures that data produced by node A can be consumed by node B.

**Failure example:**  
```
Type mismatch on edge n1 → n2:
  n1 outputs: ["detections"]
  n2 inputs:  ["video_frame"]
```

---

### **5. Capability Consistency (Optional but Recommended)**

Tools should not be chained in ways that violate semantic capability expectations.

Example:

```
OCR.extract_text → ReID.track_ids   ❌ semantically invalid
```

This is not enforced by the engine but should be flagged in governance.

---

## **Validator Output Format**

The validator must output:

- `❌` on any failure  
- `✅ All pipelines valid` on success  

Example failure output:

```
❌ Pipeline validation failed:
 - player_tracking_v1: type mismatch on edge n1→n2
 - player_tracking_v1: unknown tool reid.track_faces
 - player_tracking_v1: pipeline graph contains a cycle
```

---

## **CI Integration**

Add to GitHub Actions:

```
run: python tools/validate_pipelines.py
```

This ensures no invalid pipeline can be merged.

---

# **🔥 Phase 14 Plugin Capability Matrix**  
`docs/phase_14_plugin_capability_matrix.md`

---

## **Purpose**

This matrix provides a **single auditable view** of:

- all plugins  
- all tools  
- their declared input/output types  
- their capabilities  

This is essential for:

- DAG validation  
- pipeline design  
- debugging  
- governance  
- cross‑plugin compatibility analysis  

---

## **Matrix Format**

| Plugin | Tool | Input Types | Output Types | Capabilities |
|--------|------|-------------|--------------|--------------|
| `ocr` | `extract_text` | `image`, `video_frame` | `text_blocks` | `ocr`, `text_extraction` |
| `yolo` | `detect_players` | `video_frame` | `detections` | `player_detection` |
| `reid` | `track_ids` | `detections` | `tracks` | `reid`, `tracking` |
| `viz` | `render_overlay` | `video_frame`, `tracks` | `overlay_frame` | `visualization` |

*(Example — your actual matrix will reflect your manifests.)*

---

## **Governance Rules**

### **1. Every tool must declare:**

- `input_types`  
- `output_types`  
- `capabilities`  

Missing metadata is a **CI failure**.

---

### **2. Types must be consistent across plugins**

If YOLO outputs `"detections"`, then:

- ReID must accept `"detections"`  
- Viz must accept `"detections"` or `"tracks"`  

This matrix makes mismatches obvious.

---

### **3. Capabilities must be meaningful**

Capabilities should describe **what the tool does**, not how it’s implemented.

Good examples:

- `player_detection`
- `ocr`
- `tracking`
- `visualization`

Bad examples:

- `python`
- `fast`
- `gpu`

---

### **4. Matrix must be regenerated on every plugin change**

Add to CI:

```
python tools/generate_plugin_capability_matrix.py
git diff --exit-code docs/phase_14_plugin_capability_matrix.md
```

This ensures the matrix is always up‑to‑date.

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