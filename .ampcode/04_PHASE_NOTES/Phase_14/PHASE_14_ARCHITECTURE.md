# ⭐ PHASE 14 — ARCHITECTURE DOCUMENT

## 1. Purpose

Phase 14 introduces:

- **Cross‑plugin pipelines** — Tools from different plugins work together
- **DAG execution** — Graph‑based workflow engine
- **Tool capability metadata** — Each tool declares its contract
- **Pipeline registry** — Named pipelines stored server‑side
- **Typed edges** — Data flow validation
- **Deterministic topological execution** — Guaranteed order

This enables workflows like:

```
YOLO.detect_players → ReID.track_ids → Viz.render_overlay
```

And branching DAGs like:

```
detect → { track, heatmap } → merge → render
```

---

## 2. Core Concepts

### 2.1 Pipeline Node

A node represents a single tool invocation:

```python
class PipelineNode:
    id: str              # "n1", "n2", etc.
    plugin_id: str       # "forgesyte-yolo-tracker"
    tool_id: str         # "detect_players"
```

### 2.2 Pipeline Edge

Edges define data flow between nodes:

```python
class PipelineEdge:
    from_node: str       # "n1"
    to_node: str         # "n2"
```

### 2.3 DAG (Directed Acyclic Graph)

Pipelines **must be acyclic**:
- No cycles allowed
- Validated before execution
- Guarantees deterministic order

### 2.4 Tool Capabilities

Each tool declares its contract:

```python
class ToolMetadata:
    input_types: List[str]      # ["video_frame"]
    output_types: List[str]     # ["detections"]
    capabilities: List[str]     # ["player_detection"]
```

### 2.5 Pipeline Registry

Named pipelines stored server‑side:

```
pipelines/
  player_tracking_v1.json
  ball_tracking_v2.json
  action_recognition_v1.json
```

### 2.6 Entry and Output Nodes

```python
class Pipeline:
    entry_nodes: List[str]    # ["n1"]      — no predecessors
    output_nodes: List[str]   # ["n3"]      — returned to user
```

---

## 3. Execution Model

### 3.1 Validation Phase

Before execution:

1. **Structural validation**: Graph is acyclic
2. **Node validation**: All nodes exist
3. **Plugin/tool validation**: plugin_id and tool_id exist
4. **Type validation**: For each edge, input/output types match
5. **Entry/output validation**: Entry and output nodes exist

If any validation fails → raise error, don't execute.

### 3.2 Topological Sort

Nodes are sorted into dependency order:

```
n1 (no deps) → [n2, n3] (depend on n1) → n4 (depends on n2, n3)
```

### 3.3 Payload Merging

When a node has multiple predecessors:

```python
merged_payload = {
    **initial_payload,      # User input
    **predecessor1_output,  # From n1
    **predecessor2_output   # From n2
}
```

### 3.4 Node Execution

Each node executes in order:

```python
result = plugin_manager.run_tool(
    plugin_id=node.plugin_id,
    tool_id=node.tool_id,
    payload=merged_payload
)
```

### 3.5 Output Collection

Final output is the **merged outputs of all output_nodes**:

```python
final_output = {
    **output_node1_result,
    **output_node2_result
}
```

---

## 4. Type Compatibility Validation

For each edge `from_node → to_node`:

```python
if not (from_node.output_types & to_node.input_types):
    raise ValueError(f"Type mismatch: {from_node} → {to_node}")
```

The intersection must be **non-empty**.

**Example**:
```
detect_players:
  outputs: ["detections"]
track_ids:
  inputs: ["detections"]
→ Valid (intersection = ["detections"])

detect_players:
  outputs: ["detections"]
heatmap:
  inputs: ["heatmap"]
→ Invalid (intersection = [])
```

---

## 5. Logging & Observability

Each node execution logs:

```python
{
    "pipeline_id": "player_tracking_v2",
    "node_id": "n1",
    "plugin_id": "forgesyte-yolo-tracker",
    "tool_id": "detect_players",
    "step_index": 0,
    "input_types": ["video_frame"],
    "output_types": ["detections"],
    "execution_time_ms": 125.5,
    "status": "success"
}
```

---

## 6. Error Handling

### 6.1 Validation Errors
```python
raise PipelineValidationError("Graph contains cycle")
raise PipelineValidationError("Unknown plugin: xyz")
raise PipelineValidationError("Type mismatch: n1 → n2")
```

### 6.2 Execution Errors
```python
raise PipelineExecutionError("Node n1 failed: {reason}")
```

Both logged and returned to user.

---

## 7. Module Structure

```
app/
  models/
    pipeline_graph_models.py      # PipelineNode, PipelineEdge, Pipeline
  services/
    pipeline_registry_service.py  # Load/list/get pipelines
    dag_pipeline_service.py       # Validate, execute
  routes/
    routes_pipelines.py           # REST endpoints
  pipelines/
    *.json                        # Pipeline definitions
```

---

## 8. Data Models

### PipelineNode
```python
class PipelineNode:
    id: str
    plugin_id: str
    tool_id: str
```

### PipelineEdge
```python
class PipelineEdge:
    from_node: str
    to_node: str
```

### Pipeline
```python
class Pipeline:
    id: str
    name: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    entry_nodes: List[str]
    output_nodes: List[str]
```

### ToolMetadata
```python
class ToolMetadata:
    plugin_id: str
    tool_id: str
    input_types: List[str]
    output_types: List[str]
    capabilities: List[str]
```

---

## 9. Backward Compatibility

Phase 14 does **not** remove Phase 13 functionality.

- Single-tool runs still work (Phase 13)
- Pipelines are new (Phase 14)
- Both coexist

---

## 10. Security Considerations

### 10.1 Pipeline Validation
- Always validate before execution
- No unsigned pipelines
- Registry is immutable

### 10.2 Type Safety
- Prevent injection via type validation
- Nodes can only receive expected types

### 10.3 Logging
- All pipeline executions logged
- Full audit trail
