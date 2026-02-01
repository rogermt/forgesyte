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

Absolutely, Roger.  
I’ll keep **your exact milestone structure**, **your exact formatting**, **your exact indentation**, and simply **mark the items that are now completed** based on the current architecture and the work you’ve already verified.

I will **not rewrite**, **not re‑order**, **not re‑interpret**, and **not modernize** the milestones.  
I will **only** mark items as `[x]` where they are now complete.

Here is your milestone list with **accurate completion marks** based on everything you and I confirmed in this session.

---

# ⭐ **Milestone 1.5 — YOLO Tracker Operational Baseline**  
*(New milestone inserted between M1 and M2)*

### **1. Plugin Load & Environment Alignment**
- [x] Uninstall stale CPU wheel of `forgesyte-yolo-tracker`  
- [x] Reinstall plugin in editable mode (`pip install -e`) for CPU  
- [x] Confirm GPU + CPU environments load the same plugin path  
- [x] Add plugin‑path diagnostic script (prints active plugin file)  
- [x] Confirm plugin loads via entrypoints without errors  

### **2. BasePlugin Contract Migration**
- [x] Confirm handler string resolution works (`"handler": "player_detection"`)  
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
- [x] Create `YOLO_Tracker_Smoke_Test.ipynb`  
- [x] Load plugin inside notebook  
- [x] Load test image  
- [ ] Run each tool (player, ball, pitch, radar)  
- [ ] Visualise results  
- [ ] Validate schema compliance  
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

### **7. — OCR Plugin Migration**
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

## **Milestone 2 — Real Integration Tests**
- [ ] Add plugin discovery tests (entry points → registry)  
- [ ] Add real tool invocation tests (no mocks)  
- [ ] Add error‑path tests (missing plugin, missing tool, invalid args)  
- [ ] Add registry behaviour tests  
- [ ] Add `/run` endpoint tests with real plugin execution  
- [ ] Ensure `/run` endpoint always returns JSON  
- [ ] Add CI guardrail: no mocks for `run_plugin_tool` in integration tests  

---

### Milestone 3 — Unified Tool Execution (Frontend + Backend)

- [x] Introduce runTool() unified tool runner  
- [x] Update OCR to use runTool()  
- [x] Update YOLO to use runTool()  
- [x] Add structured logging for tool invocation  
- [ ] Add retry wrapper with exponential backoff  
- [ ] Add frame-level metrics (duration, success, error)  
- [ ] Add manifest-fetch regression test  
- [ ] Remove divergent fetch logic from useVideoProcessor  

---

### Milestone 4 — MCP Adapter Rewrite

- [ ] Auto-generate MCP endpoints from plugin registry  
- [ ] Support all plugin tools in MCP  
- [ ] Add MCP schema generation  
- [ ] Add MCP integration tests  
- [ ] Add MCP error-path tests  

---

### Milestone 5 — Governance & Guardrails

- [ ] CI: enforce BasePlugin inheritance  
- [ ] CI: enforce JSON-only responses from /run  
- [ ] CI: enforce plugin loader loads at least one plugin  
- [ ] CI: enforce manifest exists for every plugin  

---
Perfect — I’ll generate **Milestone 6** in the *exact same format* as your existing milestones, fully aligned with the **new /v1/analyze job‑based architecture**, and without altering or rewriting any of your previous milestones.

This new milestone will sit *after* Milestone 5 and will represent the **modern ForgeSyte architecture** you are now running.

Here it is, clean and ready to drop into your roadmap.

---

# **Milestone 6 — Job‑Based Pipeline & Web‑UI Migration (Current Architecture)**

### **1. Server Execution Model Migration**
- [x] Remove legacy `/run` endpoint from server  
- [x] Remove legacy tool‑level execution paths  
- [x] Introduce `/v1/analyze` as the unified execution endpoint  
- [x] Introduce `/v1/jobs/{id}` for async result retrieval  
- [x] Introduce `/v1/jobs` listing endpoint  
- [x] Confirm OCR plugin works via `/v1/analyze`  
- [x] Confirm YOLO plugin works via `/v1/analyze` (baseline job creation)  
- [ ] Add job cancellation guardrails  
- [ ] Add job timeout enforcement  
- [ ] Add job progress reporting (optional)  

---

### **2. Plugin Manifest & Discovery (New Model)**
- [x] Confirm `/v1/plugins` returns all plugins  
- [x] Confirm `/v1/plugins/{plugin}/manifest` returns tool schemas  
- [x] Remove dependency on old MCP manifest for execution  
- [x] Add schema validation tests for manifests  
- [] Add CI guardrail: every plugin must expose a manifest  

---

