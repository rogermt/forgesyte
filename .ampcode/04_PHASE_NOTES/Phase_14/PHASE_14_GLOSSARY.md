# ⭐ PHASE 14 — GLOSSARY

Technical terminology for Phase 14.

---

## Core Concepts

### Node
A single tool invocation within a pipeline.

**Structure**:
```python
{
    "id": "n1",           # Unique within pipeline
    "plugin_id": "ocr",   # Which plugin
    "tool_id": "detect"   # Which tool in that plugin
}
```

**Example**: "detect_players" node from YOLO plugin

---

### Edge
A connection showing data flow between two nodes.

**Structure**:
```python
{
    "from_node": "n1",
    "to_node": "n2"
}
```

**Semantics**: "Output from n1 flows to input of n2"

---

### Pipeline
A complete workflow describing how tools work together.

**Components**:
- `nodes`: List of tool invocations
- `edges`: List of data connections
- `entry_nodes`: Where execution starts (no predecessors)
- `output_nodes`: What gets returned to user

**Example**: "Player Tracking v1" = YOLO detect → ReID track → Viz render

---

### DAG (Directed Acyclic Graph)
A graph structure with no cycles.

**Why it matters**: 
- Guarantees termination
- Enables topological ordering
- Makes execution deterministic

**Invalid**: A → B → A (contains cycle)  
**Valid**: A → B → C (no cycles)

---

## Execution Concepts

### Entry Node
A node with no predecessors.

**Receives**: Initial user input (image, video frame, etc.)

**Example**: "detect_players" is entry node in player tracking pipeline

---

### Output Node
A node whose result is returned to the user.

**Produces**: Final result data

**Example**: "render_overlay" is output node

**Note**: A node can be both entry and output (single-node pipeline)

---

### Predecessor
A node that executes before another node.

**Example**: In A → B, node A is predecessor of B

---

### Successor
A node that executes after another node.

**Example**: In A → B, node B is successor of A

---

### Topological Sort
Ordering nodes so all predecessors execute before successors.

**Example**:
```
Input DAG:
  n1 → {n2, n3}
  {n2, n3} → n4

Topological order:
  [n1] → [n2, n3] → [n4]
```

**Why it matters**: Determines execution order

---

### Payload
Data flowing through the pipeline.

**Structure**: JSON dict

**Evolution**:
```
Initial payload (from user)
↓
After n1 executes: {**initial, **n1_output}
↓
After n2, n3 execute: {**initial, **n1_output, **n2_output, **n3_output}
↓
Final output: {**merged_all}
```

---

### Payload Merging
Combining outputs from multiple predecessors.

**Example**:
```python
# Two predecessors
payload_from_n2 = {"detections": [...]}
payload_from_n3 = {"heatmap": [...]}

# Merged for successor n4
merged = {**payload_from_n2, **payload_from_n3}
# Result: {"detections": [...], "heatmap": [...]}
```

---

## Type System

### Input Types
What data a tool accepts.

**Example**:
```json
"input_types": ["video_frame", "image_bytes"]
```

**Semantics**: Tool can process video frames OR image bytes

---

### Output Types
What data a tool produces.

**Example**:
```json
"output_types": ["detections", "bounding_boxes"]
```

**Semantics**: Tool produces detections AND bounding boxes

---

### Type Compatibility
Whether output types of one tool match input types of another.

**Rule**:
```
from_node.output_types ∩ to_node.input_types ≠ ∅
```

**Example**:
```
Node A: outputs ["detections"]
Node B: inputs ["detections"]
→ Compatible (intersection = ["detections"])

Node A: outputs ["detections"]
Node B: inputs ["heatmap"]
→ Incompatible (intersection = [])
```

---

### Type Intersection
Common types between two sets.

```python
outputs = ["detections", "confidence"]
inputs = ["detections"]
intersection = ["detections"]  # Not empty ✓
```

---

### Capability
A semantic label for what a tool does.

**Examples**:
```
"player_detection"    # Can detect players
"object_tracking"     # Can track objects
"pose_estimation"     # Can estimate poses
```

**Use**: Finding compatible tools for pipelines

---

## Validation Concepts

### Structural Validation
Checking graph properties.

**Checks**:
- Is it acyclic? (DAG check)
- Do all nodes exist?
- Do all edges reference valid nodes?

---

### Plugin/Tool Validation
Checking tools exist.

**Checks**:
- Does plugin_id exist in registry?
- Does tool_id exist in that plugin?

---

### Type Validation
Checking type compatibility.

**Checks**:
- For each edge, do output/input types overlap?

---

### Entry/Output Validation
Checking entry and output nodes exist.

**Checks**:
- All entry_nodes in nodes list?
- All output_nodes in nodes list?
- Entry nodes have no predecessors?

---

### Reachability Validation
Checking all nodes are reachable.

**Checks**:
- Can we reach every node from entry_nodes?
- If not, what nodes are unreachable?

---

## Registry Concepts

### Pipeline Registry
Server-side store of named pipelines.

**Location**: `server/app/pipelines/`

**Format**: JSON files, one per pipeline

**Access**: Via REST API or Python API

---

