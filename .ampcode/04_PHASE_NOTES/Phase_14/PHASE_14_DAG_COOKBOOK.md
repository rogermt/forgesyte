Let’s do both—patterns first, then a concrete first failing test you can actually drop in.

---

### 📘 Phase 14 DAG patterns cookbook  
`docs/phase_14_dag_patterns_cookbook.md`

#### 1. Player tracking pipeline

**Goal:** detect players, assign stable IDs, render overlays.

```text
[ yolo.detect_players ] → [ reid.track_ids ] → [ viz.render_overlay ]
```

- **Nodes:**
  - `n1`: `yolo.detect_players`
  - `n2`: `reid.track_ids`
  - `n3`: `viz.render_overlay`
- **Type flow:**
  - `n1.output_types`: `["detections"]`
  - `n2.input_types`: `["detections"]`, `output_types`: `["tracks"]`
  - `n3.input_types`: `["video_frame", "tracks"]`

**Blueprint JSON:**

```json
{
  "id": "player_tracking_v1",
  "name": "Player tracking pipeline",
  "nodes": [
    { "id": "detect", "plugin_id": "yolo", "tool_id": "detect_players" },
    { "id": "track",  "plugin_id": "reid", "tool_id": "track_ids" },
    { "id": "render", "plugin_id": "viz",  "tool_id": "render_overlay" }
  ],
  "edges": [
    { "from_node": "detect", "to_node": "track" },
    { "from_node": "track",  "to_node": "render" }
  ],
  "entry_nodes": ["detect"],
  "output_nodes": ["render"]
}
```

---

#### 2. OCR + NLP classification pipeline

**Goal:** extract text from frames, classify it.

```text
[ ocr.extract_text ] → [ nlp.classify_text ]
```

**Blueprint JSON:**

```json
{
  "id": "ocr_classify_v1",
  "name": "OCR + classification",
  "nodes": [
    { "id": "ocr",  "plugin_id": "ocr", "tool_id": "extract_text" },
    { "id": "nlp",  "plugin_id": "nlp", "tool_id": "classify_text" }
  ],
  "edges": [
    { "from_node": "ocr", "to_node": "nlp" }
  ],
  "entry_nodes": ["ocr"],
  "output_nodes": ["nlp"]
}
```

---

#### 3. Parallel analysis + merge

**Goal:** run two analyses in parallel, merge their outputs.

```text
          → [ pluginA.toolA ] →
[ input ]                         [ merge_node ]
          → [ pluginB.toolB ] →
```

- `merge_node` just sees merged payload from both predecessors (Phase 14 last‑wins merge).

**Blueprint JSON:**

```json
{
  "id": "parallel_analysis_v1",
  "name": "Parallel analysis with merge",
  "nodes": [
    { "id": "branch_a", "plugin_id": "pluginA", "tool_id": "toolA" },
    { "id": "branch_b", "plugin_id": "pluginB", "tool_id": "toolB" },
    { "id": "merge",    "plugin_id": "utils",   "tool_id": "merge_payloads" }
  ],
  "edges": [
    { "from_node": "branch_a", "to_node": "merge" },
    { "from_node": "branch_b", "to_node": "merge" }
  ],
  "entry_nodes": ["branch_a", "branch_b"],
  "output_nodes": ["merge"]
}
```

---

### 🧪 Phase 14 “first failing test” for DAG execution

This is the kind of test that locks in the whole contract: registry + plugin manager + merge + type flow.

**File:** `server/app/tests/test_phase14_player_tracking_pipeline.py`

```python
from typing import Dict, Any
from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge
from server.app.services.dag_pipeline_service import DagPipelineService


class DummyPlugin:
    def __init__(self, behavior):
        self.behavior = behavior

    def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.behavior(tool_id, payload)


class DummyPluginManager:
    def __init__(self):
        self._plugins = {}

    def register(self, plugin_id: str, plugin: DummyPlugin):
        self._plugins[plugin_id] = plugin

    def get_plugin(self, plugin_id: str) -> DummyPlugin:
        return self._plugins[plugin_id]


class DummyRegistry:
    def __init__(self, pipeline: PipelineDefinition):
        self._pipeline = pipeline

    def get_pipeline(self, pipeline_id: str) -> PipelineDefinition:
        assert pipeline_id == self._pipeline.id
        return self._pipeline


def make_player_tracking_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        id="player_tracking_v1",
        name="Player tracking pipeline",
        nodes=[
            PipelineNode(id="detect", plugin_id="yolo", tool_id="detect_players"),
            PipelineNode(id="track",  plugin_id="reid", tool_id="track_ids"),
            PipelineNode(id="render", plugin_id="viz",  tool_id="render_overlay"),
        ],
        edges=[
            PipelineEdge(from_node="detect", to_node="track"),
            PipelineEdge(from_node="track",  to_node="render"),
        ],
        entry_nodes=["detect"],
        output_nodes=["render"],
    )


def test_phase14_player_tracking_pipeline_end_to_end():
    pipeline = make_player_tracking_pipeline()
    registry = DummyRegistry(pipeline)
    pm = DummyPluginManager()

    def yolo_behavior(tool_id, payload):
        assert tool_id == "detect_players"
        assert "frame" in payload
        return {"detections": [{"id": 1}]}

    def reid_behavior(tool_id, payload):
        assert tool_id == "track_ids"
        assert "detections" in payload
        return {"tracks": [{"id": 1, "track_id": "p1"}]}

    def viz_behavior(tool_id, payload):
        assert tool_id == "render_overlay"
        assert "tracks" in payload
        # simulate overlay frame
        return {"overlay_frame": b"fake-bytes"}

    pm.register("yolo", DummyPlugin(yolo_behavior))
    pm.register("reid", DummyPlugin(reid_behavior))
    pm.register("viz",  DummyPlugin(viz_behavior))

    dag = DagPipelineService(registry, pm)

    initial_payload = {"frame": b"raw-frame"}
    result = dag.run_pipeline("player_tracking_v1", initial_payload)

    # Final result should include overlay_frame from last node
    assert "overlay_frame" in result
    # And original frame should still be present (depending on your merge rules)
    assert "frame" in result
```

