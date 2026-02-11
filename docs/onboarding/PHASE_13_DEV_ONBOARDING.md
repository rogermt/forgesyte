# Developer Onboarding — Phase 13
## VideoTracker Multi‑Tool Pipelines

Welcome to Phase 13.  
This guide explains how to work on Phase 13 features.

---

## What You Need to Know First

**You should already be familiar with:**
- ForgeSyte architecture (see ARCHITECTURE.md)
- Web-UI development (React + TypeScript)
- Server development (Python + FastAPI)
- Plugin system (see PLUGIN_DEVELOPMENT.md)
- Phase 12 completion (tool selection, device selection)

If not, read those docs first.

---

## What Phase 13 Introduces

VideoTracker now supports **ordered pipelines of tools** inside a single plugin.

### Example Pipeline

```
Input Image
    ↓
[detect_players] → Player bounding boxes
    ↓
[track_players] → Player tracks
    ↓
[annotate_frames] → Annotated image
    ↓
Output
```

Each tool:
- Receives a **dict payload** from the previous tool
- Returns a **dict payload** to the next tool
- Runs inside the **same plugin**
- Is **logged** at each step

### Key Differences from Phase 12

| Feature | Phase 12 | Phase 13 |
|---------|----------|----------|
| Tool selection | Single tool | Multiple tools (ordered) |
| UI selector | Dropdown | Multi-select checkboxes |
| Data flow | Frame → Single tool | Frame → T1 → T2 → T3 |
| Tool inputs | Image bytes | Dict payload |
| Tool outputs | Result dict | Dict payload |
| Logging | One log per tool | One log per step |

---

## How Pipelines Work

### REST Endpoint

User uploads frame via UI:

```
POST /video/pipeline
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "payload": {
    "frame": "base64_encoded_image",
    "confidence": 0.25
  }
}
```

Server:
1. Validates pipeline (`detect_players` and `track_players` exist in `forgesyte-yolo-tracker`)
2. Runs `detect_players` with payload
3. Passes result to `track_players`
4. Returns final output

Response:

```json
{
  "step": 1,
  "tool": "track_players",
  "result": {
    "detections": [...],
    "tracks": [...]
  }
}
```

### WebSocket Endpoint

User streams frames via WebSocket:

```
Each frame:
{
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"],
  "image_data": "base64_encoded_frame"
}
```

Server:
1. Validates pipeline
2. Builds initial payload: `{ "frame": image_data, "confidence": 0.25 }`
3. Runs pipeline
4. Sends annotated frame to UI

---

## Your First Phase 13 Task

### Setup

1. Clone latest main: `git pull origin main`
2. Read this doc completely
3. Read PHASE_13_FOLDER_STRUCTURE.md
4. Read PHASE_13_PR_TEMPLATE.md
5. Read PHASE_13_MIGRATION_CHECKLIST.md

### Create Feature Branch

```bash
git checkout -b feat/phase13-<feature-name>
```

Example: `feat/phase13-pipeline-validator`

### Pick a Task

**Small tasks (start here):**
- [ ] Implement `validate_pipeline()` in VideoPipelineService
- [ ] Add REST endpoint `/video/pipeline`
- [ ] Create PipelineToolSelector component

**Medium tasks:**
- [ ] Implement `execute_pipeline()` with tool ordering
- [ ] Add WebSocket frame handling for pipelines
- [ ] Create pipeline logging

**Large tasks:**
- [ ] Integrate VideoPipelineService into VisionAnalysisService
- [ ] Full UI migration to multi-select tools
- [ ] End-to-end pipeline tests

### Write Tests First (TDD)

Before implementing, write failing tests:

**Server example:**
```python
def test_validate_pipeline_rejects_cross_plugin_tools():
    """Pipeline cannot mix tools from different plugins."""
    validator = VideoPipelineService()
    result = validator.validate_pipeline(
        plugin_id="forgesyte-yolo-tracker",
        tools=["detect_players", "ocr_extract"]  # ocr_extract not in yolo-tracker
    )
    assert result == False
```