### **3. Web‑UI Migration to Job Pipeline**
- [x] Replace old execution calls with `apiClient.analyzeImage()`  
- [x] Implement job polling via `apiClient.pollJob()`  
- [x] Update upload flow to use `/v1/analyze`  
- [x] Update results panel to display job results  
- [ ] Remove `ToolSelector` (no longer needed for execution)  
- [ ] Remove `detectToolType` (obsolete)  
- [ ] Remove `runTool()` usage from UI  
- [ ] Update VideoTracker to use job pipeline instead of tool runner  
- [ ] Add job progress UI (queued → running → done)  
- [ ] Add error‑state UI for failed jobs  

---

### **4. WebSocket Streaming Alignment**
- [x] Confirm `/v1/stream` WebSocket endpoint works  
- [x] Confirm plugin switching works via WebSocket  
- [ ] Add frame‑level error handling in WebSocket stream  
- [ ] Add reconnect guardrails for unstable networks  
- [ ] Add stream‑mode → job‑mode fallback (optional)  

---

### **5. Remove Legacy Tool‑Execution Architecture**
- [x] Remove `runPluginTool()` from API client  
- [x] Remove `ToolExecutionResponse` type  
- [ ] Remove `runTool.ts` (or repurpose for job wrapper)  
- [ ] Remove `/plugins/{plugin}/tools/{tool}/run` references  
- [ ] Remove tool‑centric UI components  
- [ ] Update documentation to reflect plugin‑level execution only  

---

### **6. VideoTracker (New Architecture Integration)**
- [ ] Implement frame batching → `/v1/analyze`  
- [ ] Implement video‑to‑frames extraction (client or server)  
- [ ] Implement job polling for multi‑frame results  
- [ ] Render YOLO tracks + IDs in UI  
- [ ] Add playback controls (optional)  
- [ ] Add radar view (optional)  
- [ ] Validate output schema for multi‑frame results  

---

### **7. Governance & Guardrails (Job‑Based Model)**
- [ ] CI: enforce `/v1/analyze` returns JSON only  
- [ ] CI: enforce every job reaches terminal state  
- [ ] CI: enforce plugin loader loads ≥ 1 plugin  
- [ ] CI: enforce manifest exists for every plugin  
- [ ] CI: enforce no legacy `/run` code paths remain  

---

### Milestone 7 — VideoTracker Full Implementation (Job‑Based Architecture)

### **1. Data Flow & Contracts**
- [x] Confirm YOLO tracker plugin is addressable via `/v1/analyze?plugin=yolo-tracker`  
- [ ] Define canonical input contract for video jobs (single video file vs frame sequence)  
- [ ] Define canonical output contract for tracking (per‑frame detections, track IDs, metadata)  
- [ ] Document expected schema in plugin manifest (tools section)  
- [ ] Add schema validation tests for YOLO tracker outputs  

---

### **2. Backend Video Handling**
- [ ] Implement video ingestion path in YOLO plugin (file or frames)  
- [ ] Implement frame extraction (server‑side) with deterministic sampling  
- [ ] Implement per‑frame YOLO inference + tracking  
- [ ] Aggregate results into a single job result payload  
- [ ] Add logging for frame count, processing time, and error cases  
- [ ] Add guardrail tests for invalid video, zero frames, corrupted input  

---

### **3. Job Model for Video**
- [ ] Extend job model to support multi‑frame metadata (frame count, duration, fps)  
- [ ] Add progress reporting (e.g., frames_processed / total_frames)  
- [ ] Ensure `/v1/jobs/{id}` returns stable, incremental status for long‑running video jobs  
- [ ] Add timeout and cancellation behavior tuned for video workloads  

---

### **4. Web‑UI: Video Upload & Control Surface**
- [ ] Add “Video” mode to Upload/Stream/Jobs navigation (or extend Upload)  
- [ ] Implement video file upload wired to `/v1/analyze?plugin=yolo-tracker`  
- [ ] Show job creation + status (queued → running → done) for video jobs  
- [ ] Add basic playback controls (play/pause/seek) for processed video  
- [ ] Add overlay toggles (players, ball, pitch, tracks, radar)  

---

### **5. Web‑UI: VideoTracker Component**
- [ ] Implement `VideoTracker` as a job‑centric component (no direct tool calls)  
- [ ] Fetch job result and map per‑frame detections to overlays  
- [ ] Render bounding boxes, track IDs, and classes over video frames  
- [ ] Add timeline / scrubber synced with frame index  
- [ ] Add performance safeguards (virtualization, throttled redraws)  

---

### **6. UX & Error Handling**
- [ ] Show clear progress indicator for long video processing  
- [ ] Show structured error messages for failed video jobs  
- [ ] Provide “retry” and “download logs” options (optional)  
- [ ] Add empty‑state UX when no video jobs exist  

---

### **7. Testing & Guardrails**
- [ ] Add integration tests: video upload → job → result → UI render  
- [ ] Add regression tests for YOLO tracker schema stability  
- [ ] Add CI guardrail: YOLO tracker must pass a minimal video smoke test  
- [ ] Add performance test for max video length / resolution thresholds  

---


---
