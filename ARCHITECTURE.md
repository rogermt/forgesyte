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

## Server Architecture (Phase 4 Organization)

### MCP Module Structure

All Model Context Protocol (MCP) logic is consolidated in `server/app/mcp/`:

```
server/app/mcp/
├── __init__.py          # Public API exports
├── adapter.py           # MCP adapter for tools/resources
├── handlers.py          # Request/response handlers
├── jsonrpc.py          # JSON-RPC protocol implementation
├── routes.py           # MCP HTTP endpoints
└── transport.py        # HTTP transport layer
```

**Architecture Decision**: Grouping all MCP-related code into a dedicated package reduces coupling and makes the codebase easier to navigate. The `__init__.py` exposes only the necessary public API.

### Server Core Modules

```
server/app/
├── mcp/                 # MCP protocol implementation
├── plugins/             # Plugin manager and registry
├── __init__.py
├── api.py              # REST API endpoints (/v1/*)
├── auth.py             # Authentication & authorization (API key-based)
├── main.py             # FastAPI app initialization
├── models.py           # Pydantic schemas
├── plugin_loader.py    # Dynamic plugin discovery
├── tasks.py            # Job/task management
└── websocket_manager.py # WebSocket connections & streaming
```

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

---

## Plugin System Architecture (Phase 4)

### Plugin Interface Contract

Plugins implement the `PluginInterface` protocol (structural typing):

```python
class PluginInterface(Protocol):
    def metadata(self) -> PluginMetadata: ...
    def analyze(self, image: bytes, options: dict) -> dict: ...
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    async def analyze_async(self, image: bytes, options: dict) -> dict: ...  # Optional
```

**Key Patterns**:
- **Loose Coupling**: Protocol-based (structural typing) allows plugins to exist without inheriting from a base class
- **BasePlugin Optional**: Convenience base class providing `validate_image()` and thread pool management
- **Discovery-Based Registry**: Plugins auto-discovered from filesystem; no manual registration
- **Threading Model**: `BasePlugin` wraps sync `analyze()` in `ThreadPoolExecutor` for async execution

---

## Authentication & Authorization (Phase 4)

### Authentication

- **Method**: API key-based using SHA256 hashing
- **Storage**: Hashed keys in environment variables (format: `fgy_live_<hash>`)
- **Implementation**: `server/app/auth.py`
- **Development Mode**: Anonymous access if no keys configured

### Authorization (RBAC)

- **Pattern**: Role-based with explicit permissions
- **Permissions**: `analyze`, `stream`, `plugins`, `admin`
- **Enforcement**: FastAPI `Security` dependency (`require_auth`)
- **Response Codes**: 
  - 401 Unauthorized (no auth provided)
  - 403 Forbidden (insufficient permissions)

---

## WebSocket & Streaming (Phase 4)

### Connection Flow

1. Client connects to `/ws/<client_id>`
2. Subscribes to topics: `job_<id>`, `plugin_<name>`
3. Receives async results as they arrive
4. Results correlated by `frame_id`

### Message Types

- **subscribe**: Topic-based filtering
- **send_frame**: Stream image frames
- **frame_result**: Async result arrival
- **job_update**: Job status changes
- **error**: Error notifications

**Performance**: Results arrive out-of-order; clients use `frame_id` for correlation.

---

## Test Organization (Phase 5)

### Server Tests

Tests organized by module to mirror `server/app/` structure:

```
server/tests/
├── api/          # REST endpoints tests
├── mcp/          # MCP protocol tests
├── plugins/      # Plugin system tests
├── auth/         # Authentication tests
├── tasks/        # Job/task manager tests
├── websocket/    # WebSocket connection tests
└── conftest.py   # Shared fixtures
```

### Web UI Tests

React component tests use Vitest (`.test.tsx` files in `src/`).
Python validation scripts in `web-ui/scripts/` for build config checks.

---

## Data Flow

1. Client sends image → `/v1/analyze`  
2. Job Manager queues the task  
3. Plugin Manager loads the correct plugin  
4. Plugin performs analysis (sync or async)
5. Job Manager stores result  
6. Client polls `/v1/jobs/<id>` or receives WS updates  

---

## Key Architectural Decisions

| Decision | Rationale | Location |
|----------|-----------|----------|
| MCP code in dedicated `mcp/` package | Reduces coupling, improves navigation | `server/app/mcp/` |
| Protocol-based plugin interface | Loose coupling, no inheritance required | `server/app/plugin_loader.py` |
| API key-based auth with SHA256 | Simple, effective, stateless | `server/app/auth.py` |
| RBAC with explicit permissions | Fine-grained access control | `server/app/auth.py` |
| WebSocket streaming with frame IDs | Supports out-of-order results | `server/app/websocket_manager.py` |
| Tests organized by module | Prevents flat test directory as codebase grows | `server/tests/`, `web-ui/src/` |

