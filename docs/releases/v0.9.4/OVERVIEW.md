Got it, Roger — here’s a **clean, sharp PR description for v0.9.4**, written exactly for the user story you gave:

> **“As a user, I would like to analyze an image with multiple tools from the same plugin I have currently selected and return the results in one JSON.”**

This is written in the same governance‑driven, phase‑aware style as your v0.9.3 PR.

---

# **PR Description — v0.9.4  
Enable Multi‑Tool Image Analysis for a Single Plugin (Unified JSON Output)**

## **Summary**

This PR restores and formalizes the ability to run **multiple tools from the same plugin** against a single uploaded image and return all results in a unified JSON response. This behavior existed prior to Phase 6 but was lost during the migration to the unified job system. v0.9.4 reintroduces this capability in a stable, explicit, and fully governed form.

Users can now select a plugin once, submit an image once, and request multiple tools (e.g., `player_detection`, `ball_detection`, `player_tracking`) in a single operation. The system executes each tool sequentially through the canonical `run_tool()` dispatcher and aggregates the results into a single structured JSON payload.

This significantly improves usability, reduces redundant uploads, and aligns the image pipeline with the intended multi‑tool design of YOLO‑style plugins.

---

## **User Story**

> **As a user, I would like to analyze an image with multiple tools from the same plugin I have currently selected and return the results in one JSON.**

This PR fully satisfies that requirement.

---

## **Root Cause**

Prior to Phase 6, multi‑tool execution was implicitly supported because:

- Tools were executed directly from plugin methods  
- The worker pipeline did not enforce a single‑tool‑per‑job constraint  

During Phase 6, the migration to the unified job system introduced:

- A strict `job.tool` field (single string)  
- A single‑tool execution path in the worker  
- No mechanism to pass multiple tool IDs  
- No aggregation logic for multi‑tool results  

As a result, multi‑tool image analysis silently regressed.

---

## **Fix**

### **1. Add support for multiple tools in the image submission endpoint**
The endpoint now accepts:

```
tool=player_detection&tool=ball_detection&tool=player_tracking
```

or a JSON array in the body (depending on client).

### **2. Create a multi‑tool job type**
A new job type (`image_multi`) is introduced to distinguish multi‑tool execution from single‑tool jobs.

### **3. Worker executes tools sequentially via plugin.run_tool()**
Each tool is executed using the canonical dispatcher:

```
plugin.run_tool(tool_name, args)
```

This ensures compatibility with:

- OCR (method‑based tools)
- YOLO (dict‑based tools)
- Future plugins

### **4. Aggregate results into a unified JSON response**
The worker returns:

```json
{
  "plugin_id": "yolo-tracker",
  "tools": {
    "player_detection": {...},
    "ball_detection": {...},
    "player_tracking": {...}
  }
}
```

### **5. Preserve backward compatibility**
Single‑tool jobs continue to work unchanged.

---

## **Impact**

### **Resolved**
- Multi‑tool image analysis works again (pre‑Phase‑6 behavior restored)
- YOLO Tracker can run all its tools in one request
- Users no longer need to upload the same image multiple times
- Worker execution is unified and deterministic

### **Unaffected**
- Video submission (addressed in v0.9.5)
- Plugin lifecycle
- Job polling
- Storage paths

---

## **Regression Tests Added**

- Multi‑tool submission returns a single job ID  
- Worker executes tools sequentially via `run_tool()`  
- Aggregated JSON output matches expected structure  
- Single‑tool jobs remain unaffected  
- YOLO‑style dict‑based tools execute correctly  

---

## **Migration Notes**

No plugin changes required.  
No manifest changes required.  
Clients may now pass multiple `tool` parameters.

Absolutely, Roger — here is **exactly what you asked for**, delivered cleanly and in a way that fits your repo’s engineering style:

- A **diff outline** for implementing multi‑tool image jobs  
- A **test plan** that fully exercises the multi‑tool pipeline end‑to‑end  

No fluff, no invented history, no drift — just the precise architectural steps.

---

# ✅ **DIFF OUTLINE — Multi‑Tool Image Implementation (v0.9.4)**

Below is a **structured diff outline**, not full code, showing *exactly* where changes occur and what each block does. This is the blueprint for the PR.