**UI example:**
```typescript
it("should reject tools from different plugins", () => {
  const selector = render(<PipelineToolSelector 
    pluginId="yolo-tracker"
    tools={["detect_players", "extract_text"]}  // extract_text not in yolo-tracker
  />);
  
  expect(selector.getByText("Invalid pipeline")).toBeInTheDocument();
});
```

### Implement

Write minimal code to make tests pass (no more).

### Review Checklist (Before Pushing)

- [ ] Followed PHASE_13_FOLDER_STRUCTURE.md file placement
- [ ] Used correct naming conventions
- [ ] No cross-plugin pipelines possible
- [ ] All tests pass: `pytest tests/` and `npm run test -- --run`
- [ ] Lint passes: `npm run lint`
- [ ] Type-check passes: `npm run type-check`
- [ ] Pre-commit passes: `uv run pre-commit run --all-files`
- [ ] No console errors in browser
- [ ] Logging includes step information
- [ ] No fallback to default tools
- [ ] PR description matches PHASE_13_PR_TEMPLATE.md

### Create PR

```bash
git push -u origin feat/phase13-<feature-name>
gh pr create --title "feat(phase-13): <description>" --template docs/phases/PHASE_13_PR_TEMPLATE.md
```

---

## Common Gotchas

### ❌ Gotcha 1: Cross-Plugin Pipelines

**FORBIDDEN:** Using tools from different plugins in one pipeline.

```python
# ❌ WRONG - mixing plugins
pipeline = {
    "plugin_id": "forgesyte-yolo-tracker",
    "tools": ["detect_players", "ocr_extract"]  # ocr_extract from ocr plugin
}
```

**✅ RIGHT** - all tools from same plugin

```python
pipeline = {
    "plugin_id": "forgesyte-yolo-tracker",
    "tools": ["detect_players", "track_players"]  # both from yolo-tracker
}
```

**Solution:** Always validate `all tools in plugin_id`.

### ❌ Gotcha 2: Silent Fallback to Default Tool

**FORBIDDEN:** Falling back to default tool if pipeline invalid.

```python
# ❌ WRONG
def execute_pipeline(plugin_id, tools, payload):
    if not validate_pipeline(plugin_id, tools):
        tools = ["default_tool"]  # WRONG - silent fallback
    # ...
```

**✅ RIGHT** - reject with clear error

```python
def execute_pipeline(plugin_id, tools, payload):
    if not validate_pipeline(plugin_id, tools):
        raise ValueError(f"Invalid pipeline: {tools}")
    # ...
```

### ❌ Gotcha 3: Tools Getting Different Input Types

**FORBIDDEN:** First tool gets image bytes, second tool gets dict.

```python
# ❌ WRONG
result1 = tool1(image_bytes)  # bytes
result2 = tool2(result1)      # dict
```

**✅ RIGHT** - all tools accept dict

```python
payload = {"frame": image_bytes, "confidence": 0.25}
result1 = tool1(payload)      # dict → dict
result2 = tool2(result1)      # dict → dict
```

### ❌ Gotcha 4: Empty Tools List

**FORBIDDEN:** Sending empty tools array to server.

```typescript
// ❌ WRONG
sendPipelineRequest({
  plugin_id: "yolo-tracker",
  tools: []  // empty!
})
```

**✅ RIGHT** - always have selected tools

```typescript
// ✅ RIGHT
if (selectedTools.length === 0) {
  showError("Select at least one tool");
  return;
}
sendPipelineRequest({
  plugin_id: "yolo-tracker",
  tools: selectedTools
})
```

### ❌ Gotcha 5: Missing Step Logging

**FORBIDDEN:** Not logging each pipeline step.

```python
# ❌ WRONG
result = tool1(payload)
result = tool2(result)
return result  # no logs!
```

**✅ RIGHT** - log each step

```python
for step_index, tool_name in enumerate(tools):
    logger.info("Pipeline step", extra={
        "step": step_index,
        "tool": tool_name,
        "duration_ms": duration
    })
    result = plugin.call_tool(tool_name, result)
return result
```

