# **PHASE 13 — PR DESCRIPTION (CANONICAL)**  
Save as:  
`docs/phases/phase_13_pr_description.md`

---

## **Title**  
**Phase 13 — VideoTracker Multi‑Tool Linear Pipelines (Single‑Plugin)**

---

## **Summary**  
This PR implements **Phase 13**, introducing **linear multi‑tool pipelines** for VideoTracker.  
Instead of executing a single tool per frame or per background job, VideoTracker can now execute an **ordered sequence of tools** inside a single plugin:

```
[ detect_players → track_players → annotate_frames ]
```

Each tool receives the output of the previous tool, enabling richer, multi‑stage video analysis.

This PR includes:

- A new `VideoPipelineService`  
- REST endpoint `/video/pipeline`  
- WebSocket pipeline execution  
- UI support for selecting multiple tools  
- Removal of all fallback logic  
- Logging for each pipeline step  
- Full test suite for REST, WS, and validation  

---

## **Scope (Required)**  
This PR includes ONLY:

- Linear pipelines inside a single plugin  
- Ordered tool execution  
- REST + WebSocket integration  
- UI multi‑tool selection  
- Validation of plugin_id + tools[]  
- Logging for each pipeline step  
- Tests for REST, WS, and validation  

---

## **Out of Scope (Must NOT appear)**  
- Cross‑plugin pipelines  
- DAG pipelines  
- Tool capability matching  
- Pipeline registry  
- UI DAG editors  
- Model selection  
- Video export  
- Timeline scrubbing  
- Analytics, heatmaps, charts  
- Any UI beyond the canonical VideoTracker spec  

Any PR containing these must be rejected.

---

## **Implementation Details**

### **Server**
- Added `VideoPipelineService`  
- Added `/video/pipeline` REST endpoint  
- Updated `VisionAnalysisService` to accept `plugin_id` + `tools[]`  
- Removed fallback to `"default"` tool  
- Removed fallback to first tool in `tasks.py`  
- Added logging for each pipeline step  

### **UI**
- Added `selectedTools[]` state  
- Added `PipelineToolSelector`  
- Updated REST + WebSocket payloads to include `plugin_id` + `tools[]`  

### **Tests**
- `test_video_pipeline_rest.py`  
- `test_video_pipeline_ws.py`  
- `test_pipeline_validation.py`  

---

## **Validation Checklist**
- [ ] Pipeline executes tools in order  
- [ ] WebSocket frames include plugin_id + tools[]  
- [ ] REST endpoint rejects invalid pipelines  
- [ ] Logging shows each pipeline step  
- [ ] No fallback logic remains  
- [ ] All tools belong to the same plugin  

---

## **Reviewer Notes**
- Ensure no implicit tool selection  
- Ensure no cross‑plugin execution  
- Ensure UI sends correct pipeline structure  
- Ensure server rejects empty or invalid pipelines  

---

# **PHASE 13 — COMMIT MESSAGES (ALL 10 COMMITS)**  
Use these exact messages.

---

### **Commit 1 — Add VideoPipelineService skeleton**

```
feat(phase13): add VideoPipelineService skeleton

- Create video_pipeline_service.py
- Add run_pipeline() and _validate() stubs
- No logic yet
```

---

### **Commit 2 — Add REST endpoint /video/pipeline**

```
feat(phase13): add REST endpoint for video pipelines

- Add PipelineRequest model
- Add POST /video/pipeline route
- Wire to VideoPipelineService.run_pipeline()
```

---

### **Commit 3 — Integrate pipeline into WebSocket streaming**

```
feat(phase13): integrate pipeline execution into VisionAnalysisService

- Accept plugin_id + tools[] from WS frames
- Replace single-tool execution with pipeline call
```

---

### **Commit 4 — Add pipeline validation stubs**

```
feat(phase13): add pipeline validation stubs

- Add _validate(plugin_id, tools) to VideoPipelineService
- No validation logic yet
```

---

### **Commit 5 — Add UI state for selectedTools[]**

```
feat(phase13): add selectedTools state to VideoTracker UI

- Add selectedTools: string[]
- Add PipelineToolSelector component
```

---

### **Commit 6 — Send pipeline via REST + WebSocket**

```
feat(phase13): send plugin_id + tools[] in REST and WS

- Update runPipeline() API call
- Update useWebSocket.ts to include tools[] in frame payload
```

---

### **Commit 7 — Implement pipeline execution logic**

```
feat(phase13): implement linear pipeline execution

- Validate plugin_id + tools[]
- Execute tools sequentially
- Feed output of step N into step N+1
```

---

### **Commit 8 — Add pipeline logging**

```
feat(phase13): add logging for each pipeline step

- Log plugin_id, tool_name, step index
- Log args_keys for debugging
```

---

### **Commit 9 — Add Phase 13 tests**

```
test(phase13): add REST, WS, and validation tests

- test_video_pipeline_rest.py
- test_video_pipeline_ws.py
- test_pipeline_validation.py
```

---

### **Commit 10 — Remove all fallback logic**

```
refactor(phase13): remove default tool fallbacks

- Remove "default" fallback in WebSocket
- Remove "first tool" fallback in tasks.py
- Enforce explicit tool selection
```

---
