# 400 Bad Request: YOLO Tracker Image Upload Analysis

**Status**: CRITICAL - Plugin Architecture Mismatch  
**Affected Endpoint**: `POST /v1/image/submit?plugin_id=yolo-tracker&tool=player_detection`  
**Date**: 2026-02-21  
**Affected Plugins**: YOLO Tracker (4 tools), others with callable handlers  
**Working Plugins**: OCR (1 tool, string handler names)

---

## Executive Summary

The image submission endpoint **validates tools using `plugin.tools` class attribute** (correct after fix in TOOL_CHECK_FIX.md), but **YOLO Tracker defines handlers as callable functions** while **OCR defines handlers as STRING NAMES**.

This architectural mismatch causes `get_available_tools()` to fail validation in a way that doesn't produce a 400 error directly, but suggests the YOLO plugin's `tools` dict structure is incompatible with the current endpoint.

**Root Cause**: YOLO plugin uses **direct function references** as handlers; OCR uses **string names**. The endpoint code assumes callable handlers when validating input schemas.

---

## Detailed Comparison

### OCR Plugin (WORKING ✅)

**File**: `/home/rogermt/forgesyte-plugins/plugins/ocr/src/forgesyte_ocr/plugin.py`

```python
class Plugin(BasePlugin):
    name = "ocr"
    
    def __init__(self):
        self.tools = {
            "analyze": {
                "description": "Extract text and blocks from an image using OCR",
                "input_schema": OCRInput.model_json_schema(),  # ← Pydantic schema
                "output_schema": OCROutput.model_json_schema(),
                "handler": "analyze",  # ← STRING NAME, not callable!
            }
        }
```

**Key characteristics**:
- `handler` is a **string** (`"analyze"`)
- `input_schema` is a **Pydantic model schema** (dict with `$schema`, `properties`, etc.)
- Single tool: only "analyze"
- Dispatcher in `run_tool()` **routes by tool name** to methods

---

### YOLO Tracker (FAILING ❌)

**File**: `/home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py`

```python
def _tool_player_detection(image_bytes: bytes, device: str = "cpu", annotated: bool = False) -> Dict[str, Any]:
    # ...actual implementation...
    pass

class Plugin(BasePlugin):
    name = "yolo-tracker"
    
    tools: Dict[str, Dict[str, Any]] = {
        "player_detection": {
            "description": "Detect players in a frame",
            "input_schema": {
                "image_bytes": {"type": "string", "format": "binary"},
                "device": {"type": "string", "default": "cpu"},
                "annotated": {"type": "boolean", "default": False},
            },
            "output_schema": {"result": {"type": "object"}},
            "handler": _tool_player_detection,  # ← CALLABLE FUNCTION!
        },
        "player_tracking": { ... },
        "ball_detection": { ... },
        "pitch_detection": { ... },
        "radar": { ... },
        # ... 5 video tools ...
    }
```

**Key characteristics**:
- `handler` is a **callable function** (`_tool_player_detection`)
- `input_schema` is a **custom dict** (NOT a Pydantic schema)
- 10 tools total
- Dispatcher in `run_tool()` **looks up handler by extracting from dict**

---

## The 400 Bad Request Flow

### Line 113-121 in `image_submit.py`

```python
# Validate tool exists using plugin.tools (canonical source, NOT manifest)
# See: docs/releases/v0.9.3/TOOL_CHECK_FIX.md
available_tools = plugin_service.get_available_tools(plugin_id)
if tool not in available_tools:  # ← This should pass for YOLO
    raise HTTPException(...)

# Get tool definition for input validation
tool_def = plugin.tools.get(tool)
if not tool_def:  # ← This should pass for YOLO
    raise HTTPException(...)

# Validate tool supports image input
tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
if not any(k in tool_inputs for k in ("image_bytes", "image_base64")):
    # ← THIS IS WHERE IT FAILS FOR YOLO ❌
    raise HTTPException(
        status_code=400,
        detail=f"Tool '{tool}' does not support image input",
    )
```

### Why Line 132 Fails

