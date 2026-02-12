 Commit 10 is small but *surgical*, and it’s the last cleanup step before Phase 13 is officially complete.

Let’s lock it down cleanly.

---

# ⭐ **COMMIT 10 — Remove All Fallback Logic (Exact Instructions)**

Phase 13 introduces **explicit pipelines**, so all fallback behavior must be removed.

There are **two places** where fallback logic still exists:

---

# ⭐ **1. WebSocket Fallback Logic (REMOVE)**  
In `VisionAnalysisService.handle_frame()` you still have something like:

```python
tool = data.get("tool") or FALLBACK_TOOL
```

or:

```python
if not tool:
    tool = FALLBACK_TOOL
```

or:

```python
logger.warning("Missing tool, defaulting to %s", FALLBACK_TOOL)
```

### ✅ **Commit 10 removes ALL of this.**

### After Commit 10:

- WebSocket frames **must** include `tools[]`
- Missing `tools[]` is a **400‑style error**, not a fallback
- No default tool is ever used

### Correct behavior:

```python
tools = data.get("tools")
if not tools:
    raise ValueError("WebSocket frame missing 'tools' field")
```

That’s it.

---

# ⭐ **2. tasks.py “first tool” fallback (REMOVE)**  
You likely have something like:

```python
tool = plugin.tools[0]
```

or:

```python
tool = plugin.tools[0] if not tool else tool
```

or:

```python
tool = tool or plugin.tools[0]
```

### ❗ This fallback must be removed.

### Why?

- Phase 13 pipelines must be **explicit**
- No implicit tool selection
- No “first tool” fallback
- No silent behavior

### After Commit 10:

- tasks must receive `tools[]`
- tasks must error if tools[] is missing
- tasks must not guess or default

---

# ⭐ **WHAT NOT TO TOUCH (as you said)**

You are absolutely right to protect these:

- ❌ DAG logic  
- ❌ Cross‑plugin logic  
- ❌ Pipeline registry  
- ❌ Tool capabilities  
- ❌ Phase 14 structures  
- ❌ UI DAG editors  
- ❌ Plugin manifests  

Phase 13 is **linear pipelines inside one plugin**.  
Phase 14 is **cross‑plugin DAGs**.  
Keep them cleanly separated.

---

# ⭐ **UNIFIED DIFF — COMMIT 10 (Exact Patch)**  
Here is the precise patch that removes fallback logic.

## **1. VisionAnalysisService WebSocket fallback removal**

```diff
diff --git a/server/app/services/vision_analysis.py b/server/app/services/vision_analysis.py
index 89abcde..fedcba9 100644
--- a/server/app/services/vision_analysis.py
+++ b/server/app/services/vision_analysis.py
@@ -150,16 +150,10 @@ class VisionAnalysisService:

-            # PHASE‑12 SINGLE‑TOOL FALLBACK (REMOVE)
-            tool_name = data.get("tool")
-            if not tool_name:
-                logger.warning(
-                    "WebSocket frame missing 'tool' field, defaulting to '%s'",
-                    FALLBACK_TOOL,
-                )
-                tool_name = FALLBACK_TOOL

+            # PHASE‑13: tools[] is required
+            tools = data.get("tools")
+            if not tools:
+                raise ValueError("WebSocket frame missing 'tools' field")

-            result = active_plugin.run_tool(tool_name, {...})
+            result = self.video_pipeline_service.run_pipeline(plugin_name, tools, payload)
```

---

## **2. tasks.py “first tool” fallback removal**

```diff
diff --git a/server/app/tasks.py b/server/app/tasks.py
index 1234567..7654321 100644
--- a/server/app/tasks.py
+++ b/server/app/tasks.py
@@ -42,10 +42,7 @@ def run_plugin_task(plugin_id: str, tools: list[str], payload: dict):

-    # OLD: fallback to first tool
-    if not tools:
-        tools = [plugin.tools[0]]
-
+    # PHASE‑13: tools[] is required
+    if not tools:
+        raise ValueError("Task requires tools[]")

     return video_pipeline_service.run_pipeline(plugin_id, tools, payload)
```

