# 📘 **README — Unified Image & Video Analysis Architecture**  
### *For developers working on Forgesyte’s analysis pipeline*

---

## 🚀 Overview

Forgesyte’s analysis system uses a **plugin + tool** architecture.  
This applies **equally** to:

- Image analysis  
- Video analysis  

There are:

- ❌ No pipelines  
- ❌ No DAGs  
- ❌ No “ocr_only”  
- ❌ No hardcoded pipeline JSON  

Instead:

- The **UI (Discoveries)** selects a **plugin**  
- The **UI** selects a **tool** from that plugin’s manifest  
- The **server** stores `plugin_id` + `tool` in a Job  
- The **worker** loads the plugin and calls:

```
plugin.run_tool(tool_name, args)
```

Plugins live in the **forgesyte‑plugins** repo and enforce their own type safety.

---

# 🧠 Plugin Capabilities

## ✔ OCR Plugin  
- **Supports images only**  
- Tools: `"default"`, `"analyze"`  
- Requires: `image_bytes`  
- Rejects video tools automatically  

## ✔ YOLO‑Tracker Plugin  
- **Supports BOTH images and video**  
- Image tools: `"detect"`, `"track"`, etc.  
- Video tools: `"video_detect"`, `"video_track"`, etc.  
- Automatically switches behavior based on tool name:

```python
if "video" in tool_name:
    # video mode
else:
    # image mode
```

This is why the core system does **not** need to know which plugins support video —  
the plugin itself enforces the contract.

---

# 🧩 Architecture Summary

### Image Flow
```
UI → POST /v1/analyze?plugin=ocr&tool=analyze
Server → TaskProcessor → plugin.run_tool(tool, args)
Plugin → handler(image_bytes)
```

### Video Flow
```
UI → POST /v1/video/submit?plugin_id=yolo-tracker&tool=video_track
Server → Job(plugin_id, tool)
Worker → plugin.run_tool(tool, args)
Plugin → handler(video_path)
```

**The only difference is where the work runs (TaskProcessor vs Worker).**

---

# 🛠️ Components

## 1. Frontend (UI)

The video upload button behaves exactly like image upload:

```ts
await apiClient.submitVideo(file, selectedPlugin, selectedTools[0]);
```

## 2. API Client

```ts
POST /v1/video/submit?plugin_id=yolo-tracker&tool=video_track
```

## 3. Server Endpoint

```python
job = Job(plugin_id=plugin_id, tool=tool, input_path=input_path)
```

## 4. Worker

```python
plugin = plugin_service.get(job.plugin_id)

results = plugin.run_tool(
    job.tool,
    {
        "video_path": str(input_file_path),
        "device": "cpu",
    }
)
```

## 5. Plugin (forgesyte‑plugins repo)

Plugins remain untouched.

They already support:

- Image tools via `image_bytes`
- Video tools via `video_path`

---

# 🔒 Type Safety (Image‑Only Plugins Cannot Run Video)

This is enforced by plugin code:

### OCR (image‑only)
```python
if tool_name not in ("default", "analyze"):
    raise ValueError("Unknown tool")
```

### YOLO‑Tracker (image + video)
```python
if "video" in tool_name:
    return handler(video_path=args["video_path"])
else:
    return handler(image_bytes=args["image_bytes"])
```

If the wrong tool is used:

- The plugin raises `ValueError("Unknown tool")`
- The worker marks the job as `failed`
- The UI shows the error

No special logic is needed in core.

---

# 📦 Plugin Template (Video Support)

```python
class ExamplePlugin:
    tools = {
        "video_track": {"handler": "video_track_handler"},
        "detect": {"handler": "detect_handler"},
    }

    def run_tool(self, tool_name, args):
        if "video" in tool_name:
            return self.video_track_handler(video_path=args["video_path"])
        return self.detect_handler(image_bytes=args["image_bytes"])

    def video_track_handler(self, video_path):
        return {"frames": [{"frame": 0, "objects": []}]}

    def detect_handler(self, image_bytes):
        return {"boxes": []}
```

---

# 🧪 Test Suite (Video Jobs)

```python
def test_video_job_success(mock_storage, mock_plugin_service, fake_session):
    worker = JobWorker(...)

    job = Job(plugin_id="yolo-tracker", tool="video_track", input_path="video.mp4")

    result = worker._execute_pipeline(job, fake_session)

    mock_plugin_service.run_on_video.assert_called_once()
```

---

# 🟢 Final Developer Summary

> “Video analysis works exactly like image analysis. Discoveries picks a plugin and tool. The server stores `plugin_id` + `tool`. The worker loads the plugin and calls `plugin.run_tool(tool, args)` with `video_path`. Plugins live in forgesyte‑plugins and enforce type safety — OCR is image‑only, YOLO‑Tracker supports both image and video.”

---
Absolutely — let’s wrap this up with the three polished deliverables you asked for:

- A **diagram version** of the README  
- A **developer onboarding guide**  
- A **plugin authoring guide for video tools**  

All three are written to be copy‑paste ready for your repo, consistent with the architecture you approved, and easy for any engineer to understand.

---

# 🎨 **1. Diagram Version of the README**  
*(Markdown‑friendly, works in GitHub, Notion, Confluence, anywhere)*

## **Unified Image & Video Analysis Architecture — Diagram**

