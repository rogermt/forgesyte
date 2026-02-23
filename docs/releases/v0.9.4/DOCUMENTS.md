Absolutely, Roger — here are the **four deliverables for v0.9.4**, written cleanly, professionally, and in the same governance‑driven tone as your v0.9.3 materials. These are ready to paste directly into GitHub.

No drift. No invention. Just the exact artifacts you need.

---

# ✅ **Commit Message for v0.9.4**

```
v0.9.4 — Enable Multi‑Tool Image Analysis for a Single Plugin

This commit restores pre‑Phase‑6 multi‑tool behavior by allowing users to
submit a single image and execute multiple tools from the same plugin in
one job. The worker now dispatches each tool through the canonical
plugin.run_tool() contract and aggregates all results into a unified JSON
response. This eliminates redundant uploads, ensures deterministic
execution, and aligns the image pipeline with the intended design of
YOLO‑style multi‑tool plugins.

Includes:
- API support for multiple tool parameters
- New job_type="image_multi"
- Worker‑side sequential tool execution
- Unified JSON aggregation
- Canonical tool validation via plugin.tools
- Regression tests for multi‑tool execution
```

---

# ✅ **GitHub PR Description (Final Polished Version)**

# **v0.9.4 — Enable Multi‑Tool Image Analysis for a Single Plugin (Unified JSON Output)**

## **Summary**

This PR restores and formalizes the ability to run **multiple tools from the same plugin** against a single uploaded image and return all results in a unified JSON response. This behavior existed prior to Phase 6 but was lost during the migration to the unified job system. v0.9.4 reintroduces this capability in a stable, explicit, and fully governed form.

Users can now select a plugin once, submit an image once, and request multiple tools (e.g., `player_detection`, `ball_detection`, `player_tracking`) in a single operation. The worker executes each tool sequentially through the canonical `run_tool()` dispatcher and aggregates the results into a single structured JSON payload.

This significantly improves usability, reduces redundant uploads, and aligns the image pipeline with the intended multi‑tool design of YOLO‑style plugins.

---

## **User Story**

> **As a user, I would like to analyze an image with multiple tools from the same plugin I have currently selected and return the results in one JSON.**

---

## **Root Cause**

Multi‑tool execution was implicitly supported before Phase 6 because tools were executed directly from plugin methods and the worker did not enforce a single‑tool‑per‑job constraint. Phase 6 introduced:

- A strict `job.tool` field  
- A single‑tool execution path  
- No mechanism to pass multiple tool IDs  
- No aggregation logic  

As a result, multi‑tool image analysis silently regressed.

---

## **Fix**

### **1. API support for multiple tools**
The image submission endpoint now accepts multiple `tool` parameters and constructs a multi‑tool job.

### **2. New job type: `image_multi`**
This distinguishes multi‑tool jobs from single‑tool jobs.

### **3. Worker executes tools sequentially**
Each tool is executed via:

```
plugin.run_tool(tool_name, args)
```

### **4. Unified JSON output**
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

### **5. Backward compatibility preserved**
Single‑tool jobs remain unchanged.

---

## **Impact**

### **Resolved**
- Multi‑tool image analysis works again (pre‑Phase‑6 behavior restored)
- YOLO Tracker can run all its tools in one request
- Worker execution is unified and deterministic
- Users no longer need to upload the same image multiple times

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

---

# ✅ **Migration Note for Contributors**

### **v0.9.4 Contributor Migration Notes**

v0.9.4 introduces multi‑tool image jobs. Contributors should be aware of the following:

### **1. Plugins do not need to change**
All plugins continue to expose tools through `plugin.tools` and execute them via `run_tool()`. No plugin‑side modifications are required.

### **2. Worker now supports `image_multi` jobs**
If you add new job types in the future, ensure they follow the same pattern:

- Detect job type early  
- Normalize input schema  
- Dispatch via `run_tool()`  

### **3. API now accepts multiple `tool` parameters**
Client libraries may optionally update their SDKs to support:

```
tool=foo&tool=bar&tool=baz
```

### **4. Avoid reintroducing Phase‑6 behavior**
Do not add logic that:

- Assumes a single tool per job  
- Validates tools via `hasattr`  
- Treats lifecycle methods as tools  

### **5. Tests must cover multi‑tool execution**
Any new plugin or tool should be tested in both single‑tool and multi‑tool contexts.

---

# ✅ **Release Note for v0.9.4**

### **v0.9.4 — Multi‑Tool Image Analysis Restored**

This release reintroduces the ability to run multiple tools from the same plugin on a single uploaded image. Users can now request several tools (e.g., `player_detection`, `ball_detection`, `player_tracking`) in one operation, and the system returns all results in a unified JSON response.

This restores pre‑Phase‑6 behavior and significantly improves performance and usability for YOLO‑style multi‑tool plugins.

**Highlights:**

- Multi‑tool image jobs (`image_multi`)  
- Sequential tool execution via `run_tool()`  
- Unified JSON output  
- Canonical tool validation  
- Backward‑compatible with single‑tool jobs  

Video support will be restored in **v0.9.5**.

---

