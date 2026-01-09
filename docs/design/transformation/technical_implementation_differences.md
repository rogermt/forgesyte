# Technical Implementation Differences: Vision-MCP to ForgeSyte

## Overview
This document details the specific technical changes needed to transform the existing Vision-MCP codebase into the ForgeSyte implementation according to the design documents.

## 1. Build System Migration (requirements.txt → uv/pyproject.toml)

### Current Vision-MCP (requirements.txt):
```
# Core
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0
python-multipart>=0.0.6
httpx>=0.24.0
websockets>=11.0

# Image Processing
pillow>=10.0.0
numpy>=1.24.0

# OCR (optional)
pytesseract>=0.3.10

# Development
python-dotenv>=1.0.0

# Production
gunicorn>=21.0.0
```

### Required ForgeSyte (pyproject.toml):
```toml
[project]
name = "forgesyte"
version = "0.1.0"
description = "ForgeSyte: A modular AI-vision MCP server"
authors = [
    {name = "ForgeSyte Team"}
]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.22.0",
    "pydantic>=2.0",
    "python-multipart>=0.0.6",
    "httpx>=0.24.0",
    "websockets>=11.0",
    "pillow>=10.0.0",
    "numpy>=1.24.0",
    "pytesseract>=0.3.10",
    "python-dotenv>=1.0.0",
    "gunicorn>=21.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 2. Directory Structure Changes

### Before (Vision-MCP):
```
server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── mcp_adapter.py
│   ├── plugin_loader.py
│   ├── models.py
│   ├── tasks.py
│   ├── auth.py
│   ├── websocket_manager.py
│   └── plugins/
│       ├── __init__.py
│       ├── ocr_plugin/
│       │   └── plugin.py
│       ├── block_mapper/
│       │   └── plugin.py
│       ├── moderation/
│       │   └── plugin.py
│       └── motion_detector/
│           └── plugin.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### After (ForgeSyte):
```
server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── mcp_adapter.py
│   ├── plugin_loader.py
│   ├── models.py
│   ├── tasks.py
│   ├── auth.py
│   ├── websocket_manager.py
│   └── plugins/
│       └── __init__.py
├── pyproject.toml
└── uv.lock
example_plugins/
├── ocr_plugin/
│   └── plugin.py
├── block_mapper/
│   └── plugin.py
├── moderation/
│   └── plugin.py
└── motion_detector/
    └── plugin.py
```

## 3. Plugin Loading Logic Changes

### Current Vision-MCP plugin loading:
```python
# In plugin_loader.py
def __init__(self, plugins_dir: str = None):
    self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent / "plugins"
```

### Required ForgeSyte plugin loading:
```python
# In plugin_loader.py
def __init__(self, plugins_dir: str = None):
    # Default to example_plugins directory outside of server
    if plugins_dir is None:
        # Go up from server/app to project root, then to example_plugins
        self.plugins_dir = Path(__file__).parent.parent.parent / "example_plugins"
    else:
        self.plugins_dir = Path(plugins_dir)
```

## 4. Branding Updates

### Server Name Changes:
- Change `"Vision MCP Server"` to `"ForgeSyte"`
- Update API title, description, and version strings
- Update MCP manifest server name

### MCP Adapter Changes:
```python
# In mcp_adapter.py
def get_manifest(self) -> dict:
    # Change server name from "vision-mcp" to "forgesyte"
    manifest = MCPManifest(
        tools=tools,
        server={
            "name": "forgesyte",  # Changed from "vision-mcp"
            "version": "0.1.0",
            "description": "ForgeSyte: A vision core for engineered systems"
        },
        version="1.0"
    )
    return manifest.model_dump()
```

## 5. API Endpoint Changes

### Root Endpoint Updates:
```python
# In main.py
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ForgeSyte",  # Changed from "Vision MCP Server"
        "version": "0.1.0",
        "docs": "/docs",
        "mcp_manifest": "/.well-known/mcp-manifest",
        "gemini_extension": "/v1/gemini-extension"
    }
```

## 6. Docker Configuration Changes

### Current Vision-MCP Dockerfile:
```dockerfile
FROM python:3.11-slim
# ...
ENV VISION_PLUGINS_DIR=/app/app/plugins
# ...
```

### Required ForgeSyte Dockerfile:
```dockerfile
FROM ghcr.io/astral-sh/uv:python-3.11-slim
# ...
ENV FORGESYTE_PLUGINS_DIR=/app/example_plugins
# ...
# Install dependencies with uv
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen
# ...
```

## 7. Configuration Environment Variables

### Variable Name Changes:
- `VISION_PLUGINS_DIR` → `FORGESYTE_PLUGINS_DIR`
- `VISION_ADMIN_KEY` → `FORGESYTE_ADMIN_KEY`
- `VISION_USER_KEY` → `FORGESYTE_USER_KEY`

## 8. Code Quality Tooling

### Add Ruff Configuration (pyproject.toml):
```toml
[tool.ruff]
line-length = 88
extend-ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
extend-ignore = [
    "PLR",  # Design related pylint codes
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## 9. Type Hinting Improvements

### Enhanced Type Hints (Following ForgeSyte standards):
```python
# More specific type annotations
from typing import Dict, List, Optional, Union, Protocol, runtime_checkable
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
```

## 10. Testing Framework

### Add pytest configuration (pyproject.toml):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
]

[tool.coverage.run]
source = ["src/"]
omit = ["*/tests/*", "*/conftest.py"]
```

## 11. TypeScript Frontend Implementation

### Current Vision-MCP TypeScript Files:
```
web-ui/
├── src/
│   ├── App.tsx
│   ├── index.tsx
│   ├── components/
│   │   ├── CameraPreview.tsx
│   │   ├── JobList.tsx
│   │   ├── PluginSelector.tsx
│   │   └── ResultsPanel.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts
│   └── api/
│       └── client.ts
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Required ForgeSyte TypeScript Updates:
- Update branding from "Vision MCP Server" to "ForgeSyte"
- Apply ForgeSyte color palette (Charcoal #111318, Steel #2B3038, Forge Orange #FF6A00, Electric Cyan #00E5FF)
- Update API endpoints to match new server structure
- Update component styling to match sci-fi industrial theme
- Update WebSocket connection handling to match new backend

### TypeScript Component Updates:
- CameraPreview.tsx: Update styling and branding
- JobList.tsx: Update to match new API response structure
- PluginSelector.tsx: Update plugin loading to match new plugin system
- ResultsPanel.tsx: Update to handle new result formats
- useWebSocket.ts: Update to match new WebSocket API
- api/client.ts: Update endpoints and authentication

## 12. UI Theming and Styling

### Current Vision-MCP Styling:
- Generic styling without specific branding
- Standard UI components

### Required ForgeSyte Styling:
- Sci-fi industrial theme with dark backgrounds
- ForgeSyte color palette implementation
- Custom component styling matching branding
- Responsive design for various screen sizes
- Accessibility improvements