# 🚀 **ForgeSyte Plugin Development Guide (Updated for BasePlugin + Tools)**

ForgeSyte plugins are Python packages that implement a simple, explicit contract.  
They extend the vision capabilities of ForgeSyte without modifying the server.

This guide describes the **new plugin architecture** introduced in 2026.

---

# 🧱 Plugin Contract Overview

ForgeSyte plugins must now subclass **`BasePlugin`** and expose **tools**, not `analyze()`.

### ✔ Required

- A unique plugin name  
- A `tools` dictionary mapping tool names → callables  
- A `run_tool(tool_name, args)` method  
- JSON‑serializable outputs  
- Installation via Python entry points (`forgesyte.plugins`)

### ✔ Optional

- A `validate()` hook for model loading or environment checks  
- Any number of tools  
- Async or sync tool implementations  

---

# 🧩 Plugin Contract (New)

```python
from app.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "my_plugin"

    def __init__(self):
        self.tools = {
            "detect": self.detect,
            "classify": self.classify,
        }
        super().__init__()

    def run_tool(self, tool_name: str, args: dict):
        return self.tools[tool_name](**args)

    def detect(self, image_base64: str):
        ...

    def classify(self, image_base64: str):
        ...
```

### Key Points

- Tools receive **named arguments** matching the manifest schema  
- Tools must return **JSON‑serializable** results  
- Tools must raise exceptions for invalid input (caught by the server)  

---

# 🔌 Tool Execution Endpoint

All tools are invoked through:

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

Example:

```bash
curl -X POST \
  http://localhost:8000/v1/plugins/yolo-tracker/tools/player_detection/run \
  -H "Content-Type: application/json" \
  -d '{"frame_base64": "<...>"}'
```

---

# 📦 Plugin Packaging & Entry Points

Plugins must be installed via pip and expose an entry point:

**pyproject.toml**

```toml
[project.entry-points."forgesyte.plugins"]
yolo-tracker = "forgesyte_yolo_tracker.plugin:Plugin"
```

ForgeSyte discovers plugins automatically at startup.

---

# 🧪 Plugin Development Checklist (Updated)

### 1. Structure & Setup
- [ ] Create package: `my_plugin/`
- [ ] Add `plugin.py` with class `Plugin(BasePlugin)`
- [ ] Add entry point in `pyproject.toml`
- [ ] Plugin imports without errors

### 2. Implement Contract
- [ ] `name` attribute defined
- [ ] `tools` dict maps tool names → callables
- [ ] `run_tool()` implemented
- [ ] Each tool accepts keyword args
- [ ] Each tool returns JSON‑serializable dict

### 3. Validation & Errors
- [ ] Tools validate inputs
- [ ] Tools raise exceptions for invalid data
- [ ] Plugin logs errors using `logging`
- [ ] Optional: implement `validate()` for model loading

### 4. Documentation
- [ ] Document each tool’s input schema
- [ ] Document output schema
- [ ] Document model requirements
- [ ] Document configuration options (if any)

### 5. Testing
- [ ] Plugin loads via entry points
- [ ] Tools execute successfully
- [ ] Invalid inputs produce JSON errors
- [ ] Concurrency safe
- [ ] `validate()` runs without errors

---

# 📁 Plugin Structure

```
my_plugin/
├── pyproject.toml
├── my_plugin/
│   ├── __init__.py
│   └── plugin.py
└── README.md
```

---

# 🧪 Minimal Plugin Example (New Model)

```python
from app.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "example"

    def __init__(self):
        self.tools = {
            "count_bytes": self.count_bytes,
        }
        super().__init__()

    def run_tool(self, tool_name, args):
        return self.tools[tool_name](**args)

    def count_bytes(self, image_base64: str):
        import base64
        data = base64.b64decode(image_base64)
        return {"byte_count": len(data)}
```

---

# 🧠 Using `validate()` for Model Loading

```python
class Plugin(BasePlugin):
    name = "ml_plugin"

    def __init__(self):
        self.tools = {"predict": self.predict}
        self.model = None
        super().__init__()

    def validate(self):
        # Load model once at startup
        self.model = load_model()

    def predict(self, image_base64: str):
        img = decode(image_base64)
        return self.model.predict(img)
```

---

# 🔍 Plugin Discovery (Updated)

ForgeSyte loads plugins via entry points:

1. Read entry points from installed packages  
2. Import the module  
3. Instantiate `Plugin()`  
4. Validate BasePlugin contract  
5. Register tools  

No filesystem scanning.  
No manual registration.

---

# 🧪 Testing Your Plugin

### Manual Test

```bash
uv run fastapi dev app/main.py
```

```bash
curl -X POST \
  http://localhost:8000/v1/plugins/my_plugin/tools/count_bytes/run \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "<...>"}'
```

### Programmatic Test

```python
from app.plugin_loader import registry

plugin = registry.get("my_plugin")
result = plugin.run_tool("count_bytes", {"image_base64": "..."})
print(result)
```

---

# 🛠️ Guidelines

### Code Quality
- Use type hints  
- Keep tools small and pure  
- Avoid global state  

### Resource Management
- Load heavy models in `validate()`  
- Release resources in `on_unload()` (optional)  

### Dependencies
- Keep minimal  
- Document system dependencies  
- Handle missing dependencies gracefully  

### Performance
- Tools should return within ~10 seconds  
- Cache models  
- Avoid reloading resources per call  

### Logging
- Use `logging` module  
- Log errors with context  
- Avoid logging sensitive data  

---

# 🧩 Common Patterns

### Lazy Model Loading  
### Configurable Tools  
### Async Tools  
### Multi‑Tool Plugins  
### GPU/CPU Switching  

(Your original examples still apply — just replace `analyze()` with tool functions.)

---

# 🛠️ Troubleshooting (Updated)

### Plugin Not Loading
- Missing entry point  
- Plugin not subclassing BasePlugin  
- Missing `tools` dict  
- Tool not callable  

### Tool Not Found
- Tool name not in `tools` dict  
- Typo in endpoint URL  

### Invalid JSON from Tool
- Tool raised an exception without returning JSON  
- Tool returned non‑serializable data  

---

# 📚 API Reference (Updated)

### BasePlugin

```python
class BasePlugin(ABC):
    name: str
    tools: Dict[str, Callable]

    def run_tool(self, tool_name: str, args: dict) -> Any: ...
    def validate(self) -> None: ...
```

### Tool Execution Endpoint

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

---

# 📎 See Also

- `ARCHITECTURE.md`  
- `CONTRIBUTING.md`  
- Example plugins in `forgesyte-plugins/`  

---

