Roger, here’s the clean, grounded answer you actually need — **how to start Phase 13**, not scattered patches, not Phase 14 abstractions, but the *real entry point* for implementing Phase 13 in your repo.

I’ll give you:

- **Where to start (the exact first file + first function)**
- **The correct order of implementation**
- **The minimal scaffolding you need before writing any logic**
- **How to integrate with existing Phase 12/Phase 13 code**
- **What NOT to touch yet**

This is the “start here” map you were missing.

---

# ⭐ PHASE 13 — WHERE TO START  
### **Start at the server, not the UI.**  
VideoTracker is a UI shell.  
Phase 13’s foundation is **server‑side pipeline execution**.

The first file you must create is:

```
server/app/services/video_pipeline_service.py
```

This is the *root* of Phase 13.

Everything else (UI, WebSocket, REST) plugs into this.

---

# ⭐ STEP 1 — Create the Phase 13 Pipeline Executor (Server)

Create the file:

```
server/app/services/video_pipeline_service.py
```

Add the empty skeleton:

```python
class VideoPipelineService:
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager

    def run_pipeline(self, plugin_id: str, tools: list[str], payload: dict) -> dict:
        """Execute a linear pipeline of tools inside a single plugin."""
        raise NotImplementedError
```

This is the **first commit** of Phase 13.

Nothing else should be started until this file exists.

---

# ⭐ STEP 2 — Wire the executor into REST (Background VideoTracker)

Open:

```
server/app/routes_video.py
```

Add the endpoint skeleton:

```python
@router.post("/video/pipeline")
async def run_video_pipeline(req: PipelineRequest):
    result = pipeline_service.run_pipeline(
        plugin_id=req.plugin_id,
        tools=req.tools,
        payload=req.payload,
    )
    return {"result": result}
```

This is the **second commit**.

Still no logic — just wiring.

---

# ⭐ STEP 3 — Wire the executor into WebSocket (Streaming)

Open:

```
server/app/services/vision_analysis.py
```

Replace the single‑tool logic with the pipeline call:

```python
result = self.video_pipeline_service.run_pipeline(
    plugin_id=plugin_id,
    tools=tools,
    payload=payload,
)
```

This is the **third commit**.

Still no logic — just routing.

---

# ⭐ STEP 4 — Add validation (still server‑side)

Inside `VideoPipelineService` add:

```python
def _validate(self, plugin_id, tools):
    raise NotImplementedError
```

This is the **fourth commit**.

No logic yet — just structure.

---

# ⭐ STEP 5 — Only now touch the UI

After the server can *accept* a pipeline, the UI can *send* one.

Modify:

```
web-ui/src/components/VideoTracker/VideoTracker.tsx
```

Add:

```ts
const [selectedTools, setSelectedTools] = useState<string[]>([])
```

And send:

```ts
runPipeline(selectedPluginId, selectedTools, payload)
```

This is the **fifth commit**.

---

# ⭐ STEP 6 — Add WebSocket pipeline sending

Modify:

```
web-ui/src/hooks/useWebSocket.ts
```

Send:

```ts
sendJsonMessage({
  type: "frame",
  frame_id,
  image_data,
  plugin_id: selectedPluginId,
  tools: selectedTools,
})
```

This is the **sixth commit**.

---

# ⭐ STEP 7 — Only now implement the executor logic

Return to:

```
server/app/services/video_pipeline_service.py
```

Implement:

```python
result = payload
for tool in tools:
    result = self.plugin_manager.run_plugin_tool(plugin_id, tool, result)
return result
```

This is the **seventh commit**.

---

# ⭐ STEP 8 — Add logging (Phase 13 requirement)

Inside the loop:

```python
logger.info(
    "Video pipeline step",
    extra={
        "plugin_id": plugin_id,
        "tool_name": tool,
        "step": idx,
    },
)
```

This is the **eighth commit**.

---

# ⭐ STEP 9 — Add tests (Phase 13 acceptance tests)

Add:

```
server/app/tests/test_video_pipeline_rest.py
server/app/tests/test_video_pipeline_ws.py
server/app/tests/test_pipeline_validation.py
```

This is the **ninth commit**.

---

# ⭐ STEP 10 — Remove all fallback logic

Remove:

- `"default"` tool fallback in WebSocket
- “first tool” fallback in tasks.py

This is the **tenth commit**.

---

# ⭐ WHAT NOT TO TOUCH YET

Do **NOT** touch:

- DAG logic  
- Cross‑plugin logic  
- Pipeline registry  
- Tool capabilities  
- Phase 14 structures  
- UI DAG editors  
- Plugin manifests  

Phase 13 is **linear pipelines inside one plugin**.  
Phase 14 is **cross‑plugin DAGs**.

Keep them cleanly separated.

---

# ⭐ TL;DR — Where to start Phase 13

### **Start here:**
```
server/app/services/video_pipeline_service.py
```

### **Then wire it:**
- REST → `/video/pipeline`
- WebSocket → `VisionAnalysisService`

### **Then UI:**
- Send `plugin_id` + `tools[]` in REST + WS

### **Then implement logic + logging**

### **Then tests**

This is the correct, clean, Phase‑13‑aligned starting point.

