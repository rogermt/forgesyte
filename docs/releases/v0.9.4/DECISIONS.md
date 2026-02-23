Roger, these are the **right two questions**, and your instincts on both are spot‑on. Let me give you a crisp, authoritative confirmation so you can lock v0.9.4 without second‑guessing anything.

---

# ✅ **Question 1 — Output Format for Single‑Tool Jobs**

You proposed two options:

### **Option A — Keep single‑tool format unchanged**
- Single‑tool:
  ```json
  {"results": {...}}
  ```
- Multi‑tool:
  ```json
  {"plugin_id": "...", "tools": {...}}
  ```

### **Option B — Unify all formats**
- Single‑tool:
  ```json
  {"plugin_id": "...", "tools": {"tool_name": {...}}}
  ```
- Multi‑tool:
  ```json
  {"plugin_id": "...", "tools": {...}}
  ```

---

# ⭐ **Correct Answer: Option A (Backward Compatible)**

This is absolutely the right call for v0.9.4.

Here’s why:

### **1. Zero client breakage**
Your existing UI and API clients expect:

```json
{"results": {...}}
```

Changing this would break:
- web‑ui
- any external clients
- automation scripts
- tests

### **2. v0.9.4 is a *feature addition*, not a breaking release**
You’re adding multi‑tool support, not redesigning the job output contract.

### **3. v1.0.0 is the correct place to unify formats**
That’s when you can introduce:
- `plugin_id`
- `tools`
- consistent structure across job types

### **4. Multi‑tool jobs already require a different shape**
So it’s fine that they return:

```json
{
  "plugin_id": "...",
  "tools": {...}
}
```

### **5. Worker code stays simple**
You don’t need branching logic to wrap single‑tool results.

---

# 📌 **Final Decision for v0.9.4**
### **Single‑tool jobs:**
```json
{"results": {...}}
```

### **Multi‑tool jobs:**
```json
{
  "plugin_id": "...",
  "tools": {
    "player_detection": {...},
    "ball_detection": {...}
  }
}
```

This is correct, stable, and safe.

---

# ✅ **Question 2 — Error Handling in Multi‑Tool Loop**

You proposed:

### **Option A — Fail entire job if any tool fails**
### **Option B — Continue and record partial results**

---

# ⭐ **Correct Answer: Option A (Fail‑Fast)**

This is the right choice for v0.9.4.

Here’s why:

### **1. Predictability**
If any tool fails, the job fails.  
No ambiguity. No partial success semantics.

### **2. Matches your own governance rule**
Your plan explicitly states:

> “one tool failure fails entire job”

### **3. Avoids complex output formats**
Partial results require:
- per‑tool status
- per‑tool error messages
- mixed success/failure semantics

This is a v1.0.0‑level feature, not a v0.9.x feature.

### **4. Keeps worker code simple**
Fail‑fast means:

```python
for tool_name in tools_to_run:
    result = plugin_service.run_plugin_tool(...)
    results[tool_name] = result
```

If an exception occurs:
- worker marks job as failed
- error_message is set
- no partial results returned

### **5. Matches single‑tool behavior**
Single‑tool jobs fail if the tool fails.  
Multi‑tool should behave the same.

---

# 📌 **Final Decision for v0.9.4**
### **Fail‑fast. Entire job fails if any tool fails.**

This is the correct, simplest, and most consistent behavior.

---

# 🎉 **Final Summary — You Now Have the Correct Answers**

### **Question 1 (Output Format):**  
✔ **Option A — Keep single‑tool format unchanged**

### **Question 2 (Error Handling):**  
✔ **Option A — Fail entire job if any tool fails**

Both decisions are correct, stable, and aligned with your architecture and governance.

---

Roger, I’ve got you — here are **all four deliverables**, written cleanly, decisively, and aligned with your v0.9.4 architecture and governance style. These are ready to drop straight into your PR, documentation, or worker implementation.

I’ll keep everything crisp and deterministic.

---

# ✅ **1. Updated Worker Pseudocode (Reflecting Both Decisions)**  
**Decisions implemented:**  
- **Single‑tool output stays unchanged**  
- **Multi‑tool jobs fail‑fast**  

Here is the authoritative worker pseudocode for v0.9.4:

```
# Determine tools to run
if job.job_type == "image_multi":
    tools_to_run = json.loads(job.tool_list)
else:
    tools_to_run = [job.tool]

results = {}

try:
    for tool_name in tools_to_run:
        # Validate tool exists (plugin.tools)
        if tool_name not in plugin.tools:
            raise Exception(f"Tool '{tool_name}' not found")

        # Execute tool via canonical dispatcher
        result = plugin_service.run_plugin_tool(
            job.plugin_id,
            tool_name,
            args
        )

        # Normalize Pydantic or dict-like outputs
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        elif hasattr(result, "dict"):
            result = result.dict()

        results[tool_name] = result

    # Prepare output
    if job.job_type == "image_multi":
        output_data = {
            "plugin_id": job.plugin_id,
            "tools": results
        }
    else:
        output_data = {"results": results[job.tool]}

    job.status = "completed"
    job.results = output_data

except Exception as e:
    # Fail-fast: any tool failure fails entire job
    job.status = "failed"
    job.error_message = str(e)
```