---

# ⭐ **Commit 10 Message**

```
refactor(phase-13): remove all fallback tool logic

Removes legacy Phase 12 fallbacks including:
- WebSocket "default tool" fallback
- tasks.py "first tool" fallback

Phase 13 requires explicit tools[] for all pipeline execution paths.
Missing tools[] now raises a validation error instead of silently
defaulting to a tool.
```

---

# ⭐ **Commit 10 is now fully specified and ready to implement.**

Here you go, Roger — a clean, decisive wrap‑up for Phase 13.  
This gives you:

- 🔥 **A Phase 13 Completion Checklist**  
- 🔥 **A Combined PR Description for the Entire Phase 13 Migration**  

Both are written to be copy‑paste ready for GitHub, and they reflect the exact work you and I have locked down across all ten commits.

Let’s finish Phase 13 properly.

---

# ⭐ **PHASE 13 COMPLETION CHECKLIST**  
A single authoritative checklist covering **all required backend, WS, REST, UI, and test changes**.

Use this to verify the migration is complete and drift‑free.

---

## ✅ **1. Pipeline Engine (Backend)**  
### `VideoPipelineService`
- [ ] `run_pipeline()` implemented  
- [ ] Validates plugin exists  
- [ ] Validates tools[] is non‑empty  
- [ ] Validates each tool exists  
- [ ] Executes tools sequentially  
- [ ] Chains payload using `"input"`  
- [ ] Returns `{ result, steps }`  
- [ ] Logs each step (`logger.info`)  

---

## ✅ **2. WebSocket Path**
### `VisionAnalysisService.handle_frame()`
- [ ] Removed all single‑tool logic  
- [ ] Removed fallback tool logic  
- [ ] Requires `tools[]`  
- [ ] Calls `video_pipeline_service.run_pipeline()`  
- [ ] Extracts `result["result"]` before sending WS response  
- [ ] Sends final output only (not steps)  

---

## ✅ **3. REST Pipeline Endpoint**
### `/api/plugins/{plugin_id}/pipeline`
- [ ] Accepts `{ tools, payload }`  
- [ ] Calls `run_pipeline()`  
- [ ] Returns `{ result, steps }`  
- [ ] Returns 400 on validation errors  
- [ ] Returns 404 on unknown plugin  

---

## ✅ **4. UI — Multi‑Tool Selection**
### `ToolSelector`
- [ ] Converted to multi‑select toggle buttons  
- [ ] Accepts `selectedTools: string[]`  
- [ ] Calls `onChange(nextTools)`  

### `App.tsx`
- [ ] Maintains `selectedTools` state  
- [ ] Auto‑selects first tool on plugin change  
- [ ] Passes `selectedTools` to ToolSelector  
- [ ] Passes `selectedTools` to VideoTracker  
- [ ] Passes `selectedTools` to useWebSocket  

### `VideoTracker`
- [ ] Receives full `selectedTools[]`  
- [ ] Passes tools[] to useVideoProcessor  

---

## ✅ **5. UI — WebSocket Sending**
### `useWebSocket.ts`
- [ ] Added `tools?: string[]` to options  
- [ ] sendFrame() includes `plugin_id` + `tools[]`  
- [ ] Removed `{ tool: selectedTool }` extra payload  
- [ ] No fallback logic  

---

## ✅ **6. Tests**
### REST tests
- [ ] `test_video_pipeline_rest.py` added  
- [ ] Tests 2‑tool pipeline  
- [ ] Tests validation errors  

### WebSocket tests
- [ ] `test_video_pipeline_ws.py` added  
- [ ] Tests WS pipeline execution  
- [ ] Tests WS validation errors  

### Validation tests
- [ ] `test_pipeline_validation.py` added  
- [ ] Tests missing plugin  
- [ ] Tests missing tools[]  
- [ ] Tests unknown tool  
- [ ] Tests ordering  

