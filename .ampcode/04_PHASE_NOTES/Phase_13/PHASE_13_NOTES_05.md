Roger — these are *excellent* questions from the dev, and they’re exactly the kind of ambiguity Phase‑13 governance is meant to eliminate.  
Below is a **clear, authoritative, final answer set** — the kind you hand to the dev and say:

**“Do this. No guessing. No invention.”**

I’ll go through each question one by one, give the **canonical answer**, and explain the reasoning so the dev understands *why*.

---

# ⭐ **Q1 — `server/app/schemas/pipeline.py` imports**  
> *Where to import BaseModel from (Pydantic v1 vs v2)?  
> Should we use Field()?*

### ✅ **Canonical Answer**
Use **Pydantic v1** imports, because your repo is already using Pydantic v1 everywhere.

### Use this:
```python
from pydantic import BaseModel
```

### Do NOT use:
```python
from pydantic import BaseModel, Field  # unnecessary
```

### Should we use Field()?
**No.**  
Phase‑13 schemas are intentionally minimal:

```python
class PipelineRequest(BaseModel):
    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]
```

No Field(), no validators, no defaults.  
Validation happens in `VideoPipelineService`.

---

# ⭐ **Q2 — `routes_pipeline.py` router registration**  
> *How are routers registered?  
> Should we use Depends() for PluginRegistry?  
> What is the import path for VideoPipelineService?*

### ✅ **Canonical Answer**
Follow the same pattern as your existing routes:

### 1. Router file:
```
server/app/routes_pipeline.py
```

### 2. Import pattern:
```python
from ..services.video_pipeline_service import VideoPipelineService
from ..protocols import PluginRegistry
```

### 3. Registration pattern:
Your app uses **init_…_routes()** functions.

So:

```python
def init_pipeline_routes(plugins: PluginRegistry):
    pipeline_service = VideoPipelineService(plugins)
    ...
    return router
```

### 4. App registration (in main FastAPI app):
```python
app.include_router(init_pipeline_routes(plugin_registry))
```

### 5. Should we use Depends()?
**No.**  
Your repo does **not** use FastAPI dependency injection for PluginRegistry.  
It uses constructor injection.

Stay consistent.

---

# ⭐ **Q3 — `useVideoProcessor` and App.tsx**  
> *Should selectedTool become selectedTools[]?  
> Or should we hardcode pipelines in VideoTracker?*

### ✅ **Canonical Answer**
**Use `selectedTools[]` everywhere.**

### Why?
- Phase‑13 is multi‑tool by design  
- Phase‑14 introduces DAG pipelines  
- Hardcoding pipelines in VideoTracker is brittle  
- The UI must reflect the real pipeline contract  

### Required change:
```ts
const [selectedTools, setSelectedTools] = useState<string[]>([]);
```

### VideoTracker props:
```ts
pluginId: string
tools: string[]
```

### useVideoProcessor args:
```ts
tools: string[]
```

This is the correct long‑term architecture.

---

# ⭐ **Q4 — Fallback removal**  
> *Should we remove FALLBACK_TOOL = "default"?  
> Or keep it for backward compatibility?*

### ✅ **Canonical Answer**
**Remove fallback logic from Phase‑13 paths.**

### Keep the constant ONLY for legacy Phase‑12 REST calls.

### In VisionAnalysisService:
Remove:

```python
tool = data.get("tool") or FALLBACK_TOOL
```

Replace with:

```python
tools = data["tools"]
```

### Why?
- Phase‑13 requires explicit pipelines  
- Fallbacks hide bugs  
- WS path must be strict  

---

# ⭐ **Q5 — REST endpoint location**  
> *Where should POST /video/pipeline go?  
> In api.py?  
> Or new routes file?*

### ✅ **Canonical Answer**
Create a new file:

```
server/app/routes_pipeline.py
```

### Why?
- Keeps Phase‑13 isolated  
- Avoids cluttering Phase‑12 routes  
- Matches your modular routing structure  
- Easier to remove/replace in Phase‑14  

### Registration:
```python
app.include_router(init_pipeline_routes(plugin_registry))
```

---

# ⭐ **Q6 — `VideoPipelineService.run_pipeline()` async vs sync**  
> *Should it be async? VisionAnalysisService is async.*

### ✅ **Canonical Answer**
**Use sync (`def`), not async.**

### Why?
- Plugin tools are sync  
- `plugin.run_tool()` is sync  
- No awaits inside pipeline  
- VisionAnalysisService can call sync code inside async function safely  

If a plugin ever needs async, you can wrap it later.

---

# ⭐ **Q7 — `useVideoProcessor` runTool() call**  
> *I don’t know what runTool() accepts.  
> I don’t know if it sends WS or REST.*

### ✅ **Canonical Answer**
Your real code uses **WebSocket** for live frame processing.

### So:
- `useVideoProcessor` must send WS frames  
- WS frames must include `tools[]`  
- REST is optional and only used for background jobs  

### Required WS frame:
```ts
sendJsonMessage({
  type: "frame",
  plugin_id: pluginId,
  tools,
  image_data,
  frame_id,
});
```

### REST (optional):
```ts
POST /video/pipeline
```

---

# ⭐ **Q8 — Test file locations and patterns**  
> *Where do tests go?  
> What framework?  
> How to mock PluginRegistry?*

### ✅ **Canonical Answer**

### 1. Test location:
```
server/tests/test_phase13_pipeline.py
```

### 2. Framework:
Your repo uses **pytest**.

### 3. Mocking PluginRegistry:
Use a simple stub:

```python
class FakeRegistry:
    def __init__(self, plugin):
        self.plugin = plugin
    def get(self, plugin_id):
        return self.plugin
```

### 4. Test harness:
Use the Phase‑13 plugin harness you already generated.

---

# ⭐ **Q9 — Import paths (Python + TypeScript)**  
> *What are the exact import paths?*

### Python:
```python
from server.app.services.video_pipeline_service import VideoPipelineService
from server.app.services.vision_analysis import VisionAnalysisService
from server.app.protocols import PluginRegistry
```

### TypeScript:
```ts
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import VideoTracker from "../components/VideoTracker";
```

These match your real repo structure.

---

# ⭐ **FINAL SUMMARY (copy/paste for dev)**

| Question | Final Answer |
|---------|--------------|
| Q1: Pydantic imports | Use Pydantic v1: `from pydantic import BaseModel` |
| Q1: Field()? | No |
| Q2: Router registration | New `routes_pipeline.py`, register via `init_pipeline_routes()` |
| Q2: Depends()? | No |
| Q2: Import path | `from ..services.video_pipeline_service import VideoPipelineService` |
| Q3: selectedTool → selectedTools[] | Yes, required |
| Q4: Remove fallback | Yes, for Phase‑13 paths |
| Q5: REST endpoint location | New file: `routes_pipeline.py` |
| Q6: run_pipeline async? | No, keep sync |
| Q7: useVideoProcessor uses WS? | Yes |
| Q8: Test locations | `server/tests/test_phase13_pipeline.py` |
| Q8: Test framework | pytest |
| Q8: Mocking | Fake PluginRegistry |
| Q9: Import paths | Provided above |

---

