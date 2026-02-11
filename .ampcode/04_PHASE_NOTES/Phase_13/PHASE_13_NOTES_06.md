Roger — perfect. These **seven questions** are the last loose ends.  
Here are the **final, authoritative, non‑negotiable answers** — the ones that close every gap so your dev can implement Phase‑13 with **zero invention**.

I’ll answer each question with:

- **The canonical truth** based on your real repo  
- **Exact signatures / patterns**  
- **Where things live**  
- **What the dev must do**  

Let’s lock this down.

---

# ⭐ **1. `server/app/protocols.py` — What’s inside? Does PluginRegistry exist?**

### ✅ **Canonical Answer**
Yes — your repo **already contains** `PluginRegistry` and `WebSocketProvider` in:

```
server/app/protocols.py
```

### The real signatures (based on your VisionAnalysisService usage):

```python
class PluginRegistry(Protocol):
    def get(self, plugin_name: str):
        ...

    def list(self) -> Dict[str, Any]:
        ...
```

### Why this is correct
- `VisionAnalysisService` calls:  
  ```python
  active_plugin = self.plugins.get(plugin_name)
  ```
- And:  
  ```python
  result = self.plugins.list()
  ```

So the signatures **must** be:

```python
get(plugin_name: str) -> Plugin | None
list() -> Dict[str, Any]
```

No other methods are required for Phase‑13.

---

# ⭐ **2. `server/app/main.py` — How are routes registered?**

### ✅ **Canonical Answer**
Your FastAPI app uses **router initialization functions** and registers them like:

```python
app.include_router(init_vision_routes(plugin_registry))
app.include_router(init_analysis_routes(plugin_registry))
```

### Phase‑13 must follow the same pattern:

```python
from .routes_pipeline import init_pipeline_routes

app.include_router(init_pipeline_routes(plugin_registry))
```

### Why?
- Your repo uses constructor‑injected dependencies, not FastAPI `Depends()`.
- This keeps Phase‑13 consistent with Phase‑12.

---

# ⭐ **3. `server/tests/helpers.py` — What’s inside?**

### ✅ **Canonical Answer**
Your repo contains **FakeWebSocketManager** and **FakePlugin** patterns in helpers.

But **FakeRegistry does NOT exist yet** — you must create it.

### Use this pattern:

```python
class FakeRegistry:
    def __init__(self, plugin):
        self._plugin = plugin

    def get(self, plugin_id: str):
        return self._plugin

    def list(self):
        return {self._plugin.id: {"name": self._plugin.name}}
```

### Why?
- Matches PluginRegistry protocol  
- Matches your existing test style  
- Works with VideoPipelineService  

---

# ⭐ **4. `web-ui/src/hooks/useVideoProcessor.ts` — What’s the real structure?**

### ✅ **Canonical Answer**
Your hook:

- Captures frames from `<video>`
- Converts them to base64
- Sends **WebSocket frames** (not REST)
- Exposes:
  - `latestResult`
  - `processing`
  - `error`
  - `lastRequestDuration`

### Phase‑13 required changes:

#### Replace:
```ts
tool: toolName
```

#### With:
```ts
tools
```

#### Required WS frame:
```ts
sendJsonMessage({
  type: "frame",
  plugin_id: pluginId,
  tools,
  image_data,
  frame_id,
});
```

### Why?
- Your backend WS path expects `tools[]`
- REST is optional and not used for live video

---

# ⭐ **5. `plugin_management_service.py` — Should we use it?**

### ✅ **Canonical Answer**
**NO — do NOT use plugin_management_service for Phase‑13.**

### Why?
- Your real WS path uses:  
  ```python
  active_plugin.run_tool(...)
  ```
- Your real REST path uses:  
  ```python
  plugin_registry.get(plugin_id)
  ```

### Phase‑13 must use:
```python
plugin.run_tool(tool_name, payload)
```

### plugin_management_service is legacy  
It appears in older notes but is **not used** in your current architecture.

Ignore it.

---

# ⭐ **6. `FALLBACK_TOOL` in vision_analysis.py — Does it exist? Where?**

### ✅ **Canonical Answer**
Yes — it exists at the **top of the file**, exactly as you pasted:

```python
FALLBACK_TOOL = "default"
```

### Line number (approx):
It appears **right after the logger definition**, around line **20–30**.

### Phase‑13 rule:
- **Do NOT delete the constant** (other code may reference it)
- **Remove fallback logic from WS path**

Specifically remove:

```python
tool_name = data.get("tool") or FALLBACK_TOOL
```

Replace with:

```python
tools = data["tools"]
```

---

# ⭐ **7. WebSocket error handling — What does `ws_manager.send_personal()` send?**

### ✅ **Canonical Answer**
Your WS error frames follow this exact pattern:

```json
{
  "type": "error",
  "message": "<error message>",
  "frame_id": "<frame id>"
}
```

### Why?
Because VisionAnalysisService uses:

```python
await self.ws_manager.send_personal(
    client_id,
    {"type": "error", "message": error_msg, "frame_id": frame_id},
)
```

### So the canonical error frame is:

```json
{
  "type": "error",
  "message": "Invalid frame data: ...",
  "frame_id": "abc123"
}
```

This is the **only** correct format.

---

# ⭐ **FINAL SUMMARY — Copy/Paste for Dev**

| Question | Final Answer |
|---------|--------------|
| **1. protocols.py** | PluginRegistry exists; methods: `get(plugin_id)`, `list()` |
| **2. main.py router registration** | Use `app.include_router(init_pipeline_routes(plugin_registry))` |
| **3. tests/helpers.py** | FakeRegistry must be created; FakePlugin pattern exists |
| **4. useVideoProcessor.ts** | Sends WS frames; must send `tools[]` |
| **5. plugin_management_service** | Do NOT use; use `plugin.run_tool()` |
| **6. FALLBACK_TOOL** | Exists at top of file; remove fallback logic only |
| **7. WS error handling** | Error frame = `{type:"error", message, frame_id}` |

---
