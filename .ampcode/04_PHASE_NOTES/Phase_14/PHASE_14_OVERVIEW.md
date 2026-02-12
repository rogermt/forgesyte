# ⭐ PHASE 14 — OVERVIEW  
**Cross‑Plugin DAG Pipelines with Typed Edges**

## Vision

Phase 14 transforms the system from:

- **Phase 13**: *linear pipelines inside a single plugin*  

into  

- **Phase 14**: *graph‑based, cross‑plugin workflows with explicit type contracts*

This is the moment the system becomes a **workflow engine**, not just a plugin runner.

---

## What Changes in Phase 14

### From Single-Plugin to Cross-Plugin

**Before (Phase 13)**:
```
User Input → OCR Plugin (detect_text) → Result
User Input → YOLO Plugin (detect_players) → Result
```

Each plugin runs independently. No composition.

**After (Phase 14)**:
```
Video Frame
    ↓
YOLO.detect_players
    ↓
ReID.track_ids
    ↓
Viz.render_overlay
    ↓
Output Frame
```

Plugins work **together** in a graph.

---

## Key Capabilities

### 1. DAG Pipelines
- Workflows are **directed acyclic graphs**
- Nodes = tools
- Edges = data flow
- No cycles allowed

### 2. Tool Metadata
Each tool declares:
- `inputs: ["video_frame"]`
- `outputs: ["detections"]`
- `capabilities: ["player_detection"]`

### 3. Pipeline Registry
Named pipelines stored server-side:
```
player_tracking_v1
ball_tracking_v2
action_recognition_v1
```

### 4. Type Validation
Before execution:
- Validate graph structure (acyclic)
- Validate nodes exist
- Validate tool compatibility
- Validate type contracts on edges

### 5. Execution Engine
Topological sort → Execute in order → Merge outputs → Return result

---

## Use Cases

### Simple Linear Pipeline
```
detect_players → track_ids → render
```

### Branching Pipeline
```
detect → { track, heatmap } → merge → render
```

### Multi-Source Pipeline
```
{ video_stream_a, video_stream_b } → fusion → detect → output
```

---

## Example: Player Tracking Pipeline

```json
{
  "id": "player_tracking_v2",
  "name": "Player Tracking v2",
  "nodes": [
    {
      "id": "detect",
      "plugin_id": "forgesyte-yolo-tracker",
      "tool_id": "detect_players"
    },
    {
      "id": "track",
      "plugin_id": "forgesyte-yolo-tracker",
      "tool_id": "track_players"
    },
    {
      "id": "render",
      "plugin_id": "viz",
      "tool_id": "render_overlay"
    }
  ],
  "edges": [
    { "from_node": "detect", "to_node": "track" },
    { "from_node": "track", "to_node": "render" }
  ],
  "entry_nodes": ["detect"],
  "output_nodes": ["render"]
}
```

---

## Governance Principle

**Everything explicit, nothing implicit.**

- No default plugins
- No default tools
- No auto-wiring
- No guessing types
- Pipelines are code (JSON)
- Validation before execution

---

## Timeline

- **Commit 1-7**: Core infrastructure
- **Commit 8-9**: UI integration
- **Commit 10**: Full migration from Phase 13

---

## Success Criteria

✅ Can create cross-plugin pipelines  
✅ Can validate DAG structure  
✅ Can validate type contracts  
✅ Can execute pipelines in order  
✅ Can register and list pipelines  
✅ Can run from UI  
✅ All tests pass  

---

## Next Phase (Phase 15)

Once Phase 14 is locked:
- Job queuing for pipelines
- Pipeline history
- Pipeline performance metrics
- Pipeline versioning
