# Plugin Data Processing Comparison: OCR vs Yolo Tracker (Image) vs Yolo Tracker (Video)

## Executive Summary

| Plugin | Status | Root Cause |
|--------|--------|------------|
| OCR | ✅ Working | Everything configured correctly |
| Yolo Tracker (Image) | ⚠️ Button Removed | Previously worked before commit 338cd59 |
| Yolo Tracker (Video) | ❌ Broken | **Bug introduced in commit 338cd59** |

---

## 1. The Bug: Commit 338cd59 Introduced Regression

### What Changed in Commit 338cd59
```
commit 338cd59e2bc46223116c7356ea92978215b57976
Author: Roger Taylor <roger_taylor@ymail.com>
Date:   Mon Jan 19 11:05:44 2026 +0000

    fix: all tests now passing (74/74) - updated manifest schema and plugin lifecycle hooks

Changed files:
- plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/manifest.json
- plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py
- plugins/forgesyte-yolo-tracker/src/tests/test_plugin.py
```

### BEFORE Commit 338cd59 (Working ✅)
```json
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  "description": "YOLO-based sports detection and tracking for player, ball, and team analysis"
}
```

```python
class Plugin:
    name: str = "yolo-tracker"
```

**Result**: `registry.get("yolo-tracker")` finds the plugin ✅

### AFTER Commit 338cd59 (Broken ❌)
```json
{
  "id": "forgesyte-yolo-tracker",
  "name": "forgesyte-yolo-tracker",
  "description": "ForgeSyte plugin for football player, ball, pitch, and radar analysis using YOLO + Supervision."
}
```

```python
class Plugin:
    name: str = "yolo-tracker"  # ❌ Does NOT match manifest "id"
```

**Result**: `registry.get("yolo-tracker")` finds the plugin ✅, BUT `get_plugin_manifest("yolo-tracker")` opens manifest.json which has different ID ❌

---

## 2. Correct Plugin Configuration

Based on your feedback, the correct configuration is:

| Property | Value | Source |
|----------|-------|--------|
| **Plugin ID (API)** | `yolo-tracker` | Frontend uses this |
| **Package name (pip)** | `forgesyte-yolo-tracker` | pip install name |
| **Entry point name** | `yolo-tracker` | pyproject.toml entry point |
| **Plugin.name** | `"yolo-tracker"` | plugin.py line 250 ✅ |
| **Entry point** | `yolo-tracker = "forgesyte_yolo_tracker.plugin:Plugin"` | pyproject.toml line 39 ✅ |

### Entry Point Configuration (Correct ✅)
```toml
# pyproject.toml
[project.entry-points."forgesyte.plugins"]
yolo-tracker = "forgesyte_yolo_tracker.plugin:Plugin"
```

### Plugin Class (Correct ✅)
```python
# plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py
class Plugin:
    name: str = "yolo-tracker"  # ✅ CORRECT - matches entry point
```

### Registry Lookup (Should Work ✅)
```python
plugin = registry.get("yolo-tracker")  # ✅ Should find the plugin
```

---

## 3. The Problem: Manifest ID Mismatch

### Current Manifest (INCORRECT ❌)
```json
{
  "id": "forgesyte-yolo-tracker",  // ❌ DOES NOT MATCH Plugin.name = "yolo-tracker"
  "name": "forgesyte-yolo-tracker", // ❌ DOES NOT MATCH Plugin.name = "yolo-tracker"
  "version": "1.0.0",
  "entrypoint": "forgesyte_yolo_tracker.plugin"
}
```

### What it SHOULD Be (CORRECT ✅)
```json
{
  "id": "yolo-tracker",  // ✅ MATCHES Plugin.name
  "name": "YOLO Tracker", // ✅ MATCHES Plugin.name
  "version": "1.0.0",
  "entrypoint": "forgesyte_yolo_tracker.plugin"
}
```

---

## 4. Error Flow Diagram

