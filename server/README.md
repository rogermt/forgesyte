# ForgeSyte Server

ForgeSyte is a modular AI-vision MCP server engineered for developers who demand precision, extensibility, and absolute clarity in their tooling. Built in Python using the `uv` toolchain and designed for seamless integration with Gemini-CLI, ForgeSyte acts as a vision analysis core capable of loading, executing, and orchestrating pluggable vision modules.

## Features

- **Modular Vision Engine**: Drop-in Python plugins that implement a simple, explicit contract.
- **MCP-Native**: Exposes tools and capabilities directly to Gemini-CLI via a clean MCP manifest.
- **Python-First Architecture (uv-powered)**: FastAPI core, plugin loader, and analysis pipeline built for clarity and extensibility.
- **Deterministic & Auditable**: Every module declares its inputs, outputs, and metadata.
- **Production Ready**: Complete type hints, structured logging, resilient error handling with retries.

## Architecture Overview

The server follows a layered architecture with clear separation of concerns:

**Core Application**:
- `app/main.py`: FastAPI application with lifespan management
- `app/models.py`: Pydantic models for API and internal communication
- `app/api.py`: REST API endpoints with service layer injection

**Service Layer**:
- `app/services/`: Business logic services (ImageAcquisitionService, VisionAnalysisService, HealthCheckService)
- `app/protocols.py`: Protocol interfaces for dependency injection and testing
- `app/auth.py`: Authentication and authorization services

**Plugin System**:
- `app/plugin_loader.py`: Dynamic plugin loading with protocol validation
- `app/plugins/`: Built-in plugins (block_mapper, moderation, motion_detector, ocr_plugin)

**MCP Support**:
- `app/mcp/`: Model Context Protocol implementation (JSON-RPC 2.0, handlers, transport)

**Job Management**:
- `app/tasks.py`: Task processor and job store for async analysis
- `app/websocket_manager.py`: Real-time result streaming via WebSocket

## Quick Start

### Prerequisites

- Python 3.10+
- **uv** (https://github.com/astral-sh/uv)

### Setup

```bash
cd server
uv sync
uv run fastapi dev app/main.py
```

ForgeSyte will start at:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- MCP manifest: `http://localhost:8000/v1/mcp-manifest`

## Development

### Code Quality

The project enforces strict code quality standards via pre-commit hooks:

```bash
# Install pre-commit hooks (one-time)
uv pip install pre-commit
uv run pre-commit install

# Run all checks manually
uv run pre-commit run --all-files

# Or run individual tools
uv run black .
uv run ruff check --fix .
uv run mypy . --no-site-packages
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_api.py -v
```

## Standards Compliance

This project adheres to strict Python standards ensuring production-ready code:

- **Type Safety**: 100% type hints on all functions and classes
- **Documentation**: Google-style docstrings with Args/Returns/Raises sections
- **Logging**: Structured logging with semantic context throughout
- **Error Handling**: Specific exception types, no generic catches
- **Resilience**: Retry logic with exponential backoff for external calls
- **Testing**: 80%+ test coverage with mocked external dependencies

See `PYTHON_STANDARDS.md` in the parent directory for complete guidelines.