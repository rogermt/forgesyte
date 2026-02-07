# 🚨 Epic Issue: Project Recovery

**File:** `EPIC_PROJECT_RECOVERY.md`  
**Type:** Epic  
**Severity:** Critical  
**Status:** Open  

This epic consolidates all recovery tasks to restore ForgeSyte's architectural integrity after a critical regression involving hardcoded plugin references, mock-driven tests, and incomplete MCP integration.

---

## Summary

ForgeSyte has devolved from a truly modular, plugin-agnostic vision platform into a system that:
- Contains hardcoded references to legacy plugins (`ocr_plugin`, `motion_detector`)
- Has 100% mock-driven "integration" tests that never execute real plugins
- Only exposes a single `/analyze` endpoint via MCP, not all plugin tools
- Does not enforce any plugin contract or BasePlugin inheritance

---

## The Fix

This epic addresses all five critical areas:

1. **Plugin Contract & Loader Rewrite** - Enforce BasePlugin, validate schemas, load via entry points  
2. **Real Integration Tests** - Remove mocks, test real YOLO tracker execution  
3. **Unified Tool Execution** - Single `runTool()` utility for all plugins  
4. **MCP Adapter Rewrite** - Auto-generate endpoints for all plugin tools  
5. **Governance & Guardrails** - CI checks preventing regression  

---

## Key Success Criteria

- ✅ 100% of plugins subclass BasePlugin  
- ✅ 0% integration tests with mocks  
- ✅ 0 hardcoded plugin references  
- ✅ All YOLO tracker tools exposed via MCP  
- ✅ 5 CI governance checks enforcing architecture  

---

## Related Documents

- [ARCHITECTURAL_DEFECT_REPORT.md](../status/ARCHITECTURAL_DEFECT_REPORT.md)  
- [ROADMAP.md](../../ROADMAP.md)  
- [ARCHITECTURE.md](../../ARCHITECTURE.md)  

---

# ⭐ Milestone 1.5 — YOLO Tracker Operational Baseline

### 1. Plugin Load & Environment Alignment
- [x] Uninstall stale CPU wheel of `forgesyte-yolo-tracker`  
- [x] Reinstall plugin in editable mode (`pip install -e`) for CPU  
- [x] Confirm GPU + CPU environments load the same plugin path  
- [x] Add plugin-path diagnostic script (prints active plugin file)  
- [x] Confirm plugin loads via entrypoints without errors  

### 2. BasePlugin Contract Migration
- [x] Confirm handler string resolution works (`"handler": "player_detection"`)  
- [x] Confirm all handlers resolve to bound methods  
- [x] Confirm plugin passes contract validation end-to-end  

### 3. YOLO Model Loading
- [x] Ensure model weight paths are correct  
- [x] Ensure device selection works (CPU/GPU)  
- [x] Add logging for successful model load  
- [x] Add guardrail test: plugin `on_load()` must instantiate models  

### 4. Reinstate Image Tracking
- [x] Reinstate player detection  
- [x] Reinstate player tracking (IDs stable)  
- [x] Reinstate ball detection  
- [x] Reinstate pitch detection  
- [x] Reinstate radar view  
- [x] Validate output schemas for all tools  

### 5. Manual Smoke Test Notebook
- [x] Create `YOLO_Tracker_Smoke_Test.ipynb`  
- [x] Load plugin inside notebook  
- [x] Load test image  
- [x] Run each tool (player, ball, pitch, radar)  
- [x] Visualise results  
- [x] Validate schema compliance  
- [x] Confirm `/run` endpoint returns JSON with real inference  

### 6. JSON Output Compliance
- [x] Ensure all tool outputs are JSON-serializable  
- [x] Convert numpy arrays → lists  
- [x] Convert torch tensors → lists  
- [x] Convert bounding boxes → dicts  
- [x] Remove non-serializable objects  
- [x] Validate output against `output_schema`  
- [x] Add logging for tool output before serialization  
- [x] Add guardrail test: tool must return valid JSON  

### 7. OCR Plugin Migration
- [x] Remove legacy `app.plugins` imports  
- [x] Rewrite OCR plugin to subclass `BasePlugin`  
- [x] Add correct entrypoint: `forgesyte.plugins`  
- [x] Add `tools` dict with string handler names  
- [x] Add `OCRInput` + `OCROutput` schemas  
- [x] Add `OCREngine` wrapper  
- [x] Ensure plugin loads via entrypoints  
- [x] Ensure plugin passes contract validation  
- [x] Ensure `/run` endpoint returns valid JSON  

---

# ⭐ Milestone 2 — Real Integration Tests

- [x] Add plugin discovery tests (entry points → registry)  
- [x] Add real tool invocation tests (no mocks)  
- [x] Add error-path tests (missing plugin, missing tool, invalid args)  
- [x] Add registry behaviour tests  
- [x] Add `/run` endpoint tests with real plugin execution  
- [x] Ensure `/run` endpoint always returns JSON  
- [x] Add CI guardrail: no mocks for `run_plugin_tool` in integration tests  

---

# ⭐ Milestone 3 — Unified Tool Execution (Frontend + Backend)

- [x] Introduce runTool() unified tool runner  
- [x] Update OCR to use runTool()  
- [x] Update YOLO to use runTool()  
- [x] Add structured logging for tool invocation  
- [x] Add retry wrapper with exponential backoff  
- [x] Add frame-level metrics (duration, success, error)  
- [x] Add manifest-fetch regression test  
- [x] Remove divergent fetch logic from useVideoProcessor  

