# v0.9.5 Implementation Plan

## Overview
Enable video input for plugins by adding a video-capable tool to the YOLO tracker plugin and updating the UI to filter tools by video capability.

## Current State Analysis

### ForgeSyte Repo (Main)
- `video_submit.py`: Creates jobs with `job_type="video"`, validates tools support video input
- `worker.py`: Handles video jobs, passes `video_path` to plugins
- `job.py`: Supports `job_type="video"`
- `VideoUpload.tsx`: Allows video upload but doesn't filter tools by video capability

### ForgeSyte-Plugins Repo (YOLO Tracker)
- `manifest.json`: Has 4 tools with `input_types: ["video_frame"]` - **NO video tools with `input_types: ["video"]`**
- `plugin.py`: Has video tool implementations but they require `output_path` and save annotated video files
- `player_detection_video.py`: Processes videos but outputs annotated video files, not JSON frame results

### Gap Identified
The YOLO plugin manifest lacks a tool with `input_types: ["video"]` that the worker expects. The existing video tools output annotated video files, but v0.9.5 requires JSON frame-level output using YOLO streaming inference.

---

## Repository 1: forgesyte-plugins (YOLO Tracker Plugin)

### Phase 1: Add Video Tool to Manifest (TDD: Write test first)

#### Commit 1.1: Add contract test for video tool
**Files to modify:**
- `plugins/forgesyte-yolo-tracker/tests_contract/test_video_tool_contract.py` (create)

**Changes:**
- Test that manifest has a tool with `input_types: ["video"]`
- Test tool has correct input/output schema
- Test tool id is `video_player_detection`

**Pre-commit tests:**
```bash
cd plugins/forgesyte-yolo-tracker
uv run pytest tests_contract/test_video_tool_contract.py -v  # expect failure
```

#### Commit 1.2: Update manifest.json with video_player_detection tool
**Files to modify:**
- `plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/manifest.json`

**Changes:**
Add new tool to `tools` array:
```json
{
  "id": "video_player_detection",
  "title": "Video Player Detection",
  "description": "Run player detection on every frame of a video.",
  "input_types": ["video"],
  "output_types": ["video_detections"],
  "capabilities": ["player_detection"],
  "inputs": {
    "video_path": "string",
    "device": "string",
    "annotated": "boolean"
  },
  "outputs": {
    "frames": "array",
    "summary": "object"
  }
}
```

**Pre-commit tests:**
```bash
cd plugins/forgesyte-yolo-tracker
uv run pytest tests_contract/test_video_tool_contract.py -v  # expect pass
uv run pre-commit run --all-files
```

---

### Phase 2: Implement Video Tool (TDD: Write test first)

#### Commit 2.1: Add unit test for video_player_detection tool
**Files to modify:**
- `plugins/forgesyte-yolo-tracker/tests_contract/test_video_player_detection.py` (create)

**Changes:**
- Test tool accepts `video_path` and `device` parameters
- Test tool returns JSON with `frames` and `summary`
- Test uses mock YOLO model to avoid heavy inference
- Test frame structure: `{"frame_index": int, "detections": array}`
- Test summary structure: `{"total_frames": int, "total_detections": int}`

**Pre-commit tests:**
```bash
cd plugins/forgesyte-yolo-tracker
uv run pytest tests_contract/test_video_player_detection.py -v  # expect failure
```

#### Commit 2.2: Implement video_player_detection tool
**Files to modify:**
- `plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py`

**Changes:**
1. Add new function `_tool_video_player_detection()`:
```python
def _tool_video_player_detection(
    video_path: str, device: str = "cpu", annotated: bool = False
) -> Dict[str, Any]:
    """Run player detection on video frames.
    
    Args:
        video_path: Path to input video file
        device: Device to run model on ('cpu' or 'cuda')
        annotated: Whether to include annotated frames (not implemented in v0.9.5)
    
    Returns:
        Dict with frames array and summary
    """
    from ultralytics import YOLO
    import supervision as sv
    
    model = YOLO(MODEL_PATH).to(device=device)
    
    frame_results = []
    frame_index = 0
    
    # Use YOLO streaming inference
    results = model(video_path, stream=True, verbose=False)
    
    for result in results:
        detections = sv.Detections.from_ultralytics(result)
        
        frame_results.append({
            "frame_index": frame_index,
            "detections": {
                "xyxy": detections.xyxy.tolist() if len(detections) > 0 else [],
                "class_id": detections.class_id.tolist() if len(detections) > 0 else [],
                "confidence": detections.confidence.tolist() if len(detections) > 0 else [],
            }
        })
        frame_index += 1
    
    return {
        "frames": frame_results,
        "summary": {
            "total_frames": frame_index,
            "total_detections": sum(
                len(f["detections"]["xyxy"]) for f in frame_results
            )
        }
    }
```

2. Add tool to `tools` dict:
```python
"video_player_detection": {
    "description": "Detect players in a video",
    "input_schema": {
        "video_path": {"type": "string"},
        "device": {"type": "string", "default": "cpu"},
        "annotated": {"type": "boolean", "default": False},
    },
    "output_schema": {
        "frames": {"type": "array"},
        "summary": {"type": "object"}
    },
    "handler": _tool_video_player_detection,
},
```

3. Update `run_tool()` dispatcher to handle video tools:
```python
elif tool_name == "video_player_detection":
    return handler(
        video_path=args.get("video_path"),
        device=args.get("device", "cpu"),
        annotated=args.get("annotated", False),
    )
```

