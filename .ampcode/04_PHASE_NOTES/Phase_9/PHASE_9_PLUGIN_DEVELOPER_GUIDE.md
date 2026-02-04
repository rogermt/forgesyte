
**Interpretation:**  
- `AnalyzeRequest` → creates a job  
- `JobResponse` → wraps job state  
- `AnalysisResult` → plugin output  
- `PluginMetadata` → describes plugin  
- `MCPTool` + `MCPManifest` → expose plugin tools  
- `PluginToolRunRequest/Response` → run tools  
- `WebSocketMessage` → Phase 10 real‑time channel  

---

# ⭐ **2. Guide — How to Write a Plugin Using These Models**  
### *Drop into:* `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_PLUGIN_DEVELOPER_GUIDE.md`

## **How to Write a Plugin Using Phase‑9 Models**

This guide explains how to implement a plugin that integrates cleanly with the Phase‑9 API and Phase‑10 real‑time pipeline.

---

# 1. **Define Plugin Metadata**

Every plugin must expose a `PluginMetadata` instance.

```python
metadata = PluginMetadata(
    name="ocr",
    description="Optical character recognition plugin",
    version="1.0.0",
    inputs=["image"],
    outputs=["json"],
    permissions=[],
    config_schema={
        "threshold": {"type": "number", "default": 0.5, "description": "OCR threshold"}
    },
)
```

This metadata is used to:

- register the plugin  
- generate MCP manifest entries  
- validate configuration  
- power the Phase‑10 plugin inspector panel  

---

# 2. **Implement the `analyze()` Method**

Your plugin must return an `AnalysisResult`.

```python
from server.app.models import AnalysisResult

def analyze(image, options) -> AnalysisResult:
    text, blocks, confidence = run_ocr(image)

    return AnalysisResult(
        text=text,
        blocks=blocks,
        confidence=confidence,
        language="eng",
        extra={"raw_blocks": blocks},
    )
```

### Rules:
- `text` must be a string  
- `blocks` must be a list of dicts  
- `confidence` must be 0.0–1.0  
- `extra` is plugin‑specific  

---

# 3. **Expose Tools (Optional but Phase‑10‑Ready)**

If your plugin exposes tools:

```python
from server.app.models import MCPTool

tools = [
    MCPTool(
        id="ocr_detect",
        title="OCR Detection",
        description="Detects text regions",
        inputs=["image"],
        outputs=["json"],
        invoke_endpoint="/v1/tools/ocr_detect",
        permissions=[],
    )
]
```

These tools appear in the MCP manifest.

---

# 4. **Implement Tool Execution**

Tools use `PluginToolRunRequest` and return `PluginToolRunResponse`.

```python
def run_tool(request: PluginToolRunRequest) -> PluginToolRunResponse:
    frame = decode(request.args["frame_base64"])
    detections = detect_text_regions(frame)

    return PluginToolRunResponse(
        tool_name="ocr_detect",
        plugin_id="ocr",
        result={"detections": detections},
        processing_time_ms=12,
    )
```

---

# 5. **Return Results Through the Job System**

Your plugin does NOT return HTTP responses directly.  
It returns `AnalysisResult` to the job runner, which wraps it in:

- `JobResponse` (status)  
- `JobResultResponse` (final result)  

---

# 6. **Phase‑10 Real‑Time Compatibility**

Your plugin is automatically compatible with Phase‑10 real‑time features because:

- `AnalysisResult` is serializable  
- `PluginToolRunResponse` is serializable  
- `WebSocketMessage` can wrap any plugin output  

---

# ⭐ **3. Document — How Phase 10 Extends These Models**  
### *Drop into:* `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_MODEL_EXTENSIONS.md`

# **How Phase 10 Extends Phase‑9 Models**

Phase 10 introduces real‑time insights, plugin pipeline upgrades, and richer job tracking.  
These features extend — but do not break — the Phase‑9 model contract.

---

# 1. **Extensions to JobResponse**

Phase 10 adds optional fields:

```python
progress: Optional[float]  # 0–100
plugin_timings: Optional[Dict[str, float]]  # per-plugin latency
warnings: Optional[List[str]]  # soft failures
```

### Why:
- Real‑time progress bar  
- Plugin inspector panel  
- Debugging and observability  

---

# 2. **Extensions to AnalysisResult**

Phase 10 allows plugins to include:

```python
extra: Dict[str, Any]  # richer plugin-specific data
```

Examples:
- YOLO detections  
- Tracking vectors  
- Heatmaps  
- Pose estimation  

---

# 3. **Extensions to WebSocketMessage**

Phase 10 introduces new message types:

```
frame
partial_result
progress
plugin_status
warning
error
ping/pong
```

### Purpose:
- Real‑time overlay updates  
- Real‑time plugin health  
- Real‑time progress  

---

# 4. **Extensions to PluginMetadata**

Phase 10 adds optional fields:

```python
latency_budget_ms: Optional[int]
supports_realtime: Optional[bool]
```

### Purpose:
- Real‑time plugin scheduling  
- Pipeline orchestration  

---

# 5. **Extensions to MCPTool / MCPManifest**

Phase 10 adds:

- Real‑time tool invocation  
- Streaming tool outputs  
- Tool health indicators  

---

# 6. **New Phase‑10 Models (Additive Only)**

Phase 10 introduces new models but does NOT modify Phase‑9 models in breaking ways.

Examples:

```python
class RealtimeFrame(BaseModel):
    frame_id: str
    data: Dict[str, Any]
    timestamp: datetime
```

```python
class PluginHealth(BaseModel):
    plugin_id: str
    status: str
    latency_ms: float
```

These models are **additive**, not replacements.

---

# ⭐ Final Summary

You now have:

### ✔ A complete model relationship diagram  
### ✔ A plugin developer guide  
### ✔ A Phase‑10 model extension document  

All three are aligned with:

- Phase 9 Developer Contract  
- Phase 9 Compliance Matrix  
- Phase 9 → Phase 10 Dependency Map  
- Your actual coding tendencies  
