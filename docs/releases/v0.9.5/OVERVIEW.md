# ⭐ **PR Title — v0.9.5**  
**v0.9.5 — Add Video Job Type, Restore Video Upload Pipeline, and Enable Video‑Capable Tools**

---

# ⭐ **PR Description — v0.9.5  
Enable Video Input for Plugins + Worker Support for Video Jobs**

## **Summary**

This PR introduces **first‑class video job support** to the backend.  
The system can now:

- Accept video uploads via `/v1/video/submit`
- Store the uploaded video once
- Create a job with `job_type="video"`
- Pass the stored `video_path` to the plugin
- Execute any plugin tool that declares `input_types: ["video"]`
- Return a unified JSON response containing frame‑level results

This restores the intended behavior for YOLO‑style plugins, which rely on the Ultralytics API’s built‑in video streaming interface:

```python
results = model(video_path, stream=True)
```

This PR does **not** modify existing image‑only tools.  
Instead, it enables plugins to add new tools that explicitly support video input.

---

## **User Story**

> **As a user, I want to upload a video and run a plugin tool that supports video input, receiving frame‑level results in a single JSON response.**

This PR fully enables that workflow.

---

## **Root Cause of Video Failures**

Video uploads were failing because:

### **1. The worker only supported `image` and `image_multi` job types**
Video jobs were incorrectly validated as image jobs.

### **2. Tools were validated as if they only accepted images**
Even when a plugin intended to support video, the worker rejected the job with:

```
Tool 'player_detection' does not support video input
```

### **3. No unified schema existed for video input**
The worker expected `image_bytes` or `image_path`, even for video jobs.

---

## **Fix**

### **1. Add `video` job type**
Jobs now distinguish:

- `"image"`
- `"image_multi"`
- `"video"`

### **2. Normalize video input schema**

Video jobs now pass:

```json
{
  "video_path": "/storage/videos/<uuid>.mp4"
}
```

### **3. Worker executes video tools**

```python
if job.job_type == "video":
    args = {"video_path": job.video_path}
    result = plugin.run_tool(job.tool, args)
```

### **4. Plugins may now declare video‑capable tools**

Example:

```json
"input_types": ["video"]
```

### **5. Unified JSON output**

```json
{
  "plugin_id": "yolo-tracker",
  "tool": "video_player_detection",
  "frames": [...],
  "summary": {...}
}
```

This matches the structure used for single‑tool image jobs.

---

## **Impact**

### **Enabled**
- Plugins can now implement tools that accept video input.
- Worker correctly routes video jobs.
- Video uploads no longer fail due to image‑only validation.
- Backend supports Ultralytics `stream=True` workflows.

### **Unaffected**
- Image jobs  
- Multi‑tool image jobs (v0.9.4)  
- Plugin lifecycle  
- Job polling  
- Storage paths  

---

## **Regression Tests Added**

### **API**
- `/v1/video/submit` returns a valid job ID  
- Job is created with `job_type="video"`  
- Video is stored correctly  

### **Validation**
- Worker accepts tools with `input_types=["video"]`  
- Worker rejects tools that do not support video  

### **Worker**
- Worker routes video jobs through the new execution path  
- Worker passes `video_path` to plugin  
- Worker does not expect `image_bytes` for video jobs  

### **Plugin Integration**
- YOLO plugin receives `video_path`  
- YOLO streaming inference runs (`stream=True`)  
- Frame‑level results are returned  

---

## **Migration Notes**

- Existing plugins do **not** need to change unless they want to support video.
- To enable video support, a plugin simply adds a new tool with:

```json
"input_types": ["video"]
```

- No breaking changes for image workflows.

---

# ⭐ **This is the corrected, complete, developer‑ready PR description.**

Everything that was correct in your draft is preserved.  
Everything that was inaccurate is fixed.  
Everything now matches your real plugin manifest and backend architecture.
