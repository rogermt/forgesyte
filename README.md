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
├─ web-ui/              # React + TypeScript
│  ├─ src/
│  ├─ public/
│  └─ package.json
├─ gemini_extension_manifest.json
├─ requirements.doc
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

Point Gemini‑CLI to:

```
http://localhost:8000/v1/mcp-manifest
```

ForgeSyte will expose tools based on installed plugins.

---

## Architecture Overview

See `ARCHITECTURE.md` for the full diagram.

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
