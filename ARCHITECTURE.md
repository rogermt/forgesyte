# 🚀 **ForgeSyte Architecture (Updated for Plugin Contract + Tool Runner)**

ForgeSyte is composed of four major subsystems:

1. **FastAPI Core**  
2. **Plugin Manager (Entry‑Point Based)**  
3. **Job Manager**  
4. **Optional React UI**

This document describes the high‑level architecture and the new plugin contract introduced in 2025–2026.

---

# 🏛️ High‑Level Architecture

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
                        |  /v1/plugins/.../run              |
                        |  /v1/analyze (legacy)             |
                        |  /v1/jobs                         |
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
                         |  (entry-point discovery)     |
                         |  (BasePlugin contract)       |
                         +------------------------------+
                                         |
                                         v
                         +------------------------------+
                         |   Python Vision Plugins      |
                         |  (YOLO, OCR, Motion, etc.)   |
                         +------------------------------+

Optional:

+-------------------+       REST / WS       +---------------------------+
| React Web UI      | <-------------------> | ForgeSyte Core (FastAPI) |
+-------------------+                       +---------------------------+
```

---

# 🔄 Data Flow (Updated)

1. Client (Gemini‑CLI or UI) calls:  
   ```
   POST /v1/plugins/<plugin>/tools/<tool>/run
   ```
2. Plugin Manager resolves plugin + tool  
3. Plugin executes tool via `run_tool()`  
4. Job Manager handles async execution (if needed)  
5. Result returned as JSON  
6. UI or CLI consumes result  

Legacy `/v1/analyze` still works for OCR‑style plugins but is being phased out.

---

# 🧩 Server Architecture

## MCP Module Structure

All Model Context Protocol (MCP) logic is consolidated in `server/app/mcp/`:

```
server/app/mcp/
├── __init__.py
├── adapter.py        # MCP adapter for plugin tools
├── handlers.py       # Request/response handlers
├── jsonrpc.py        # JSON-RPC protocol implementation
├── routes.py         # MCP HTTP endpoints
└── transport.py      # HTTP transport layer
```

### Key Update  
The MCP adapter now reflects the **plugin tool model**, not the old `analyze()` model.

---

## Server Core Modules

```
server/app/
├── mcp/                 # MCP protocol implementation
├── plugins/             # Plugin system (BasePlugin + registry)
├── api.py               # REST API endpoints (/v1/plugins/.../run)
├── auth.py              # Authentication & authorization
├── main.py              # FastAPI app initialization
├── models.py            # Pydantic schemas
├── plugin_loader.py     # Entry-point plugin discovery
├── tasks.py             # Job/task management
└── websocket_manager.py # WebSocket connections & streaming
```

### Key Update  
`plugin_loader.py` now loads plugins via entry points and enforces the `BasePlugin` contract.

---

# 🔌 Plugin System Architecture (Updated)

## Plugin Contract (New)

All plugins must now subclass `BasePlugin`:

```python
class BasePlugin(ABC):
    name: str
    tools: Dict[str, Callable]

    @abstractmethod
    def run_tool(self, tool_name: str, args: dict) -> Any:
        ...
```

### Why this change?

- Ensures consistent behavior across all plugins  
- Enables dynamic tool discovery  
- Enables MCP auto‑generation  
- Prevents malformed plugins from loading  
- Eliminates hardcoded plugin assumptions  

### Plugin Lifecycle

1. Plugin discovered via entry points  
2. Plugin instantiated  
3. Contract validated  
4. Optional `validate()` hook executed  
5. Tools registered in the registry  

### Tool Execution

All tools are invoked through:

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

This replaces the old `analyze()`‑only model.

---

# 🔐 Authentication & Authorization

No changes here — the system still uses:

- API key authentication  
- SHA256 hashed keys  
- RBAC permissions (`analyze`, `stream`, `plugins`, `admin`)  

---

# 📡 WebSocket & Streaming

Unchanged, but now supports:

- Streaming frames to any plugin tool  
- Receiving tool results asynchronously  
- Correlating results via `frame_id`  

---

# 🧪 Test Organization (Updated)

```
server/tests/
├── api/          # /v1/plugins/.../run tests
├── mcp/          # MCP protocol tests
├── plugins/      # Plugin contract + loader tests
├── auth/         # Authentication tests
├── tasks/        # Job/task manager tests
├── websocket/    # WebSocket tests
└── conftest.py
```

### Key Update  
Integration tests now execute **real plugins**, not mocks.

---

# 🧠 Key Architectural Decisions (Updated)

| Decision | Rationale | Location |
|----------|-----------|----------|
| BasePlugin contract | Ensures consistent plugin behavior | `server/app/plugins/base.py` |
| Entry‑point plugin loading | True dynamic plugin ecosystem | `server/app/plugin_loader.py` |
| Tool‑based execution model | Supports multiple tools per plugin | `/v1/plugins/.../tools/.../run` |
| Unified tool runner (frontend) | Consistent error handling + retries | `web-ui/src/utils/runTool.ts` |
| MCP auto‑generation | Tools exposed dynamically | `server/app/mcp/adapter.py` |
| JSON‑only error responses | Prevents “Invalid JSON from tool” | Global exception handler |

---

# 🎯 Summary

ForgeSyte has evolved from a single‑purpose OCR pipeline into a **general‑purpose vision plugin platform**.  
The new architecture:

- Enforces a stable plugin contract  
- Supports multiple tools per plugin  
- Uses entry‑point discovery  
- Provides consistent REST + MCP interfaces  
- Enables real integration testing  
- Powers both CLI and UI clients  

This document reflects the architecture as of 2026.

---

