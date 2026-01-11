# ForgeSyte Documentation Index

Quick guide to all project documentation. Use this to find what you need.

---

## 📋 Project Overview

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](/README.md) | Project overview, quick start | Everyone |
| [SOFTWARE_DESIGN_GUIDE.md](design/SOFTWARE_DESIGN_GUIDE.md) | Architecture, design principles | Developers, architects |
| [ARCHITECTURE.md](/ARCHITECTURE.md) | System architecture, data flows | Engineers |
| [CONTRIBUTING.md](/CONTRIBUTING.md) | How to contribute | Contributors |

---

## 👨‍💻 Development Standards

| Document | Purpose | Audience |
|----------|---------|----------|
| [AGENTS.md](/AGENTS.md) | **Agent commands & conventions** | AI agents, developers |
| ↳ Git Workflow | Branch strategy, merge process | All |
| ↳ Python Conventions | Code style, type hints, testing | Python developers |
| ↳ TypeScript/React Standards | Type safety, component patterns | Frontend developers |
| ↳ Linting & Type Checking | Tools setup, pre-commit hooks | All |

---

## 📚 Feature Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [PLUGIN_DEVELOPMENT.md](/PLUGIN_DEVELOPMENT.md) | How to build vision plugins | Plugin developers |
| [docs/guides/MCP_CONFIGURATION.md](guides/MCP_CONFIGURATION.md) | MCP setup, endpoints, version negotiation | MCP clients, Gemini users |
| [docs/guides/MCP_API_REFERENCE.md](guides/MCP_API_REFERENCE.md) | Complete API endpoint documentation | Integration engineers |
| [docs/guides/PLUGIN_IMPLEMENTATION.md](guides/PLUGIN_IMPLEMENTATION.md) | Practical plugin development guide | Plugin developers |

---

## 🧪 Testing & Quality

| Document | Purpose | Audience |
|----------|---------|----------|
| [REFACTORING_PLAN.md](work-tracking/REFACTORING_PLAN.md) | Code quality improvement plan (6 phases) | Developers |
| Learnings.md | Project learnings from each work unit | Team, future developers |
| Progress.md | Current work status, timeline | Project leads |

---

## 🎨 Design & UI

| Document | Purpose | Audience |
|----------|---------|----------|
| [BRANDING.md](/BRANDING.md) | Visual identity, color palette | Designers, maintainers |

---

## 🔧 Quick Reference

### Running Commands

**Python Backend:**
```bash
cd server
uv run python -m uvicorn app.main:app --reload  # Dev server
uv run pytest                                     # Tests
uv run mypy app/ --no-site-packages             # Type check
uv run ruff check --fix app/                    # Lint
uv run black app/                               # Format
```

**React Frontend:**
```bash
cd web-ui
npm run dev                    # Dev server
npm run build                  # Build
npm run preview              # Preview build
npm test                     # Tests
```

### Key Files

**Backend:**
- `server/app/main.py` – FastAPI app
- `server/app/mcp_routes.py` – MCP endpoint (/v1/mcp)
- `server/app/plugin_loader.py` – Plugin discovery
- `server/app/plugins/` – Vision plugins

**Frontend:**
- `web-ui/src/App.tsx` – Main app component
- `web-ui/src/hooks/useWebSocket.ts` – WebSocket hook
- `web-ui/src/api/client.ts` – API client

---

## 📊 Standards Summary

### Python (Backend)

- **Type hints:** 100% with mypy
- **Code style:** PEP 8 + Black
- **Linting:** Ruff
- **Testing:** pytest, 80%+ coverage
- **Pre-commit:** Black, Ruff, Mypy

### TypeScript/React (Frontend)

- **Type safety:** Full type annotations
- **Component patterns:** Functional + hooks
- **Testing:** Vitest, 80%+ coverage
- **Code style:** ESLint, Prettier (if configured)

### MCP Protocol

- **Version:** 2024-11-05
- **Transport:** JSON-RPC 2.0 over HTTP POST
- **Endpoint:** `POST /v1/mcp`
- **Tools:** Discoverable via `initialize` and `tools/list`

---

## 🚀 Deployment

| Document | Purpose |
|----------|---------|
| [README.md](/README.md) - Deployment section | Production deployment guide |
| [CONTRIBUTING.md](/CONTRIBUTING.md) - CI/CD | Automated testing & deployment |

---

## ❓ Getting Help

**For questions about:**
- **Project direction** → See [SOFTWARE_DESIGN_GUIDE.md](design/SOFTWARE_DESIGN_GUIDE.md)
- **Code style** → See [AGENTS.md](/AGENTS.md)
- **Plugin development** → See [PLUGIN_DEVELOPMENT.md](/PLUGIN_DEVELOPMENT.md)
- **MCP integration** → See [docs/guides/MCP_CONFIGURATION.md](guides/MCP_CONFIGURATION.md)
- **Architecture** → See [ARCHITECTURE.md](/ARCHITECTURE.md)
- **Contributing** → See [CONTRIBUTING.md](/CONTRIBUTING.md)

---

## 📅 Document Status

| Document | Last Updated | Status |
|----------|--------------|--------|
| AGENTS.md | 2026-01-11 | ✅ Updated post-migration |
| SOFTWARE_DESIGN_GUIDE.md | 2026-01-11 | ✅ Created |
| ARCHITECTURE.md | 2026-01-09 | ✅ Current |
| PLUGIN_DEVELOPMENT.md | 2026-01-10 | ✅ Current |
| README.md | 2026-01-09 | ✅ Current |

---

**Last Updated:** 2026-01-11 at 14:35 UTC
