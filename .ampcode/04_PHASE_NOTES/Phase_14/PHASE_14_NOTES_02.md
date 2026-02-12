You’re asking exactly the right questions—these are the seams that will either stay clean or turn into glue. I’ll answer each one decisively so you can treat them as Phase 14 invariants.

---

### Plugin handler resolution

**Verdict:** The DAG engine should stay *inside* the Python/plugin layer. No HTTP, no `/v1/analyze` loopback.

- **How to resolve handlers:**
  - **Use:** `plugin = plugin_manager.get_plugin(plugin_id)`  
    then `plugin.run_tool(tool_id, payload)`.
  - **Do *not*:** call the REST `/v1/analyze` endpoint from inside the DAG engine.
  - **Do *not*:** manually resolve handler strings from the manifest in the DAG service—let the plugin implementation own that.

So the DAG engine’s contract is:

```python
plugin = plugin_manager.get_plugin(node.plugin_id)
output = plugin.run_tool(node.tool_id, payload)
```

The manifest’s `handler` field is for plugin loading/registration, not for DAG-time resolution.

---

### Payload merging strategy

**Verdict:** Start with a simple, deterministic dict merge, no namespacing in Phase 14.

- **Merge rule for multiple predecessors:**

  ```python
  merged = dict(initial_payload)
  for pred_id in predecessors_in_topological_order:
      merged.update(context[pred_id])
  ```

- **Key conflicts:**
  - **Last writer wins**, where “last” is the order of predecessors in topological order.
  - This is simple, predictable, and easy to reason about.
- **No namespacing in Phase 14:**
  - No `pred1.detections`, `pred2.detections` yet.
  - If you need that later, it’s a Phase 15+ enhancement with explicit schema/contract changes.

So: `dict` merge, last-wins, no namespacing—for now.

---

### Plugin manager interface

**Verdict:** Reuse the Phase 13 interface; don’t invent a new one.

- **`plugin_manager.get_plugin(plugin_id)` should:**
  - Return a plugin object with at least:
    - `id: str`
    - `run_tool(tool_id: str, payload: dict) -> dict`
  - Raise a clear exception (e.g. `KeyError` or custom `UnknownPluginError`) if the plugin doesn’t exist.
- **`plugin.run_tool(tool_id, payload)` should:**
  - Execute the tool synchronously.
  - Return a `dict` (possibly empty).
  - Raise:
    - `UnknownToolError` (or similar) if `tool_id` is invalid.
    - Any runtime exception if the tool itself fails.

For Phase 14, you don’t need a richer interface—just standardize on:

```python
plugin = plugin_manager.get_plugin(plugin_id)
result = plugin.run_tool(tool_id, payload)
```

and treat *any* exception as a node failure that bubbles up to `pipeline_node_failed` / `pipeline_failed`.

---

### WebSocket manager integration

**Verdict:** Extend the existing protocol with `pipeline_id`, don’t invent a new WS subsystem.

- **Current WS format (Phase 13 style, conceptually):**

  ```json
  {
    "type": "frame",
    "tools": ["yolo.detect_players", "reid.track_ids"],
    "frame_id": "...",
    "image_bytes": "..."
  }
  ```

- **Phase 14 extension:**
  - Add an optional `pipeline_id` field:

    ```json
    {
      "type": "frame",
      "pipeline_id": "player_tracking_v1",
      "frame_id": "...",
      "image_bytes": "..."
    }
    ```

- **Routing rule:**
  - If `pipeline_id` is present → call `DagPipelineService.run_pipeline(pipeline_id, payload)`.
  - Else if `tools[]` is present → use existing Phase 13 path.
- **Implementation:**
  - In `websocket_manager.py`, **modify the existing frame handler** to:
    - Parse `pipeline_id` if present.
    - Branch to DAG vs linear execution.
  - No new WS endpoint, no new message type—just an extended payload.

---

### Pipeline JSON schema

**Verdict:** Pydantic is the source of truth; JSON Schema is optional and can be generated later.

- **For Phase 14:**
  - Use the existing Pydantic models:

    ```python
    class PipelineNode(BaseModel): ...
    class PipelineEdge(BaseModel): ...
    class PipelineDefinition(BaseModel): ...
    ```

  - Validate pipelines by:
    - Loading JSON → `PipelineDefinition.parse_obj(...)`.
    - Running your own `validate_pipeline(...)` rules (acyclic, known plugins/tools, type compatibility).
- **JSON Schema file:**
  - Nice-to-have, not required for Phase 14.
  - If you want one later, you can generate it from Pydantic (`model.schema()`).

