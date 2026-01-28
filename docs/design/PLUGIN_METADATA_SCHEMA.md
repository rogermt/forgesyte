# **Plugin Metadata Schema Documentation (Updated for BasePlugin + Tools)**  
**Last Updated:** 2026‑01‑28  
**Status:** Implemented  
**Version:** 2.0.0  

## Overview

ForgeSyte plugins now follow the **BasePlugin + Tools** architecture.

Each plugin exposes:

- A unique plugin name  
- A human‑readable description  
- A semantic version  
- A dictionary of **tools**, each with:
  - description  
  - input schema  
  - output schema  

This metadata is used by:

- The Web‑UI (dynamic plugin host)  
- The MCP adapter (Gemini‑CLI)  
- The `/v1/plugins` endpoint  
- The unified `runTool()` execution path  

---

# 📦 Plugin Metadata Model (Plugin‑Level)

```python
class PluginMetadata(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    tools: Dict[str, ToolMetadata]
```

### Fields

### `name` (required)
- Unique plugin identifier  
- Lowercase, hyphens/underscores allowed  
- Used in:
  - `/v1/plugins/<plugin>/tools/...`
  - MCP tool IDs  
  - UI plugin selector  

### `description` (required)
- Human‑readable description  
- Displayed in UI and MCP manifest  

### `version` (optional)
- Semantic version  
- Defaults to `"1.0.0"`  

### `tools` (required)
A dictionary mapping tool names → tool metadata.

Example:

```json
{
  "player_detection": { ... },
  "ball_detection": { ... }
}
```

---

# 🧩 Tool Metadata Model (Tool‑Level)

```python
class ToolMetadata(BaseModel):
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
```

### Fields

### `description` (required)
- Human‑readable description of the tool  
- Shown in UI tool selector  

### `input_schema` (required)
JSON‑schema‑like structure describing expected arguments.

Example:

```json
{
  "frame_base64": {
    "type": "string",
    "description": "Base64‑encoded video frame"
  },
  "threshold": {
    "type": "number",
    "default": 0.5,
    "min": 0.0,
    "max": 1.0
  }
}
```

### `output_schema` (required)
Describes the shape of the tool’s output.

Example:

```json
{
  "detections": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "bbox": {"type": "array", "items": {"type": "number"}},
        "confidence": {"type": "number"},
        "label": {"type": "string"}
      }
    }
  }
}
```

---

# 🧱 Example Full Plugin Metadata

```json
{
  "name": "yolo-tracker",
  "description": "YOLOv8-based player and ball detection",
  "version": "1.2.0",
  "tools": {
    "player_detection": {
      "description": "Detect players in a frame",
      "input_schema": {
        "frame_base64": {"type": "string"}
      },
      "output_schema": {
        "detections": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "bbox": {"type": "array"},
              "confidence": {"type": "number"},
              "label": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

---

# 🔌 How Plugins Provide Metadata

Plugins implement:

```python
class Plugin(BasePlugin):
    name = "yolo-tracker"
    description = "YOLOv8-based player and ball detection"
    version = "1.2.0"

    def __init__(self):
        self.tools = {
            "player_detection": {
                "description": "Detect players in a frame",
                "input_schema": {...},
                "output_schema": {...},
            }
        }
        super().__init__()
```

The server converts this into `PluginMetadata` + `ToolMetadata`.

---

# 🌐 `/v1/plugins` Response Shape

```json
{
  "plugins": [
    {
      "name": "yolo-tracker",
      "description": "YOLOv8-based player and ball detection",
      "version": "1.2.0",
      "tools": {
        "player_detection": {
          "description": "Detect players in a frame",
          "input_schema": {...},
          "output_schema": {...}
        }
      }
    }
  ]
}
```

---

# 🤖 MCP Integration (Updated)

Each tool becomes an MCP tool:

```
id: vision.<plugin>.<tool>
invoke_endpoint: /v1/plugins/<plugin>/tools/<tool>/run
input_schema: tool.input_schema
output_schema: tool.output_schema
```

Example:

```json
{
  "id": "vision.yolo-tracker.player_detection",
  "title": "Player Detection",
  "description": "Detect players in a frame",
  "input_schema": {...},
  "output_schema": {...},
  "invoke_endpoint": "/v1/plugins/yolo-tracker/tools/player_detection/run"
}
```

---

# 🧪 Validation Rules

### Plugin‑level
- `name`: non‑empty string  
- `description`: non‑empty string  
- `version`: semantic version  
- `tools`: non‑empty dict  

### Tool‑level
- `description`: non‑empty  
- `input_schema`: dict  
- `output_schema`: dict  

---

# 🧠 Best Practices

- Keep schemas small and explicit  
- Use JSON‑schema conventions  
- Provide defaults for optional fields  
- Document every argument  
- Keep output schemas stable across versions  
- Increment version on breaking changes  

---

# 🎯 Summary

This updated schema:

- Matches your BasePlugin + tools architecture  
- Powers the Web‑UI dynamic plugin host  
- Powers the MCP manifest  
- Ensures consistent plugin behavior  
- Eliminates the old `metadata()` + `analyze()` model  

This is now the **canonical Plugin Metadata Schema** for ForgeSyte.

---

]