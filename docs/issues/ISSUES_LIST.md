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

### Milestone 1 — Plugin Contract & Loader

- [ ] Introduce BasePlugin abstract class
- [ ] Enforce plugin contract (name, tools, run_tool)
- [ ] Rewrite plugin loader to use entry points only
- [ ] Validate plugin schemas on load
- [ ] Reject invalid plugins with explicit errors
- [ ] Remove hardcoded plugin references (ocr_plugin, motion_detector)
- [ ] Add CI guardrail: all plugins must subclass BasePlugin

### Milestone 2 — Real Integration Tests

- [ ] Add plugin discovery tests (entry points → registry)
- [ ] Add real tool invocation tests (no mocks)
- [ ] Add error-path tests (missing plugin, missing tool, invalid args)
- [ ] Add registry behavior tests
- [ ] Add /run endpoint tests with real plugin execution
- [ ] Ensure /run endpoint always returns JSON
- [ ] Add CI guardrail: no mocks for run_plugin_tool in integration tests

### Milestone 3 — Unified Tool Execution (Frontend + Backend)

- [ ] Introduce runTool() unified tool runner
- [ ] Update OCR to use runTool()
- [ ] Update YOLO to use runTool()
- [ ] Add structured logging for tool invocation
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

