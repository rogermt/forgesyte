# ⭐ PHASE 14 — DEVELOPER GUIDE

## 1. Adding Tool Capability Metadata

Plugin authors must declare what their tools accept and produce.

### Step 1: Define Tool Capabilities

In your plugin's tool definition, add:

```python
class MyTool:
    """My amazing tool."""
    
    # What data does this tool accept?
    input_types = ["video_frame", "image_bytes"]
    
    # What data does this tool produce?
    output_types = ["detections", "bounding_boxes"]
    
    # What capabilities does it have?
    capabilities = ["object_detection", "player_detection"]
```

### Step 2: Update Plugin Manifest

In your `manifest.json`:

```json
{
  "tools": {
    "detect_players": {
      "handler": "detect_players",
      "description": "Detect players in video frames",
      "input_types": ["video_frame"],
      "output_types": ["detections"],
      "capabilities": ["player_detection"],
      "input_schema": {...},
      "output_schema": {...}
    }
  }
}
```

---

## 2. Creating a Pipeline

Pipelines are JSON files describing how tools work together.

### Step 1: Define Nodes

Each node is a tool invocation:

```json
{
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
    }
  ]
}
```

### Step 2: Define Edges

Edges show how data flows:

```json
{
  "edges": [
    {
      "from_node": "detect",
      "to_node": "track"
    }
  ]
}
```

### Step 3: Define Entry and Output Nodes

Entry nodes have no predecessors (they receive initial input):

```json
{
  "entry_nodes": ["detect"]
}
```

Output nodes are returned to the user:

```json
{
  "output_nodes": ["track"]
}
```

### Step 4: Full Pipeline Example

```json
{
  "id": "player_tracking_v2",
  "name": "Player Tracking v2",
  "description": "Detect and track players in video",
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
      "plugin_id": "viz-plugin",
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

## 3. Registering a Pipeline

### Step 1: Place JSON File

Put your pipeline JSON in:

```
server/app/pipelines/player_tracking_v2.json
```

### Step 2: Registry Auto-Load

The `PipelineRegistry` loads all `*.json` files from `server/app/pipelines/` on startup.

```python
registry = PipelineRegistry("server/app/pipelines")
pipeline = registry.get("player_tracking_v2")
```

### Step 3: Validation on Load

Pipeline is validated when loaded:
- Graph structure (acyclic)
- Node existence
- Type compatibility
- Entry/output nodes exist

If invalid → error logged, pipeline skipped.

---

## 4. Running a Pipeline

### Via REST

```bash
POST /pipelines/player_tracking_v2/run
Content-Type: application/json

{
  "image": "base64_encoded_image_or_url"
}
```

Response:

```json
{
  "status": "success",
  "output": {
    "detections": [...],
    "tracks": [...],
    "visualization": "base64_frame"
  },
  "execution_time_ms": 425.5
}
```

### Via WebSocket

```javascript
ws.send(JSON.stringify({
  type: "frame",
  pipeline_id: "player_tracking_v2",
  frame_id: "frame_001",
  image: "base64_image_data"
}));

// Response on same WebSocket
{
  "type": "result",
  "frame_id": "frame_001",
  "output": {...}
}
```

---

## 5. Validating Your Pipeline

### Manual Validation

Use the validation endpoint:

```bash
POST /pipelines/validate
Content-Type: application/json