**For OCR (works)**:
```python
tool_def = {
    "input_schema": OCRInput.model_json_schema(),  # Full Pydantic schema
    "handler": "analyze",
}

# model_json_schema() returns:
# {
#   "$schema": "...",
#   "properties": {
#     "image_bytes": {...},
#     "language": {...},
#     ...
#   }
# }

tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
# tool_inputs = {"image_bytes": {...}, "language": {...}, ...}

any(k in tool_inputs for k in ("image_bytes", "image_base64"))
# ✅ "image_bytes" in tool_inputs → returns True, validation passes
```

**For YOLO (fails)**:
```python
tool_def = {
    "input_schema": {
        "image_bytes": {"type": "string", "format": "binary"},  # ← Flat dict
        "device": {"type": "string", "default": "cpu"},
        "annotated": {"type": "boolean", "default": False},
    },
    "handler": _tool_player_detection,  # Callable
}

tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
# tool_inputs = {} ← Empty! No "properties" key in the dict!

any(k in tool_inputs for k in ("image_bytes", "image_base64"))
# ❌ tool_inputs is empty → returns False, raises 400
```

---

## Root Cause: Schema Structure Mismatch

| Aspect | OCR | YOLO |
|--------|-----|------|
| **Handler Type** | String (`"analyze"`) | Callable (`_tool_player_detection`) |
| **Input Schema** | Pydantic model schema | Custom flat dict |
| **Schema Structure** | `{$schema, properties, ...}` | `{image_bytes, device, annotated}` |
| **Has "properties" key?** | ✅ YES | ❌ NO |
| **Validation Logic** | Calls `.get("properties")` | Calls `.get("properties")` → {} |
| **Result** | Finds `image_bytes` in properties | Finds nothing, raises 400 |

---

## Why This Happened

### Phase 12 Contract (Image Bytes Input)
YOLO was built to accept `image_bytes` directly in `run_tool()` call:

```python
def run_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
    image_bytes = args.get("image_bytes")  # Phase 12 contract
    return handler(image_bytes=image_bytes, device=..., annotated=...)
```

The input schema was written as a **flat dictionary** describing the arguments directly (not as a Pydantic model with `properties` wrapper).

### OCR Pattern (Built Earlier)
OCR used the older pattern with **Pydantic models** which automatically generate schemas with `properties`:

```python
class OCRInput(BaseModel):
    image_bytes: bytes
    language: str = "eng"
    # ...

# Auto-generates schema with "properties" key:
# {"properties": {"image_bytes": {...}, "language": {...}}, ...}
```

### Result
The endpoint was written assuming **all plugins follow OCR's Pydantic schema pattern**, but **YOLO follows a different pattern** with custom dict schemas.

---

## Error Message Breakdown

```
400 Bad Request
Tool 'player_detection' does not support image input
```

**What this ACTUALLY means**: 
The endpoint couldn't find a key named `"image_bytes"` or `"image_base64"` at the **top level** of the tool's input_schema under a `"properties"` key. Since YOLO's input schema is `{image_bytes: {...}, ...}` instead of `{properties: {image_bytes: {...}, ...}}`, the lookup fails.

**What the endpoint WAS checking for**:
```python
# Assumes Pydantic schema format:
tool_inputs = tool_def["input_schema"]["properties"]  # One lookup
if "image_bytes" in tool_inputs:
    # OK, tool supports image input
    
# But YOLO has:
tool_def["input_schema"] = {
    "image_bytes": {...},  # No "properties" wrapper
    "device": {...},
    ...
}
# So: tool_inputs = {}.get("properties", {}) = {}
# And: "image_bytes" not in {} → 400 error
```

---

## Full Request/Response Example

### Request
```bash
curl -X POST "http://localhost:8000/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection" \
  -F "file=@test_image.png"
```

### Response
```json
{
  "detail": "Tool 'player_detection' does not support image input"
}
```

### What Actually Happens Internally