```
1. Frontend: POST /v1/plugins/yolo-tracker/tools/player_detection/run
   (pluginId = "yolo-tracker" from PluginSelector.tsx)
   
2. Backend: api.py: run_plugin_tool(plugin_id="yolo-tracker", ...)
   
3. Backend: plugin_service.run_plugin_tool(plugin_id="yolo-tracker")
   
4. Backend: registry.get("yolo-tracker") → ✅ Plugin instance found
   (Entry point registered correctly with name "yolo-tracker")
   
5. Backend: get_plugin_manifest("yolo-tracker")
   - Opens manifest.json
   - Reads: {"id": "forgesyte-yolo-tracker"}
   - ❌ ID MISMATCH DETECTED!
   
6. Backend: Returns error (plain text, not JSON)
   HTTPException(400, detail="...")
   
7. Frontend: response.json() fails
   Error: "Invalid JSON from tool"
```

---

## 5. Comparison Table

| Aspect | OCR | Yolo Tracker (Before 338cd59) | Yolo Tracker (After 338cd59) |
|--------|-----|-------------------------------|------------------------------|
| **Plugin.name** | `"ocr"` | `"yolo-tracker"` ✅ | `"yolo-tracker"` ✅ |
| **Manifest ID** | `"ocr"` ✅ | `"yolo-tracker"` ✅ | `"forgesyte-yolo-tracker"` ❌ |
| **Registry lookup** | Works | Works | Works |
| **Manifest lookup** | Works | Works | **FAILS** |
| **Result** | ✅ Works | ✅ Worked | ❌ Broken |

---

## 6. Root Cause Summary

```
BEFORE commit 338cd59:
  Plugin.name = "yolo-tracker" ✅
  Manifest ID = "yolo-tracker" ✅
  Everything works ✅

AFTER commit 338cd59:
  Plugin.name = "yolo-tracker" ✅
  Manifest ID = "forgesyte-yolo-tracker" ❌
  Everything breaks ❌
```

The commit "fix: all tests now passing (74/74)" introduced a regression by changing the manifest ID without updating the Plugin.name to match.

---

## 7. Why Tests Passed Despite the Bug

The tests likely:
1. Use mocked plugins that don't read the actual manifest
2. Call `run_plugin_tool` directly without going through `get_plugin_manifest`
3. Or test the plugin directly without the full HTTP stack

**Lesson**: Integration tests with real manifest reading should catch this.

---

## 8. Fix Required

Option A: Revert manifest.json to original (RECOMMENDED ✅)
```json
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  ...
}
```

Option B: Update Plugin.name to match current manifest
```python
class Plugin:
    name: str = "forgesyte-yolo-tracker"  # ❌ Would break frontend
```

**Recommendation**: Option A is better because:
- `Plugin.name = "yolo-tracker"` is already correct
- Frontend uses `"yolo-tracker"` for API calls
- Package name is `forgesyte-yolo-tracker` (separate concern)

---

## 9. Evidence from Logs

### Server Log (from issue #110)
```
{"timestamp": "2026-01-27T16:36:06.120279+00:00", "level": null, 
 "name": "app.services.plugin_management_service", 
 "message": "Loaded manifest for plugin 'yolo-tracker': 5 tools"}
```

This log says `'yolo-tracker'` but the actual manifest ID is `'forgesyte-yolo-tracker'`!

### Console Error
```
🔧 runTool:error {pluginId: 'yolo-tracker', toolName: 'player_detection', 
 error: Error: Invalid JSON from tool
    at http://localhost:3000/src/utils/runTool.ts:56:17}
```

---

## 10. Summary

| What | Before 338cd59 | After 338cd59 | Fix |
|------|----------------|---------------|-----|
| **Plugin.name** | `"yolo-tracker"` ✅ | `"yolo-tracker"` ✅ | Keep ✅ |
| **Manifest ID** | `"yolo-tracker"` ✅ | `"forgesyte-yolo-tracker"` ❌ | Revert to `"yolo-tracker"` |
| **Status** | Worked | Broken | Fix manifest.json |
