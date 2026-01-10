# ForgeSyte

ForgeSyte is a modular AI‑vision MCP server engineered for developers who demand precision, extensibility, and absolute clarity in their tooling. Built in Python using the `uv` toolchain and designed for seamless integration with Gemini‑CLI, ForgeSyte acts as a vision analysis core capable of loading, executing, and orchestrating pluggable vision modules.

At its heart, ForgeSyte is a forge: a place where perception is shaped, refined, and extended. Every module—OCR, object detection, mapping, classification, or custom logic—slots into a unified contract, enabling reproducible, auditable, and future‑proof workflows.

Whether you're building automated analysis pipelines, real‑time camera tools, or domain‑specific vision systems, ForgeSyte provides the foundation: a stable schema, a clean API surface, and a plugin architecture engineered for growth.

---

## Features

- **Modular Vision Engine**  
  Drop‑in Python plugins that implement a simple, explicit contract.

- **MCP‑Native**  
  Exposes tools and capabilities directly to Gemini‑CLI via a clean MCP manifest.

- **Python‑First Architecture (uv‑powered)**  
  FastAPI core, plugin loader, and analysis pipeline built for clarity and extensibility.

- **Optional React UI**  
  A lightweight React/TypeScript interface for live camera streaming, job monitoring, and plugin management.

- **Deterministic & Auditable**  
  Every module declares its inputs, outputs, and metadata.

---

## Repository Structure

```text
forgesyte/
├─ server/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api.py
│  │  ├─ mcp_adapter.py
│  │  ├─ plugin_loader.py
│  │  ├─ plugins/
│  │  │  └─ __init__.py
│  │  ├─ models.py
│  │  └─ tasks.py
│  ├─ pyproject.toml
│  └─ uv.lock
├─ example_plugins/
│  ├─ ocr_plugin/
│  └─ block_mapper/
├─ web-ui/
│  ├─ src/
│  ├─ public/
│  └─ package.json
├─ gemini_extension.json
├─ PLUGIN_DEVELOPMENT.md
├─ CONTRIBUTING.md
└─ README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+  
- **uv** (https://github.com/astral-sh/uv)  
- Node.js 18+ (for React UI)  
- Optional: Docker

---

## Backend Setup (uv)

```bash
cd server
uv sync
uv run fastapi dev app/main.py
```

ForgeSyte will start at:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- MCP manifest: `http://localhost:8000/v1/mcp-manifest`

---

## Frontend Setup (React)

```bash
cd web-ui
npm install
npm run dev
```

Runs at:

```
http://localhost:5173
```

---

## Using ForgeSyte with Gemini‑CLI

ForgeSyte integrates with Gemini‑CLI as an MCP server. There are two steps:

---

### 1. Install ForgeSyte as a Gemini‑CLI extension

```bash
# Install directly from GitHub
gemini extensions install https://github.com/rogermt/forgesyte

# Or install from a local checkout
gemini extensions install /path/to/forgesyte
```

---

### 2. Add ForgeSyte to Gemini‑CLI MCP configuration

Edit your Gemini‑CLI user config (e.g., `~/.gemini-cli/settings.json`):

```json
{  
  "$schema": "https://raw.githubusercontent.com/google-gemini/gemini-cli/main/schemas/settings.schema.json",  
  "mcpServers": {  
    "forgesyte": {  
      "httpUrl": "http://localhost:8000",  
      "timeout": 30000,  
      "description": "ForgeSyte AI-vision MCP server"  
    }  
  }  
}
```

Restart Gemini‑CLI, then verify:

```bash
gemini-cli tools list
```

You should see tools such as:

- `vision.ocr`
- `vision.block_mapper`

---

## Architecture Overview

See `ARCHITECTURE.md` for the full diagram.

---

## Troubleshooting MCP Discovery

### ForgeSyte not appearing in `gemini-cli tools list`

- Ensure the server is running:

  ```bash
  curl http://localhost:8000/v1/mcp-manifest
  ```

- Check your Gemini config for typos in:

  - `mcpServers`
  - `forgesyte`
  - `httpUrl`

- Restart Gemini‑CLI after editing settings.

### Manifest returns 500

- A plugin likely has invalid metadata.
- Check ForgeSyte logs for `ValidationError`.

### Tool invocation returns 404

- Plugin name in `?plugin=` may not match the plugin folder name.
- Ensure plugin is loaded by `plugin_loader.py`.

---

## Contributing

See `CONTRIBUTING.md`.

---

## Plugin Development

See `PLUGIN_DEVELOPMENT.md`.

---

## Branding

See `BRANDING.md`.

---

## License

TBD.
```

---

# ✅ 2. **Gemini‑CLI Quickstart Mini‑Guide**

```md
# ForgeSyte + Gemini‑CLI Quickstart

This guide shows the fastest way to use ForgeSyte as an MCP server inside Gemini‑CLI.

---

## 1. Start ForgeSyte

```bash
cd forgesyte/server
uv sync
uv run fastapi dev app/main.py
```

---

## 2. Install ForgeSyte as a Gemini extension

```bash
gemini extensions install https://github.com/rogermt/forgesyte
```

---

## 3. Add ForgeSyte to Gemini MCP config

Edit your Gemini settings file:

```json
{
  "mcpServers": {
    "forgesyte": {
      "httpUrl": "http://localhost:8000",
      "type": "http"
    }
  }
}
```

---

## 4. Verify tools are available

```bash
gemini-cli tools list
```

You should see:

- `vision.ocr`
- `vision.block_mapper`

---

## 5. Use ForgeSyte inside Gemini

Examples:

- “Use ForgeSyte OCR on this screenshot.”
- “Analyze this image with the block mapper.”
```

---

# ✅ 3. **Troubleshooting Block (MCP Discovery Issues)**

```md
# MCP Discovery Troubleshooting

### ForgeSyte does not appear in `gemini-cli tools list`

- Ensure ForgeSyte is running:

  ```bash
  curl http://localhost:8000/v1/mcp-manifest
  ```

- Check Gemini config for typos:

  - `mcpServers`
  - `forgesyte`
  - `httpUrl`

- Restart Gemini‑CLI after editing settings.

---

### Manifest returns 500

- A plugin likely has invalid metadata.
- Check ForgeSyte logs for:

  - `ValidationError`
  - Missing fields in `metadata()`
  - Incorrect types

---

### Tools appear but invocation fails

- Ensure plugin name matches:

  ```
  /v1/analyze?plugin=<name>
  ```

- Confirm plugin folder name matches plugin `name` field.

---

### Gemini‑CLI says “server unreachable”

- Check port:

  ```bash
  curl http://localhost:8000/
  ```

- Ensure no firewall is blocking localhost.
```

---

# ✅ 4. **Correct `gemini_extension.json`**

This is the correct filename and structure for Gemini extensions.

```json
{
  "name": "ForgeSyte",
  "version": "0.1.0",
  "description": "Modular AI-vision MCP server exposing pluggable vision tools.",
  "homepage": "https://github.com/rogermt/forgesyte",
  "repository": {
    "type": "git",
    "url": "https://github.com/rogermt/forgesyte.git"
  },
  "license": "MIT",
  "categories": [
    "vision",
    "analysis",
    "developer-tools"
  ],
  "author": {
    "name": "ForgeSyte",
    "url": "https://github.com/rogermt"
  },
  "mcpServers": {
    "forgesyte": {
      "httpUrl": "http://localhost:8000",
      "type": "http"
    }
  }
}
```
