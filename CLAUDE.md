# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForgeSyte is a modular AI-vision MCP (Model Context Protocol) server that provides pluggable vision analysis tools to AI clients like Gemini-CLI. It has two main components:

- **Server** (`server/`): Python/FastAPI backend with plugin system, job management, and MCP protocol implementation
- **Web-UI** (`web-ui/`): React/TypeScript frontend for camera streaming, job monitoring, and plugin management

```
Gemini-CLI (MCP client)
       │
       │ MCP HTTP
       ▼
ForgeSyte Server (FastAPI)
       │
       ├── Plugin Manager (entry-point based, BasePlugin contract)
       ├── Job Manager (async + thread pool)
       └── MCP Adapter (tool exposure)
              │
              ▼
       Python Vision Plugins (OCR, YOLO, etc.)

Optional: Web-UI ←→ REST/WebSocket → Server
```

## Quick Start

```bash
# Server
cd server && uv sync && uv run fastapi dev app/main.py

# Web-UI
cd web-ui && npm install && npm run dev
```

## Development Commands

### Server (Python/FastAPI)

```bash
cd server

# Run server
uv run fastapi dev app/main.py

# Tests
uv run pytest tests/api/ -v                    # API tests
uv run pytest tests/contract/ -v              # Contract tests (JSON-safe output)
uv run pytest tests/plugins -v                # Plugin registry tests
uv run pytest tests/execution -v               # Execution governance tests

# Single test
uv run pytest tests/api/test_jobs.py::test_name -v

# Code quality
uv run black . && uv run ruff check --fix . && uv run mypy . --no-site-packages
uv run pre-commit run --all-files
```

### Web-UI (React/TypeScript)

```bash
cd web-ui

# Run dev server
npm run dev

# Tests
npm run test -- --run                           # Run tests once
npm run test -- src/api/client.test.ts          # Single test file

# Code quality (REQUIRED before committing)
npm run lint && npm run type-check
```

### Execution Governance

Before committing, run the full verification suite:

```bash
# 1. Run execution governance scanner (repo root)
python scripts/scan_execution_violations.py

# 2. Run all core tests
cd server && uv run pytest tests/ -v --tb=short
```

CI runs the same checks on every PR and push to `main`.

## Architecture

### Plugin System

Plugins must implement `BasePlugin` and are loaded via entry points:

```python
class BasePlugin(ABC):
    name: str
    tools: Dict[str, Dict[str, Any]]  # handler, description, input_schema, output_schema

    def run_tool(self, tool_name: str, args: dict) -> Any: ...
```

Tool execution path: `POST /v1/plugins/<plugin>/tools/<tool>/run`

### Execution Pipeline

```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

Each layer has single responsibility: API (request/response), Services (orchestration), ToolRunner (validation/execution/metrics).

### Job Lifecycle

Jobs transition: `PENDING → RUNNING → SUCCESS / FAILED`

### Database

DuckDB with SQLAlchemy (`app/core/database.py`), Alembic for migrations.

## Key Conventions

### TDD Workflow
1. Write failing test first
2. Run test to verify it fails
3. Implement code
4. Run test to verify it passes
5. Run lint and type-check
6. Commit

### Pre-commit Hooks
**Never use `--no-verify`** to bypass hooks. Hooks enforce:
- black, ruff, mypy (server)
- eslint, type-check (web-ui)
- Server tests before commit
- Skipped test policy validation

### Skipped Tests Policy
Skipped tests require `APPROVED` comment:
```typescript
it.skip('test description', () => {
  // APPROVED: Reason for skipping
});
```

### Commit Message Format
```
<type>: <subject>

Types: feat, fix, refactor, test, docs, chore
```

### Test Changes
Include `TEST-CHANGE:` in commit message body when modifying tests.

## Key Files

| File | Purpose |
|------|---------|
| `server/app/plugins/base.py` | BasePlugin ABC contract |
| `server/app/plugin_loader.py` | Plugin entry-point discovery |
| `server/app/mcp/adapter.py` | MCP tool exposure |
| `server/app/services/` | Business logic (VisionAnalysis, PluginExecution, JobExecution) |
| `server/app/api_routes/routes/execution.py` | Tool execution endpoint |
| `scripts/scan_execution_violations.py` | Governance scanner |
| `web-ui/src/api/client.ts` | REST API client |
| `web-ui/src/hooks/useWebSocket.ts` | WebSocket streaming |

## Documentation

- `ARCHITECTURE.md` - Overall system architecture
- `AGENTS.md` - Agent commands and conventions
- `docs/design/execution-governance.md` - Execution layer rules
- `PLUGIN_DEVELOPMENT.md` - Plugin development guide
