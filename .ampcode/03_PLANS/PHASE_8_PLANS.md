# ⭐ Phase 8 Plans — Metrics, Normalisation, Overlays, Performance

**Status:** Planned → Active  
**Owner:** Roger  
**Depends on:** Phase 7 (Closed)  
**Unblocks:** Phase 9  

Phase 8 establishes the observability, normalisation, overlay, and performance foundations for the job-based architecture.

---

## 1. Objectives

- Add structured metrics across the job pipeline using DuckDB
- Introduce a canonical normalisation layer for all plugin outputs
- Build a unified overlay renderer for visual outputs
- Add FPS and performance controls for video workloads
- Add device selector logic (CPU/GPU) with guardrails
- Enforce governance via CI guardrails and documentation

---

## 2. Scope

**In scope:**

- Server-side metrics (jobs, plugins, overlays, device usage)
- Normalisation of plugin outputs into a canonical schema
- Web-UI overlay rendering refactor
- FPS throttling and performance safeguards
- Device selector wiring (UI → API → plugin)
- CI checks for logging, normalisation, manifests, job lifecycle

**Out of scope:**

- Advanced VideoTracker UX (Phase 9)
- Full Prometheus/Grafana stack (Phase 10+)
- New plugins or tools

---

## 3. Architecture Decisions

**Metrics Storage:** DuckDB
- Local, analytical, zero-ops
- Location: `server/app/observability/duckdb/metrics.db`
- Schema: `server/app/observability/duckdb/PHASE_8_METRICS_SCHEMA.sql`
- Writer: `server/app/observability/metrics_writer.py`
- Reader: `server/app/observability/metrics_reader.py`

**Normalisation:** Central module
- Location: `server/app/schemas/normalisation.py`
- Enforces canonical schema for all plugin outputs
- Integrated into job pipeline before response

**Overlay Renderer:** React component
- Location: `web-ui/src/components/OverlayRenderer.tsx`
- Unifies rendering for players, ball, pitch, radar, track IDs
- Decoupled from plugin output format

**Device Selector:** Query parameter
- API: `POST /v1/analyze?device=cpu|gpu`
- Server propagates to plugin loader
- Plugin enforces guardrails + GPU→CPU fallback

**Structured Logging:** Python logging with JSON formatter
- All `print()` calls replaced with `logging` module
- Correlation IDs: `job_id`, `request_id`, `plugin`, `tool`
- Levels: debug, info, warn, error

**Governance:** Phase 8 CI guardrails
- Script: `scripts/phase8_guardrails.sh`
- Enforces: no print(), structured logging, normalisation usage, manifest validity, no legacy `/run` paths

---

## 4. Work Streams

### 4.1 Metrics & Observability (DuckDB)

**Tasks:**
- [ ] Create `server/app/observability/duckdb/` directory
- [ ] Add `PHASE_8_METRICS_SCHEMA.sql` (job, plugin, overlay, device usage tables)
- [ ] Initialise `metrics.db` using schema
- [ ] Implement `metrics_writer.py` with write methods for all metric types
- [ ] Implement `metrics_reader.py` with query methods for analysis
- [ ] Wire job pipeline to emit job metrics (queued → running → done)
- [ ] Wire plugin wrapper to emit plugin execution metrics
- [ ] Wire overlay renderer to emit overlay performance metrics
- [ ] Wire device selector to emit device usage metrics
- [ ] Add basic analysis queries (job summary, plugin duration, device stats)

**Deliverables:**
- Metrics database with 4 tables
- Writer + reader classes
- Integration with job pipeline and plugins
- CI check that metrics.db exists

---

### 4.2 Structured Logging

**Tasks:**
- [ ] Add JSON formatter to `server/app/main.py` logging config
- [ ] Replace all `print()` calls in server with `logging.info/warn/error`
- [ ] Add correlation IDs to every log statement
- [ ] Add plugin-side logging for inference steps
- [ ] Add error-path logging for failed jobs and plugins
- [ ] Verify no raw `print()` in CI

**Deliverables:**
- All logs structured with JSON format
- Correlation IDs on every log entry
- Plugin logging hooks in place

---

### 4.3 Normalisation Layer

**Tasks:**
- [ ] Create `server/app/schemas/normalisation.py`
- [ ] Define canonical result schema:
  - Bounding boxes: `{x1, y1, x2, y2}` (normalized to 0-1)
  - Confidence scores: float (0-1)
  - Class labels: string
  - Multi-frame results: include `frame_index`
  - Metadata: `plugin`, `tool`, `device`
- [ ] Implement normalisation functions for each plugin type
- [ ] Add schema validation tests (check boxes, scores, labels)
- [ ] Wire job pipeline to normalise all plugin outputs before response
- [ ] Add CI check: all results must pass normalisation

**Deliverables:**
- Centralised normalisation module
- Schema validation tests
- Integration into job pipeline

---

### 4.4 Overlay Renderer

**Tasks:**
- [ ] Create `web-ui/src/components/OverlayRenderer.tsx`
- [ ] Implement bounding box rendering (with styles)
- [ ] Implement track ID rendering (labels)
- [ ] Implement pitch line rendering (static lines)
- [ ] Implement radar rendering (if applicable)
- [ ] Add overlay toggles (checkbox per overlay type)
- [ ] Refactor `VideoTracker.tsx` to delegate rendering to `OverlayRenderer`
- [ ] Pass normalised results to `OverlayRenderer`
- [ ] Add performance logging (render time, FPS)

**Deliverables:**
- Unified overlay renderer component
- Overlay toggles in UI
- Performance metrics emitted

---

### 4.5 FPS & Performance Controls

