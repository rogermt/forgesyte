# ⭐ **1. Video Job State‑Flow Diagram (v0.9.5)**

```
 ┌──────────────────────────────┐
 │   Video Submitted (POST)     │
 │   tool=player_detection      │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  API Validates Tool          │
 │  (plugin.tools)              │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Store Video File            │
 │  video_path=/storage/...mp4  │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Create Job (job_type=video) │
 │  job.tool="player_detection" │
 │  job.video_path=...          │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Worker Fetches Job          │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Worker Detects job_type     │
 │  IF video → use video_path   │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  plugin.run_tool(tool, args) │
 │  args={"video_path": "..."}  │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Plugin Runs YOLO Streaming  │
 │  model(video_path, stream=1) │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Aggregate Frame Results     │
 └───────────────┬─────────────┘
                 │
                 ▼
 ┌──────────────────────────────┐
 │  Return Unified JSON         │
 │  { plugin_id, tool, frames } │
 └──────────────────────────────┘
```

---

# ⭐ **2. Worker Execution Sequence for YOLO Streaming**

```
User → API: POST /video?tool=player_detection
API → Storage: save video file
API → JobService: create job(job_type="video", video_path)
JobService → DB: insert job

Worker → DB: fetch next job
Worker → PluginRegistry: get plugin instance
Worker → Worker: detect job_type == "video"

Worker → Plugin:
    run_tool("player_detection", {"video_path": ".../file.mp4"})

Plugin → YOLO:
    model = YOLO("yolo26n.pt")
    results = model(video_path, stream=True)

loop for each frame
    YOLO → Plugin: frame_result
    Plugin → Worker: append frame JSON
end

Worker → DB: store aggregated results
Worker → API: return unified JSON
API → User: { frames: [...] }
```

This is the exact execution path restored in v0.9.5.

---

# ⭐ **3. Plugin‑Level Flow for `model(video_path, stream=True)`**

This diagram shows what happens *inside the plugin* when the worker calls `run_tool()`.

```
 ┌────────────────────────────────────┐
 │ run_tool("player_detection", args) │
 └───────────────────┬────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────┐
 │ Extract video_path from args       │
 │ video_path = args["video_path"]    │
 └───────────────────┬────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────┐
 │ Load YOLO Model                    │
 │ model = YOLO("yolo26n.pt")         │
 └───────────────────┬────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────┐
 │ Run Streaming Inference            │
 │ results = model(video_path,        │
 │            stream=True)            │
 └───────────────────┬────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────┐
 │ Iterate Over Frames                │
 │ for frame in results:              │
 │     frames.append(frame.tojson())  │
 └───────────────────┬────────────────┘
                     │
                     ▼
 ┌────────────────────────────────────┐
 │ Return List of Frame JSON Objects  │
 └────────────────────────────────────┘
```

This is the exact plugin‑level contract v0.9.5 enforces.

---

# ⭐ **4. Combined Architecture Diagram (v0.9.3 → v0.9.5)**

This shows how the system evolves across the three versions:

```
v0.9.3 — Unified Tool Execution
--------------------------------
- Canonical tool validation (plugin.tools)
- Worker uses plugin.run_tool()
- No lifecycle methods treated as tools
- Fixes Phase‑16/17 regressions


v0.9.4 — Multi‑Tool Image Jobs
--------------------------------
API:
  Accept multiple tool parameters
Job:
  job_type="image_multi"
  tool_list=[t1,t2,t3]
Worker:
  Sequential run_tool() calls
  Unified JSON aggregation


v0.9.5 — Video Job Restoration
--------------------------------
API:
  Accept video uploads
Job:
  job_type="video"
  video_path=/storage/videos/...
Worker:
  Detect video job
  Pass video_path to plugin
Plugin:
  YOLO(video_path, stream=True)
Output:
  Unified frame-level JSON
```

And here is the combined flow as a single diagram:

```
                ┌──────────────────────────────┐
                │          v0.9.3              │
                │  Unified Tool Execution      │
                └──────────────┬──────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │          v0.9.4              │
                │  Multi‑Tool Image Jobs       │
                │  image_multi job type        │
                │  Sequential run_tool()       │
                └──────────────┬──────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │          v0.9.5              │
                │  Video Job Restoration       │
                │  YOLO Streaming Support      │
                │  video job type              │
                └──────────────────────────────┘
```

This is the complete architectural evolution.

---

# ⭐ If you want, I can also generate:

- A **full architecture document** (v0.9.3 → v0.9.5)  
- A **plugin authoring guide** for YOLO/OCR/Motion Detector  
- A **worker lifecycle diagram**  
- A **storage pipeline diagram**  
- A **client SDK update guide**  

Just tell me what you want next.