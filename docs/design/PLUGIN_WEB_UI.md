# **PLUGIN_WEB-UI.md**  
### *How the Web‑UI Interacts with Server Plugins in ForgeSyte*

ForgeSyte’s Web‑UI is not a static React application.  
It is a **dynamic plugin host** that adapts to whatever plugins the server exposes.

This document explains how the Web‑UI discovers plugins, renders plugin‑driven UI, and executes plugin tools.

---

# 🧭 Overview

ForgeSyte plugins live on the **server**.  
The Web‑UI does **not** contain plugin‑specific code.

Instead:

- The server exposes plugin metadata and tool schemas  
- The Web‑UI fetches this metadata  
- The Web‑UI renders UI dynamically  
- The Web‑UI calls plugin tools via `/v1/plugins/<plugin>/tools/<tool>/run`  
- The Web‑UI renders results generically  

This architecture ensures:

- No hardcoded plugin names  
- No plugin‑specific React components  
- No UI changes required when adding new plugins  
- Full compatibility with OCR, YOLO, Motion, Radar, or future plugins  

---

# 🏗️ High‑Level Architecture

```text
                          ┌──────────────────────────────────────────┐
                          │                Web‑UI                    │
                          │     (React • Dynamic Plugin Host)        │
                          └───────────────────────┬──────────────────┘
                                                  │
                                                  │ 1. Fetch plugin list
                                                  │    GET /v1/plugins
                                                  ▼
                     ┌────────────────────────────────────────────────────┐
                     │               UI Plugin Manager                    │
                     │────────────────────────────────────────────────────│
                     │ • Stores plugin metadata from server               │
                     │ • Populates PluginSelector                         │
                     │ • Drives dynamic rendering in ResultsPanel         │
                     └───────────────────────┬────────────────────────────┘
                                             │
                                             │ 2. User selects plugin
                                             ▼
                     ┌────────────────────────────────────────────────────┐
                     │               PluginSelector.tsx                   │
                     │────────────────────────────────────────────────────│
                     │ • Renders list from metadata                       │
                     │ • No hard‑coded plugin names                       │
                     │ • Emits selected plugin + tool                     │
                     └───────────────────────┬────────────────────────────┘
                                             │
                                             │ 3. POST /v1/plugins/<plugin>/tools/<tool>/run
                                             │    Body:
                                             │    • args (JSON)
                                             │    • frame_base64 / image_base64
                                             ▼
                     ┌────────────────────────────────────────────────────┐
                     │                 ForgeSyte API                      │
                     │────────────────────────────────────────────────────│
                     │ • Validates request                                │
                     │ • Dispatches to PluginManager                      │
                     └───────────────────────┬────────────────────────────┘
                                             │
                                             │ 4. registry.get(plugin).run_tool(tool, args)
                                             ▼
                     ┌────────────────────────────────────────────────────┐
                     │                 PluginManager                      │
                     │────────────────────────────────────────────────────│
                     │ • Discovers plugins via entry points               │
                     │ • Validates BasePlugin contract                    │
                     │ • Exposes tools + schemas                          │
                     └───────────────────────┬────────────────────────────┘
                                             │
                                             │ 5. plugin.run_tool(tool, args)
                                             ▼
                     ┌────────────────────────────────────────────────────┐
                     │                     Plugin                         │
                     │────────────────────────────────────────────────────│
                     │ • Tool-specific logic                              │
                     │ • Returns JSON result                              │
                     └───────────────────────┬────────────────────────────┘
                                             │
                                             │ 6. Return JSON result
                                             ▼
                     ┌────────────────────────────────────────────────────┐
                     │                ResultsPanel.tsx                    │
                     │────────────────────────────────────────────────────│
                     │ • Renders result generically                       │
                     │ • No plugin-specific UI logic                      │
                     └────────────────────────────────────────────────────┘
```

---

# 🔌 Server Plugin Model (Summary)

Server plugins must:

- Subclass `BasePlugin`
- Define `name`
- Define `tools: dict[str, callable]`
- Implement `run_tool(tool_name, args)`
- Return JSON‑serializable results

Example:

```python
class Plugin(BasePlugin):
    name = "yolo-tracker"

    def __init__(self):
        self.tools = {
            "player_detection": self.player_detection,
            "ball_detection": self.ball_detection,
        }
        super().__init__()

    def run_tool(self, tool_name, args):
        return self.tools[tool_name](**args)
```

---

# 🧩 Web‑UI Plugin Model

The Web‑UI does **not** implement plugins.  
It **hosts** plugins exposed by the server.

The Web‑UI has three core responsibilities:

1. **Discover plugins**  
2. **Render plugin‑driven UI**  
3. **Execute plugin tools**  

---

# 1. Plugin Discovery (Web‑UI)

The Web‑UI fetches plugin metadata at startup:

```ts
GET /v1/plugins
```

Each plugin entry includes:

```ts
{
  name: string,
  description: string,
  version: string,
  tools: {
    [toolName: string]: {
      description: string,
      input_schema: object,
      output_schema: object
    }
  }
}
```

This metadata drives:

- PluginSelector  
- ToolSelector  
- Dynamic forms  
- Dynamic result rendering  

---

# 2. UI Plugin Manager

`uiPluginManager.ts` is responsible for:

- Fetching plugin metadata  
- Caching plugin list  
- Exposing helper functions:

```ts
getPlugins()
getPlugin(name)
getTools(pluginName)
getToolSchema(pluginName, toolName)
```

This keeps React components clean and declarative.

---

# 3. PluginSelector.tsx

Responsibilities:

- Render plugin list from metadata  
- Render tool list for selected plugin  
- Emit `(pluginName, toolName)` to parent components  
- No hardcoded plugin names  
- No plugin‑specific UI logic  

---

# 4. Tool Execution (runTool)

All tool execution goes through the unified runner:

```ts
runTool({
  pluginId,
  toolName,
  args
})
```

This handles:

- Logging  
- Retry  
- Error normalization  
- JSON parsing  
- Timing metrics  

The Web‑UI never calls `fetch()` directly for plugin tools.

---

# 5. ResultsPanel.tsx

Responsibilities:

- Render results generically  
- No plugin‑specific branches  
- Use schemas to interpret fields  
- Support:
  - bounding boxes  
  - labels  
  - confidence  
  - text  
  - structured JSON  

Example:

```ts
if (result.boxes) renderBoxes(result.boxes)
if (result.text) renderText(result.text)
if (result.error) renderError(result.error)
```

---

# 6. Video + Frame‑Based Plugins

For plugins like YOLO:

- `useVideoProcessor` captures frames  
- Each frame is sent to:

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

- Results are streamed back into the UI  
- The UI overlays bounding boxes on the video  

This is fully plugin‑agnostic.

---

# 🧠 Architectural Invariants

These rules keep the UI plugin‑agnostic:

### ✔ No hardcoded plugin names  
### ✔ No plugin‑specific React components  
### ✔ All plugins discovered via `/v1/plugins`  
### ✔ All tools executed via `/run`  
### ✔ All results rendered generically  
### ✔ Adding a plugin requires **zero UI changes**  

---

# 🧪 Testing UI Plugins

Tests should verify:

- Plugin list is fetched  
- PluginSelector renders dynamically  
- runTool is called with correct args  
- ResultsPanel renders generic fields  
- No plugin‑specific branches exist  

---

# 🎯 Summary

The Web‑UI is a **dynamic plugin host**, not a static app.

- Server plugins define tools  
- Web‑UI discovers them  
- Web‑UI renders them  
- Web‑UI executes them  
- Web‑UI displays results generically  

This architecture supports:

- OCR  
- YOLO tracking  
- Motion detection  
- Radar  
- Future plugins  

…without ever modifying the UI.

---