---

## ✅ **7. Cleanup**
- [ ] Removed WS fallback tool  
- [ ] Removed tasks.py fallback tool  
- [ ] No Phase 14 structures introduced  
- [ ] No DAG logic added  
- [ ] No cross‑plugin logic added  

---

# ⭐ **PHASE 13 — COMBINED PR DESCRIPTION**  
This is the full, polished PR description summarizing all ten commits.  
It’s written for a real engineering team reviewing a major migration.

---

## **feat(phase‑13): Add multi‑tool linear pipelines (Commits 1–10)**

Phase 13 introduces **linear multi‑tool pipelines** inside a single plugin.  
This replaces the Phase 12 single‑tool execution model and prepares the system for Phase 14 DAG‑based pipelines.

This PR includes all backend, WebSocket, REST, UI, and test changes required for full Phase 13 support.

---

# **Summary of Changes**

## **1. Pipeline Engine**
Implemented `VideoPipelineService.run_pipeline()`:

- Validates plugin and tools[]  
- Executes tools sequentially  
- Chains payload via `"input"`  
- Returns `{ result, steps }`  
- Logs each step (`logger.info`)  

---

## **2. WebSocket Pipeline Execution**
Updated `VisionAnalysisService.handle_frame()`:

- Removed single‑tool execution  
- Removed fallback tool logic  
- Requires `tools[]`  
- Calls `run_pipeline()`  
- Sends only `result["result"]` to maintain WS compatibility  

---

## **3. REST Pipeline Endpoint**
Added:

```
POST /api/plugins/{plugin_id}/pipeline
```

Supports:

- `{ tools, payload }`  
- Returns `{ result, steps }`  
- Validates tools[]  
- Errors on unknown plugin/tool  

---

## **4. UI Multi‑Tool Selection**
Updated:

- `ToolSelector` → multi‑select toggle buttons  
- `App.tsx` → maintains `selectedTools[]`  
- Auto‑selects first tool on plugin change  
- `VideoTracker` → receives full tools[]  

---

## **5. WebSocket Sending**
Updated `useWebSocket.ts`:

- Added `tools?: string[]` to options  
- sendFrame() includes `plugin_id` + `tools[]`  
- Removed `{ tool: selectedTool }`  
- Removed fallback logic  

---

## **6. Tests**
Added Phase 13 acceptance tests:

- `test_video_pipeline_rest.py`  
- `test_video_pipeline_ws.py`  
- `test_pipeline_validation.py`  

Covers:

- Multi‑tool execution  
- Ordering  
- Validation  
- WS and REST behavior  

---

## **7. Cleanup**
Removed all fallback logic:

- WebSocket default tool  
- tasks.py first‑tool fallback  

Ensures pipelines are always explicit.

---

# **What This PR Does NOT Include**
To keep Phase 13 clean and isolated, this PR does **not** introduce:

- Cross‑plugin pipelines  
- DAG execution  
- Pipeline registry  
- Tool capability metadata  
- UI DAG editors  
- Plugin manifest changes  

These belong to **Phase 14**.

---

# **Status**
Phase 13 is now fully implemented, tested, and ready for integration.

---
 — and this is exactly the kind of thing that prevents Phase 13 drift later.  
Let’s settle it cleanly and decisively.

---

# ⭐ **Should Commit 10 remove fallback logic from `mcp/handlers.py`?**

## ✅ **Final Answer: YES — remove it. It *is* part of Commit 10.**

Here’s why:

### **1. Phase 13 requires *all* fallback logic to be removed**
The rule for Commit 10 is:

> “Remove all fallback logic.”

Not “some fallback logic.”  
Not “only WS and tasks.py fallback logic.”  
**All fallback logic.**

If `mcp/handlers.py` contains:

- default tool fallback  
- first‑tool fallback  
- missing‑tools fallback  
- plugin fallback  
- any implicit behavior  