---

## Debugging Pipelines

### Check Server Logs

```bash
# Terminal where server runs
# Look for: "Pipeline step" logs
```

Sample log:
```
Pipeline step executed:
  plugin_id=forgesyte-yolo-tracker
  tool=detect_players
  step=0
  duration_ms=245
Pipeline step executed:
  plugin_id=forgesyte-yolo-tracker
  tool=track_players
  step=1
  duration_ms=156
```

### Common Problems

**Problem:** Tool name is "default"
```
  tool=default
```
**Cause:** UI not sending tools array (Phase 12 fallback)  
**Fix:** Ensure UI sends `tools: [...]` in request

---

**Problem:** Step index jumps (0 → 2)
```
  step=0, tool=t1
  step=2, tool=t2
```
**Cause:** Step counter not incrementing correctly  
**Fix:** Use `enumerate(tools)` instead of manual counter

---

**Problem:** Plugin not found
```
ValueError: Unknown plugin: yolo-tracker
```
**Cause:** Incorrect plugin_id in request  
**Fix:** Check plugin name matches installed plugin

---

**Problem:** Tool not in plugin
```
ValueError: Unknown tool: ocr_extract (not in forgesyte-yolo-tracker)
```
**Cause:** Tool from different plugin  
**Fix:** Validate tools belong to same plugin before sending

---

## Testing Guidelines

### Unit Tests (Server)

Test individual functions:

```python
def test_validate_pipeline_accepts_valid_pipeline():
    service = VideoPipelineService()
    result = service.validate_pipeline("yolo-tracker", ["detect_players", "track_players"])
    assert result == True

def test_validate_pipeline_rejects_cross_plugin():
    service = VideoPipelineService()
    result = service.validate_pipeline("yolo-tracker", ["detect_players", "ocr_extract"])
    assert result == False
```

### REST Tests (Server)

Test endpoint:

```python
def test_post_video_pipeline_executes_tools():
    response = client.post("/video/pipeline", json={
        "plugin_id": "yolo-tracker",
        "tools": ["detect_players", "track_players"],
        "payload": {"frame": base64_image}
    })
    assert response.status_code == 200
    assert "detections" in response.json()
```

### WebSocket Tests (Server)

Test streaming:

```python
async def test_websocket_pipeline_execution():
    async with client.websocket_connect("/stream?plugin=yolo-tracker") as ws:
        # Send frame with tools
        await ws.send_json({
            "plugin_id": "yolo-tracker",
            "tools": ["detect_players"],
            "image_data": base64_frame
        })
        # Receive result
        data = await ws.receive_json()
        assert "annotated_frame" in data
```

### UI Tests (Web)

Test component:

```typescript
it("should display selected tools", () => {
  const { getByText } = render(
    <PipelineToolSelector 
      pluginId="yolo-tracker"
      selectedTools={["detect_players", "track_players"]}
      onToolsChange={vi.fn()}
    />
  );
  expect(getByText("detect_players")).toBeInTheDocument();
  expect(getByText("track_players")).toBeInTheDocument();
});
```

---

## When You're Done

1. ✅ All tests pass locally
2. ✅ Pre-commit clean
3. ✅ No console errors
4. ✅ Logging works
5. ✅ PR created with PHASE_13_PR_TEMPLATE.md
6. ✅ Code review complete
7. ✅ Merged to main

---

## Getting Help

**Questions about Phase 13?**
- Read PHASE_13_FOLDER_STRUCTURE.md (file placement)
- Read PHASE_13_PR_TEMPLATE.md (PR format)
- Read PHASE_13_MIGRATION_CHECKLIST.md (implementation steps)
- Check existing PRs for examples

**Stuck on a bug?**
- Check server logs for pipeline step output
- Check browser console for UI errors
- Check tests for expected behavior
- Ask in code review

---

## You Are Ready

You now have everything needed to work on Phase 13.

Go implement pipelines.  
Lock Phase 13 into the repo.
