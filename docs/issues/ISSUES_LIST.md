# 🗂️ **GitHub Issue List (Ready to Paste)**

Here’s the issue list derived from Section 6, formatted for GitHub:

```
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

Next:

- A **README badge block** showing roadmap status  