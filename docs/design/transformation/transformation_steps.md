# Transformation Steps: Vision-MCP to ForgeSyte

## Overview
This document outlines the step-by-step process to transform the Vision-MCP codebase into the ForgeSyte implementation according to the design specifications.

## Phase 1: Project Setup and Configuration

### Step 1: Create New Project Structure
```bash
# In the forgesyte project root
mkdir -p server/app
mkdir -p example_plugins
mkdir -p web-ui/src/components
mkdir -p web-ui/src/hooks
mkdir -p web-ui/src/api

# Move existing server code to new structure
# Move vision-mcp/server/app/* to forgesyte/server/app/
# Move vision-mcp/server/app/plugins/* to forgesyte/example_plugins/
```

### Step 2: Create pyproject.toml
Create `/home/rogermt/forgesyte/server/pyproject.toml` with the following content:

```toml
[project]
name = "forgesyte"
version = "0.1.0"
description = "ForgeSyte: A modular AI-vision MCP server engineered for developers"
authors = [
    {name = "ForgeSyte Team", email = "team@forgesyte.ai"}
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
    "black>=23.0.0",
    "isort>=5.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "black>=23.0.0",
    "isort>=5.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

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

### Step 3: Update Import Statements
Update all import statements to reflect the new structure:
- Change imports from `server.app.*` to relative imports within the app
- Update plugin loading to look in `../example_plugins` instead of `./plugins`

## Phase 2: Code Modifications

### Step 4: Update Server Application Files

#### Update `server/app/main.py`:
1. Change title from "Vision MCP Server" to "ForgeSyte"
2. Update plugin loading path to look in example_plugins directory
3. Update branding in root endpoint

#### Update `server/app/mcp_adapter.py`:
1. Change server name from "vision-mcp" to "forgesyte"
2. Update description to match ForgeSyte branding

#### Update `server/app/plugin_loader.py`:
1. Modify the default plugins directory to point to example_plugins
2. Update any hardcoded paths

### Step 5: Update Environment Variables
Replace all environment variable references:
- `VISION_PLUGINS_DIR` → `FORGESYTE_PLUGINS_DIR`
- `VISION_ADMIN_KEY` → `FORGESYTE_ADMIN_KEY`
- `VISION_USER_KEY` → `FORGESYTE_USER_KEY`

### Step 6: Update Plugin Files
Move all plugin files from `server/app/plugins/` to `example_plugins/`:
- `server/app/plugins/ocr_plugin/plugin.py` → `example_plugins/ocr_plugin/plugin.py`
- `server/app/plugins/block_mapper/plugin.py` → `example_plugins/block_mapper/plugin.py`
- `server/app/plugins/moderation/plugin.py` → `example_plugins/moderation/plugin.py`
- `server/app/plugins/motion_detector/plugin.py` → `example_plugins/motion_detector/plugin.py`

Update plugin loading logic to look in the new location.

## Phase 3: Documentation and Configuration

### Step 7: Create Missing Documentation Files
Create the following files based on the design docs:

1. `PLUGIN_DEVELOPMENT.md` - Already exists, but verify it matches the structure
2. `CONTRIBUTING.md` - Already exists, but verify it matches the structure
3. `ARCHITECTURE.md` - Already exists, but verify it matches the structure
4. `BRANDING.md` - Already exists

### Step 8: Update README.md
Update the existing README.md to reflect ForgeSyte instead of Vision-MCP:
- Change project name and description
- Update quick start commands to use uv
- Update API examples to reflect new branding
- Update configuration section to reflect new env vars

## Phase 4: Testing and Validation

### Step 9: Create Test Suite
Create basic tests to validate the transformation:

1. `tests/test_api.py` - Test basic API endpoints
2. `tests/test_plugins.py` - Test plugin loading
3. `tests/test_mcp.py` - Test MCP manifest generation

### Step 10: Update Installation Script
Create a new installation script that uses uv instead of pip:

```bash
#!/bin/bash
set -e

echo "🔧 ForgeSyte Installation"
echo "========================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Navigate to server directory
cd server

# Sync dependencies
echo "📥 Installing dependencies with uv..."
uv sync

# Generate API keys
echo ""
echo "🔐 Generating API keys..."
ADMIN_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
USER_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create .env file
cat > .env << EOF
# ForgeSyte Configuration
FORGESYTE_ADMIN_KEY=$ADMIN_KEY
FORGESYTE_USER_KEY=$USER_KEY
FORGESYTE_PLUGINS_DIR=../example_plugins
CORS_ORIGINS=*
EOF

echo "✓ Configuration saved to server/.env"
echo ""
echo "🔑 API Keys (save these!):"
echo "   Admin: $ADMIN_KEY"
echo "   User:  $USER_KEY"
echo ""

echo "✅ Installation complete!"
echo ""
echo "To start the server:"
echo "  cd server"
echo "  uv run fastapi dev app/main.py"
echo ""
echo "API docs: http://localhost:8000/docs"
echo "MCP manifest: http://localhost:8000/v1/mcp-manifest"
```

## Phase 5: Verification

### Step 11: Run the Server
```bash
cd server
uv sync
uv run fastapi dev app/main.py
```

### Step 12: Verify Endpoints
- Check that `/` returns ForgeSyte branding
- Check that `/v1/mcp-manifest` returns correct server name
- Test plugin loading from example_plugins directory
- Verify all API endpoints work correctly

### Step 13: Run Tests
```bash
cd server
uv run pytest
```

## Expected Outcomes

After completing these steps:
1. The project will be built with uv instead of pip
2. Plugins will be located in example_plugins/ directory
3. All branding will reflect ForgeSyte identity
4. Environment variables will use FORGESYTE_ prefix
5. The project structure will match the design specification
6. All functionality will remain intact but with improved tooling

## Potential Issues to Watch For

1. Plugin loading paths may need adjustment after moving directories
2. Relative imports may need updating after restructuring
3. Docker configuration will need to be updated if used
4. Web UI may need path adjustments for API endpoints
5. Any hardcoded paths in the code will need updating