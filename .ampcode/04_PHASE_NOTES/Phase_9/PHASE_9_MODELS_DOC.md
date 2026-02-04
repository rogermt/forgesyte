Absolutely, Roger — here’s a **clean, developer‑focused documentation file** that explains the purpose, structure, and usage of every model in your `models.py`.  
It’s written in the same tone and structure as your `.ampcode` documentation, and it assumes this file lives at:

```
server/app/models.py
```

You can drop this directly into:

```
.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MODELS_DOC.md
```

---

# **Phase 9 — `models.py` Documentation**  
### *Developer Guide to Request/Response Models and Validation Contracts*

This document explains the purpose, structure, and usage of all Pydantic models defined in `server/app/models.py`.  
These models form the **API boundary contract** for Phase 9 and the foundation for Phase 10’s real‑time and plugin‑pipeline features.

---

# 1. **Overview**

The models in `models.py` serve three purposes:

1. **Validate incoming requests**  
2. **Enforce typed, stable API responses**  
3. **Provide shared schemas for plugin metadata, results, and real‑time messages**

All models use **Pydantic v2**, which provides:

- Strict field validation  
- Automatic OpenAPI schema generation  
- Runtime safety at API boundaries  
- Consistent serialization for plugins and WebSocket messages  

These models are the **canonical source of truth** for API shape.

---

# 2. **JobStatus Enum**

```python
class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    NOT_FOUND = "not_found"
```

### Purpose  
Defines the lifecycle states of an analysis job.

### Used in:
- `JobResponse.status`
- Job polling endpoints
- Real‑time status messages (Phase 10)

### Notes  
String‑based enum ensures clean JSON serialization.

---

# 3. **AnalyzeRequest**

```python
class AnalyzeRequest(BaseModel):
    plugin: str
    options: Optional[Dict[str, Any]]
    image_url: Optional[str]
```

### Purpose  
Represents the **incoming request** to start an analysis job.

### Fields  
- `plugin`: which plugin to run  
- `options`: plugin‑specific configuration  
- `image_url`: remote image to fetch  

### Notes  
This model is intentionally flexible — plugins may define their own option schemas.

---

# 4. **JobResponse**

```python
class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    plugin: str
    progress: Optional[float]
```

### Purpose  
Represents the **status and results** of an analysis job.

### Used for:
- `/v1/jobs/{id}`
- `/v1/jobs/{id}/result`
- Phase 10 real‑time progress updates

### Field meanings  
- `job_id`: unique identifier  
- `status`: queued → running → done/error  
- `result`: plugin output (only when done)  
- `error`: error message (only when error)  
- `created_at`: timestamp  
- `completed_at`: timestamp or `None`  
- `plugin`: plugin used  
- `progress`: optional 0–100 progress indicator  

### Notes  
This model is the **Phase 9 typed response contract**.

---

# 5. **PluginMetadata**

```python
class PluginMetadata(BaseModel):
    name: str
    description: str
    version: str
    inputs: List[str]
    outputs: List[str]
    permissions: List[str]
    config_schema: Optional[Dict[str, Any]]
```

### Purpose  
Defines the **metadata schema** for all plugins.

### Used for:
- Plugin registry  
- Plugin inspector panel (Phase 10)  
- MCP manifest generation  

### Key features  
- Validates plugin name and description  
- Supports semantic versioning  
- Supports input/output type declarations  
- Supports permission declarations  
- Supports optional JSON schema for configuration  

### Notes  
This is the foundation for Phase 10’s plugin pipeline upgrade.

---

# 6. **AnalysisResult**

```python
class AnalysisResult(BaseModel):
    text: str
    blocks: List[Dict[str, Any]]
    confidence: float
    language: Optional[str]
    error: Optional[str]
    extra: Optional[Dict[str, Any]]
```

### Purpose  
Defines the **standard output contract** for plugin analysis.

### Used for:
- Plugin return values  
- JobResponse.result  
- Storage and serialization  

### Field meanings  
- `text`: extracted text (OCR, NLP, etc.)  
- `blocks`: detected regions (OCR blocks, bounding boxes, etc.)  
- `confidence`: 0.0–1.0  
- `language`: optional language code  
- `error`: optional plugin error  
- `extra`: plugin‑specific data  

### Notes  
This model ensures **cross‑plugin consistency**.

---

# 7. **MCPTool & MCPManifest**

### MCPTool

```python
class MCPTool(BaseModel):
    id: str
    title: str
    description: str
    inputs: List[str]
    outputs: List[str]
    invoke_endpoint: str
    permissions: List[str]
```