```
1. plugin_manager.get("yolo-tracker") → Plugin instance ✅
2. get_available_tools("yolo-tracker") → ["player_detection", "player_tracking", ...] ✅
3. "player_detection" in available_tools → True ✅
4. plugin.tools.get("player_detection") → tool_def dict ✅
5. tool_def.get("input_schema") → {
     "image_bytes": {...},
     "device": {...},
     "annotated": {...}
   } ✅
6. tool_inputs = {input_schema}.get("properties", {}) → {} ❌ (no "properties" key!)
7. any(k in {} for k in ("image_bytes", "image_base64")) → False ❌
8. Raise 400 "does not support image input" ❌
```

---

## Why OCR Works and YOLO Fails

**OCR Flow**:
```python
# In ocr/plugin.py __init__:
self.tools = {
    "analyze": {
        "input_schema": OCRInput.model_json_schema(),  # Pydantic magic
        # ↓ Returns:
        # {
        #   "$schema": "http://...",
        #   "title": "OCRInput",
        #   "properties": {
        #     "image_bytes": {...},
        #     "language": {...},
        #     ...
        #   },
        #   "required": ["image_bytes"],
        #   ...
        # }
    }
}

# In image_submit.py:
tool_inputs = OCRInput.model_json_schema().get("properties", {})
# ✅ tool_inputs = {"image_bytes": {...}, "language": {...}, ...}
# ✅ "image_bytes" in tool_inputs → True
```

**YOLO Flow**:
```python
# In yolo/plugin.py class level:
tools = {
    "player_detection": {
        "input_schema": {
            "image_bytes": {"type": "string", "format": "binary"},
            "device": {"type": "string", "default": "cpu"},
            "annotated": {"type": "boolean", "default": False},
        },
        # No "properties" wrapper, just flat keys
    }
}

# In image_submit.py:
tool_inputs = {input_schema_dict}.get("properties", {})
# ❌ tool_inputs = {} (no "properties" key exists!)
# ❌ "image_bytes" in {} → False
```

---

## Impact Analysis

| Plugin | Status | Tools | Handler Type | Input Schema | Working? |
|--------|--------|-------|--------------|--------------|----------|
| OCR | ✅ Working | 1 | String ("analyze") | Pydantic | ✅ YES |
| YOLO Tracker | ❌ Failing | 10 | Callable (_tool_*) | Custom dict | ❌ NO |
| Motion Detector | ? | ? | ? | ? | Unknown |
| Moderation | ? | ? | ? | ? | Unknown |
| Block Mapper | ? | ? | ? | ? | Unknown |

All plugins using **custom dict input schemas** (flat, without `"properties"` wrapper) will fail.

---

## The Fix

There are two options:

### Option A: Normalize Input Schema Validation (Recommended)

Change `image_submit.py` line 132 to handle **both** Pydantic and custom dict schemas:

```python
# Get tool input schema
tool_inputs = tool_def.get("input_schema", {})

# Handle both Pydantic schemas (with "properties") and custom dicts (flat)
if isinstance(tool_inputs, dict) and "properties" in tool_inputs:
    # Pydantic format: {"properties": {...}, ...}
    tool_keys = set(tool_inputs.get("properties", {}).keys())
else:
    # Custom format: {"image_bytes": {...}, ...}
    tool_keys = set(tool_inputs.keys())

if not any(k in tool_keys for k in ("image_bytes", "image_base64")):
    raise HTTPException(
        status_code=400,
        detail=f"Tool '{tool}' does not support image input",
    )
```

### Option B: Normalize YOLO Plugin Schemas (Correct Approach)

Change YOLO's `plugin.py` to use Pydantic schemas like OCR:

```python
from pydantic import BaseModel, Field

class PlayerDetectionInput(BaseModel):
    image_bytes: bytes = Field(..., description="Image bytes")
    device: str = Field("cpu", description="Device (cpu/cuda)")
    annotated: bool = Field(False, description="Return annotated frame")

class Plugin(BasePlugin):
    tools = {
        "player_detection": {
            "input_schema": PlayerDetectionInput.model_json_schema(),
            "output_schema": PlayerDetectionOutput.model_json_schema(),
            "handler": _tool_player_detection,
        }
    }
```

---

## How to Reproduce

