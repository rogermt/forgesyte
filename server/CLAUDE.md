# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForgeSyte is a modular AI-vision MCP (Model Context Protocol) server built in Python with FastAPI. It provides a plugin-based vision analysis system that exposes tools to AI clients like Gemini-CLI.

## Development Commands

```bash
# Install dependencies
cd server && uv sync

# Run the server (development)
uv run fastapi dev app/main.py

# Run the server (production)
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Run tests
uv run pytest                    # All tests
uv run pytest tests/api/         # Specific directory
uv run pytest tests/api/test_specific.py::test_name -v  # Single test
uv run pytest --cov=app --cov-report=html  # With coverage

# Code quality
uv run pre-commit run --all-files
uv run black .
uv run ruff check --fix .
uv run mypy . --no-site-packages
```

## Architecture

### Core Components

- **app/main.py**: FastAPI application factory (`create_app()`), lifespan management, WebSocket endpoint at `/v1/stream`
- **app/plugin_loader.py**: `PluginRegistry` class that loads plugins via Python entry points (`forgesyte.plugins`)
- **app/plugins/base.py**: `BasePlugin` ABC - canonical plugin contract all plugins must implement
- **app/mcp/**: MCP protocol implementation (JSON-RPC 2.0, handlers, HTTP transport)
- **app/services/**: Business logic layer (VisionAnalysisService, PluginExecutionService, JobExecutionService)

### Plugin System

Plugins are loaded via entry points and must:
1. Subclass `BasePlugin`
2. Define `name: str` (unique identifier)
3. Define `tools: Dict[str, Dict[str, Any]]` with handler, description, input_schema, output_schema
4. Implement `run_tool(tool_name, args)`

Built-in plugin directories: `app/plugins/` (health, inspector, lifecycle, loader, sandbox)

### Database & Jobs

- **DuckDB** with SQLAlchemy for persistence (see `app/core/database.py`)
- **Alembic** for migrations (`alembic.ini` at project root)
- Job processing via `JobWorker` thread (disabled in tests via `FORGESYTE_ENABLE_WORKERS=0`)
- Models in `app/models/` (Job, JobTool)

### API Routes Structure

- `app/api.py` - Main API router with health, manifest, tools endpoints
- `app/api_routes/routes/` - Organized route handlers (execution, jobs, video_file_processing, etc.)
- `app/mcp/` - MCP protocol routes
- `app/routes/` - Pipeline routes

### Realtime

- `app/websocket_manager.py` - WebSocket connection manager
- `app/realtime/` - Job progress streaming

## Testing

Tests are in `tests/` directory with 1600+ test cases. Key fixtures in `tests/conftest.py`:
- `FORGESYTE_ENABLE_WORKERS=0` - Disables job worker thread to prevent DB lock errors
- `FORGESYTE_DATABASE_URL=duckdb:///:memory:` - In-memory database for tests
- `FORGESYTE_STORAGE_BACKEND=local` - Avoids S3 dependencies

Test markers: `@pytest.mark.asyncio`, `@pytest.mark.unit`, `@pytest.mark.integration`

## Key Settings

Environment variables (see `app/settings.py`):
- `FORGESYTE_LOG_LEVEL`, `FORGESYTE_LOG_FILE` - Logging
- `FORGESYTE_STORAGE_BACKEND` - local or s3
- `FORGESYTE_DATABASE_URL` - Database connection
- `FORGESYTE_ADMIN_KEY`, `FORGESYTE_USER_KEY` - API authentication
- `CORS_ORIGINS` - CORS allowed origins (JSON array)
