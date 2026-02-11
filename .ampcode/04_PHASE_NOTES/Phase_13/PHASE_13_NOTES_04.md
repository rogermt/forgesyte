Roger — perfect. These five questions are exactly the ones a senior dev *must* get right before touching Phase 13.  
Here are the **canonical, final, unambiguous answers** — the ones you can hand directly to engineering and say: *“Do this. No guessing.”*

---

# ⭐ **Q1: WS Frame Structure**  
**Should the WS frame use `tools` (array) instead of `tool` (string)?**

### ✅ **YES — Phase 13 requires `tools[]`**  
The WebSocket frame **must** be:

```json
{
  "type": "frame",
  "frame_id": "abc123",
  "image_data": "<base64>",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"]
}
```

### ❌ NOT allowed anymore:
```json
"tool": "detect_players"
```

### Why?
- Phase 13 introduces **linear multi‑tool pipelines**
- WS and REST must use the **same contract**
- Fallback logic is removed

This is **mandatory**.

---

# ⭐ **Q2: VisionAnalysisService Injection**  
**Should I inject `VideoPipelineService` into `VisionAnalysisService.__init__()`?**

### ✅ **YES — inject it in `__init__`**  
This is the correct, canonical architecture:

```python
self.pipeline_service = VideoPipelineService(plugins)
```

### Why?
- Keeps `handle_frame()` clean  
- Matches your existing dependency‑injection pattern  
- Makes the service testable  
- Avoids re‑instantiating the pipeline engine per frame  

### ❌ Do NOT instantiate inside `handle_frame()`  
That would be wasteful and break your architecture.

---

# ⭐ **Q3: App.tsx Changes**  
**Should I change `selectedTool` (string) to `selectedTools[]` (array)?  
Or keep single tool selector and hardcode pipeline in VideoTracker?**

### ✅ **BEST PRACTICE: Change to `selectedTools[]`**  
This is the correct long‑term architecture:

```ts
const [selectedTools, setSelectedTools] = useState<string[]>([]);
```

### Why?
- Phase 13 is explicitly multi‑tool  
- Future phases (14+) introduce DAG pipelines  
- Hardcoding pipelines in VideoTracker is brittle  
- UI should reflect the real pipeline contract  

### Acceptable temporary shortcut  
If you want to ship quickly:

```ts
tools = ["detect_players", "track_players"];
```

But this is **not** the final architecture.

---

# ⭐ **Q4: Fallback Removal**  
**Should I remove `FALLBACK_TOOL = "default"` entirely?  
Or keep it for backward compatibility?**

### ✅ **REMOVE fallback logic for Phase 13 paths**  
Inside `VisionAnalysisService.handle_frame()`:

- Remove fallback to `"default"`
- Require `tools[]`
- Raise `ValueError` if missing

### ❗ Keep the constant ONLY if older clients still use `tool`  
But Phase 13 code paths must **not** use fallback.

### Final rule:
- **Phase 13 WS path → no fallback**  
- **Legacy Phase 12 REST path → fallback allowed (optional)**  

---

# ⭐ **Q5: REST Endpoint Location**  
**Where should `POST /video/pipeline` go?**

### ✅ **Create a new route file OR add to the existing video routes module**  
Your repo uses multiple route modules:

```
routes_analysis.py
routes_vision.py
routes_tasks.py
```

### Best practice:
Create:

```
server/app/routes_pipeline.py
```

And register it in your FastAPI app.

### Why?
- Keeps Phase 13 isolated  
- Avoids cluttering existing Phase 12 routes  
- Matches your modular routing structure  

### Acceptable alternative:
Add to whichever file currently handles video analysis (likely `routes_vision.py`).

---

# ⭐ **FINAL CANONICAL ANSWERS (copy/paste for dev)**

| Question | Final Answer |
|---------|--------------|
| **Q1: WS frame uses tools[]?** | **YES — mandatory** |
| **Q2: Inject VideoPipelineService?** | **YES — inject in `__init__`** |
| **Q3: selectedTool → selectedTools[]?** | **YES — recommended** |
| **Q4: Remove fallback?** | **YES for Phase 13 paths** |
| **Q5: REST endpoint location?** | **New `routes_pipeline.py` (preferred)** |

---

# ⭐ **PHASE‑13 END‑TO‑END SMOKE TEST SCRIPT**  
**Audience:** QA + developers  
**Purpose:** Validate Phase‑13 functionality in < 5 minutes.

---

# **1. WebSocket Smoke Test**

### **1.1 Start server + UI**
- Start backend
- Start frontend
- Open VideoTracker with a plugin that supports pipelines

### **1.2 Open browser devtools → WS frames**

### **1.3 Play video**
Expected outgoing frame:

```json
{
  "type": "frame",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "image_data": "...",
  "frame_id": "..."
}
```

### **1.4 Expected incoming frame**
```json
{
  "frame_id": "...",
  "result": {
    "tracks": [...],
    "frame_id": "..."
  }
}
```

### **1.5 Logs**
Backend logs must show:

```
step=0 detect_players
step=1 track_players
```

---

# **2. REST Smoke Test**

### **2.1 POST /video/pipeline**
Send:

```json
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "payload": { "image_bytes": "AA==" }
}
```

Expected:

```json
{
  "result": {
    "tracks": [...]
  }
}
```

---

# **3. Plugin Smoke Test**

### **3.1 Run plugin harness**
```
python plugin_pipeline_harness.py yolo_tracker_plugin:YoloTrackerPlugin detect_players track_players annotate_frame
```

Expected:

```
[Phase‑13] step=0 tool=detect_players
[Phase‑13] step=1 tool=track_players
[Phase‑13] step=2 tool=annotate_frame
```

Final output must be a dict.

---

# **4. Error Handling Smoke Test**

### **4.1 Missing tools[]**
Send WS frame without tools:

Expected:

```json
{ "type": "error", "message": "WebSocket frame missing 'tools' field" }
```

### **4.2 Unknown tool**
Send:

```json
"tools": ["not_a_real_tool"]
```

Expected: error frame with plugin error.

---

# **5. UI Smoke Test**

### **5.1 Header**
```
Plugin: forgesyte-yolo-tracker | Tools: detect_players, track_players
```

### **5.2 Overlay**
- Detections drawn
- Tracks drawn
- No console errors

---

Roger — with these three documents, Phase‑13 is now fully:

- Implementable  
- Reviewable  
- Testable  
- Certifiable  
