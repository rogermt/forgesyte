## ForgeSyte Roadmap 

This is a rewritten, modern view of your roadmap, aligned with the **current server reality**: `/v1/analyze`, `/v1/jobs`, `/v1/plugins`, `/v1/stream`, and a job‑centric execution model. It preserves your intent but removes `/run` as a first‑class concept.

---

### Milestone 1 — Core Plugin & Environment Baseline

- **Plugin load & environment alignment**
  - Ensure all plugins (OCR, YOLO tracker) are installed in editable mode
  - Confirm CPU/GPU environments load the same plugin paths
  - Add diagnostics to print active plugin file and entrypoint resolution
- **BasePlugin contract**
  - All plugins subclass `BasePlugin`
  - Handlers resolve from string names to bound methods
  - Contract validation passes end‑to‑end for each plugin

---

### Milestone 1.5 — YOLO Tracker Operational Baseline

- **YOLO plugin wiring**
  - YOLO tracker loads via entrypoints without errors
  - Model weights and device selection (CPU/GPU) are correctly configured
  - `on_load()` instantiates models and logs success
- **Image tracking**
  - Reinstate player, ball, pitch detection and tracking
  - Validate JSON‑serializable outputs and schemas
- **Smoke test notebook**
  - `YOLO_Tracker_Smoke_Test.ipynb` runs plugin on test images
  - Visualize detections and validate schema compliance

---

### Milestone 2 — Real Integration Tests

- **Plugin discovery**
  - Tests for entrypoints → registry → plugin instances
- **Execution paths**
  - Tests for valid plugin execution via the canonical API
  - Error‑path tests: missing plugin, invalid args, bad input
- **Registry behavior**
  - Ensure consistent plugin registration and reload behavior

*(In the modern model, these tests should target `/v1/analyze` + `/v1/jobs`, not `/run`.)*

---

### Milestone 3 — Unified Execution Abstractions

- **Client‑side unification**
  - Introduce a unified “analyze” helper (replacing `runTool`) that:
    - calls `/v1/analyze`
    - polls `/v1/jobs/{id}`
    - returns a stable result object
  - OCR and YOLO flows both use this unified path
- **Observability**
  - Structured logging for each analysis invocation
  - Optional retry wrappers for transient network/JSON errors
  - Frame‑level metrics (duration, success, error) where applicable

---

### Milestone 4 — MCP Adapter (On Top of Job Model)

- **MCP surface**
  - Auto‑generate MCP schemas from plugin manifests
  - Map MCP tool calls to `/v1/analyze` + `/v1/jobs`
- **Testing**
  - MCP integration tests for OCR and YOLO
  - MCP error‑path tests (invalid tool, invalid args, plugin errors)

---

### Milestone 5 — Governance & Guardrails

- **Plugin invariants**
  - CI: enforce `BasePlugin` inheritance
  - CI: enforce manifest exists for every plugin
  - CI: enforce at least one plugin loads successfully
- **Response invariants**
  - CI: enforce JSON‑only responses from public endpoints
  - CI: enforce job results are always JSON‑serializable
- **Architecture invariants**
  - CI: forbid reintroduction of legacy `/run` paths
  - CI: forbid bypassing the job model for long‑running work

---

### Milestone 6 — Job‑Based Pipeline & Web‑UI Migration

- **Server**
  - `/v1/analyze` as the single entrypoint for analysis
  - `/v1/jobs`, `/v1/jobs/{id}` for async tracking
  - `/v1/plugins`, `/v1/plugins/{plugin}/manifest` for discovery
- **Web‑UI**
  - Upload flow uses `analyzeImage` + `pollJob`
  - Jobs view lists and inspects jobs
  - Results panel renders job results (not tool responses)
  - WebSocket streaming uses `/v1/stream` for live camera
- **Cleanup**
  - Remove `runPluginTool`, `ToolExecutionResponse`, and tool‑centric execution assumptions
  - Keep tools only as schema/UX hints, not execution units

---

### Milestone 7 — VideoTracker Full Implementation

- **Backend**
  - Video ingestion, frame extraction, YOLO tracking, and aggregated job results
- **Job model**
  - Progress, cancellation, and timeouts tuned for video workloads
- **Web‑UI**
  - Video upload, job‑aware VideoTracker component, overlays, playback controls
- **Guardrails**
  - Integration tests from upload → job → UI
  - CI checks for YOLO tracker correctness and schema stability