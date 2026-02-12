Absolutely, Roger — this is the big one.  
**Commit 7 is where the pipeline actually becomes real.**  
Up to now, everything was wiring, routing, and UI.  
Commit 7 is the first commit that touches **backend logic**.

Below is the **canonical, final, Phase‑13‑approved implementation** of:

- `VideoPipelineService.run_pipeline()`
- Validation rules
- Sequential tool execution
- Error handling
- Return format
- Unified diff patch

This is the commit that makes the whole system *work*.

Let’s lock it down.

---

# ⭐ **PHASE‑13 — COMMIT 7: Implement Pipeline Execution Logic**

## 🎯 **Objective**
Implement the actual pipeline execution logic in:

```
server/app/services/video_pipeline_service.py
```

This commit adds:

- Validation of plugin existence  
- Validation of tools[]  
- Sequential execution of tools  
- Passing intermediate results to the next tool  
- Returning the final output  

No WebSocket changes.  
No REST changes.  
No VisionAnalysisService changes.  
No plugin changes.

Just the pipeline engine.

---

# ⭐ **THE CANONICAL PIPELINE CONTRACT**

### Input:
```python
run_pipeline(
    plugin_id: str,
    tools: list[str],
    payload: dict,
)
```

### Behavior:
1. Validate plugin exists  
2. Validate tools[] is non‑empty  
3. Validate each tool exists in plugin  
4. Execute tools sequentially  
5. Pass previous result into next tool as `"input"`  
6. Return final result  

### Output:
```python
{
    "result": <final tool output>,
    "steps": [
        {"tool": "detect_players", "output": {...}},
        {"tool": "track_players", "output": {...}},
        ...
    ]
}
```

---

# ⭐ **THE EXACT IMPLEMENTATION (NO GUESSING)**

Here is the **canonical implementation** of `VideoPipelineService.run_pipeline()`.

```python
class VideoPipelineService:
    def __init__(self, plugins: PluginRegistry) -> None:
        self.plugins = plugins

    def run_pipeline(self, plugin_id: str, tools: list[str], payload: dict) -> dict:
        # Validate plugin
        plugin = self.plugins.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        # Validate tools[]
        if not tools or not isinstance(tools, list):
            raise ValueError("Pipeline requires a non-empty tools[] array")

        steps = []
        current_payload = payload

        for tool_name in tools:
            # Validate tool exists
            if tool_name not in plugin.tools:
                raise ValueError(f"Tool '{tool_name}' not found in plugin '{plugin_id}'")

            # Execute tool
            output = plugin.run_tool(tool_name, current_payload)

            # Record step
            steps.append({
                "tool": tool_name,
                "output": output,
            })

            # Prepare payload for next tool
            current_payload = {
                **payload,          # original frame data
                "input": output,    # previous tool output
            }

        # Final output is the last tool's output
        return {
            "result": steps[-1]["output"],
            "steps": steps,
        }
```

This is the **official Phase‑13 pipeline engine**.

---

# ⭐ **UNIFIED DIFF — COMMIT 7 (EXACT PATCH)**

```diff
diff --git a/server/app/services/video_pipeline_service.py b/server/app/services/video_pipeline_service.py
index 1111111..2222222 100644
--- a/server/app/services/video_pipeline_service.py
+++ b/server/app/services/video_pipeline_service.py
@@ -1,6 +1,48 @@
 from typing import Any, Dict, List
 from ..protocols import PluginRegistry

+
 class VideoPipelineService:
     def __init__(self, plugins: PluginRegistry) -> None:
         self.plugins = plugins
+
+    def run_pipeline(self, plugin_id: str, tools: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
+        # Validate plugin
+        plugin = self.plugins.get(plugin_id)
+        if plugin is None:
+            raise ValueError(f"Plugin '{plugin_id}' not found")
+
+        # Validate tools[]
+        if not tools or not isinstance(tools, list):
+            raise ValueError("Pipeline requires a non-empty tools[] array")
+
+        steps: List[Dict[str, Any]] = []
+        current_payload = payload
+
+        for tool_name in tools:
+            # Validate tool exists
+            if tool_name not in plugin.tools:
+                raise ValueError(f"Tool '{tool_name}' not found in plugin '{plugin_id}'")
+
+            # Execute tool
+            output = plugin.run_tool(tool_name, current_payload)
+
+            # Record step
+            steps.append({
+                "tool": tool_name,
+                "output": output,
+            })
+
+            # Prepare payload for next tool
+            current_payload = {
+                **payload,          # original frame data
+                "input": output,    # previous tool output
+            }
+
+        # Final output is the last tool's output
+        return {
+            "result": steps[-1]["output"],
+            "steps": steps,
+        }
```

---

# ⭐ **PR DESCRIPTION — COMMIT 7**

## **feat(phase‑13): Implement pipeline execution logic (Commit 7/10)**

### Summary
This commit implements the actual multi‑tool pipeline execution engine in `VideoPipelineService`. Tools are now executed sequentially, with each tool receiving the previous tool’s output as `"input"`.