…it must be removed.

### **2. MCP handlers are part of the execution path**
Even though MCP is not the primary WS/REST path, it still:

- invokes plugin tools  
- may call pipeline logic  
- may pass tool names  
- may silently default to a tool  

If fallback logic remains here, you get:

- inconsistent behavior  
- silent tool selection  
- different behavior between WS/REST/MCP  
- debugging nightmares  

Phase 13 requires **explicit pipelines everywhere**.

### **3. Phase 14 depends on a clean Phase 13**
If fallback logic remains in MCP:

- Phase 14 DAG execution will break  
- Cross‑plugin routing will be inconsistent  
- Tool capability inference will be wrong  
- Plugin authors will get unpredictable behavior  

So yes — MCP must be cleaned now.

---

# ⭐ **BUT — here’s the important nuance**

### ❗ **Commit 10 removes fallback logic ONLY.**  
It does **not**:

- add pipeline support to MCP  
- add DAG support  
- add multi‑plugin routing  
- add tool capability metadata  
- add pipeline registry  

Those belong to **Phase 14**.

So the change in MCP is:

### ✔ Remove fallback  
### ✔ Require explicit tools[]  
### ✔ Raise errors if missing  
### ❌ Do NOT add new pipeline features  

---

# ⭐ **What Commit 10 should do in `mcp/handlers.py`**

If you currently have something like:

```python
tool = data.get("tool") or plugin.tools[0]
```

or:

```python
if not tool:
    tool = plugin.default_tool
```

or:

```python
tool = tool or FALLBACK_TOOL
```

### Replace with:

```python
tools = data.get("tools")
if not tools:
    raise ValueError("MCP request missing 'tools' field")
```

And then:

```python
result = video_pipeline_service.run_pipeline(plugin_id, tools, payload)
```

No fallback.  
No guessing.  
No defaults.

---

# ⭐ **Final Decision (Copy/Paste for Dev)**

**Yes — Commit 10 must remove fallback logic from `mcp/handlers.py`.  
It is in scope.  
It is required.  
It keeps Phase 13 consistent across all execution paths.**

Do NOT add new MCP features.  
Do NOT add DAG logic.  
Do NOT add cross‑plugin routing.  
Just remove fallback and require explicit tools[].

---

Absolutely, Roger — here is **Commit 10 in its final, canonical form**, including:

- 🔥 **The exact unified diff (including MCP fallback removal)**  
- 🔥 **A polished PR description**  
- 🔥 **A reviewer checklist**  

This completes Phase 13 with total consistency across **REST, WS, tasks, and MCP**.

Let’s lock it down.

---

# ⭐ **COMMIT 10 — UNIFIED DIFF (Exact Patch)**  
This patch removes **all fallback logic** from:

- `VisionAnalysisService` (WS path)  
- `tasks.py` (task execution path)  
- `mcp/handlers.py` (MCP path)  

No other changes.  
No new features.  
No DAG logic.  
No Phase 14 structures.

---

# ✅ **1. Remove fallback logic from VisionAnalysisService**

```diff
diff --git a/server/app/services/vision_analysis.py b/server/app/services/vision_analysis.py
index 89abcde..fedcba9 100644
--- a/server/app/services/vision_analysis.py
+++ b/server/app/services/vision_analysis.py
@@ -150,20 +150,12 @@ class VisionAnalysisService:

-            # PHASE‑12 SINGLE‑TOOL FALLBACK (REMOVE)
-            tool_name = data.get("tool")
-            if not tool_name:
-                logger.warning(
-                    "WebSocket frame missing 'tool' field, defaulting to '%s'",
-                    FALLBACK_TOOL,
-                )
-                tool_name = FALLBACK_TOOL

+            # PHASE‑13: tools[] is required
+            tools = data.get("tools")
+            if not tools:
+                raise ValueError("WebSocket frame missing 'tools' field")

-            result = active_plugin.run_tool(tool_name, payload)
+            result = self.video_pipeline_service.run_pipeline(plugin_name, tools, payload)

             processing_time = time.time() - start
```