### MCPManifest

```python
class MCPManifest(BaseModel):
    tools: List[MCPTool]
    server: Dict[str, str]
    version: str
```

### Purpose  
These models define the **Machine Control Protocol (MCP)** interface for exposing plugin tools.

### Used for:
- Tool discovery  
- Plugin capability introspection  
- Future multi‑plugin orchestration  

### Notes  
Phase 10 will extend these for real‑time tool invocation.

---

# 8. **WebSocketMessage**

```python
class WebSocketMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime
```

### Purpose  
Defines the **message protocol** for real‑time communication.

### Used for:
- Streaming frames  
- Streaming progress  
- Streaming plugin results  
- Heartbeats (ping/pong)  

### Notes  
This is the backbone of Phase 10’s real‑time insights channel.

---

# 9. **PluginToolRunRequest & PluginToolRunResponse**

### PluginToolRunRequest

```python
class PluginToolRunRequest(BaseModel):
    args: Dict[str, Any]
```

### PluginToolRunResponse

```python
class PluginToolRunResponse(BaseModel):
    tool_name: str
    plugin_id: str
    result: Dict[str, Any]
    processing_time_ms: int
```

### Purpose  
Defines the request/response schema for **running plugin tools**.

### Used for:
- Tool invocation API  
- Plugin inspector panel  
- Real‑time tool execution (Phase 10)  

### Notes  
These models unify plugin execution across all plugin types.

---

# 10. **How These Models Fit Together**

Here’s the high‑level flow:

```
AnalyzeRequest  →  Job created
                   ↓
               JobResponse (status=queued/running)
                   ↓
             Plugin executes → AnalysisResult
                   ↓
               JobResponse (status=done)
                   ↓
          WebSocketMessage (Phase 10 real‑time)
```

Plugins use:

```
PluginMetadata
AnalysisResult
PluginToolRunRequest
PluginToolRunResponse
```

The MCP layer uses:

```
MCPTool
MCPManifest
```

---

# 11. **Phase 9 Guarantees**

These models guarantee:

- Typed API boundaries  
- Stable response shapes  
- Plugin‑agnostic result schemas  
- Real‑time extensibility for Phase 10  
- Consistent OpenAPI documentation  

They are the **foundation** for all future phases.

---
Roger, let’s build the **three Phase‑9‑aligned, Phase‑10‑ready documents** you asked for.  
They’re clean, architectural, and written exactly in the style of your `.ampcode` notes.

No fluff — just the diagrams and guides you need.

---

# ⭐ **1. Diagram — How All Models Relate**  
### *Drop into:* `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MODEL_RELATION_DIAGRAM.md`

```
                         ┌──────────────────────────┐
                         │        AnalyzeRequest     │
                         │  (incoming API request)   │
                         └───────────────┬───────────┘
                                         │
                                         ▼
                         ┌──────────────────────────┐
                         │      JobResponse          │
                         │ (status + result wrapper) │
                         └───────────────┬───────────┘
                                         │
                                         │ result (when DONE)
                                         ▼
                         ┌──────────────────────────┐
                         │     AnalysisResult        │
                         │ (plugin output contract)  │
                         └───────────────┬───────────┘
                                         │
                                         │ produced by plugin
                                         ▼
                         ┌──────────────────────────┐
                         │     PluginMetadata        │
                         │ (declares capabilities)   │
                         └───────────────┬───────────┘
                                         │
                                         │ used to build
                                         ▼
                         ┌──────────────────────────┐
                         │         MCPTool           │
                         │ (tool definition)         │
                         └───────────────┬───────────┘
                                         │
                                         │ aggregated into
                                         ▼
                         ┌──────────────────────────┐
                         │       MCPManifest         │
                         │ (all tools + server info) │
                         └───────────────┬───────────┘
                                         │
                                         │ used by clients
                                         ▼
                         ┌──────────────────────────┐
                         │    PluginToolRunRequest   │
                         │ (invoke plugin tool)      │
                         └───────────────┬───────────┘
                                         │
                                         ▼
                         ┌──────────────────────────┐
                         │   PluginToolRunResponse   │
                         │ (tool execution result)   │
                         └───────────────┬───────────┘
                                         │
                                         │ streamed in Phase 10 via
                                         ▼
                         ┌──────────────────────────┐
                         │     WebSocketMessage      │
                         │ (frame/result/status/etc) │
                         └───────────────────────────┘
```