### Changes
- Added validation for plugin existence  
- Added validation for tools[]  
- Added sequential execution loop  
- Added step recording for debugging  
- Added intermediate payload chaining  
- Final result is last tool’s output  

### What This Enables
- Full multi‑tool pipelines over WebSocket  
- Deterministic tool chaining  
- Debuggable pipeline steps  
- Foundation for REST pipeline endpoint (Commit 8)

### What This Does NOT Change
- No changes to VisionAnalysisService  
- No changes to WebSocket routing  
- No changes to REST  
- No changes to plugins  

---

# ⭐ **REVIEWER CHECKLIST — COMMIT 7**

### Validation
- [ ] Plugin existence validated  
- [ ] tools[] validated  
- [ ] Each tool validated against plugin.tools  

### Execution
- [ ] Tools executed sequentially  
- [ ] Output of each tool passed as `"input"` to next  
- [ ] Steps recorded  

### Output
- [ ] Final result = last tool output  
- [ ] Steps array included  

### No unrelated changes
- [ ] No changes to WebSocket  
- [ ] No changes to REST  
- [ ] No changes to plugin registry  
- [ ] No changes to plugin code  

---

Roger — these are *exactly* the right questions to ask before locking in Commit 7.  
Let’s settle them cleanly so your dev doesn’t have to guess or break the WS protocol.

Below is the **canonical, Phase‑13‑correct answer** to each point, followed by the **final required actions**.

---

# ⭐ 1. **Should VisionAnalysisService.handle_frame() be updated to handle the new pipeline output format?**

### ✅ **YES — absolutely required.**

If you do *not* update `handle_frame()`, the WebSocket protocol will break.

Why?

Because after Commit 7, `run_pipeline()` returns:

```python
{
  "result": <final_output>,
  "steps": [...]
}
```

But the WS protocol (Phase‑12 and Phase‑13) expects:

```json
{
  "type": "result",
  "frame_id": "...",
  "plugin_id": "...",
  "result": <actual tool output>,
  "processing_time": ...
}
```

If you send the entire pipeline object, the UI will break.

### ✔ Required fix:

Inside `VisionAnalysisService.handle_frame()`:

Replace:

```python
await self.ws_manager.send_frame_result(
    client_id, frame_id, plugin_name, result, processing_time
)
```

With:

```python
await self.ws_manager.send_frame_result(
    client_id,
    frame_id,
    plugin_name,
    result["result"],   # extract final output
    processing_time,
)
```

### This preserves backward compatibility.

The UI still receives the same shape it always has.

---

# ⭐ 2. **Should run_pipeline() include logging?**

### ✅ **YES — but minimal logging only.**

The updated plan omitted logging because:

- Logging belongs in a later commit (Commit 10: Observability)
- Logging is not required for correctness
- Logging can clutter the pipeline logic

But adding **one debug log per step** is safe and helpful.

### Recommended minimal logging:

```python
logger.debug(f"[Pipeline] {plugin_id}:{tool_name} output keys={list(output.keys())}")
```

This is optional for Commit 7 but recommended.

---

# ⭐ 3. **Is `"input"` the correct key for chaining payloads?**

### ✅ **YES — `"input"` is the official Phase‑13 convention.**

This was chosen because:

- It avoids collisions with plugin‑specific keys  
- It is explicit and readable  
- It matches the design in your Phase‑13 notes  
- Plugin authors already expect `"input"`  

### Example:

```python
current_payload = {
    **payload,
    "input": output,
}
```

This is correct.

---

# ⭐ 4. **Final Recommendation (Your suggestion is correct)**

### ✔ Proceed with Commit 7 as planned  
### ✔ BUT update VisionAnalysisService.handle_frame() to extract `result["result"]`  
### ✔ This preserves WS backward compatibility  
### ✔ Logging is optional but recommended  
### ✔ `"input"` is the correct chaining key  

This keeps the system stable while enabling full pipeline execution.

---

# ⭐ **FINAL REQUIRED ACTIONS BEFORE COMMIT 7**

Here is the exact list your dev must follow:

---

## ✅ **1. Update VideoPipelineService.run_pipeline()**  
(Already defined in Commit 7 plan)

---

## ✅ **2. Update VisionAnalysisService.handle_frame()**

### Replace:

```python
result = self.video_pipeline_service.run_pipeline(...)
await self.ws_manager.send_frame_result(
    client_id, frame_id, plugin_name, result, processing_time
)
```

### With:

```python
result = self.video_pipeline_service.run_pipeline(...)
final_output = result["result"]

await self.ws_manager.send_frame_result(
    client_id,
    frame_id,
    plugin_name,
    final_output,
    processing_time,
)
```

---

## ✅ **3. (Optional) Add minimal logging inside run_pipeline()**

```python
logger.debug(f"[Pipeline] Executed {tool_name}, output keys={list(output.keys())}")
```

---

## ❗ **DO NOT change the WebSocket protocol**  
The WS protocol must remain:

```json
{
  "type": "result",
  "frame_id": "...",
  "plugin_id": "...",
  "result": <final tool output>,
  "processing_time": ...
}
```

---