---

# ⭐ Milestone 4 — MCP Adapter Rewrite

- [x] Auto-generate MCP endpoints from plugin registry  
- [x] Support all plugin tools in MCP  
- [x] Add MCP schema generation  
- [x] Add MCP integration tests  
- [x] Add MCP error-path tests  

---

# ⭐ Milestone 5 — Governance & Guardrails

- [x] CI: enforce BasePlugin inheritance  
- [x] CI: enforce JSON-only responses from /run  
- [x] CI: enforce plugin loader loads at least one plugin  
- [x] CI: enforce manifest exists for every plugin  

---

# ⭐ Milestone 6 — Job-Based Pipeline & Web-UI Migration

*(Already completed — omitted here for brevity)*

---

# ⭐ Milestone 7 — VideoTracker Full Implementation

*(Already completed — omitted here for brevity)*

---

# ⭐ Milestone 8 — Full Plugin Ecosystem Stabilization

### 1. Plugin Contract Hardening
- [x] Enforce `BasePlugin` inheritance across all plugins  
- [x] Enforce `tools` dict with string handler names  
- [x] Enforce `input_schema` + `output_schema` for every tool  
- [x] Add CI guardrail: plugin missing schema → fail  
- [x] Add runtime guardrail: plugin missing handler → fail  
- [x] Add plugin-level health check endpoint  

### 2. Plugin Loader Finalization
- [x] Replace ad-hoc loader with entrypoint-only loader  
- [x] Add plugin manifest validation on startup  
- [x] Add plugin dependency/version validation  
- [x] Add plugin load-order determinism  
- [x] Add plugin load-failure isolation  

### 3. Plugin Registry Maturity
- [x] Add plugin metadata  
- [x] Add plugin-level metrics  
- [x] Add plugin enable/disable toggle  
- [x] Add plugin hot-reload support  
- [x] Add registry introspection endpoint  

### 4. Plugin Testing Framework
- [x] Add plugin contract tests  
- [x] Add plugin smoke tests  
- [x] Add plugin error-path tests  
- [x] Add plugin performance tests  
- [x] Add plugin serialization tests  

### 5. Plugin Documentation
- [x] Auto-generate plugin docs  
- [x] Add plugin README template  
- [x] Add plugin troubleshooting guide  
- [x] Add plugin development quickstart  
- [x] Add plugin versioning guidelines  

---

# ⭐ Milestone 9 — End-to-End Vision Pipeline (Unified Architecture)

### 1. Unified Vision Pipeline
- [x] Define canonical pipeline stages  
- [x] Add pipeline orchestration layer  
- [x] Add pipeline-level error handling  
- [x] Add pipeline-level metrics  
- [x] Add pipeline-level schema validation  

### 2. Multi-Tool Composition
- [x] Support chaining tools  
- [x] Support branching pipelines  
- [x] Add pipeline manifest format  
- [x] Add pipeline execution tests  
- [x] Add pipeline visualization  

### 3. Video + Image Hybrid Support
- [x] Add unified input contract  
- [x] Add frame batching  
- [x] Add multi-frame schema  
- [x] Add video metadata  
- [x] Add video error handling  

### 4. Analytics Layer
- [x] Add analytics plugin type  
- [x] Add derived metrics  
- [x] Add analytics schemas  
- [x] Add analytics test suite  
- [x] Add analytics visualization endpoints  

### 5. End-to-End Integration
- [x] Image → YOLO → Tracking → Analytics → JSON  
- [x] Video → YOLO → Tracking → Analytics → JSON  
- [x] Add golden-file tests  
- [x] Add regression tests  
- [x] Add CI guardrail: pipeline smoke test  

### 6. Developer Experience
- [x] Add pipeline builder CLI  
- [x] Add pipeline debugging tools  
- [x] Add pipeline profiling tools  
- [x] Add pipeline documentation generator  
- [x] Add pipeline examples  

---

# ⭐ Milestone 10 — ForgeSyte Platform Hardening & Release Readiness

### 1. Stability & Reliability
- [x] Add global exception handler for all API routes  
- [x] Add structured logging across all services  
- [x] Add rate limiting for heavy endpoints  
- [x] Add plugin sandboxing (resource isolation)  
- [x] Add job timeout + cancellation enforcement  

### 2. Performance
- [x] Add inference caching layer  
- [x] Add model warm-start on server boot  
- [x] Add async job batching for video workloads  
- [x] Add performance regression tests  
- [x] Add GPU/CPU auto-selection heuristics  

### 3. Security
- [x] Add plugin signature verification  
- [x] Add manifest integrity checks  
- [x] Add input sanitization for all endpoints  
- [x] Add audit logging for plugin execution  
- [x] Add permission model for plugin access  

### 4. Developer Experience
- [x] Add CLI for plugin scaffolding  
- [x] Add CLI for pipeline creation  
- [x] Add local dev server with hot reload  
- [x] Add plugin debugging dashboard  
- [x] Add end-to-end developer tutorial  

### 5. Release Readiness
- [x] Add versioned API documentation  
- [x] Add plugin compatibility matrix  
- [x] Add release checklist  
- [x] Add migration guide for plugin authors  
- [x] Tag v1.0.0 release candidate  

---

