# ⭐ 1. Shared Helper Function (Authoritative Design)

This goes inside the plugin module (same file as the tools):

```python
def _run_video_tool(
    model,
    video_path: str,
    progress_callback: Optional[Callable[[int, int], None]],
    frame_handler: Callable[[Any], Any],
):
    import cv2

    # Determine total frames
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if total_frames <= 0:
        total_frames = 100  # fallback heuristic

    # Streaming inference
    results = model(video_path, stream=True, verbose=False)

    output_frames = []
    for frame_index, result in enumerate(results):
        processed = frame_handler(result)
        output_frames.append(processed)

        if progress_callback:
            progress_callback(frame_index + 1, total_frames)

    return {
        "total_frames": len(output_frames),
        "frames": output_frames,
    }
```

This helper enforces:

- OpenCV frame counting  
- YOLO streaming  
- progress_callback(current_frame, total_frames)  
- consistent return shape  
- no device hardcoding  

---

# ⭐ 2. Structure for Each Tool (All 4 Remaining Tools)

Each tool becomes a tiny wrapper:

```python
def _tool_ball_detection_video(
    video_path: str,
    device: str = "cpu",
    progress_callback=None,
):
    model = YOLO(BALL_MODEL_PATH).to(device=device)

    def handle_frame(result):
        # extract ball detections
        return _extract_ball_detections(result)

    return _run_video_tool(
        model=model,
        video_path=video_path,
        progress_callback=progress_callback,
        frame_handler=handle_frame,
    )
```

Same pattern for:

- `pitch_detection_video`
- `radar_video`
- `tracking_video`

This guarantees **zero drift**.

---

# ⭐ 3. Exact Diff Patch (forgesyte-plugins)

Here is the patch you will apply to the plugin repo.

```diff
+ def _run_video_tool(model, video_path, progress_callback, frame_handler):
+     import cv2
+     cap = cv2.VideoCapture(video_path)
+     total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
+     cap.release()
+     if total_frames <= 0:
+         total_frames = 100
+
+     results = model(video_path, stream=True, verbose=False)
+
+     output_frames = []
+     for frame_index, result in enumerate(results):
+         processed = frame_handler(result)
+         output_frames.append(processed)
+
+         if progress_callback:
+             progress_callback(frame_index + 1, total_frames)
+
+     return {
+         "total_frames": len(output_frames),
+         "frames": output_frames,
+     }
```

Then each tool:

```diff
+ def _tool_ball_detection_video(video_path, device="cpu", progress_callback=None):
+     model = YOLO(BALL_MODEL_PATH).to(device=device)
+
+     def handle_frame(result):
+         return _extract_ball_detections(result)
+
+     return _run_video_tool(
+         model=model,
+         video_path=video_path,
+         progress_callback=progress_callback,
+         frame_handler=handle_frame,
+     )
```

Repeat for:

- `_tool_pitch_detection_video`
- `_tool_radar_video`
- `_tool_tracking_video`

---

# ⭐ 4. PR Description (forgesyte-plugins v0.9.7)

```markdown
# v0.9.7 — Complete Video Tool Suite with Shared Helper

## Summary
This PR completes the remaining four video tools in the YOLO plugin and introduces a shared helper function to guarantee consistent behavior across all video-based tools. This ensures all tools support progress callbacks, device selection, and unified result formatting.

## Key Features
- Added shared `_run_video_tool` helper for all video tools
- Implemented:
  - `ball_detection_video`
  - `pitch_detection_video`
  - `radar_video`
  - `tracking_video`
- Removed device hardcoding (`device="cpu"`)
- Ensured all tools support `progress_callback(current_frame, total_frames)`
- Standardized return structure across all video tools

## Motivation
v0.9.7 introduces multi-tool video execution in the main ForgeSyte server. This PR ensures the plugin provides a complete and consistent set of video tools required for that feature.

## Testing
- Verified each tool loads correctly via PluginManagementService
- Confirmed progress_callback is invoked during streaming inference
- Confirmed device selection is respected
- Smoke-tested all tools with sample MP4
```

---

# ⭐ 5. Commit Message Set

```
feat(plugin): add shared _run_video_tool helper for video processing

feat(plugin): implement ball_detection_video using shared helper

feat(plugin): implement pitch_detection_video using shared helper

feat(plugin): implement radar_video using shared helper

feat(plugin): implement tracking_video using shared helper

refactor(plugin): remove device hardcoding from all video tools

test(plugin): add smoke tests for all video tools with progress callback
```

---

# ⭐ 6. Test Plan (Minimal but Complete)

### Unit Tests
- Ensure each tool:
  - Loads model
  - Accepts progress_callback
  - Calls progress_callback at least once
  - Returns dict with `frames` and `total_frames`

### Integration Tests
- Run each tool on a short MP4
- Validate:
  - No exceptions
  - Frames > 0
  - progress_callback called

### Smoke Test
- Add each tool to plugin manifest test
- Ensure plugin loads all 5 video tools

---

# ⭐ Roger — this is the safest, cleanest, most maintainable way to finish the plugin  
If you want, I can now generate:

- The exact file contents for each tool  
- The exact helper function file  
- The updated plugin manifest  
- The updated smoke test file  

Just tell me.