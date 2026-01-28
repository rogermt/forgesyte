---

# 🧨 1. **Formal Architectural Defect Report**

## Title  
**System-wide Plugin Architecture Regression and Mock-Driven False Integration Coverage**

## Severity  
**Critical — Architectural Integrity Failure**

## Summary  
The plugin system no longer behaves as a generic, dynamic plugin ecosystem.  
Hardcoded plugin references, mock-driven tests, and incomplete MCP integration have created a system that only works for two legacy plugins (OCR, motion) and fails for any real third-party plugin (e.g., YOLO tracker).

## Defects Identified

### 1. Hardcoded Plugin References  
Found in:
- `main.py`
- `health_check.py`
- `vision_analysis.py`
- test fixtures
- MCP adapter examples

**Impact:**  
Breaks plugin-agnostic design. Prevents new plugins from functioning.

### 2. Fake Integration Tests  
All “integration” tests mock `PluginManagementService.run_plugin_tool`, bypassing:
- entry point loading  
- registry behavior  
- real tool invocation  
- error handling  

**Impact:**  
False confidence. No real plugin has ever been tested.

### 3. Incomplete Plugin Loader  
Entry points are mocked in tests.  
Real plugin loading is never validated.

### 4. MCP Adapter Not Plugin-Agnostic  
Only supports `/v1/analyze?plugin=xxx`.  
Does not expose plugin tools dynamically.

### 5. BasePlugin Contract Not Enforced  
Plugins can be anything.  
No schema, no validation, no lifecycle guarantees.

---

# 🚀 2. **Migration Plan to a Real Plugin Ecosystem**

## Phase 1 — Establish Canonical Plugin Contract  
- Define `BasePlugin` with required attributes:  
  - `name`  
  - `tools` dict  
  - `schema` for each tool  
  - `validate()` lifecycle hook  
- Enforce inheritance.

## Phase 2 — Rewrite Plugin Loader  
- Load via entry points only  
- Validate plugin contract  
- Register tools dynamically  
- Reject invalid plugins with explicit errors

## Phase 3 — Remove Hardcoded References  
- Replace all `ocr_plugin` / `motion_detector` references with registry lookups  
- Update WebSocket defaults to dynamic plugin selection  
- Update health checks to iterate over registry

## Phase 4 — Real Integration Tests  
- Install YOLO plugin as dev dependency  
- Load via entry points  
- Invoke real tools  
- Validate real outputs

## Phase 5 — MCP Adapter Rewrite  
- Auto-generate MCP endpoints from plugin registry  
- Support all tools, not just `analyze`

---

# 🧪 3. **Test Suite Overhaul Plan**

## Replace Mock-Driven Tests with Real Integration Tests  
### New test categories:

### **1. Plugin Discovery Tests**
- Ensure entry points load real plugins  
- Ensure invalid plugins fail with clear errors  

### **2. Tool Invocation Tests**
- Call real plugin methods  
- Validate schema compliance  
- Validate error handling  

### **3. Registry Behavior Tests**
- Register multiple plugins  
- Resolve by name  
- Handle missing plugins gracefully  

### **4. API Endpoint Tests**
- Hit `/v1/plugins/{plugin}/tools/{tool}/run`  
- Validate real execution  
- Validate error paths  

### **5. MCP Compatibility Tests**
- Ensure MCP adapter exposes all tools  
- Validate request/response schemas  

---

# 📜 4. **Plugin Contract Specification**

## Base Requirements  
Every plugin **must** implement:

### **Attributes**
- `name: str`  
- `description: str`  
- `tools: dict[str, ToolSpec]`

### **ToolSpec**
Each tool must define:
- `input_schema: dict`  
- `output_schema: dict`  
- `handler: callable`  

### **Methods**
- `validate(self)`  
- `get_tools(self)`  
- `run_tool(self, tool_name, args)`  

### **Error Contract**
Plugins must raise:
- `PluginToolNotFound`  
- `PluginValidationError`  
- `PluginExecutionError`  

---

# 🧱 5. **BasePlugin Enforcement Strategy**

## Step 1 — Introduce `BasePlugin` Abstract Class  
Use `abc.ABC` to enforce required methods.

## Step 2 — Validate on Registration  
When loading entry points:
- Check subclass of BasePlugin  
- Validate tool schemas  
- Validate tool names  
- Validate callable handlers  