This is the exact behavior you want for v0.9.4.

---

# ✅ **2. Updated Test Cases for Fail‑Fast Behavior**

These tests enforce the fail‑fast rule and ensure single‑tool output remains unchanged.

---

## **Backend Worker Tests**

### **Test 1 — Multi‑tool: second tool fails → job fails**
```
Given:
  tools_to_run = ["t1", "t2"]
  t1 succeeds
  t2 raises Exception("boom")

Expect:
  job.status == "failed"
  job.error_message == "boom"
  job.results is None
```

### **Test 2 — Multi‑tool: first tool fails immediately**
```
Given:
  tools_to_run = ["t1", "t2"]
  t1 raises Exception("bad input")

Expect:
  job.status == "failed"
  job.error_message == "bad input"
  t2 is never executed
```

### **Test 3 — Multi‑tool: all tools succeed**
```
Expect:
  job.status == "completed"
  job.results == {
    "plugin_id": "...",
    "tools": {
      "t1": {...},
      "t2": {...}
    }
  }
```

### **Test 4 — Single‑tool: failure still fails job**
```
Expect:
  job.status == "failed"
  job.error_message contains exception
  output format remains {"results": ...}
```

### **Test 5 — Single‑tool: success keeps old format**
```
Expect:
  job.results == {"results": {...}}
```

---

# ⭐ **3. v0.9.4 — Final Architecture Contract**

This is the authoritative, stable contract for v0.9.4.  
It defines exactly what the system guarantees and what plugin authors and clients can rely on.

---

# **v0.9.4 Architecture Contract — Multi‑Tool Image Jobs**

## **1. Job Types**
- `"image"` — single‑tool image job  
- `"image_multi"` — multi‑tool image job  

No other job types are modified in v0.9.4.

---

## **2. Job Fields**
| Field        | Single‑Tool | Multi‑Tool | Notes |
|--------------|-------------|------------|-------|
| `tool`       | string      | null       | Single‑tool only |
| `tool_list`  | null        | JSON list  | Multi‑tool only |
| `job_type`   | "image"     | "image_multi" | Required |
| `input_path` | required    | required   | Same for both |

---

## **3. API Contract**
### **Single‑tool submission**
```
POST /image/submit?tool=t1
```

### **Multi‑tool submission**
```
POST /image/submit?tool=t1&tool=t2&tool=t3
```

### **Validation rules**
- All tools must exist in `plugin.tools`
- All tools must support image input
- Lifecycle methods are never valid tools

---

## **4. Worker Contract**
### **Single‑tool**
- Executes exactly one tool  
- Output format:
  ```json
  {"results": {...}}
  ```

### **Multi‑tool**
- Executes tools sequentially  
- Fail‑fast: any tool failure fails the job  
- Output format:
  ```json
  {
    "plugin_id": "...",
    "tools": {
      "t1": {...},
      "t2": {...}
    }
  }
  ```

---

## **5. Plugin Contract**
Plugins do **not** change in v0.9.4.

They must:
- expose tools via `plugin.tools`
- implement `run_tool(tool_name, args)`
- return dict‑like or Pydantic‑like objects

---

## **6. Frontend Contract**
- `submitImage()` now accepts an array of tools  
- UI displays multi‑tool results under `results.tools`  
- Single‑tool UI remains unchanged  

---

## **7. Backward Compatibility**
- Single‑tool jobs behave exactly as before  
- No plugin changes required  
- No manifest changes required  
- No schema migrations beyond JSON string field  

---

# ⭐ **4. v1.0.0 Proposal — Unified Output Format**

This is the clean, future‑proof format you can adopt once you’re ready to break compatibility.

---

# **v1.0.0 Unified Output Format Proposal**

## **Unified JSON Structure**
All job types (image, image_multi, video, video_multi, future types) return:

```json
{
  "job_id": "uuid",
  "plugin_id": "yolo-tracker",
  "job_type": "image" | "image_multi" | "video" | ...,
  "tools": {
    "tool_name": {
      "status": "success" | "error",
      "data": {...} | null,
      "error": "..." | null
    }
  },
  "status": "completed" | "failed",
  "error_message": null | "job-level error"
}
```

---

## **Benefits**
- One format for all job types  
- Per‑tool success/error reporting  
- Supports partial success (optional)  
- Cleaner UI and API client logic  
- Future‑proof for multi‑tool video jobs  

---

## **Migration Strategy**
1. Introduce unified format behind a feature flag  
2. Update frontend to support both formats  
3. Deprecate old format  
4. Remove old format in v1.0.0  

---

Roger, this gives you everything you need:

- Updated worker pseudocode  
- Updated fail‑fast test cases  
- Final v0.9.4 architecture contract  
- A clean v1.0.0 proposal for unified output  

If you want, I can now generate:

- A v1.0.0 migration guide  
- A combined v0.9.3 → v0.9.5 architecture document  
- A contributor onboarding guide for the new job types