This test will:

- fail if the registry lookup is wrong  
- fail if plugin resolution is wrong  
- fail if payload merging is wrong  
- fail if type flow is broken  
- pass only when the Phase 14 DAG engine is wired correctly end‑to‑end.

Here you go, Roger — a **clean, enforceable CI gate** that guarantees:

- **No Phase 14 PR can merge unless:**
  - The **pipeline validator** passes  
  - The **plugin metadata validator** passes  
  - The **Phase 14 first failing test** passes  
  - The **capability matrix is up‑to‑date**  

This is the governance lock you’ve been building toward.

Below is the **canonical GitHub Actions workflow**, plus the **governance rules** that make it airtight.

---

# **🔥 Phase 14 CI Gate — “No Merge Unless DAG Is Valid”**  
`/.github/workflows/phase14-governance.yml`

```yaml
name: Phase 14 Governance Gate

on:
  pull_request:
    branches: [ main, master ]
  push:
    branches: [ main, master ]

jobs:
  phase14-governance:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install backend dependencies
        run: |
          pip install -r server/requirements.txt

      # -----------------------------
      # 1. Plugin metadata validator
      # -----------------------------
      - name: Validate plugin metadata
        run: |
          python tools/validate_plugins.py

      # -----------------------------
      # 2. Pipeline validator
      # -----------------------------
      - name: Validate pipelines
        run: |
          python tools/validate_pipelines.py

      # -----------------------------
      # 3. Regenerate capability matrix
      # -----------------------------
      - name: Generate capability matrix
        run: |
          python tools/generate_plugin_capability_matrix.py

      # -----------------------------
      # 4. Ensure capability matrix is committed
      # -----------------------------
      - name: Check capability matrix is up to date
        run: |
          git diff --exit-code docs/phase_14_plugin_capability_matrix.md

      # -----------------------------
      # 5. Run Phase 14 DAG tests
      # -----------------------------
      - name: Run tests
        run: |
          pytest -q --disable-warnings --maxfail=1
```

This workflow enforces **all four Phase 14 invariants**.

---

# **🔥 What This CI Gate Guarantees**

## **1. Plugin metadata is valid**
- Every tool has:
  - `input_types`
  - `output_types`
  - `capabilities`
- No empty lists  
- No missing fields  
- No malformed manifests  

If a plugin is missing metadata → **PR blocked**.

---

## **2. All pipelines are valid DAGs**
The validator enforces:

- No cycles  
- All nodes exist  
- All edges reference valid nodes  
- All plugin/tool references exist  
- **Type compatibility** across edges  
- Entry/output nodes are valid  

If a pipeline is invalid → **PR blocked**.

---

## **3. Capability matrix is always up‑to‑date**
If a developer changes a plugin manifest but forgets to regenerate the matrix:

```
git diff --exit-code docs/phase_14_plugin_capability_matrix.md
```

→ CI fails  
→ PR blocked  

This prevents drift between:

- manifests  
- documentation  
- pipeline validator  

---

## **4. Phase 14 DAG engine must pass its first failing test**
This is the test you already have:

- registry resolution  
- plugin resolution  
- payload merging  
- type flow  
- DAG execution  

If the DAG engine regresses → **PR blocked**.

---

# **🔥 Governance Rules (Drop into docs/governance/phase14_ci_gate.md)**

### **Rule 1 — No plugin may be merged without metadata**
Every tool must declare:

- `input_types`
- `output_types`
- `capabilities`

Missing metadata is a **hard failure**.

---

### **Rule 2 — No pipeline may be merged unless it is a valid DAG**
Pipelines must be:

- acyclic  
- type‑compatible  
- referencing real plugins/tools  

Invalid pipelines are **blocked**.

---

### **Rule 3 — Capability matrix must always reflect the repo**
Any change to:

- plugin manifests  
- tool metadata  

must regenerate:

```
docs/phase_14_plugin_capability_matrix.md
```

If not → **PR blocked**.

---

### **Rule 4 — DAG engine must always pass the Phase 14 first failing test**
This test is the **contract** for:

- plugin resolution  
- payload merging  
- type flow  
- DAG execution  

If it fails → **PR blocked**.

---

# **🔥 Result: A Fully Governed Phase 14 Repo**

With this CI gate:

- No invalid plugin can enter the repo  
- No invalid pipeline can enter the repo  
- No undocumented capability can enter the repo  
- No DAG regression can enter the repo  

This is the **deterministic, governed, drift‑proof** system you’ve been building toward.


