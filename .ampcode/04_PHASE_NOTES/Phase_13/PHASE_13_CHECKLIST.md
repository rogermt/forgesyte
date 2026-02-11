Roger — here are the **three final Phase‑13 governance deliverables**, written exactly the way you’d hand them to engineering, QA, and plugin authors.  
They close the loop on Phase‑13 and make the system fully maintainable, testable, and certifiable.

Let’s lock them in.

---

# ⭐ **PHASE‑13 FINAL IMPLEMENTATION CHECKLIST**  
**Audience:** Backend + Frontend engineers  
**Purpose:** Ensure Phase‑13 is implemented correctly, deterministically, and without regressions.

---

## ✅ **1. Backend: Pipeline Engine**
### **1.1 Add VideoPipelineService**
- File created: `server/app/services/video_pipeline_service.py`
- Implements:
  - `run_pipeline(plugin_id, tools, payload)`
  - Dict‑in → dict‑out chaining
  - Validation of plugin + tools
  - Fail‑fast behavior
- Uses `plugin.run_tool(tool_name, payload)` exactly like VisionAnalysisService.

### **1.2 Inject into VisionAnalysisService**
- Add in `__init__`:

```python
self.pipeline_service = VideoPipelineService(plugins)
```

### **1.3 Replace single‑tool execution**
- Remove:

```python
tool = data.get("tool")
active_plugin.run_tool(tool, ...)
```

- Add:

```python
tools = data["tools"]
self.pipeline_service.run_pipeline(plugin_id, tools, payload)
```

### **1.4 Remove fallback logic**
- No `"default"` tool fallback
- Missing `tools[]` → `ValueError`

---

## ✅ **2. Backend: WebSocket Path**
### **2.1 WS frame must include tools[]**
Required:

```json
"tools": ["detect_players", "track_players"]
```

### **2.2 WS error handling unchanged**
- Validation errors → send error frame
- Plugin errors → send error frame

---

## ✅ **3. Backend: REST Path**
### **3.1 Add POST /video/pipeline**
- New route file recommended: `routes_pipeline.py`
- Endpoint returns:

```json
{ "result": <final tool output> }
```

### **3.2 REST must accept tools[]**
No more `tool: string`.

---

## ✅ **4. Frontend: VideoTracker**
### **4.1 Props updated**
```ts
pluginId: string
tools: string[]
```

### **4.2 Header updated**
```
Plugin: <pluginId> | Tools: t1, t2, t3
```

### **4.3 Pass tools[] into useVideoProcessor**

---

## ✅ **5. Frontend: useVideoProcessor**
### **5.1 WS frame must send tools[]**
```ts
sendJsonMessage({
  type: "frame",
  plugin_id: pluginId,
  tools,
  image_data,
  frame_id,
})
```

### **5.2 REST payload must send tools[]**

---

## ✅ **6. Plugin Requirements**
- Tools accept `**payload`
- Tools return `dict`
- Tools are pure (no state)
- Tools listed in `plugin.tools`
- Tools handle missing fields gracefully

---

## ✅ **7. QA Validation**
- WS pipeline works
- REST pipeline works
- Tools run in order
- No fallback logic
- Final output = last tool output
- Logging includes plugin + tool + step

---

# ⭐ **PHASE‑13 CODE REVIEW CHECKLIST**  
**Audience:** Senior engineers reviewing PRs  
**Purpose:** Ensure Phase‑13 code meets architectural and governance standards.

---

## 🔍 **1. Pipeline Engine**
- [ ] `VideoPipelineService` exists
- [ ] Validates plugin_id + tools[]
- [ ] Executes tools in order
- [ ] Uses `plugin.run_tool` (not plugin_manager)
- [ ] Returns dict
- [ ] Raises ValueError for invalid pipelines
- [ ] No fallback logic

---

## 🔍 **2. VisionAnalysisService**
- [ ] Injects `VideoPipelineService` in `__init__`
- [ ] Requires `tools[]` in WS frames
- [ ] Removes fallback to `"default"`
- [ ] Builds payload: `{ image_bytes, options, frame_id }`
- [ ] Calls `pipeline_service.run_pipeline(...)`
- [ ] Error handling unchanged

---

## 🔍 **3. REST Endpoint**
- [ ] New `/video/pipeline` endpoint exists
- [ ] Accepts `{ plugin_id, tools[], payload }`
- [ ] Returns `{ result: ... }`
- [ ] No fallback logic

---

## 🔍 **4. Frontend**
### VideoTracker
- [ ] Props: `tools[]` instead of `toolName`
- [ ] Header shows tools list
- [ ] Passes tools[] into useVideoProcessor

### useVideoProcessor
- [ ] Sends WS frames with tools[]
- [ ] Sends REST payloads with tools[]
- [ ] No references to `toolName`

---

## 🔍 **5. Plugins**
- [ ] Tools accept `**payload`
- [ ] Tools return dict
- [ ] Tools are pure
- [ ] Tools listed in manifest
- [ ] Tools handle missing fields

---

## 🔍 **6. Logging**
- [ ] Logs each pipeline step
- [ ] Includes plugin, tool, step index

---

## 🔍 **7. Tests**
- [ ] Regression suite passes
- [ ] Smoke test passes
- [ ] Plugin harness passes

---


