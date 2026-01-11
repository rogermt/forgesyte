# ForgeSyte – Software Design Guide

This document defines the design principles, architecture, and development process for **ForgeSyte**, an AI-vision MCP server engineered for developers.

We follow a structured approach:

1. Define What You're Building
2. Design the User Experience
3. Understand the Technical Needs
4. Implement Testing and Security Measures
5. Plan the Work
6. Identify Ripple Effects
7. Understand the Broader Context

Everything we implement should align with this guide.

---

## 1. Define What You're Building

### 1.1 What ForgeSyte is

**ForgeSyte** is:

- An **MCP (Model Context Protocol) 2024-11-05 server** for integration with **Gemini CLI** and other MCP clients.
- Purpose-built to provide modular, AI-powered image and media analysis capabilities.
- A plugin-based system for extensible computer vision and media processing.

**Intended audience:**

- **Developers** building AI applications that need vision capabilities.
- **DevOps/ML teams** wanting to deploy modular media analysis at scale.
- **Gemini users** who need advanced image processing in their AI workflows.

### 1.2 Problem we solve

- Existing vision APIs are monolithic, expensive, or require separate integrations.
- Developers need composable, swappable vision processors (OCR, motion detection, moderation, etc.).
- MCP standardizes integration with LLM tools, making vision processing accessible across multiple clients.

**How it operates (high-level):**

1. ForgeSyte server starts (FastAPI + MCP transport at `POST /v1/mcp`).
2. Gemini CLI discovers available tools via `initialize` and `tools/list`.
3. Gemini invokes tools like:
   - `ocr` – Extract text from images
   - `motion_detector` – Detect frame-to-frame motion
   - `moderation` – Detect unsafe content
   - `block_mapper` – Map colors to Minecraft blocks
4. Server processes images through plugins and returns structured results.

### 1.3 Domain-Driven Design (DDD) approach

Core domain concepts:

**Value Objects & Models:**
- `Plugin` – A vision processor with metadata and execution logic.
- `AnalysisJob` – A unit of work (image + plugin + options).
- `MCPTool` – MCP-compliant tool descriptor (name, description, inputSchema).
- `PluginMetadata` – Plugin capabilities and requirements.

**Bounded Contexts:**

- **Plugin System**
  - Core: Plugin registration, loading, metadata.
  - Service layer: Plugin discovery, validation.
  - Extensibility: Plugin developers add new processors.

- **MCP Protocol Context**
  - JSON-RPC 2.0 transport (HTTP).
  - Tool discovery and invocation.
  - Protocol version negotiation.

- **Analysis Processing**
  - Job queuing and execution.
  - Result formatting.
  - Error handling and recovery.

- **WebSocket Streaming**
  - Real-time frame processing.
  - Stream management.
  - Connection lifecycle.

### 1.4 Simplify the model

We deliberately **avoid** overcomplication:

- **Single responsibility:** Each plugin does one thing well.
- **No monolithic inference:** Plugins use standard libraries (PIL, NumPy, pytesseract).
- **Stateless design:** Each request is independent (no session state in plugins).
- **Simple configuration:** Plugins declared via metadata, no complex DSLs.

### 1.5 MVP vs Vision

**Vision (mature ForgeSyte):**
- Multi-language plugin support (Python, JavaScript, Go).
- Distributed plugin execution.
- Result caching and optimization.
- Plugin marketplace.

**Current MVP:**
- Python plugins only.
- Single-instance FastAPI server.
- 4 core plugins (OCR, motion detection, moderation, block mapping).
- Streaming and batch processing.
- Full Gemini CLI integration.

---

## 2. Design the User Experience

### 2.1 Main user stories

**US1 – Discover and use vision tools via Gemini**

- As a **Gemini user**, I want to discover ForgeSyte tools and use them in my prompts.
- Flow:
  - Gemini CLI connects to ForgeSyte MCP server.
  - `gemini /mcp` shows "forgesyte - Ready (4 tools)".
  - User asks: "Analyze this image for text (OCR)."
  - Gemini invokes `ocr` tool with image data.
  - Tool returns extracted text.

**US2 – Stream real-time analysis**

