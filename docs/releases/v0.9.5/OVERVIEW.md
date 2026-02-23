# **PR Description — v0.9.5  
Restore Video Input Support for YOLO Plugins (Phase‑1 Behavior)**

## **Summary**

This PR restores full video‑input support for YOLO‑style plugins, returning the system to the correct behavior originally implemented in **Phase 1**. Video uploads have been failing since Phase 6 due to schema mismatches and incorrect tool‑input validation, resulting in errors such as:

```
Tool 'player_detection' does not support video input
```

v0.9.5 reintroduces the correct video‑processing pipeline:

- Accept video files in `/v1/video/submit`
- Store the video once
- Pass the video path to the plugin
- Execute YOLO with `model(video_path, stream=True)`
- Stream frame‑level results
- Return a unified JSON response

This matches the expected behavior of YOLO‑based plugins and restores compatibility with the Ultralytics API:

```python
from ultralytics import YOLO
model = YOLO("yolo26n.pt")
results = model("path/to/video.mp4", stream=True)
```

---

## **User Story**

> **As a user, I would like to upload a video and run YOLO tools on it, receiving frame‑level results in a single JSON response.**

This PR fully satisfies that requirement.

---

## **Root Cause**

Two regressions caused video tools to fail:

### **1. Schema mismatch**
The worker incorrectly expected `image_bytes` or `image_path` even for video jobs.

### **2. Incorrect tool‑input validation**
The worker validated tools as if they only supported images, rejecting video paths and treating YOLO video tools as invalid.

This caused YOLO video tools to be rejected at execution time even though they passed submission.

---

## **Fix**

### **1. Normalize video input schema**
Video jobs now pass:

```json
{
  "video_path": "/storage/videos/<uuid>.mp4"
}
```

### **2. Add explicit `video` job type**
The job model now distinguishes:

- `image`
- `image_multi`
- `video`

### **3. Worker detects video jobs**
The worker now routes video jobs through the correct path:

```python
args = {"video_path": job.video_path}
result = plugin.run_tool(job.tool, args)
```

### **4. YOLO plugin uses Ultralytics API**
The plugin now executes:

```python
model = YOLO("yolo26n.pt")
results = model(video_path, stream=True)
return [frame.tojson() for frame in results]
```

### **5. Unified JSON output**
Worker returns:

```json
{
  "plugin_id": "yolo-tracker",
  "tool": "player_detection",
  "frames": [...]
}
```

---

## **Impact**

### **Resolved**
- YOLO video tools work again  
- Video uploads behave exactly like Phase‑1  
- Worker no longer rejects video inputs  
- Schema is consistent across all plugins  
- Frame‑level results are returned in a unified JSON structure  

### **Unaffected**
- Image jobs  
- Multi‑tool image jobs (v0.9.4)  
- Plugin lifecycle  
- Job polling  
- Storage paths  

---

## **Regression Tests Added**

- Video upload returns a job ID  
- Worker detects `job_type="video"`  
- Worker passes `video_path` to plugin  
- YOLO plugin receives correct arguments  
- YOLO inference runs with `stream=True`  
- Output JSON contains frame‑level results  
- No fallback to image‑only validation  
- No lifecycle methods appear as tools  

---

## **Migration Notes**

No plugin changes required beyond implementing `run_tool()` for video.  
No manifest changes required.  
Clients may now upload videos exactly as in Phase‑1.

---

# **DIFF OUTLINE — Video Input Restoration (v0.9.5)**

## **1. API Layer — Accept video uploads**

### `routes/video_submit.py`

```diff
+ job_type = "video"
+ job = job_service.create_job(
+     plugin_id,
+     tool,
+     job_type=job_type,
+     video_path=stored_path,
+ )
```

---

## **2. Job Model — Add video_path + job_type**

### `models/job.py`

```diff
+ video_path: Optional[str] = None
+ job_type: str = "image"
```

---

## **3. Job Service — Store video jobs**

### `job_service.py`

```diff
if job_type == "video":
    job.video_path = video_path
```

---

## **4. Worker — Detect and execute video jobs**

### `worker.py`

```diff
if job.job_type == "video":
+   args = {"video_path": job.video_path}
+   result = plugin.run_tool(job.tool, args)
+   return {
+       "plugin_id": job.plugin_id,
+       "tool": job.tool,
+       "frames": result,
+   }
```

---

## **5. YOLO Plugin — Use Ultralytics API**

### `plugins/yolo_tracker/plugin.py`

```diff
if "video_path" in args:
+   model = YOLO("yolo26n.pt")
+   results = model(args["video_path"], stream=True)
+   return [frame.tojson() for frame in results]
```

---

# **TEST PLAN — Video Jobs (v0.9.5)**

## **1. API Tests**

### Test: Upload video
- POST `/v1/video/submit`
- Expect:
  - job_type = `"video"`
  - video_path stored

---

## **2. Validation Tests**

### Test: Tool exists for video
- plugin.tools must include the tool
- No image‑only validation

---

## **3. Worker Tests**

### Test: Worker detects video job
- job.job_type = `"video"`
- Expect:
  - worker passes `video_path` to plugin
  - worker does NOT expect `image_bytes`

### Test: YOLO plugin receives correct args
- plugin.run_tool("player_detection", {"video_path": "..."})

---

## **4. YOLO Integration Test**

### Test: YOLO runs inference
- Mock YOLO model
- Expect:
  - model(video_path, stream=True) called
  - results streamed
  - JSON returned

---

## **5. Regression Tests**

### Test: Phase‑6 regression never returns
- Worker must NOT reject video input  
- Worker must NOT require image_bytes  
- Worker must NOT treat video tools as image‑only  

---

ersions  
- A GitHub release note bundle