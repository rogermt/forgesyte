# Issue: selectedTool not wired through WebSocket/task execution paths

## Problem

When streaming via WebSocket or running background tasks, the server always executes `player_detection` regardless of which tool the user selects in the UI. The REST API path (`/plugins/{id}/tools/{tool}/run`) works correctly.

## Root Cause

`selectedTool` state exists in `App.tsx` but is never passed into the WebSocket frame payload. The server falls back to a default tool when none is provided.

## Affected Paths

| Path | File | Behavior |
|------|------|----------|
| WebSocket streaming | `useWebSocket.ts` → `vision_analysis.py` | Tool defaults to `"default"` |
| Background tasks | `tasks.py` | Tool defaults to first in `plugin.tools` |
| REST API (VideoTracker) | `runTool.ts` → `api.py` | **Works correctly** — tool in URL path |

---

## Task List

### Task 1: Wire `selectedTool` into `sendFrame()` in App.tsx

**File:** `web-ui/src/App.tsx` (lines 138-144)

**Current:**
```ts
sendFrame(imageData);
```

**Fix:**
```ts
sendFrame(imageData, undefined, { tool: selectedTool });
```

**Note:** `sendFrame` already accepts `(imageData, frameId?, extra?)` and spreads `extra` into the JSON payload via `...(extra ?? {})`. No changes needed in `useWebSocket.ts`.

**Add `selectedTool` to the `useCallback` dependency array.**

---

### Task 2: Add warning log in `vision_analysis.py` when tool is missing

**File:** `server/app/services/vision_analysis.py` (line 109)

**Current:**
```python
tool_name = data.get("tool", "default")
```

**Fix:**
```python
tool_name = data.get("tool")
if not tool_name:
    logger.warning("WebSocket frame missing 'tool' field, defaulting to 'default'")
    tool_name = "default"
```

**Keep backward compatibility** — don't raise ValueError. Just warn so it's visible in logs.

---

### Task 3: Add warning log in `tasks.py` when tool is missing

**File:** `server/app/tasks.py` (lines 399-405)

**Current:**
```python
tool_name = options.get("tool")
if not tool_name:
    if isinstance(plugin.tools, dict):
        tool_name = next(iter(plugin.tools.keys()))
    else:
        tool_name = plugin.tools[0]["name"]
```

**Fix:** Add a warning before the fallback:
```python
tool_name = options.get("tool")
if not tool_name:
    if isinstance(plugin.tools, dict):
        tool_name = next(iter(plugin.tools.keys()))
    else:
        tool_name = plugin.tools[0]["name"]
    logger.warning(
        "Background task missing 'tool' option, defaulting to '%s'",
        tool_name,
    )
```

**Keep backward compatibility** — don't raise ValueError.

---

### Task 4: Upgrade log level in `plugin_management_service.py`

**File:** `server/app/services/plugin_management_service.py` (line 338)

**Current:**
```python
logger.debug(f"Found tool: {plugin}.{tool_name}")
```

**Fix:**
```python
logger.info(
    "Executing plugin tool",
    extra={"plugin_id": plugin_id, "tool_name": tool_name},
)
```

This gives ground truth in logs to confirm routing.

---

### Task 5: Write tests

**5a. Web-UI test** — Verify `sendFrame` receives tool in extra payload

**File:** `web-ui/src/App.tdd.test.tsx` or new test file

- Mock `useWebSocket` and capture `sendFrame` calls
- Select a non-default tool
- Trigger `handleFrame`
- Assert `sendFrame` was called with `(imageData, undefined, { tool: "ball_detection" })`

**5b. Server test** — Verify `vision_analysis.py` uses tool from frame data

- Send frame with `{"tool": "ball_detection", ...}`
- Assert `plugin.run_tool` called with `"ball_detection"`

**5c. Server test** — Verify `tasks.py` logs warning on missing tool

- Call task processor without `"tool"` in options
- Assert warning logged and first tool used as fallback

---

### Task 6: Run verification suite

```bash
# Web-UI
cd web-ui
npm run lint
npm run type-check        # MANDATORY
npm run test -- --run

# Server
cd server
uv run pytest tests/ -v --tb=short

# Pre-commit
cd /home/rogermt/forgesyte
uv run pre-commit run --all-files
```

---

## Files Changed (summary)

| File | Change |
|------|--------|
| `web-ui/src/App.tsx` | Pass `{ tool: selectedTool }` as extra to `sendFrame()` |
| `server/app/services/vision_analysis.py` | Warn when tool missing from WebSocket frame |
| `server/app/tasks.py` | Warn when tool missing from background task options |
| `server/app/services/plugin_management_service.py` | Upgrade log to `info` level with structured fields |

## Files NOT changed

| File | Reason |
|------|--------|
| `web-ui/src/hooks/useWebSocket.ts` | Already supports `extra` param — spreads into payload |
| `server/app/api.py` | REST path already works — tool is a URL path param |
| Any scripts | Not involved in tool routing |