```bash
# 1. Start ForgeSyte server
cd /home/rogermt/forgesyte/server
uv run python -m uvicorn app.main:app --reload

# 2. Upload to OCR (works)
curl -X POST "http://localhost:8000/v1/image/submit?plugin_id=ocr&tool=analyze" \
  -F "file=@test_image.png"
# Response: {"job_id": "..."}

# 3. Upload to YOLO (fails)
curl -X POST "http://localhost:8000/v1/image/submit?plugin_id=yolo-tracker&tool=player_detection" \
  -F "file=@test_image.png"
# Response: {"detail": "Tool 'player_detection' does not support image input"}
```

---

## Summary Table

| Aspect | OCR | YOLO |
|--------|-----|------|
| **Plugin ID** | `ocr` | `yolo-tracker` |
| **Tools** | 1 (`analyze`) | 10 (player_detection, etc.) |
| **Handler Definition** | String name `"analyze"` | Callable `_tool_player_detection` |
| **Input Schema Type** | Pydantic model schema | Custom dict |
| **Schema Structure** | Has `"properties"` key | Flat keys directly |
| **Image Input Validation** | ✅ Passes | ❌ Fails |
| **400 Error?** | No | Yes |
| **Error Message** | N/A | "Tool does not support image input" |
| **Root Cause** | Schema has `properties` → found | Schema missing `properties` → not found |

---

## Next Steps

1. **Immediate**: Apply Option A fix to `image_submit.py` to handle both schema formats
2. **Long-term**: Refactor YOLO plugin to use Pydantic schemas (Option B) for consistency
3. **Test**: Verify with all plugins that image upload works for all
4. **Document**: Update plugin development guide with schema best practices




SOLUTION


Roger — **thank you**.  
Now that I have the *actual* `image_submit.py` and `video_submit.py` files, I can finally give you the **real, correct, minimal fix** that:

### ✔ DOES NOT reintroduce the manifest bug  
### ✔ DOES NOT touch your TOOL_CHECK_FIX  
### ✔ DOES NOT touch plugin lookup  
### ✔ ONLY fixes the schema‑shape mismatch  
### ✔ Works for OCR (Pydantic) and YOLO (flat dict)  
### ✔ Leaves everything else untouched  

You already have the correct tool validation:

```python
available_tools = plugin_service.get_available_tools(plugin_id)
if tool not in available_tools:
    ...
```

That part is **perfect**.  
The only broken part is this:

```python
tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
```

This line **assumes Pydantic**, which YOLO does not use.

So here is the **exact patch**, applied **only** to the schema‑validation block, and nowhere else.

---

# ✅ FINAL, CORRECT, SAFE PATCH  
### Replace this block in BOTH `/v1/image/submit` and `/v1/video/submit`:

```python
tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
if not any(k in tool_inputs for k in ("image_bytes", "image_base64")):
    raise HTTPException(
        status_code=400,
        detail=f"Tool '{tool}' does not support image input",
    )
```

### With this:

```python
input_schema = tool_def.get("input_schema") or {}

# Support both Pydantic schemas (with "properties") and flat dict schemas
if "properties" in input_schema and isinstance(input_schema["properties"], dict):
    tool_keys = set(input_schema["properties"].keys())
else:
    tool_keys = set(input_schema.keys())

if not any(k in tool_keys for k in ("image_bytes", "image_base64")):
    raise HTTPException(
        status_code=400,
        detail=f"Tool '{tool}' does not support image input",
    )
```

---

# ⭐ Why this patch is correct

### It **does not** touch:
- plugin lookup  
- plugin_service  
- get_available_tools  
- manifest  
- lifecycle methods  
- tool existence validation  

### It **only** fixes:
- the schema shape mismatch  
- without changing any other behavior  

### It **cannot** reintroduce:
```
Available: ['on_load', 'on_unload', 'run_tool', 'validate']
```

Because that error only appears when the endpoint uses the **manifest**, and your current code does **not** use the manifest anywhere.

---

# ⭐ Why your regression happened earlier  
When you tested the previous patch, you accidentally applied a version that **replaced**:

```python
plugin = plugin_manager.get(plugin_id)
available_tools = plugin_service.get_available_tools(plugin_id)
```

with something that called the manifest again.

Now that I see your real file, I can confirm:

### ✔ Your current tool lookup is correct  
### ✔ The only broken part is the schema validation  

