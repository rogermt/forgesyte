[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/rogermt/forgesyte)
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

## Execution Governance

ForgeSyte's execution layer is governed by strict mechanical rules enforced via a static scanner and CI pipeline.

### Quick Links

- **Execution Governance Documentation:** [`docs/design/execution-governance.md`](docs/design/execution-governance.md)
  - Architecture overview
  - Plugin lifecycle states
  - Job lifecycle
  - Validation rules
  - Error envelope format
  - Scanner rules
  - CI enforcement

- **Architecture Diagrams:** [`docs/design/execution-architecture.drawio`](docs/design/execution-architecture.drawio)
  - Visual execution flow
  - Component dependencies
  - Job lifecycle diagram
  - Registry state machine
  - Error envelope flow

- **Developer Onboarding:** [`docs/design/execution-onboarding.md`](docs/design/execution-onboarding.md)
  - Core mental model
  - Running tests
  - Running the scanner
  - Adding plugins
  - Adding execution features
  - Debugging execution issues

- **Phase 12 Wrap‑Up:** [`docs/phase12-wrap-up.md`](docs/phase12-wrap-up.md)
  - What Phase 12 achieved
  - Key guarantees enforced
  - Future enhancements

- **Repository Audit Checklist:** [`docs/repo-audit-checklist.md`](docs/repo-audit-checklist.md)
  - Verify governance compliance
  - Check directory structure
  - Validate architecture
  - Ensure CI enforcement

### Running the Mechanical Scanner

The scanner enforces execution governance invariants:

```bash
python scripts/scan_execution_violations.py
```

If it prints `✅ PASSED`, you're compliant. If it prints violations, fix them before committing.

CI runs this automatically on every PR and push to `main`.

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

## Contract Tests (JSON-Safe Output Validation)

ForgeSyte enforces that all plugin tools return JSON-serializable output. This prevents numpy arrays, tensors, or custom objects from leaking into API responses.

### Running Contract Tests

**CPU (CI environment):**
```bash
cd server
uv run pytest tests/contract/ -v
```

**GPU (Kaggle with YOLO models):**
```bash
cd server
RUN_MODEL_TESTS=1 uv run pytest tests/contract/ -v
```

### What Contract Tests Verify

- **All plugins loaded** via `entry_points(group="forgesyte.plugins")`
- **All tools callable** via `plugin.run_tool(tool_name, args)`
- **All outputs JSON-safe** — can be serialized via `json.dumps()`
- **No numpy/torch leaks** — arrays and tensors rejected

See `server/tests/contract/` for implementation details.

---

## Scope Guardrails

The following features are **explicitly out of scope** for ForgeSyte and must not be implemented:

- No export  
- No record button  
- No model selector  
- No WebSocket selector  

Any PR adding these features will be rejected.

See `docs/design/video-tool-runner.md` for the canonical Video Tool Runner UI specification.

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
