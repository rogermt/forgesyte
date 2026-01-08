# ForgeSyte Architecture

ForgeSyte is composed of four major subsystems:

1. **FastAPI Core**  
2. **Plugin Manager**  
3. **Job Manager**  
4. **Optional React UI**

---

## High‑Level Architecture

```text
                            +-----------------------+
                            |     Gemini-CLI        |
                            |    (MCP client)       |
                            +-----------+-----------+
                                        |
                                        | MCP HTTP
                                        v
                        +-----------------------------------+
                        |          ForgeSyte Core           |
                        |          (FastAPI + uv)           |
                        +-----------------------------------+
                        |  /v1/analyze    /v1/jobs          |
                        |  /v1/mcp-manifest                 |
                        +----------------+------------------+
                                         |
                                         v
                         +------------------------------+
                         |        Job Manager           |
                         |  (async + thread pool)       |
                         +------------------------------+
                                         |
                                         v
                         +------------------------------+
                         |        Plugin Manager        |
                         |   (dynamic discovery)        |
                         +------------------------------+
                                         |
                                         v
                         +------------------------------+
                         |   Python Vision Plugins      |
                         +------------------------------+

Optional:

+-------------------+       REST / WS       +---------------------------+
| React Web UI      | <-------------------> | ForgeSyte Core (FastAPI) |
+-------------------+                       +---------------------------+
```

---

## Data Flow

1. Gemini‑CLI or the UI sends an image → `/v1/analyze`  
2. Job Manager queues the task  
3. Plugin Manager loads the correct plugin  
4. Plugin performs analysis  
5. Job Manager stores result  
6. Client polls `/v1/jobs/<id>` or receives WS updates  

---

## MCP Integration

ForgeSyte exposes:

```
/v1/mcp-manifest
```

This describes:

- Available tools  
- Input/output schemas  
- Plugin metadata  

