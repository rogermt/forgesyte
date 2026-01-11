"""ForgeSyte server package.

This package provides the core FastAPI application and supporting infrastructure
for running the ForgeSyte vision analysis server with modular plugins.

Modules:
    app: Main FastAPI application and router definitions
    scripts: Utility scripts for server administration

The server provides:
    - REST API endpoints for job management, analysis, and plugin discovery
    - WebSocket support for real-time streaming results
    - MCP (Model Context Protocol) 2.0 endpoint for client integration
    - Plugin system for modular vision analysis capabilities
    - Structured logging and observability

Quick Start:
    ```python
    from server.app.main import app

    # Run with uvicorn
    # uv run fastapi dev server/app/main.py
    ```

Configuration:
    See server/app/main.py for FastAPI application setup.
    Environment variables (via .env):
    - FORGESYTE_ADMIN_KEY: Admin API key
    - FORGESYTE_USER_KEY: User API key
    - PLUGINS_DIR: Directory containing plugins (default: ./plugins)
"""