**Tasks:**
- [ ] Add FPS throttling to overlay rendering (target: 30 FPS on video)
- [ ] Add frame skipping for slow devices
- [ ] Record render time per frame in metrics
- [ ] Add FPS measurement + storage in metrics
- [ ] Add regression tests: verify FPS > 20 under normal load
- [ ] Add optional UI indicator for performance state (CPU/GPU load)

**Deliverables:**
- FPS throttling + frame skipping
- Performance metrics visible in DuckDB
- Regression tests

---

### 4.6 Device Selector Logic

**Tasks:**
- [ ] Add device selector dropdown to Web-UI config panel
- [ ] Pass `?device=cpu|gpu` to `/v1/analyze` endpoint
- [ ] Update server to accept and validate device parameter
- [ ] Propagate device preference to plugin loader
- [ ] Implement plugin-side device guardrails:
  - If GPU requested but unavailable → fallback to CPU + warn
  - If GPU fails → fallback to CPU + log error
- [ ] Add device usage logging to metrics
- [ ] Add device selection tests

**Deliverables:**
- Device selector in UI
- Device param wiring (UI → API → plugin)
- Fallback logic
- Device usage metrics

---

### 4.7 Governance & CI

**Tasks:**
- [ ] Create `scripts/phase8_guardrails.sh` with checks for:
  - No raw `print()` in server/ or plugins/
  - DuckDB schema + metrics.db exists
  - Normalisation module present + used
  - Manifest validation active
  - No legacy `/run` endpoints
- [ ] Add `phase8_guardrails.sh` to CI workflow
- [ ] Create Phase 8 escalation template
- [ ] Update `.ampcode/INDEX.md` with Phase 8 completion status
- [ ] Prepare Phase 8 Closure PR with all acceptance checklist items green

**Deliverables:**
- CI guardrails enforced
- Phase 8 documentation complete

---

## 5. Success Criteria

✅ **All Phase 8 acceptance checklist items green**

- [ ] Metrics emitted for `/v1/analyze`, job lifecycle, plugins, overlays, device usage
- [ ] Correlation IDs on all metrics + logs
- [ ] Structured logging active (no print())
- [ ] Canonical normalisation schema defined + enforced
- [ ] All plugin outputs normalised before response
- [ ] Schema validation tests passing
- [ ] Unified overlay renderer implemented + integrated
- [ ] All overlay types rendering (players, ball, pitch, radar)
- [ ] Overlay toggles functional
- [ ] FPS throttling active + measurable
- [ ] Frame skipping for slow devices
- [ ] Performance regression tests passing
- [ ] Device selector in UI + functional
- [ ] Device param wired to `/v1/analyze`
- [ ] Plugin-side device guardrails + fallback
- [ ] Device usage metrics visible in DuckDB
- [ ] CI guardrails enforced
- [ ] No regressions vs Phase 7

---

## 6. Sequenced Execution (Order of Operations)

### Step 1: Metrics & Logging Foundation (Days 1-3)
1. Create DuckDB schema + initialize metrics.db
2. Implement metrics_writer.py + metrics_reader.py
3. Wire job pipeline + plugins to emit metrics
4. Add JSON logging config + replace print() calls
- **Exit criteria:** Metrics flowing, logs structured with correlation IDs

### Step 2: Normalisation Layer (Days 4-6)
5. Create normalisation.py + define canonical schema
6. Implement normalisation functions per plugin
7. Add schema validation tests
8. Wire job pipeline to normalise outputs
- **Exit criteria:** All outputs normalised, tests passing

### Step 3: Overlay Renderer (Days 7-10)
9. Implement OverlayRenderer.tsx
10. Add overlay toggles
11. Refactor VideoTracker to use OverlayRenderer
12. Add performance logging
- **Exit criteria:** Overlays rendering, metrics emitted

### Step 4: FPS & Performance (Days 11-13)
13. Add FPS throttling + frame skipping
14. Add regression tests
- **Exit criteria:** Stable FPS, no regressions

### Step 5: Device Selector (Days 14-16)
15. Add device selector to UI
16. Wire device param through stack
17. Implement fallback logic
18. Add device usage metrics
- **Exit criteria:** End-to-end device selection working

### Step 6: Governance & Closure (Days 17-18)
19. Finalize CI guardrails
20. Run full acceptance checklist
21. Prepare + merge Phase 8 Closure PR
- **Exit criteria:** Phase 8 Closure PR merged, Phase 9 unblocked

---

## 7. Risk Mitigation

**Risk:** Performance regression during overlay refactor
- *Mitigation:* Parallel VideoTracker impl, regression tests, benchmark baseline from Phase 7

**Risk:** Device fallback logic causes unexpected plugin behaviour
- *Mitigation:* Plugin-side tests, device mismatch warnings in logs

**Risk:** Normalisation breaks existing plugin integrations
- *Mitigation:* Schema validation tests, backwards-compat checks before wiring pipeline

**Risk:** DuckDB query performance degrades with large datasets
- *Mitigation:* Incremental indexing, archival plan in Phase 10

---

## 8. Dependencies

- Phase 7 complete ✅
- Job pipeline stable ✅
- Plugin loader functional ✅
- No breaking changes to server API

---

## 9. Handoff to Phase 9

Once Phase 8 is closed:
- Metrics layer ready for Phase 9 analysis
- Normalisation stable for all plugins
- Overlay renderer ready for advanced UX work
- Device selector ready for multi-device scenarios
- Logging + observability foundation in place

Phase 9 can proceed with:
- Advanced VideoTracker UX
- Multi-frame visualisation
- Timeline/scrubber controls
- Performance tuning for long videos

---