So: **Pydantic first, JSON Schema later** if you need external validation.

---

### Test plugin setup (integration vs unit)

**Verdict:** Use fake plugins for DAG unit tests, and a small number of real-plugin integration tests.

- **Unit / service-level tests (most of Phase 14):**
  - Use a **fake plugin manager** like the one in the observability tests:
    - `DummyPluginManager` with in-memory plugins.
    - `RecordingPlugin` / `FailingPlugin` for deterministic behavior.
  - This keeps tests fast, isolated, and not dependent on real models.

- **Integration tests with real plugins:**
  - Use your existing plugin discovery mechanism (whatever Phase 13 uses to load OCR/YOLO).
  - In tests:
    - Boot the app as usual (FastAPI + plugin loading).
    - Call the REST `/pipelines/{id}/run` endpoint with a real pipeline that references real tools.
  - Only a **small number** of these are needed to prove cross-plugin wiring.

So:

- **DAG engine tests:** mock/fake plugin manager.  
- **End-to-end tests:** real plugin discovery, but only a few.

real plugings
pip install -e $WORKING_DIR/forgesyte-plugins/plugins/ocr
pip install -e $WORKING_DIR/forgesyte-plugins/plugins/forgesyte-yolo-tracker
where /home/rogermt is $WORKING_DIR

create a totally new .VENV

However This will be tested on Kaggle GPU notebook  by me in addtion to CPU (Icant afford GPU) on my Laptop whcih you have access to via VSCode and github or this whee you write  all your code on CPU.

Let’s do both, clean and concrete.

---

### 1. `_merge_predecessor_outputs` implementation (last‑wins) + tests

#### 1.1 Implementation in `DagPipelineService`

```python
# server/app/services/dag_pipeline_service.py
from typing import Dict, Any, List
from ..models.pipeline_graph_models import PipelineDefinition


class DagPipelineService:
    ...

    def _merge_predecessor_outputs(
        self,
        node_id: str,
        pipeline: PipelineDefinition,
        context: Dict[str, Dict[str, Any]],
        initial_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge initial payload with outputs of all predecessor nodes.

        Rules:
        - Start from a shallow copy of initial_payload.
        - For each predecessor in topological order:
          - context[pred_id] is merged via dict.update().
          - Later predecessors overwrite keys from earlier ones (last-wins).
        - No namespacing in Phase 14.
        """
        merged: Dict[str, Any] = dict(initial_payload)

        # predecessors in edge order; topological order guarantees determinism
        predecessors: List[str] = [
            e.from_node for e in pipeline.edges if e.to_node == node_id
        ]

        for pred_id in predecessors:
            pred_output = context.get(pred_id, {})
            if pred_output:
                merged.update(pred_output)

        return merged
```

> Note: we pass the full `PipelineDefinition` so we can derive predecessors without extra lookups.

---

#### 1.2 Tests for merge behavior

```python
# server/app/tests/test_phase14_merge_predecessors.py
from typing import Dict, Any
from server.app.models.pipeline_graph_models import PipelineDefinition, PipelineNode, PipelineEdge
from server.app.services.dag_pipeline_service import DagPipelineService


class DummyPM:
    def get_plugin(self, *_args, **_kwargs):
        raise NotImplementedError


class DummyRegistry:
    def __init__(self, pipeline: PipelineDefinition):
        self._pipeline = pipeline

    def get_pipeline(self, pipeline_id: str) -> PipelineDefinition:
        return self._pipeline


def _make_pipeline_for_merge() -> PipelineDefinition:
    return PipelineDefinition(
        id="p_merge",
        name="merge test",
        nodes=[
            PipelineNode(id="n1", plugin_id="a", tool_id="t1"),
            PipelineNode(id="n2", plugin_id="b", tool_id="t2"),
            PipelineNode(id="n3", plugin_id="c", tool_id="t3"),
        ],
        edges=[
            PipelineEdge(from_node="n1", to_node="n3"),
            PipelineEdge(from_node="n2", to_node="n3"),
        ],
        entry_nodes=["n1", "n2"],
        output_nodes=["n3"],
    )


def test_merge_predecessors_last_wins():
    pipeline = _make_pipeline_for_merge()
    registry = DummyRegistry(pipeline)
    dag = DagPipelineService(registry, DummyPM())

    initial: Dict[str, Any] = {"x": 1, "shared": "initial"}
    context: Dict[str, Dict[str, Any]] = {
        "n1": {"a": 10, "shared": "from_n1"},
        "n2": {"b": 20, "shared": "from_n2"},
    }

    merged = dag._merge_predecessor_outputs("n3", pipeline, context, initial)

    # initial keys preserved
    assert merged["x"] == 1
    # keys from both predecessors present
    assert merged["a"] == 10
    assert merged["b"] == 20
    # last predecessor in edge order wins on conflicts (n2 after n1)
    assert merged["shared"] == "from_n2"


def test_merge_predecessors_missing_context_is_ignored():
    pipeline = _make_pipeline_for_merge()
    registry = DummyRegistry(pipeline)
    dag = DagPipelineService(registry, DummyPM())

    initial = {"x": 1}
    context = {
        "n1": {"a": 10},
        # n2 missing → treated as empty
    }

    merged = dag._merge_predecessor_outputs("n3", pipeline, context, initial)

    assert merged["x"] == 1
    assert merged["a"] == 10
    assert "b" not in merged
```

