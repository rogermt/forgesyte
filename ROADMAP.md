# 🗺️ **ROADMAP.md (Drop‑In Ready for Project Root)**

```markdown
# ForgeSyte Vision Platform — Roadmap

This roadmap defines the architectural direction, milestones, and guardrails for
building a stable, plugin‑agnostic, testable, and MCP‑compatible vision
processing platform.

It is intentionally explicit and non‑negotiable: every milestone restores or
reinforces the platform’s core contract — **plugins must be first‑class
citizens**, not special‑cased exceptions.

---

## 🎯 Vision

ForgeSyte must support any vision plugin — OCR, YOLO, Motion, Radar, or future
third‑party tools — with:

- A unified execution model  
- A stable plugin contract  
- Real integration tests  
- Dynamic tool discovery  
- Predictable error handling  
- Full MCP compatibility  

No plugin should require hardcoded references, mocks, or bespoke endpoints.

---

# 🚀 Milestone 1 — Plugin Contract & Loader Rewrite  
**Goal:** Restore architectural integrity by enforcing a real plugin contract and
loading plugins dynamically via entry points.

### Deliverables
- Introduce `BasePlugin` abstract class  
- Enforce required attributes (`name`, `tools`, `run_tool`)  
- Rewrite plugin loader to use entry points only  
- Validate plugin schemas on load  
- Reject invalid plugins with explicit errors  
- Remove all hardcoded plugin references (`ocr_plugin`, `motion_detector`, etc.)  
- Add CI guardrails to prevent regressions  

### Success Criteria
- All plugins subclass `BasePlugin`  
- Registry contains only validated plugins  
- Loader fails fast with clear errors  
- No hardcoded plugin names remain in the codebase  

---

# 🧪 Milestone 2 — Real Integration Tests  
**Goal:** Replace mock‑driven tests with real plugin execution tests.

### Deliverables
- Install YOLO tracker plugin as dev dependency  
- Add plugin discovery tests (entry points → registry)  
- Add real tool invocation tests (no mocks)  
- Add error‑path tests (missing plugin, missing tool, invalid args)  
- Add registry behavior tests  
- Add `/run` endpoint tests with real plugin execution  
- Ensure all `/run` failures return JSON (never raw 500s)  

### Success Criteria
- No integration test mocks `run_plugin_tool`  
- YOLO plugin executes in tests  
- OCR plugin executes in tests  
- `/run` endpoint always returns JSON  
- Test suite catches plugin import failures  

---

# 🔌 Milestone 3 — Unified Tool Execution (Frontend + Backend)  
**Goal:** Ensure all plugins use the same execution path and telemetry.

### Deliverables
- Introduce `runTool()` unified tool runner (frontend)  
- Update OCR + YOLO to use `runTool()`  
- Add structured logging for every tool invocation  
- Add retry wrapper with exponential backoff  
- Add frame‑level metrics (duration, success, error)  
- Add manifest‑fetch regression test  
- Remove divergent fetch logic from `useVideoProcessor`  

### Success Criteria
- All plugins use the same execution path  
- All tool calls logged with plugin/tool/duration  
- Retries handled consistently  
- Manifest always fetched on plugin change  
- No direct fetch calls to `/run` outside `runTool()`  

---

# 🔄 Milestone 4 — MCP Adapter Rewrite  
**Goal:** Make MCP a first‑class interface for all plugins and tools.

### Deliverables
- Auto‑generate MCP endpoints from plugin registry  
- Support all tools, not just `/v1/analyze?plugin=xxx`  
- Add MCP schema generation from plugin tool schemas  
- Add MCP integration tests  
- Add MCP error‑path tests  

### Success Criteria
- MCP adapter exposes all plugin tools  
- MCP responses match REST responses  
- MCP errors match REST errors  
- MCP tests run real plugin execution  

---

# 🛡️ Milestone 5 — Governance & Guardrails  
**Goal:** Prevent architectural drift from ever happening again.

### Deliverables
- CI rule: no mocks for `run_plugin_tool` in integration tests  
- CI rule: all plugins must subclass `BasePlugin`  
- CI rule: `/run` endpoint must always return JSON  
- CI rule: plugin loader must load at least one plugin  
- CI rule: manifest must exist for every plugin  

### Success Criteria
- Architectural regressions are mechanically impossible  
- Plugin ecosystem remains stable and predictable  
- New plugins can be added without modifying core code  

---

# 📌 Status Tracking

Each milestone should be represented as a GitHub Milestone with issues linked
from Section 6 of the architecture report.

---

# 🧭 Summary

This roadmap restores ForgeSyte’s original promise:  
**a modular, extensible, plugin‑driven vision platform with real guarantees.**

It replaces ad‑hoc behavior with explicit contracts, replaces mocks with real
integration tests, and replaces hardcoded logic with dynamic discovery.

ForgeSyte becomes predictable, testable, and future‑proof.

```

---

