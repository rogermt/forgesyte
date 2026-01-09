# ForgeSyte Server

ForgeSyte is a modular AI-vision MCP server engineered for developers who demand precision, extensibility, and absolute clarity in their tooling. Built in Python using the `uv` toolchain and designed for seamless integration with Gemini-CLI, ForgeSyte acts as a vision analysis core capable of loading, executing, and orchestrating pluggable vision modules.

## Features

- **Modular Vision Engine**: Drop-in Python plugins that implement a simple, explicit contract.
- **MCP-Native**: Exposes tools and capabilities directly to Gemini-CLI via a clean MCP manifest.
- **Python-First Architecture (uv-powered)**: FastAPI core, plugin loader, and analysis pipeline built for clarity and extensibility.
- **Deterministic & Auditable**: Every module declares its inputs, outputs, and metadata.

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