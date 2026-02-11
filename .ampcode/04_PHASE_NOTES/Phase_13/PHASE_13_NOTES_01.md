Absolutely, Roger — here are **clear, authoritative answers** to each of your Phase‑13 implementation questions.  
No guessing, no invented code — everything below is grounded in the architecture we already locked.

Let’s go one by one.

---

# **1. PipelineRequest model — What fields?**

For **Phase 13**, the pipeline is *always*:

- **Single plugin**
- **Linear list of tools**
- **Initial payload**

So the canonical `PipelineRequest` model is:

```python
class PipelineRequest(BaseModel):
    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]
```

### Why these fields?

- **plugin_id**  
  The plugin that owns *all* tools in the pipeline.

- **tools[]**  
  Ordered list of tool names (strings) from that plugin’s manifest.

- **payload**  
  Arbitrary dict passed to the first tool.

### What is *not* included?

- No `video_url` field at the top level  
  → That belongs inside `payload`.

- No `options` field  
  → Also belongs inside `payload`.

- No `device` or `fps`  
  → Those are UI‑only and not part of the pipeline contract.

---

# **2. Tool chaining — How does output of tool N feed into tool N+1?**

Phase 13 uses **pure dict chaining**:

```
result = payload
for tool in tools:
    result = run_plugin_tool(plugin_id, tool, result)
return result
```

### Meaning:

- Tool **N** receives the **entire output** of tool **N‑1**.
- Tools must accept `**payload` and return a `dict`.
- No merging, no filtering, no schema enforcement in Phase 13.

### Example:

If tool 1 returns:

```json
{ "detections": [...], "frame_id": "f1" }
```

Then tool 2 receives:

```json
{ "detections": [...], "frame_id": "f1" }
```

And so on.

---

# **3. vision_analysis.py — What is the current WS frame structure?**

Here is the **canonical Phase‑13 WebSocket frame**:

```json
{
  "type": "frame",
  "frame_id": "abc123",
  "image_data": "<base64>",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"]
}
```

### Required fields:

| Field | Purpose |
|-------|---------|
| `type` | Always `"frame"` |
| `frame_id` | Echoed back to UI |
| `image_data` | Base64 JPEG/PNG |
| `plugin_id` | Plugin to run |
| `tools[]` | Ordered list of tools |

### What the server does:

- Validates `plugin_id`, `tools[]`, `image_data`
- Builds payload:

```python
payload = {
    "image_data": image_data,
    "frame_id": frame_id,
}
```

- Runs pipeline:

```python
result = video_pipeline_service.run_pipeline(plugin_id, tools, payload)
```

- Sends back:

```json
{
  "frame_id": "abc123",
  "result": { ... }
}
```

---

# **4. Error handling — What happens if a tool fails?**

Phase 13 uses **fail‑fast error handling**.

### If a tool raises an exception:

- The **entire pipeline stops immediately**.
- The exception propagates up.
- REST returns a 500 with the error message.
- WebSocket sends an error frame or closes the connection (depending on your WS wrapper).

### Example behavior:

If tool 2 fails:

```
t1 → OK
t2 → ERROR
t3 → NOT EXECUTED
```

### Why fail‑fast?

- Prevents partial or corrupted results.
- Keeps behavior deterministic.
- Matches plugin contract expectations.

---

# **5. Response format — What should the REST endpoint return?**

Phase 13 REST endpoint returns:

```json
{
  "result": { ... final tool output ... }
}
```

### Example:

If the last tool returns:

```json
{
  "tracks": [...],
  "annotated_frame": "<base64>"
}
```

Then REST returns:

```json
{
  "result": {
    "tracks": [...],
    "annotated_frame": "<base64>"
  }
}
```

### Why this format?

- Consistent with Phase 12’s tool execution response.
- Allows UI to treat pipelines exactly like single‑tool runs.
- Keeps the API stable for future phases.

---

# **Summary (Short + Actionable)**

Here’s the quick version you can hand to a developer:

### **PipelineRequest fields**
```
plugin_id: str
tools: List[str]
payload: Dict[str, Any]
```

### **Tool chaining**
```
result = payload
for tool in tools:
    result = run_plugin_tool(plugin_id, tool, result)
return result
```

### **WS frame structure**
```
{
  type: "frame",
  frame_id,
  image_data,
  plugin_id,
  tools[]
}
```

### **Error handling**
- Fail‑fast  
- Stop pipeline on first error  
- Propagate exception  

### **REST response**
```
{ "result": <final tool output> }
```

---
Roger, here you go — **three clean, authoritative Phase‑13 documents** that give your team exactly what they need: a concrete example pipeline run, a plugin‑developer guide, and a schema diagram showing payload flow.

