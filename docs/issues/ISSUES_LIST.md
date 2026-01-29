---

## 🚨 Epic Issue: Project Recovery

**File:** `EPIC_PROJECT_RECOVERY.md`  
**Type:** Epic  
**Severity:** Critical  
**Status:** Open  

This epic consolidates all recovery tasks to restore ForgeSyte's architectural integrity after a critical regression involving hardcoded plugin references, mock-driven tests, and incomplete MCP integration.

### Summary

ForgeSyte has devolved from a truly modular, plugin-agnostic vision platform into a system that:
- Contains hardcoded references to legacy plugins (`ocr_plugin`, `motion_detector`)
- Has 100% mock-driven "integration" tests that never execute real plugins
- Only exposes a single `/analyze` endpoint via MCP, not all plugin tools
- Does not enforce any plugin contract or BasePlugin inheritance

### The Fix

This epic addresses all five critical areas:

1. **Plugin Contract & Loader Rewrite** - Enforce BasePlugin, validate schemas, load via entry points
2. **Real Integration Tests** - Remove mocks, test real YOLO tracker execution
3. **Unified Tool Execution** - Single `runTool()` utility for all plugins
4. **MCP Adapter Rewrite** - Auto-generate endpoints for all plugin tools
5. **Governance & Guardrails** - CI checks preventing regression

### Key Success Criteria

- ✅ 100% of plugins subclass BasePlugin
- ✅ 0% integration tests with mocks
- ✅ 0 hardcoded plugin references
- ✅ All YOLO tracker tools exposed via MCP
- ✅ 5 CI governance checks enforcing architecture

### Related Documents

- [ARCHITECTURAL_DEFECT_REPORT.md](../status/ARCHITECTURAL_DEFECT_REPORT.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)

---

# ⭐ **Milestone 1.5 — YOLO Tracker Operational Baseline**  
*(New milestone inserted between M1 and M2)*

### **1. Plugin Load & Environment Alignment**
<<<<<<< Updated upstream
- [ ] Uninstall stale CPU wheel of `forgesyte-yolo-tracker`  
- [ ] Reinstall plugin in editable mode (`pip install -e`) for CPU  
- [ ] Confirm GPU + CPU environments load the same plugin path  
- [ ] Add plugin‑path diagnostic script (prints active plugin file)  
- [ ] Confirm plugin loads via entrypoints without errors  
=======
- [x] Uninstall stale CPU wheel of `forgesyte-yolo-tracker`  
- [x] Reinstall plugin in editable mode (`pip install -e`) for CPU  
- [x] Confirm GPU + CPU environments load the same plugin path  
- [x] Add plugin‑path diagnostic script (prints active plugin file)  
- [x] Confirm plugin loads via entrypoints without errors  
>>>>>>> Stashed changes

### **2. BasePlugin Contract Migration**
- [ ] Confirm handler string resolution works (`"handler": "player_detection"`)  
- [ ] Confirm all handlers resolve to bound methods  
- [ ] Confirm plugin passes contract validation end‑to‑end  

### **3. YOLO Model Loading**
- [ ] Ensure model weight paths are correct  
- [ ] Ensure device selection works (CPU/GPU)  
- [ ] Add logging for successful model load  
- [ ] Add guardrail test: plugin `on_load()` must instantiate models  

### **4. Reinstate Image Tracking**
- [ ] Reinstate player detection  
- [ ] Reinstate player tracking (IDs stable)  
- [ ] Reinstate ball detection  
- [ ] Reinstate pitch detection  
- [ ] Reinstate radar view (optional but recommended)  
- [ ] Validate output schemas for all tools  

### **5. Manual Smoke Test Notebook**
- [ ] Create `YOLO_Tracker_Smoke_Test.ipynb`  
- [ ] Load plugin inside notebook  
- [ ] Load test image  
- [ ] Run each tool (player, ball, pitch, radar)  
- [ ] Visualise results  
- [ ] Validate schema compliance  
<<<<<<< Updated upstream
- [ ] Confirm `/run` endpoint returns JSON with real inference  

---

## **Milestone 2 — Real Integration Tests**
- [ ] Add plugin discovery tests (entry points → registry)  
- [ ] Add real tool invocation tests (no mocks)  
- [ ] Add error‑path tests (missing plugin, missing tool, invalid args)  
- [ ] Add registry behaviour tests  
- [ ] Add `/run` endpoint tests with real plugin execution  
- [ ] Ensure `/run` endpoint always returns JSON  
- [ ] Add CI guardrail: no mocks for `run_plugin_tool` in integration tests  
- [ ] Confirm `/run` endpoint returns JSON with real inference 

### **6. JSON Output Compliance**
- [ ] Ensure all tool outputs are JSON‑serializable  
- [ ] Convert numpy arrays → lists  
- [ ] Convert torch tensors → lists  
- [ ] Convert bounding boxes → dicts  
- [ ] Remove non‑serializable objects  
- [ ] Validate output against `output_schema`  
- [ ] Add logging for tool output before serialization  
- [ ] Add guardrail test: tool must return valid JSON 

### **7. — OCR Plugin Migration** ✅ COMPLETE
- [x] Remove legacy `app.plugins` imports  
- [x] Rewrite OCR plugin to subclass `BasePlugin`  
- [x] Add correct entrypoint: `forgesyte.plugins`  
- [x] Add `tools` dict with string handler names  
- [x] Add `OCRInput` + `OCROutput` schemas  
- [x] Add `OCREngine` wrapper  
- [x] Ensure plugin loads via entrypoints  
- [x] Ensure plugin passes contract validation  
- [x] Ensure `/run` endpoint returns valid JSON  

**PR #76 merged** — 34/34 tests passing, 96% coverage, mypy clean  


### Milestone 2 — Real Integration Tests

- [ ] Add plugin discovery tests (entry points → registry)
- [ ] Add real tool invocation tests (no mocks)
- [ ] Add error-path tests (missing plugin, missing tool, invalid args)
- [ ] Add registry behavior tests
- [ ] Add /run endpoint tests with real plugin execution
- [ ] Ensure /run endpoint always returns JSON
- [ ] Add CI guardrail: no mocks for run_plugin_tool in integration tests
>>>>>>> Stashed changes


### Milestone 3 — Unified Tool Execution (Frontend + Backend)

- [x] Introduce runTool() unified tool runner
- [x] Update OCR to use runTool()
- [x] Update YOLO to use runTool()
- [x] Add structured logging for tool invocation
- [ ] Add retry wrapper with exponential backoff
- [ ] Add frame-level metrics (duration, success, error)
- [ ] Add manifest-fetch regression test
- [ ] Remove divergent fetch logic from useVideoProcessor

### Milestone 4 — MCP Adapter Rewrite

- [ ] Auto-generate MCP endpoints from plugin registry
- [ ] Support all plugin tools in MCP
- [ ] Add MCP schema generation
- [ ] Add MCP integration tests
- [ ] Add MCP error-path tests

### Milestone 5 — Governance & Guardrails

- [ ] CI: enforce BasePlugin inheritance
- [ ] CI: enforce JSON-only responses from /run
- [ ] CI: enforce plugin loader loads at least one plugin
- [ ] CI: enforce manifest exists for every plugin
```

---