- As a **developer**, I want to stream camera frames for real-time processing.
- Flow:
  - WebSocket connection to `/v1/stream`.
  - Send frames as base64 JSON.
  - Receive analyzed results in real-time.
  - Switch plugins mid-stream without reconnecting.

**US3 – Build custom vision plugins**

- As a **plugin developer**, I want to add my own vision processor to ForgeSyte.
- Flow:
  - Create Python file inheriting from `BasePlugin`.
  - Define metadata (name, description, inputs/outputs).
  - Implement `analyze(image_bytes, options)`.
  - ForgeSyte auto-discovers and exposes via MCP tools.

### 2.2 MCP Tool Design

Each tool has:

```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "image": {
        "type": "string",
        "description": "Base64-encoded or URL image"
      },
      "options": {
        "type": "object",
        "properties": {}
      }
    },
    "required": ["image"]
  }
}
```

Design principles:
- **Simple inputs:** Image data, optional configuration.
- **Structured outputs:** JSON with type, status, content fields.
- **Error transparency:** Failed tools return error details, not silent failures.

### 2.3 UX design principles

- **Consistency:** All tools follow same input/output format.
- **Discoverability:** Tool names and descriptions are clear.
- **Composability:** Tools work independently and in sequences.
- **Performance:** Real-time WebSocket for streaming, batching for jobs.

---

## 3. Understand the Technical Needs

### 3.1 Essential technical details

**Backend:**
- **Runtime:** Python 3.10+
- **Web Framework:** FastAPI
- **MCP Transport:** JSON-RPC 2.0 over HTTP POST
- **Plugin System:** Dynamic loading from `server/app/plugins/`

**Frontend:**
- **Runtime:** Node 18+, TypeScript 5+
- **Framework:** React with Vite
- **WebSocket:** Real-time streaming UI

**Data Models:**
- **Validation:** Pydantic v2 (BaseModel)
- **Type Safety:** Full type hints (mypy 100% compliance)

**Key Features:**
- Streaming: WebSocket at `/v1/stream`
- Batching: JSON-RPC batch requests
- Caching: Manifest TTL caching (5 minutes)
- Backwards compatibility: JSON-RPC v1.0 support with deprecation

### 3.2 Structural organization

**Backend (Python/FastAPI):**

```
server/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── api.py                  # REST endpoints
│   ├── mcp_routes.py          # MCP endpoint
│   ├── mcp_handlers.py        # MCP method handlers
│   ├── mcp_transport.py       # JSON-RPC transport
│   ├── mcp_jsonrpc.py         # JSON-RPC models
│   ├── plugin_loader.py       # Plugin discovery
│   ├── websocket_manager.py   # WebSocket lifecycle
│   ├── auth.py                # API key validation
│   └── plugins/               # Plugin implementations
│       ├── ocr_plugin/
│       ├── motion_detector/
│       ├── moderation/
│       └── block_mapper/
└── tests/                      # Comprehensive test suite

web-ui/                         # React frontend
├── src/
│   ├── components/            # React components
│   ├── hooks/                # Custom hooks
│   └── api/                  # API client
└── tests/                    # Component & integration tests
```

**Frontend (React/TypeScript):**
- Component-based architecture
- Custom hooks for API/WebSocket
- Real-time streaming UI

### 3.3 Code quality standards

- **Linting:** `ruff` (100% pass)
- **Formatting:** `black` (enforced)
- **Type Safety:** `mypy` (100% compliance, no `# type: ignore`)
- **Testing:** `pytest` (backend), `vitest` (frontend)
- **Coverage:** 80%+ for both backend and frontend
- **Pre-commit hooks:** Black, Ruff, Mypy (auto-enforced)

### 3.4 Edge cases & testability

Explicit support for:

- Large images (>10MB) – stream-process instead of loading entirely
- Malformed image data – return structured error
- Missing plugins – graceful 404
- Network failures – retry with exponential backoff
- WebSocket disconnects – automatic reconnect on client side
- Concurrent requests – thread-safe plugin execution

---

## 4. Implement Testing and Security Measures

### 4.1 Testing strategy

**Coverage goals:**
- Backend: 80%+ for all core modules
- Frontend: 80%+ for components
- MCP integration: 100% for protocol compliance

**Test types:**
- **Unit tests:** Pure functions, data models
- **Integration tests:** Plugin execution, API endpoints
- **E2E tests:** WebSocket streaming, Gemini CLI integration
- **Contract tests:** MCP protocol compliance