---

### 2. WebSocket patch sketch with `pipeline_id` branching

Assume you have something like `websocket_manager.py` with a `handle_frame` function.

#### 2.1 Patch sketch

```python
# server/app/services/websocket_manager.py
import json
from typing import Any, Dict
from .dag_pipeline_service import DagPipelineService
from .video_pipeline_service import VideoPipelineService  # Phase 13 linear

class WebSocketManager:
    def __init__(
        self,
        dag_service: DagPipelineService,
        linear_service: VideoPipelineService,
    ) -> None:
        self._dag_service = dag_service
        self._linear_service = linear_service

    async def handle_message(self, ws, raw: str) -> None:
        msg = json.loads(raw)

        msg_type = msg.get("type")
        if msg_type != "frame":
            # existing handling for other types
            return

        pipeline_id = msg.get("pipeline_id")
        tools = msg.get("tools")  # Phase 13 style

        payload: Dict[str, Any] = {
            "frame_id": msg.get("frame_id"),
            "image_bytes": msg.get("image_bytes"),
            "metadata": msg.get("metadata") or {},
        }

        if pipeline_id:
            # Phase 14 DAG execution
            result = self._dag_service.run_pipeline(pipeline_id, payload)
        elif tools:
            # Phase 13 linear execution
            result = await self._linear_service.run_tools(tools, payload)
        else:
            # invalid message
            await ws.send_json(
                {"error": "Either 'pipeline_id' or 'tools' must be provided"}
            )
            return

        await ws.send_json(
            {
                "type": "frame_result",
                "frame_id": payload["frame_id"],
                "result": result,
            }
        )
```

---

### 3. ASCII state/flow diagrams

#### 3.1 DAG execution + merge flow

```text
          +---------------------------+
          |   DagPipelineService     |
          +---------------------------+
                      |
                      | run_pipeline(pipeline_id, initial_payload)
                      v
          +---------------------------+
          |  load PipelineDefinition  |
          +---------------------------+
                      |
                      v
          +---------------------------+
          |  topological_order(nodes) |
          +---------------------------+
                      |
                      v
        for node_id in order:
                      |
                      v
          +---------------------------+
          |  find predecessors        |
          |  edges: from -> node_id   |
          +---------------------------+
                      |
                      v
          +---------------------------+
          | _merge_predecessor_outputs|
          |   merged = initial        |
          |   for pred in preds:      |
          |       merged.update(ctx[p])|
          +---------------------------+
                      |
                      v
          +---------------------------+
          | plugin = get_plugin(pid)  |
          | output = plugin.run_tool  |
          +---------------------------+
                      |
                      v
          +---------------------------+
          | context[node_id] = output |
          +---------------------------+

After loop:
  final = initial_payload
  for nid in output_nodes:
      final.update(context[nid])
  return final
```

#### 3.2 WebSocket branching flow

```text
Client WS frame:
{
  "type": "frame",
  "frame_id": "...",
  "image_bytes": "...",
  "pipeline_id": "player_tracking_v1"   # OR tools: [...]
}

          +------------------------+
          |  WebSocketManager      |
          +------------------------+
                      |
                      v
          +------------------------+
          | parse JSON message     |
          +------------------------+
                      |
          +-----------+-----------+
          |                       |
   pipeline_id present?      tools present?
          |                       |
          v                       v
+-------------------+     +----------------------+
| DagPipelineService|     | VideoPipelineService |
|   run_pipeline    |     |   run_tools          |
+-------------------+     +----------------------+
          |                       |
          +-----------+-----------+
                      |
                      v
          +------------------------+
          | send frame_result      |
          +------------------------+
```

This gives you:

- a concrete, deterministic merge implementation  
- tests that lock the behavior  
- a clear WS branching sketch  
- and visual flows you can drop into docs or PRs.