```text
                          ┌───────────────────────────┐
                          │         Discoveries        │
                          │  (Plugin + Tool Selector)  │
                          └──────────────┬────────────┘
                                         │
                                         ▼
                         ┌──────────────────────────────────┐
                         │            Frontend               │
                         │  Image: analyzeImage()            │
                         │  Video: submitVideo()             │
                         └──────────────┬───────────────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────────┐
                    │                 API Server                  │
                    │  /v1/analyze?plugin=X&tool=Y (image)        │
                    │  /v1/video/submit?plugin_id=X&tool=Y (video)│
                    └──────────────┬─────────────────────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────────────────────┐
                    │                Job Store                    │
                    │  Stores: plugin_id, tool, input_path        │
                    └──────────────┬─────────────────────────────┘
                                   │
                     ┌─────────────┴──────────────┐
                     │                            │
                     ▼                            ▼
     ┌──────────────────────────────┐   ┌──────────────────────────────┐
     │        TaskProcessor         │   │           JobWorker           │
     │     (Image Processing)       │   │       (Video Processing)      │
     └──────────────┬──────────────┘   └──────────────┬──────────────┘
                    │                                 │
                    ▼                                 ▼
     ┌──────────────────────────────┐   ┌──────────────────────────────┐
     │        Plugin Manager        │   │        Plugin Manager        │
     │   plugin = get(plugin_id)    │   │   plugin = get(plugin_id)    │
     └──────────────┬──────────────┘   └──────────────┬──────────────┘
                    │                                 │
                    ▼                                 ▼
     ┌──────────────────────────────┐   ┌──────────────────────────────┐
     │        Plugin.run_tool       │   │        Plugin.run_tool       │
     │  tool="analyze" → image      │   │  tool="video_track" → video  │
     └──────────────┬──────────────┘   └──────────────┬──────────────┘
                    │                                 │
                    ▼                                 ▼
     ┌──────────────────────────────┐   ┌──────────────────────────────┐
     │     Image Handler (plugin)   │   │     Video Handler (plugin)    │
     └──────────────────────────────┘   └──────────────────────────────┘
```

---

# 📘 **2. Developer Onboarding Guide**  
*(Drop this into `/docs/onboarding.md`)*

# **Developer Onboarding — Image & Video Analysis**

Welcome to the Forgesyte analysis system.  
This guide explains how image and video analysis work, how plugins are discovered, and how jobs are executed.

---

## 🚀 Core Concepts

### 1. **Plugins live in the forgesyte‑plugins repo**
They are:

- Versioned independently  
- Loaded dynamically  
- Discovered via `/v1/plugins`  
- Typed via their manifest (`manifest.json`)  
- Responsible for their own tool logic  

### 2. **Tools come from plugin manifests**
Each plugin exposes tools like:

```json
{
  "id": "video_track",
  "title": "Track objects in video",
  "inputs": {...},
  "outputs": {...}
}
```

The UI displays these tools automatically.

### 3. **Jobs store plugin + tool**
Every job contains:

```json
{
  "plugin_id": "yolo-tracker",
  "tool": "video_track",
  "input_path": "123.mp4"
}
```

### 4. **Worker executes plugin.run_tool()**
The worker does not know anything about:

- Pipelines  
- DAGs  
- Multi‑tool chains  
- Hardcoded logic  

It simply calls:

```python
plugin.run_tool(tool_name, args)
```

---

## 🧩 Image vs Video (identical architecture)

| Step | Image | Video |
|------|--------|--------|
| UI | analyzeImage() | submitVideo() |
| API | /v1/analyze | /v1/video/submit |
| Job | plugin_id + tool | plugin_id + tool |
| Executor | TaskProcessor | JobWorker |
| Plugin | run_tool(image_bytes) | run_tool(video_path) |

---

## 🔒 Type Safety

Plugins enforce their own type rules:

- OCR → image only  
- YOLO‑Tracker → image + video  
- Wrong tool = plugin throws `ValueError`  

Core never needs to guess.

---

## 🧪 Testing

Video job tests mirror image job tests:

```python
mock_plugin.run_on_video.return_value = {...}
worker._execute_pipeline(job, session)
```

---

# 🎉 You’re ready to build.

---

# 🛠️ **3. Plugin Authoring Guide for Video Tools**  
*(Drop this into `/docs/plugin-authoring-video.md`)*

# **Plugin Authoring Guide — Video Tools**

This guide explains how to add video support to a plugin in the **forgesyte‑plugins** repo.

---

## 🧩 1. Manifest Definition

Add a video tool to your plugin’s `manifest.json`:

```json
{
  "id": "video_track",
  "title": "Track objects in video",
  "description": "Runs YOLO tracking on video frames",
  "inputs": {
    "video_path": "string"
  },
  "outputs": {
    "frames": "array"
  }
}
```

---

## 🧠 2. Implement run_tool()

Your plugin must route video tools based on the tool name.

### Example (YOLO‑Tracker style)

```python
def run_tool(self, tool_name: str, args: Dict[str, Any]):
    if "video" in tool_name:
        return self._run_video_tool(tool_name, args)
    return self._run_image_tool(tool_name, args)
```

---

## 🎥 3. Implement the video handler

```python
def _run_video_tool(self, tool_name, args):
    video_path = args["video_path"]
    device = args.get("device", "cpu")

    if tool_name == "video_track":
        return self.video_track_handler(video_path, device)

    raise ValueError(f"Unknown video tool: {tool_name}")
```

---

## 🖼️ 4. Implement the image handler (optional)

```python
def _run_image_tool(self, tool_name, args):
    image_bytes = args["image_bytes"]
    return self.detect_handler(image_bytes)
```

---

## 🔒 5. Type Safety

If a plugin does not support video:

```python
raise ValueError("Unknown tool")
```

This prevents:

- OCR from running video tools  
- Video tools from being used on image-only plugins  

---

## 🧪 6. Testing

```python
def test_video_tool():
    plugin = MyPlugin()
    result = plugin.run_tool("video_track", {"video_path": "/tmp/test.mp4"})
    assert "frames" in result
```

---


