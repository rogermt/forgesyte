# ⭐ **User Stories for v0.9.4 (Multi‑Tool Image Analysis)**

### **User Story 1 — Multi‑Tool Image Analysis**
**As a user**,  
I want to upload a single image and select multiple tools from the same plugin,  
**so that** I can receive all results in one unified JSON response without re‑uploading the image.

---

### **User Story 2 — Deterministic Tool Execution**
**As a system**,  
I want to execute tools sequentially through the canonical `run_tool()` dispatcher,  
**so that** tool execution is deterministic, auditable, and plugin‑agnostic.

---

### **User Story 3 — Canonical Tool Validation**
**As a backend service**,  
I want to validate all requested tools against `plugin.tools`,  
**so that** lifecycle methods and non‑tools are never treated as valid tool names.

---

### **User Story 4 — Unified Output Format**
**As a client**,  
I want the worker to return a single JSON object containing all tool results,  
**so that** I can consume the output without merging multiple responses.

---

### **User Story 5 — Backward Compatibility**
**As a developer**,  
I want single‑tool jobs to continue working unchanged,  
**so that** existing clients do not break when v0.9.4 is deployed.

---

### **User Story 6 — No Plugin Changes Required**
**As a plugin author**,  
I want multi‑tool support to work without modifying my plugin,  
**so that** existing plugins remain compatible with the new job type.

---

# ⭐ **State‑Flow Diagram (v0.9.4 Multi‑Tool Image Job)**

Here is a clean, readable UML‑style state flow diagram:

```
 ┌──────────────────────┐
 │  Image Submitted      │
 │  tool=[t1, t2, t3]    │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │  API Validates Tools  │
 │  (plugin.tools)       │
 └──────────┬───────────┘
            │
            ▼
 ┌────────────────────────────┐
 │  Create Job (image_multi)  │
 │  job.tool_list=[t1,t2,t3]  │
 │  job.tool=None             │
 └──────────┬────────────────┘
            │
            ▼
 ┌──────────────────────┐
 │  Worker Picks Job     │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │  Worker Detects job_type     │
 │  IF image_multi              │
 │     iterate tool_list        │
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │  For Each Tool:              │
 │  plugin.run_tool(tool, args) │
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │  Aggregate Results            │
 │  results[tool] = output      │
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │  Return Unified JSON          │
 │  { plugin_id, tools:{...} }   │
 └──────────────────────────────┘
```

---

# ⭐ **Sequence Diagram (Worker Execution Path)**

```
User → API: POST /image?tool=t1&tool=t2&tool=t3
API → PluginRegistry: validate tools
API → JobService: create job (image_multi)
JobService → DB: store job
Worker → DB: fetch next job
Worker → PluginRegistry: get plugin instance
loop for each tool
    Worker → Plugin: run_tool(tool, args)
    Plugin → YOLO/OCR/etc: execute tool
    Plugin → Worker: tool_result
end
Worker → DB: store aggregated results
Worker → API: return unified JSON
API → User: { tools: { t1:..., t2:..., t3:... } }
```

---

# ⭐ **Job Lifecycle Diagram (Single‑Tool vs Multi‑Tool)**

```
                ┌──────────────────────────────┐
                │          image               │
                │      (single-tool)           │
                └──────────────┬──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │ job.tool = t1    │
                     │ job.tool_list=[] │
                     └──────────────────┘


                ┌──────────────────────────────┐
                │        image_multi           │
                │     (multi-tool image)       │
                └──────────────┬──────────────┘
                               │
                               ▼
                     ┌──────────────────────────────┐
                     │ job.tool = None               │
                     │ job.tool_list=[t1,t2,t3]      │
                     └──────────────────────────────┘
```

---