### 4.2 Security & safety

- **Input validation:** Pydantic models validate all inputs
- **No code execution:** Plugins use library calls only (PIL, NumPy, etc.)
- **No shell commands:** All execution through Python APIs
- **Rate limiting:** Consider per-API-key rate limits
- **Error handling:** Never expose internal stack traces
- **CORS:** Configurable allow-origins
- **Auth:** API key validation on all endpoints

### 4.3 Performance & optimization

- **Image processing:** Plugins optimize memory (thumbnails, streaming)
- **Caching:** Manifest caching, optional result caching
- **Batching:** Batch multiple plugin invocations
- **Monitoring:** Structured logging, performance metrics

---

## 5. Plan the Work

### 5.1 Completed Phases

- ✅ **Phase 1:** Core FastAPI setup + plugin system
- ✅ **Phase 2:** React frontend with WebSocket streaming
- ✅ **Phase 3:** MCP protocol implementation (JSON-RPC 2.0)
- ✅ **Phase 4:** Gemini CLI integration + tool discovery
- ✅ **Phase 5:** Optimization (batching, caching, v1.0 compat)

### 5.2 Current Phase: Refactoring & Code Quality

1. **Phase 1:** Fix failing tests (4 tests with old format expectations)
2. **Phase 2:** Type safety (add missing stubs, 100% mypy compliance)
3. **Phase 3:** Test coverage analysis (target 80%+)
4. **Phase 4:** Code organization (MCP module structure)
5. **Phase 5:** Documentation updates
6. **Phase 6:** Performance optimization

### 5.3 Future phases (post-refactoring)

- Tools/call implementation for actual plugin invocation
- Plugin-specific input schema enhancements
- Resource streaming support
- Multi-region deployment

---

## 6. Identify Ripple Effects

### 6.1 Beyond code

- **Documentation:** ARCHITECTURE.md, TESTING.md, PLUGIN_DEVELOPMENT.md
- **Release notes:** Changelog for each version
- **Community:** Plugin development guide, contribution guidelines

### 6.2 Impact zones

- **Backend changes:** Update API docs, OpenAPI schema
- **Protocol changes:** Verify MCP compliance, update Gemini CLI integration
- **Plugin changes:** Update plugin registry, documentation

---

## 7. Understand the Broader Context

### 7.1 Constraints & limitations

- **MCP Protocol:** Locked to 2024-11-05 version (manage via negotiate_mcp_version)
- **Plugin language:** Python 3.10+ only (for MVP)
- **Image formats:** PNG, JPEG, WebP (others may fail gracefully)

### 7.2 Future extensions

- **Multi-language plugins:** JavaScript, Go, Rust
- **Plugin marketplace:** Discover, install, publish plugins
- **Distributed execution:** Run plugins on GPU clusters
- **Caching layer:** Redis for result caching
- **Analytics:** Track plugin usage, performance metrics

### 7.3 Standards & compliance

- **MCP:** 2024-11-05 protocol version
- **OpenAPI:** Auto-generated from FastAPI
- **JSON Schema:** For tool inputSchema
- **Python:** PEP 8, PEP 484 (type hints)
- **TypeScript:** ESLint, Prettier, strict mode

---

## Working Agreement

### Development Standards

1. **All code must have types** (mypy 100% or documented exception)
2. **All tests must pass before committing** (207+ tests)
3. **Test-Driven Development (TDD)** for new features
4. **Pre-commit hooks enforce standards** (black, ruff, mypy)
5. **Documentation updated with code** (docstrings, ARCHITECTURE.md)

### Feature Workflow

1. Create feature branch (`feature/description`)
2. Write failing tests first (TDD)
3. Implement to pass tests
4. Run full test suite (pytest, coverage)
5. Ensure pre-commit hooks pass
6. Update documentation
7. Create PR and merge to main

### Code Review Checklist

- [ ] Tests pass (307+ total)
- [ ] Coverage maintained (80%+)
- [ ] Type hints complete (mypy passing)
- [ ] No ruff violations
- [ ] Docstrings updated
- [ ] ARCHITECTURE.md updated if relevant
- [ ] Backward compatibility maintained