Reject plugin if:
- Missing attributes  
- Missing schemas  
- Missing tools  
- Wrong inheritance  

## Step 3 — Add CI Guardrails  
- Test that all plugins subclass BasePlugin  
- Test that all tools have schemas  
- Test that plugin registry loads without mocks  

---

---

## 6. Immediate Remediation & Guardrail Task List

This section translates the architectural findings into **concrete, atomic tasks** that can be implemented, reviewed, and closed without ambiguity.

### 6.1 Backend: Plugin Architecture & Loader

- **Task 6.1.1 — Introduce `BasePlugin` and enforce contract**
  - **Goal:** All plugins must subclass `BasePlugin` and implement `name`, `tools`, and `run_tool`.
  - **Acceptance:** YOLO, OCR, motion plugins all subclass `BasePlugin`; registry rejects non‑conforming plugins with explicit errors.

- **Task 6.1.2 — Refactor `plugin_loader` to use entry points only**
  - **Goal:** Remove any ad‑hoc or hardcoded plugin loading; rely solely on `forgesyte.plugins` entry points.
  - **Acceptance:** A failing or missing entry point causes a clear startup error and is covered by tests.

- **Task 6.1.3 — Remove hardcoded plugin references**
  - **Goal:** Eliminate `ocr_plugin`, `motion_detector`, etc. from `main.py`, `health_check.py`, `vision_analysis.py`, and tests.
  - **Acceptance:** All plugin references go through the registry; tests assert no hardcoded plugin IDs remain.

---

### 6.2 Backend: Endpoint & Error Handling

- **Task 6.2.1 — Normalize `/run` endpoint error responses**
  - **Goal:** `/v1/plugins/{plugin_id}/tools/{tool_name}/run` must *always* return JSON, even on 500.
  - **Acceptance:** Global exception handler wraps all unhandled errors into a JSON `{ error, detail }` payload; `Invalid JSON from tool` can no longer occur.

- **Task 6.2.2 — Add structured logging to `run_plugin_tool`**
  - **Goal:** Every tool invocation logs plugin, tool, arg keys, and outcome.
  - **Acceptance:** Logs show: `plugin_id`, `tool_name`, `arg_keys`, `status`, `duration_ms`, and error (if any).

- **Task 6.2.3 — Add real integration test for YOLO tracker**
  - **Goal:** Hit `/v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run` with a real base64 frame.
  - **Acceptance:** Test runs without mocks, asserts valid JSON response shape, and fails if plugin import or execution breaks.

---

### 6.3 Frontend: Unified Tool Runner & Telemetry

- **Task 6.3.1 — Adopt `runTool` for OCR and YOLO**
  - **Goal:** All plugin tools (OCR, YOLO, future plugins) use the same `runTool` utility.
  - **Acceptance:** No direct `fetch('/v1/plugins/.../run')` calls remain outside `runTool`.

- **Task 6.3.2 — Add frame‑level metrics and logs to `useVideoProcessor`**
  - **Goal:** Every frame processed records success/failure, duration, and error.
  - **Acceptance:** `metrics` and `logs` from `useVideoProcessor` are asserted in tests; regressions are visible.

- **Task 6.3.3 — Manifest fetch regression test**
  - **Goal:** Ensure manifest is always fetched when plugin changes.
  - **Acceptance:** Test fails if plugin selection does not trigger `/plugins/{plugin_id}/manifest`.

---

### 6.4 Governance & CI Guardrails

- **Task 6.4.1 — CI check: no mocks for `run_plugin_tool` in integration tests**
  - **Goal:** Prevent future “fake integration” tests that bypass real plugin execution.
  - **Acceptance:** CI fails if `PluginManagementService.run_plugin_tool` is patched in any `integration/` test.

- **Task 6.4.2 — CI check: all plugins subclass `BasePlugin`**
  - **Goal:** Enforce plugin contract mechanically.
  - **Acceptance:** CI fails if any registered plugin is not a `BasePlugin` subclass.

- **Task 6.4.3 — CI check: `/run` endpoint always returns JSON**
  - **Goal:** Guard against regressions that reintroduce non‑JSON 500s.
  - **Acceptance:** A test hits `/run` with a failing tool and asserts `Content-Type: application/json` and `{ error, detail }` shape.

---


---