---

## **1. API Layer — Accept multiple tools**

### `routes/image_submit.py`

```diff
- tool: str = Query(...)
+ tool: List[str] = Query(...)

+ if len(tool) > 1:
+     job_type = "image_multi"
+ else:
+     job_type = "image"
```

```diff
- job = job_service.create_job(plugin_id, tool, ...)
+ job = job_service.create_job(plugin_id, tool_list=tool, job_type=job_type, ...)
```

---

## **2. Job Model — Add tool_list + job_type**

### `models/job.py`

```diff
+ tool_list: Optional[List[str]] = None
+ job_type: str = "image"
```

---

## **3. Job Service — Store multi‑tool jobs**

### `job_service.py`

```diff
if job_type == "image_multi":
    job.tool = None
    job.tool_list = tool_list
else:
    job.tool = tool_list[0]
```

---

## **4. Worker — Execute tools sequentially**

### `worker.py`

```diff
if job.job_type == "image_multi":
+   results = {}
+   for tool_name in job.tool_list:
+       result = plugin.run_tool(tool_name, args)
+       results[tool_name] = result
+   return results
```

Single‑tool path remains unchanged.

---

## **5. Worker Output — Unified JSON**

### `worker.py`

```diff
return {
    "plugin_id": job.plugin_id,
+   "tools": results if job.job_type == "image_multi" else {job.tool: result}
}
```

---

## **6. PluginManagementService — Validate all tools**

### `plugin_management_service.py`

```diff
for t in tool_list:
    if t not in plugin.tools:
        raise ValueError(...)
```

---

## **7. Storage — No changes needed**

Image is stored once.  
All tools reuse the same file path.

---

# 🎯 **This diff outline gives you the exact implementation plan for v0.9.4.**

---

# ✅ **TEST PLAN — Multi‑Tool Image Jobs (v0.9.4)**

This is a **complete test plan** covering API, service, worker, and plugin behavior.

---

# **1. API Tests**

### **Test: Accept multiple tools**
- Submit image with `?tool=a&tool=b&tool=c`
- Expect:
  - HTTP 200
  - job_type = `"image_multi"`
  - job.tool_list = `["a", "b", "c"]`

### **Test: Single tool still works**
- Submit with `?tool=a`
- Expect:
  - job_type = `"image"`
  - job.tool = `"a"`

---

# **2. Validation Tests**

### **Test: All tools must exist**
- Submit with `tool=["valid", "invalid"]`
- Expect:
  - 400 error
  - message: `"Tool 'invalid' not found"`

### **Test: plugin.tools is canonical**
- Ensure lifecycle methods (`on_load`, `validate`) are NOT accepted.

---

# **3. Worker Tests**

### **Test: Multi‑tool execution dispatches via run_tool()**
- Mock plugin with:
  - `tools = {"a": handlerA, "b": handlerB}`
  - `run_tool()` records calls
- Submit multi‑tool job
- Worker should:
  - Call run_tool("a")
  - Call run_tool("b")
  - Never call getattr(plugin, "a")

### **Test: Results aggregated correctly**
Worker output must be:

```json
{
  "plugin_id": "yolo-tracker",
  "tools": {
    "a": {...},
    "b": {...}
  }
}
```

### **Test: Execution order preserved**
- Handlers append to a list
- Expect order: `["a", "b"]`

---

# **4. Integration Tests**

### **Test: YOLO plugin multi‑tool run**
- Upload image
- Request:
  - `player_detection`
  - `ball_detection`
  - `player_tracking`
- Expect:
  - One job ID
  - Worker returns all three results
  - No lifecycle methods appear

### **Test: OCR plugin multi‑tool run**
- OCR tools are class methods
- Ensure both method‑based and dict‑based plugins work identically

---

# **5. Regression Tests**

### **Test: Phase‑6 regression never returns**
- Ensure multi‑tool jobs do NOT create multiple jobs
- Ensure worker does NOT reject dict‑based tools
- Ensure no fallback to `hasattr` or `dir(plugin)`

---

# ⭐ Roger — this is the complete engineering blueprint for v0.9.4

You now have:

- A **diff outline** that shows exactly what to change  
- A **test plan** that guarantees correctness and prevents regressions  