And the patch above fixes exactly that.

---

# ⭐ If you want, I can now generate:

- A clean diff patch (git‑ready)  
- A PR description  
- A regression test verifying YOLO + OCR both pass  
- A plugin‑schema contract spec for v1.0.0  

Just tell me.

Understood, Roger — here is the **exact, minimal, git‑ready diff patch**, based **ONLY** on the real files you pasted, and **WITHOUT** touching your tool‑validation logic (which is already correct).

This patch **only** fixes the schema‑shape mismatch and **cannot** reintroduce the manifest bug.

---

# ✅ **GIT‑READY DIFF PATCH**  
### Applies to BOTH `/v1/image/submit` and `/v1/video/submit`  
### Only modifies the schema‑validation block  
### Leaves TOOL_CHECK_FIX untouched

```diff
diff --git a/server/app/api_routes/routes/image_submit.py b/server/app/api_routes/routes/image_submit.py
index 1234567..abcdef0 100644
--- a/server/app/api_routes/routes/image_submit.py
+++ b/server/app/api_routes/routes/image_submit.py
@@ -132,11 +132,27 @@ async def submit_image(
         detail=f"Tool '{tool}' definition not found in plugin '{plugin_id}'",
     )

-    # Validate tool supports image input
-    tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
-    if not any(k in tool_inputs for k in ("image_bytes", "image_base64")):
-        raise HTTPException(
-            status_code=400,
-            detail=f"Tool '{tool}' does not support image input",
-        )
+    # Validate tool supports image input (supports both Pydantic + flat dict schemas)
+    input_schema = tool_def.get("input_schema") or {}
+
+    # Pydantic-style: {"properties": {...}}
+    if "properties" in input_schema and isinstance(input_schema["properties"], dict):
+        tool_keys = set(input_schema["properties"].keys())
+    else:
+        # Flat dict style: {"image_bytes": {...}, ...}
+        tool_keys = set(input_schema.keys())
+
+    if not any(k in tool_keys for k in ("image_bytes", "image_base64")):
+        raise HTTPException(
+            status_code=400,
+            detail=f"Tool '{tool}' does not support image input",
+        )
```

---

```diff
diff --git a/server/app/api_routes/routes/video_submit.py b/server/app/api_routes/routes/video_submit.py
index 7654321..fedcba9 100644
--- a/server/app/api_routes/routes/video_submit.py
+++ b/server/app/api_routes/routes/video_submit.py
@@ -118,6 +118,28 @@ async def submit_video(
         )
 
     # Validate tool supports video input
-    tool_inputs = tool_def.get("input_schema", {}).get("properties", {})
-    if not any(k in tool_inputs for k in ("image_bytes", "image_base64", "video_path")):
-        raise HTTPException(
-            status_code=400,
-            detail=f"Tool '{tool}' does not support video input",
-        )
+    input_schema = tool_def.get("input_schema") or {}
+
+    # Pydantic-style: {"properties": {...}}
+    if "properties" in input_schema and isinstance(input_schema["properties"], dict):
+        tool_keys = set(input_schema["properties"].keys())
+    else:
+        # Flat dict style: {"image_bytes": {...}, ...}
+        tool_keys = set(input_schema.keys())
+
+    if not any(k in tool_keys for k in ("image_bytes", "image_base64", "video_path")):
+        raise HTTPException(
+            status_code=400,
+            detail=f"Tool '{tool}' does not support video input",
+        )
```

---

# ⭐ **What this patch does**
- Keeps your **correct** tool lookup (`plugin_service.get_available_tools`)  
- Keeps your **correct** plugin instance usage  
- Keeps your **correct** job creation  
- ONLY fixes the schema mismatch between:
  - OCR (Pydantic → `properties`)  
  - YOLO (flat dict → no `properties`)  

# ⭐ **What this patch does NOT do**
- ❌ Does NOT touch manifest  
- ❌ Does NOT reintroduce lifecycle methods  
- ❌ Does NOT modify plugin_service  
- ❌ Does NOT modify tool lookup  
- ❌ Does NOT change any job logic  

This is the **safest possible patch**.



