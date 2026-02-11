# **PHASE 13 — VideoTracker Multi‑Tool Pipelines (Canonical Architecture Specification)**  
**Status:** Approved for implementation  
**Owner:** Roger  
**Scope:** VideoTracker (UI + Server + Plugin Contract)  
**Purpose:** Enable ordered multi‑tool pipelines for video analysis and streaming.

---

# **1. Purpose**

Phase 13 introduces **multi‑tool pipelines** to VideoTracker.

Instead of running a single tool (e.g., `track_players`), VideoTracker must support **ordered sequences** of tools inside a single plugin:

```
[ detect_players → track_players → annotate_frames ]
```

Each tool consumes the previous tool’s output and produces the next tool’s input.

This applies to:

- Background video processing (REST)
- Live streaming (WebSocket)
- Any future video‑based workflows

This phase **does not** introduce cross‑plugin pipelines.  
All tools in a pipeline must belong to the **same plugin**.

---

# **2. Out‑of‑Scope (Explicitly Forbidden)**

Phase 13 does **not** include:

- Cross‑plugin pipelines  
- Parallel pipelines  
- Conditional branching  
- Tool graphs (DAGs)  
- Tool parameter UIs  
- Tool‑specific UI panels  
- Model selection  
- Timeline scrubbing  
- Video export  
- Heatmaps, analytics, charts  
- Any UI beyond the existing VideoTracker layout  

Any PR containing these must be rejected.

---

# **3. High‑Level Architecture**

VideoTracker now has **three cooperating layers**:

```
UI (VideoTracker)
   ↓
Server (VideoPipelineService)
   ↓
Plugin (ordered tool execution)
```

### 3.1. UI Responsibilities

- Allow user to select **multiple tools** in order.
- Send pipeline definition to server:
  - For background jobs → REST
  - For streaming → WebSocket
- Display final annotated frames.

### 3.2. Server Responsibilities

- Validate pipeline (plugin exists, tools exist, order valid).
- Execute pipeline sequentially.
- Pass output of step N into step N+1.
- Log each step for traceability.

### 3.3. Plugin Responsibilities

- Each tool must accept a **dict payload**.
- Each tool must return a **dict payload**.
- Tools must be pure functions (no global state).

---

# **4. Canonical Data Contracts**

## 4.1. Pipeline Definition (UI → Server)

```json
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players", "annotate_frames"],
  "payload": {
    "video_url": "...",
    "frame_stride": 5
  }
}
```

## 4.2. Tool Contract (Plugin Side)

Each tool must follow:

```python
def tool_name(self, **payload) -> dict:
    ...
```

- Input: dict  
- Output: dict  
- No positional args  
- No return types other than dict  

---

# **5. End‑to‑End Flows**

## 5.1. Background Video Processing (REST)

```
UI → POST /video/pipeline → VideoPipelineService → Plugin tools → UI
```

Steps:

1. User selects plugin + ordered tools.
2. UI sends pipeline request.
3. Server executes tools in order.
4. Final output returned to UI.

## 5.2. Live Streaming (WebSocket)

```
UI → WS frame {plugin_id, tools, image_data} → VisionAnalysisService → VideoPipelineService → Plugin tools → WS response
```

Steps:

1. UI sends each frame with pipeline definition.
2. Server runs pipeline on each frame.
3. Final annotated frame returned.

---

# **6. Server Architecture (Phase 13)**

## 6.1. New Component: `VideoPipelineService`

**File:** `server/app/services/video_pipeline_service.py`

**Responsibility:**  
Execute ordered tool pipelines.

### Core Algorithm

```
result = initial_payload
for each tool in tools:
    result = run_plugin_tool(plugin_id, tool, result)
return result
```

## 6.2. REST Endpoint

**File:** `server/app/routes_video.py`

```
POST /video/pipeline
```

Accepts:

- plugin_id
- tools[]
- payload

Returns:

- final pipeline output

## 6.3. WebSocket Integration

**File:** `server/app/services/vision_analysis.py`

WebSocket frames must include:

```
plugin_id
tools[]
image_data
```

Server must reject frames missing any of these.

---

# **7. UI Architecture (Phase 13)**

## 7.1. VideoTracker UI Changes

- Replace single tool dropdown with **multi‑tool ordered selector**.
- Maintain state:

```
selectedPluginId: string
selectedTools: string[]
```

## 7.2. Background Job Path

UI sends:

```ts
runPipeline(selectedPluginId, selectedTools, payload)
```

## 7.3. Streaming Path

UI sends each frame:

```json
{
  "type": "frame",
  "frame_id": "...",
  "image_data": "...",
  "plugin_id": selectedPluginId,
  "tools": selectedTools
}
```

---

# **8. Logging & Traceability**

Every pipeline step must be logged:

```
Video pipeline step:
  plugin_id=forgesyte-yolo-tracker
  tool_name=track_players
  step=1
```

Every plugin tool execution must be logged:

```
Executing plugin tool:
  plugin_id=ocr
  tool_name=extract_text
  args_keys=['image_data', 'frame_id', '_pipeline_step']
```

This ensures:

- No silent fallbacks  
- No hidden defaults  
- Full traceability  

---

# **9. Validation Rules (Non‑Negotiable)**

- `plugin_id` must exist.
- `tools[]` must be non‑empty.
- All tools must exist in the plugin manifest.
- All tools must belong to the same plugin.
- Server must reject:
  - Missing plugin_id
  - Missing tools[]
  - Empty tools[]
  - Unknown tools
  - Cross‑plugin pipelines

---

# **10. Phase 13 Deliverables**

### Server

- `VideoPipelineService` (new)
- REST endpoint `/video/pipeline`
- WebSocket pipeline execution
- Logging for each pipeline step
- Validation for plugin_id + tools[]

### UI

- Multi‑tool selector
- Pipeline state management
- REST + WebSocket pipeline sending

### Plugins

- Tools must accept/return dict payloads
- Tools must be pure functions

---

# **11. Phase 13 Completion Criteria**

VideoTracker must:

- Run ordered pipelines in background jobs  
- Run ordered pipelines in streaming mode  
- Reject invalid pipelines  
- Log every step  
- Produce deterministic results  

If all of the above are true, Phase 13 is complete.

---

