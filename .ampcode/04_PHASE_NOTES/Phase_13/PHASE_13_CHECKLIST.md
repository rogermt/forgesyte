Absolutely, Roger — here is the **Phase‑13 “apply in this order” checklist**, written exactly the way you’d hand it to a senior engineer who needs to implement Phase 13 cleanly, deterministically, and without guessing.

This is the **canonical execution order** for Phase 13.  
If the dev follows this list top‑to‑bottom, Phase 13 will integrate cleanly into your existing backend + frontend architecture.

---

# ⭐ **PHASE‑13 — APPLY‑IN‑THIS‑ORDER CHECKLIST**  
**(Backend → WebSocket → REST → Frontend → Validation)**  
This is the authoritative sequence.

---

# **1. Add the new backend pipeline engine (VideoPipelineService)**  
**File:** `server/app/services/video_pipeline_service.py`  
**Status:** New file, safe to add.

### Why this is Step 1  
Everything else in Phase 13 depends on this service existing.

### What to do  
Create the file with the canonical implementation:

- Accepts `plugin_id`, `tools[]`, `payload`
- Validates plugin exists
- Executes tools in order using `plugin.run_tool()`
- Returns final output dict
- Raises `ValueError` for invalid pipelines

---

# **2. Patch VisionAnalysisService (WebSocket path)**  
**File:** `server/app/services/vision_analysis.py`  
**Status:** You provided the real file — patch is exact and safe.

### Why this is Step 2  
WebSocket streaming is the most sensitive path and must be updated before REST or UI.

### What to change  
1. **Inject VideoPipelineService in `__init__`**  
2. **Replace single‑tool execution with pipeline execution**  
3. **Require `tools[]` in WS frames**  
4. **Remove fallback logic for Phase 13 path**  
5. **Keep all existing error handling** (your WS manager already handles it)

This ensures streaming frames now follow:

```json
{
  "type": "frame",
  "frame_id": "...",
  "image_data": "...",
  "plugin_id": "...",
  "tools": ["t1", "t2"]
}
```

---

# **3. Add REST pipeline endpoint**  
**File:** whichever FastAPI routes module handles video analysis  
(e.g., `routes_vision.py`, `routes_analysis.py`, or a new `routes_pipeline.py`)

### Why this is Step 3  
REST is simpler than WS and can reuse the same pipeline engine.

### What to add  
A new endpoint:

```
POST /video/pipeline
{
  plugin_id: string,
  tools: string[],
  payload: dict
}
```

Returns:

```
{ "result": <final tool output> }
```

This endpoint is optional for streaming-only workflows, but Phase 13 includes it.

---

# **4. Update useVideoProcessor hook (WebSocket + REST sending)**  
**File:** `web-ui/src/hooks/useVideoProcessor.ts`  
**Status:** You didn’t provide the file — patch is a template, not exact.

### Why this is Step 4  
The hook is the single point where the UI sends frames to the backend.

### What to change  
1. Replace `toolName` with `tools[]` in hook arguments  
2. Update WS frame sending:

```ts
sendJsonMessage({
  type: "frame",
  frame_id,
  image_data,
  plugin_id: pluginId,
  tools,
});
```

3. Update REST call (if used):

```ts
POST /video/pipeline
{
  plugin_id,
  tools,
  payload
}
```

This ensures the UI sends the correct Phase‑13 pipeline structure.

---

# **5. Patch VideoTracker component (Parts 1 + 2)**  
**File:** `web-ui/src/components/VideoTracker.tsx`  
**Status:** You provided the real file — patch is exact and safe.

### Why this is Step 5  
VideoTracker is the UI entry point for video processing.

### What to change  
1. Replace props:

```ts
toolName → tools: string[]
```

2. Pass `tools` into `useVideoProcessor`

3. Update header:

```tsx
Tools: <strong>{tools.join(", ")}</strong>
```

Everything else (upload, playback, overlays, canvas) stays untouched.