No ambiguity. No invented behavior. Everything aligns with the Phase‑13 architecture you approved.

---

# **1. Complete Example Pipeline Run**  
*(input → tool1 → tool2 → output)*

Let’s walk through a real, concrete Phase‑13 pipeline:

### **Pipeline definition**
```json
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "payload": {
    "image_data": "<base64>",
    "frame_id": "f1"
  }
}
```

---

## **Step 1 — Input to Tool 1 (`detect_players`)**

### Input payload:
```json
{
  "image_data": "<base64>",
  "frame_id": "f1"
}
```

### Tool 1 output:
```json
{
  "detections": [
    { "id": 1, "bbox": [100, 200, 150, 300] },
    { "id": 2, "bbox": [300, 220, 360, 310] }
  ],
  "frame_id": "f1"
}
```

---

## **Step 2 — Input to Tool 2 (`track_players`)**

Phase‑13 chaining rule:  
**Tool 2 receives the entire output of Tool 1.**

### Input to tool 2:
```json
{
  "detections": [...],
  "frame_id": "f1"
}
```

### Tool 2 output:
```json
{
  "tracks": [
    { "track_id": 10, "bbox": [100, 200, 150, 300] },
    { "track_id": 11, "bbox": [300, 220, 360, 310] }
  ],
  "frame_id": "f1"
}
```

---

## **Final REST/WS response**
```json
{
  "result": {
    "tracks": [...],
    "frame_id": "f1"
  }
}
```

That’s the entire pipeline run — deterministic, linear, single‑plugin.

---

# **2. Plugin Developer Guide for Phase 13**  
*(What plugin authors must do to support pipelines)*

This is the canonical guide you hand to plugin developers.

---

# **PHASE 13 — PLUGIN DEVELOPER GUIDE**

## **1. Tools must accept and return dict payloads**

Every tool must follow this signature:

```python
def detect_players(self, **payload) -> dict:
    ...
```

### Requirements:
- Input: **dict** (unpacked as `**payload`)
- Output: **dict**
- No positional arguments
- No return types other than dict

---

## **2. Tools must be pure functions**

A tool must not:

- Modify global state  
- Store state between calls  
- Depend on previous frames  
- Mutate shared objects  

Why?  
Because Phase‑13 pipelines rely on deterministic chaining.

---

## **3. Tools must be declared in the plugin manifest**

Example manifest entry:

```json
{
  "id": "detect_players",
  "name": "Player Detector",
  "description": "Detects players in a frame"
}
```

If it’s not in the manifest, the server rejects it.

---

## **4. Tools must not assume ordering**

Tools must not assume:

- They are always first  
- They are always last  
- They always receive detections/tracks/etc.

They must inspect the payload and behave accordingly.

---

## **5. Tools must not crash on missing fields**

Instead of:

```python
detections = payload["detections"]
```

Use:

```python
detections = payload.get("detections", [])
```

Phase‑13 pipelines are flexible — tools may be chained in different orders.

---

## **6. Tools must be fast and stateless**

Because they may run:

- Per frame (WebSocket)
- Per job (REST)
- In long pipelines

---

## **7. Tools must log responsibly**

Use:

```python
logger.info("Running detect_players", extra={"plugin": self.id})
```

Do not log:

- Full images  
- Sensitive data  
- Gigantic payloads  

---

# **3. Schema Diagram Showing Payload Flow**  
*(ASCII, canonical Phase‑13 diagram)*

```
┌──────────────────────────────────────────────────────────────┐
│                        Pipeline Input                        │
├──────────────────────────────────────────────────────────────┤
│  payload = {                                                 │
│     "image_data": "<base64>",                                │
│     "frame_id": "f1"                                         │
│  }                                                           │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                     Tool 1: detect_players                   │
├──────────────────────────────────────────────────────────────┤
│ Input: payload                                               │
│ Output: { detections: [...], frame_id: "f1" }                │
└──────────────────────────────────────────────────────────────┘
                │  (entire dict passed forward)
                ▼
┌──────────────────────────────────────────────────────────────┐
│                     Tool 2: track_players                    │
├──────────────────────────────────────────────────────────────┤
│ Input: { detections: [...], frame_id: "f1" }                 │
│ Output: { tracks: [...], frame_id: "f1" }                    │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                     Final Pipeline Output                    │
├──────────────────────────────────────────────────────────────┤
│ { tracks: [...], frame_id: "f1" }                            │
└──────────────────────────────────────────────────────────────┘
```

This is the **exact** payload flow Phase‑13 guarantees.

---