{
  "nodes": [...],
  "edges": [...],
  "entry_nodes": [...],
  "output_nodes": [...]
}
```

Response:

```json
{
  "valid": false,
  "errors": [
    "Graph contains cycle: detect → track → detect",
    "Unknown plugin: nonexistent-plugin",
    "Type mismatch: detect (outputs detections) → heatmap (inputs heatmap)"
  ]
}
```

### Common Errors

**Cycle**:
```
detect → track → detect
```
❌ Not allowed. DAGs must be acyclic.

**Unknown Plugin**:
```
"plugin_id": "nonexistent-plugin"
```
❌ Plugin must exist in registry.

**Type Mismatch**:
```
detect outputs: ["detections"]
heatmap inputs: ["heatmap"]
```
❌ No type overlap. Cannot connect.

**Missing Entry Node**:
```
"entry_nodes": ["nonexistent"]
```
❌ Entry node must exist in nodes list.

---

## 6. Debugging a Pipeline

### Enable Verbose Logging

Set environment variable:

```bash
PIPELINE_DEBUG=1 python -m uvicorn app.main:app
```

Output includes:
- Validation steps
- Topological sort result
- Node execution order
- Payload merging details
- Execution times per node

### Check Pipeline Registry

```bash
curl http://localhost:8000/pipelines/list
```

Returns all registered pipelines with metadata.

### Inspect a Pipeline

```bash
curl http://localhost:8000/pipelines/player_tracking_v2/info
```

Returns:
- Nodes
- Edges
- Entry/output nodes
- Expected input schema
- Expected output schema

---

## 7. Best Practices

### 7.1 Naming Conventions

- Pipeline IDs: `snake_case_v#` (e.g., `player_tracking_v2`)
- Node IDs: Short descriptive (e.g., `detect`, `track`, `render`)
- Plugin IDs: Match plugin directory (e.g., `forgesyte-yolo-tracker`)
- Tool IDs: Match tool handler (e.g., `detect_players`)

### 7.2 Pipeline Design

- Keep pipelines focused (one concern per pipeline)
- Use version numbers for breaking changes
- Document expected input/output in description
- Test extensively before registering

### 7.3 Type Contracts

- Always declare input_types and output_types
- Keep types consistent across similar tools
- Use semantic names (not generic "data")
- Document why types matter

### 7.4 Documentation

Include in pipeline JSON:

```json
{
  "description": "Detect and track players in video frames",
  "tags": ["sports", "tracking", "yolo"],
  "author": "vision-team",
  "version": "2.0.0",
  "changelog": "Added ReID for better tracking"
}
```

---

## 8. Example: Custom Pipeline

Let's build a **ball tracking pipeline**.

### Step 1: Check Available Tools

```bash
curl http://localhost:8000/tools/list | jq '.[] | select(.capabilities | contains(["ball"])'
```

Output:
```json
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tool_id": "detect_ball",
  "output_types": ["detections"]
}
```

### Step 2: Create Pipeline JSON

```json
{
  "id": "ball_tracking_v1",
  "name": "Ball Tracking",
  "description": "Track ball movement across frames",
  "nodes": [
    {
      "id": "detect_ball",
      "plugin_id": "forgesyte-yolo-tracker",
      "tool_id": "detect_ball"
    },
    {
      "id": "track_ball",
      "plugin_id": "forgesyte-yolo-tracker",
      "tool_id": "track_ball"
    }
  ],
  "edges": [
    { "from_node": "detect_ball", "to_node": "track_ball" }
  ],
  "entry_nodes": ["detect_ball"],
  "output_nodes": ["track_ball"]
}
```

### Step 3: Save and Register

```bash
cp ball_tracking_v1.json server/app/pipelines/
```

### Step 4: Restart Server

The pipeline is auto-loaded.

### Step 5: Test It

```bash
POST /pipelines/ball_tracking_v1/run
{
  "image": "base64_video_frame"
}
```

---

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| Pipeline not found | Check spelling, ensure JSON is in `server/app/pipelines/` |
| Type mismatch error | Check input_types/output_types match between consecutive nodes |
| Cycle detection error | Redraw your graph on paper, ensure no circular dependencies |
| Node not found | Verify plugin_id and tool_id exist |
| Execution failed | Check logs with `PIPELINE_DEBUG=1`, verify tool input schema |

---

## 10. Testing Your Pipeline

Write a test:

```python
async def test_ball_tracking_pipeline():
    registry = PipelineRegistry("server/app/pipelines")
    pipeline = registry.get("ball_tracking_v1")
    
    # Validate
    assert pipeline.validate()
    
    # Execute
    result = await pipeline.execute(
        image_bytes=test_frame,
        plugin_manager=mock_plugin_manager
    )
    
    # Verify output
    assert "detections" in result
    assert "tracks" in result
```