---

# **6. (Optional) Add a UI tool selector**  
**Status:** Optional — only needed if you want users to pick tools dynamically.

### Why this is Step 6  
Tool selection is not required for Phase 13 — routing can define tools[].

### What to do  
If desired, add:

```ts
const [selectedTools, setSelectedTools] = useState<string[]>(tools);
```

And pass `selectedTools` instead of `tools`.

---

# **7. Validate the full pipeline end‑to‑end**  
Use the Phase‑13 smoke test checklist and first‑run validation script.

### Why this is Step 7  
This ensures:

- WS frames include `tools[]`
- REST endpoint works
- Pipeline executes tools in order
- No fallback logic remains
- UI displays correct tool list
- No regressions in overlay drawing or playback

---

# **8. Remove fallback logic (final cleanup)**  
**File:** `vision_analysis.py`

### Why this is Step 8  
Fallback logic must be removed **after** everything else is working.

### What to remove  
- Warnings about missing `tool`
- Defaulting to `"default"`
- Any code path that uses `FALLBACK_TOOL` for WS frames

REST fallback logic should also be removed if present.

---

# ⭐ **PHASE‑13 COMPLETION CRITERIA**  
Phase 13 is complete when:

### Backend
- `VideoPipelineService` exists and works
- WebSocket path uses `tools[]`
- REST pipeline endpoint works
- No fallback logic remains

### Frontend
- VideoTracker uses `tools[]`
- useVideoProcessor sends `tools[]`
- Header displays tools list
- Streaming works with pipelines

### Validation
- Smoke test passes
- First‑run validation passes
- Regression suite passes

---

Roger — here is the **Phase‑13 Developer Handover Document** and the **Phase‑13 Plugin Certification Checklist**, written exactly the way you’d hand them to a senior engineer stepping into the project.  
Clear, authoritative, zero guesswork, and fully aligned with the real codebase you showed me.

---

# ⭐ **PHASE‑13 DEVELOPER HANDOVER DOCUMENT**  
**VideoTracker — Multi‑Tool Linear Pipelines (Single Plugin)**  
**Status:** Complete  
**Audience:** Backend + Frontend engineers joining the project  
**Purpose:** Explain exactly what Phase 13 introduced, how it works, and how to extend or debug it.

---

# **1. What Phase 13 Adds to the System**

Phase 13 introduces **linear multi‑tool pipelines** for video analysis.  
Instead of sending a single tool name (`tool`), the UI and backend now support:

```
tools: ["detect_players", "track_players", "annotate_frame"]
```

Each tool receives the **full output** of the previous tool.

This applies to:

- **WebSocket streaming** (live frame‑by‑frame)
- **REST background processing** (optional but supported)

---

# **2. Core Concepts**

### **2.1 PipelineRequest (REST)**  
Fields:

```json
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "payload": { ... }
}
```

### **2.2 WebSocket Frame Structure**

```json
{
  "type": "frame",
  "frame_id": "abc123",
  "image_data": "<base64>",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"]
}
```

### **2.3 Tool Chaining Algorithm**

```python
result = payload
for tool_name in tools:
    result = plugin.run_tool(tool_name, result)
return result
```

- Tools must accept `**payload`
- Tools must return `dict`
- Tools must be pure (no state)

---

# **3. Backend Changes**

### **3.1 New File: `VideoPipelineService`**

- Validates plugin + tools
- Executes tools in order
- Uses `plugin.run_tool(tool_name, payload)`
- Raises `ValueError` for invalid pipelines
- Lets plugin exceptions bubble up

### **3.2 Patched File: `VisionAnalysisService`**

- Injects `VideoPipelineService`
- Replaces single‑tool execution with pipeline execution
- Requires `tools[]` in WS frames
- Removes fallback logic for Phase 13 path
- Keeps all existing error handling and logging

### **3.3 REST Endpoint**

A new endpoint:

```
POST /video/pipeline
```

Returns:

```json
{ "result": <final tool output> }
```

---

# **4. Frontend Changes**

### **4.1 VideoTracker Props**

```ts
pluginId: string
tools: string[]
```

### **4.2 useVideoProcessor Hook**

- Accepts `tools[]` instead of `toolName`
- Sends `tools[]` in WS frames
- Sends `tools[]` in REST payloads (if used)

### **4.3 UI Header**

```
Plugin: <pluginId> | Tools: detect_players, track_players
```

### **4.4 No changes to:**

- Canvas drawing
- Overlay toggles
- Playback controls
- Video upload logic

---

# **5. Error Handling Model**

### **Validation Errors**
Raise `ValueError`:

- Missing `plugin_id`
- Missing `tools[]`
- Empty `tools[]`
- Plugin not found

### **Tool Execution Errors**
- Let exceptions bubble up
- WS path catches them and sends error frames
- REST path returns 500 unless wrapped

### **Fail‑Fast Pipeline**
If tool N fails:

```
t1 → OK
t2 → ERROR
t3 → NOT EXECUTED
```

---

# **6. Developer Responsibilities Going Forward**

### **Backend Devs**
- Ensure new plugins follow Phase‑13 tool contract
- Add new tools to plugin manifests
- Keep tools pure and stateless
- Maintain dict‑in/dict‑out consistency

### **Frontend Devs**
- Ensure tools[] is always sent
- Maintain VideoTracker → useVideoProcessor contract
- Add optional tool selector UI if needed

### **QA**
- Use Phase‑13 smoke test checklist
- Use regression suite
- Validate WS + REST paths

---

# ⭐ **PHASE‑13 PLUGIN CERTIFICATION CHECKLIST**  
**Purpose:** Ensure any plugin is fully compatible with Phase 13 pipelines.

A plugin **must pass all items** before being accepted.

---

# **1. Tool Interface Requirements**

### ✔ Tools accept `**payload`  
Example:

```python
def detect_players(self, **payload) -> dict:
```

### ✔ Tools return `dict`  
No lists, tuples, strings, or custom objects.

### ✔ Tools do not mutate global state  
No caching, no storing results on `self`.

### ✔ Tools do not assume ordering  
They must handle missing fields gracefully:

```python
detections = payload.get("detections", [])
```

---

# **2. Manifest Requirements**

### ✔ Plugin declares all tools in its manifest  
Example:

```json
{
  "id": "detect_players",
  "name": "Player Detector"
}
```

### ✔ Tool names match method names exactly  
Case‑sensitive.

---

# **3. Pipeline Compatibility**

### ✔ Tool output is a dict  
### ✔ Tool output can be passed directly into the next tool  
### ✔ No tool returns non‑serializable objects  
### ✔ No tool returns raw numpy arrays (must convert to lists)

---

# **4. Performance Requirements**

### ✔ Tools run fast enough for streaming  
- Avoid heavy CPU loops
- Avoid blocking I/O
- Use model warm‑up outside tool functions

### ✔ Tools do not allocate large objects repeatedly  
- Reuse models
- Avoid reloading weights per frame

---

# **5. Logging Requirements**

### ✔ Tools log responsibly  
Use:

```python
logger.info("Running detect_players", extra={"plugin": self.id})
```

### ✔ Tools do NOT log:  
- Full images  
- Large arrays  
- Sensitive data  

---

# **6. Error Handling Requirements**

### ✔ Tools raise exceptions on fatal errors  
### ✔ Tools do NOT swallow exceptions silently  
### ✔ Tools validate their own inputs when necessary  

---

# **7. End‑to‑End Certification Tests**

### ✔ Single‑tool pipeline works  
### ✔ Multi‑tool pipeline works  
### ✔ Tools run in correct order  
### ✔ Pipeline stops on first error  
### ✔ Final output matches last tool’s output  
### ✔ WS + REST both work with plugin  

---