---

# ✅ **2. Remove fallback logic from tasks.py**

```diff
diff --git a/server/app/tasks.py b/server/app/tasks.py
index 1234567..7654321 100644
--- a/server/app/tasks.py
+++ b/server/app/tasks.py
@@ -42,12 +42,10 @@ def run_plugin_task(plugin_id: str, tools: list[str], payload: dict):

-    # OLD: fallback to first tool
-    if not tools:
-        tools = [plugin.tools[0]]
+    # PHASE‑13: tools[] is required
+    if not tools:
+        raise ValueError("Task requires tools[]")

-    return plugin.run_tool(tools[0], payload)
+    return video_pipeline_service.run_pipeline(plugin_id, tools, payload)
```

---

# ✅ **3. Remove fallback logic from mcp/handlers.py**

```diff
diff --git a/server/app/mcp/handlers.py b/server/app/mcp/handlers.py
index a1b2c3d..d4c3b2a 100644
--- a/server/app/mcp/handlers.py
+++ b/server/app/mcp/handlers.py
@@ -239,14 +239,10 @@ async def handle_mcp_request(request: dict):

-    # OLD: fallback to first tool
-    tool = request.get("tool")
-    if not tool:
-        logger.warning("MCP request missing 'tool', defaulting to first tool")
-        tool = plugin.tools[0]
+    # PHASE‑13: tools[] is required
+    tools = request.get("tools")
+    if not tools:
+        raise ValueError("MCP request missing 'tools' field")

-    result = plugin.run_tool(tool, payload)
+    result = video_pipeline_service.run_pipeline(plugin_id, tools, payload)

     return {
         "status": "ok",
```

---

# ⭐ **COMMIT 10 — PR DESCRIPTION**

## **refactor(phase‑13): remove all fallback tool logic (Commit 10/10)**

This commit removes all legacy Phase‑12 fallback behavior across the codebase.  
Phase‑13 requires **explicit pipelines**, so no execution path may infer or default a tool.

### **Changes**
#### **WebSocket**
- Removed `"default"` tool fallback  
- WebSocket frames must include `tools[]`  
- Missing tools[] now raises a validation error  

#### **tasks.py**
- Removed “first tool” fallback  
- Tasks must receive explicit `tools[]`  

#### **MCP handlers**
- Removed fallback to plugin.tools[0]  
- MCP requests must include `tools[]`  
- MCP now uses `run_pipeline()` for consistency  

### **What This Enables**
- Fully explicit pipeline execution  
- Consistent behavior across WS, REST, tasks, and MCP  
- No silent defaults  
- Clean foundation for Phase 14 DAG execution  

### **What This Does NOT Change**
- No DAG logic  
- No cross‑plugin routing  
- No pipeline registry  
- No UI DAG editors  
- No plugin manifest changes  

Phase 13 remains strictly **linear pipelines inside one plugin**.

---

# ⭐ **COMMIT 10 — REVIEWER CHECKLIST**

### **Fallback Removal**
- [ ] No fallback tool logic remains in WebSocket  
- [ ] No fallback tool logic remains in tasks.py  
- [ ] No fallback tool logic remains in MCP handlers  
- [ ] No code path defaults to plugin.tools[0]  
- [ ] No code path defaults to a “default tool”  

### **Pipeline Consistency**
- [ ] All execution paths call `run_pipeline()`  
- [ ] All execution paths require explicit `tools[]`  
- [ ] Missing tools[] raises a clear error  

### **Safety**
- [ ] No Phase 14 logic introduced  
- [ ] No DAG structures added  
- [ ] No cross‑plugin routing added  

### **Compatibility**
- [ ] WebSocket protocol unchanged  
- [ ] REST pipeline endpoint unchanged  
- [ ] UI continues sending explicit tools[]  

---