### Pipeline ID
Unique identifier for a pipeline.

**Format**: `snake_case_v#`

**Examples**:
- `player_tracking_v1`
- `ball_tracking_v2`
- `pose_estimation_v1`

---

### Pipeline Metadata
Non-execution info about a pipeline.

**Includes**:
- id, name, description
- author, version, tags
- nodes count, edges count

**Use**: Displaying in UI without loading full pipeline

---

### Immutable Registry
Pipelines cannot be modified after registration.

**Rule**: Only create new versions, don't modify existing

**Example**:
```
player_tracking_v1  ← Frozen
player_tracking_v2  ← New version (if changes needed)
```

---

## Logging Concepts

### Node Execution Log
Record of one node running.

**Data**:
```json
{
  "pipeline_id": "player_tracking_v1",
  "node_id": "detect",
  "plugin_id": "forgesyte-yolo-tracker",
  "tool_id": "detect_players",
  "step": 1,
  "status": "success",
  "execution_time_ms": 125.5,
  "timestamp": "2026-02-12T10:30:45Z"
}
```

---

### Pipeline Execution Log
Record of entire pipeline execution.

**Includes**:
- Overall status (success/error)
- Start/end time
- All node logs
- Final output

---

### Audit Trail
Complete history of pipeline executions.

**Use**: Debugging, compliance, performance analysis

---

## Error Concepts

### Validation Error
Error during pipeline validation (before execution).

**Examples**:
- "Graph contains cycle"
- "Unknown plugin: xyz"
- "Type mismatch: detect → heatmap"

**Handling**: Reject pipeline, don't execute

---

### Execution Error
Error during pipeline execution.

**Examples**:
- "Node n1 failed: model not loaded"
- "Node n2 received invalid input"

**Handling**: Log error, return to user, stop execution

---

### Type Error
Validation error about types.

**Example**: "Node n1 outputs [detections], node n2 inputs [heatmap]"

---

## Tool Concepts

### Tool
A single function within a plugin.

**Example**: `forgesyte-yolo-tracker.detect_players`

**Properties**:
- input_types (what it accepts)
- output_types (what it produces)
- capabilities (what it can do)
- handler (function name)

---

### Tool Metadata
Declaration of tool properties.

**Declared in**: Plugin manifest.json

**Example**:
```json
{
  "detect_players": {
    "handler": "detect_players",
    "input_types": ["video_frame"],
    "output_types": ["detections"],
    "capabilities": ["player_detection"]
  }
}
```

---

### Tool Handler
The Python function that executes.

**Example**:
```python
def detect_players(image_bytes, options):
    # Implementation
    return {"detections": [...]}
```

---

## WebSocket Concepts

### Pipeline Frame Message
WebSocket message to run a pipeline.

**Format**:
```json
{
  "type": "frame",
  "pipeline_id": "player_tracking_v1",
  "frame_id": "frame_001",
  "image": "base64_image_data"
}
```

---

### Pipeline Result Message
WebSocket response with results.

**Format**:
```json
{
  "type": "result",
  "frame_id": "frame_001",
  "status": "success",
  "output": {...},
  "execution_time_ms": 425.5
}
```

---

## API Concepts

### REST Pipeline Endpoints
HTTP endpoints for pipelines.

**Examples**:
- `GET /pipelines/list` — List all pipelines
- `GET /pipelines/{id}/info` — Get metadata
- `POST /pipelines/{id}/run` — Execute
- `POST /pipelines/validate` — Validate spec

---

### Pipeline Validation Endpoint
Endpoint to check if pipeline spec is valid.

**Input**: Pipeline JSON

**Output**: Valid (true/false) + errors list

---

## UI Concepts

### Pipeline Selector
UI component for choosing a pipeline.

**Features**:
- Dropdown/select menu
- Shows all available pipelines
- Shows metadata on hover
- Fires callback on selection

---

### Pipeline Preview
UI showing pipeline structure.

**Shows**:
- Nodes (as boxes)
- Edges (as arrows)
- Entry/output nodes (highlighted)

---

## Comparison: Phase 13 vs Phase 14

| Aspect | Phase 13 | Phase 14 |
|--------|----------|----------|
| Execution | Single plugin | Multiple plugins |
| Flow | Linear | Graph (DAG) |
| Configuration | Implicit | Explicit |
| Types | Ignored | Validated |
| Fallback | Yes | No |
| Data flow | Single | Merged |
| Output | One tool | Multiple tools |

---

## Quick Reference

**Key Files**:
- `app/models/pipeline_graph_models.py` — Data structures
- `app/services/pipeline_registry_service.py` — Load/list pipelines
- `app/services/dag_pipeline_service.py` — Validate/execute
- `app/routes/routes_pipelines.py` — REST API
- `app/pipelines/*.json` — Pipeline definitions

**Key Functions**:
- `registry.get(id)` — Load pipeline
- `service.validate(pipeline)` — Check structure
- `await service.execute(pipeline, payload)` — Run

**Key Tests**:
- `tests/pipelines/test_pipeline_models.py`
- `tests/pipelines/test_dag_validation.py`
- `tests/pipelines/test_pipeline_execution.py`