**Pre-commit tests:**
```bash
cd plugins/forgesyte-yolo-tracker
uv run pytest tests_contract/test_video_player_detection.py -v  # expect pass
uv run pre-commit run --all-files
```

---

### Phase 3: Integration Test

#### Commit 3.1: Add integration test for video job flow
**Files to modify:**
- `plugins/forgesyte-yolo-tracker/tests_contract/test_video_job_integration.py` (create)

**Changes:**
- Test `plugin.run_tool("video_player_detection", {"video_path": "...", "device": "cpu"})`
- Verify JSON output structure matches expected schema
- Test with small test video fixture

**Pre-commit tests:**
```bash
cd plugins/forgesyte-yolo-tracker
uv run pytest tests_contract/ -v
uv run pre-commit run --all-files
```

---

## Repository 2: forgesyte (Main Repo)

### Phase 1: UI Tool Filtering (TDD: Write test first)

#### Commit 1.1: Add test for VideoUpload tool filtering
**Files to modify:**
- `web-ui/src/components/VideoUpload.test.tsx`

**Changes:**
- Test that only tools with `input_types` containing "video" are shown
- Test fallback message when no video tools available
- Test tool filtering logic

**Pre-commit tests:**
```bash
cd web-ui
npm run test -- --run  # expect failure
```

#### Commit 1.2: Implement tool filtering in VideoUpload
**Files to modify:**
- `web-ui/src/components/VideoUpload.tsx`

**Changes:**
1. Add tool filtering logic:
```typescript
// Filter tools that support video input
const availableTools = plugin?.tools?.filter(
  (t: any) => t.input_types?.includes("video")
) ?? [];

// Show fallback if no video tools
if (availableTools.length === 0) {
  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2>Video Upload</h2>
      <p>No video-compatible tools available for this plugin.</p>
    </div>
  );
}
```

2. Use filtered tools for selection:
```typescript
// Use first available video tool
const selectedTool = availableTools[0]?.id;
```

**Pre-commit tests:**
```bash
cd web-ui
npm run test -- --run  # expect pass
npm run lint
npm run type-check  # MANDATORY
```

---

### Phase 2: API Validation Update

#### Commit 2.1: Update video_submit to check input_types
**Files to modify:**
- `server/app/api_routes/routes/video_submit.py`

**Changes:**
Update validation to check `input_types` array:
```python
# Validate tool supports video input using input_types
input_types = tool_def.get("input_types", [])
if "video" not in input_types:
    raise HTTPException(
        status_code=400,
        detail=f"Tool '{tool}' does not support video input (input_types: {input_types})",
    )
```

**Pre-commit tests:**
```bash
cd server
uv run pytest tests/api/routes/test_video_submit.py -v
uv run pytest tests/api/routes/test_video_submit_plugin_tool.py -v
uv run pre-commit run --all-files
```

---

### Phase 3: Worker Output Format

#### Commit 3.1: Update worker to return unified JSON for video jobs
**Files to modify:**
- `server/app/workers/worker.py`

**Changes:**
Ensure video job output matches image job format:
```python
# v0.9.4: Prepare output based on job type
if is_multi_tool:
    output_data = {"plugin_id": job.plugin_id, "tools": results}
else:
    # Single-tool job (image or video)
    output_data = {
        "plugin_id": job.plugin_id,
        "tool": tools_to_run[0],
        "results": results[tools_to_run[0]]
    }
```

**Pre-commit tests:**
```bash
cd server
uv run pytest tests/app/workers/test_worker.py -v
uv run pre-commit run --all-files
```

---

### Phase 4: Full Test Suite

#### Commit 4.1: Run complete test suite
**Pre-commit tests:**
```bash
# Python linting and tests
uv run pre-commit run --all-files
cd server && uv run pytest tests/ -v

# Governance check
python scripts/scan_execution_violations.py

# TypeScript/Web-UI
cd web-ui
npm run lint
npm run type-check  # MANDATORY
npm run test -- --run
```

---

## Branch Strategy

### forgesyte-plugins repo:
```bash
git checkout -b v0.9.5
# Execute Phase 1-3 commits
git push origin v0.9.5
```

### forgesyte repo:
```bash
git checkout -b v0.9.5
# Execute Phase 1-4 commits
git push origin v0.9.5
```

---

## Test Commands Reference

### forgesyte-plugins:
```bash
cd plugins/forgesyte-yolo-tracker
uv run pre-commit run --all-files
uv run pytest tests_contract/ -v
```

### forgesyte:
```bash
# Python
uv run pre-commit run --all-files
cd server && uv run pytest tests/ -v
python scripts/scan_execution_violations.py

# TypeScript/Web-UI
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

---

## Success Criteria

1. ✅ YOLO plugin manifest has `video_player_detection` tool with `input_types: ["video"]`
2. ✅ Plugin returns JSON with `frames` and `summary` (not annotated video)
3. ✅ UI filters tools to show only video-compatible tools
4. ✅ Worker accepts video jobs and passes `video_path` to plugin
5. ✅ All tests pass (Python + TypeScript)
6. ✅ Pre-commit hooks pass (black/ruff/mypy + eslint)
7. ✅ Type-check passes (tsc --noEmit)
8. ✅ Governance scan passes

---

## Notes

- OCR plugin stays image-only (no changes needed)
- Only `video_player_detection` implemented in v0.9.5 (other video tools in v0.9.6+)
- No annotated frames for video in v0.9.5 (JSON only)
- `device` parameter supported for consistency with image tools
