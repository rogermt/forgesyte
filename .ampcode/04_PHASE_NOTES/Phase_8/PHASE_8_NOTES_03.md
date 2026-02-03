

---

### `

```md
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

## 3. Work Streams

1. Metrics & Observability (DuckDB)
2. Structured Logging
3. Normalisation Layer
4. Overlay Renderer
5. FPS & Performance Controls
6. Device Selector Logic
7. Governance & CI

Each work stream maps directly to the Phase 8 acceptance checklist.

---

## 4. Architecture Decisions

- Metrics storage: DuckDB (local, analytical, zero-ops)
- Normalisation: central module `server/app/schemas/normalisation.py`
- Overlay renderer: new React component `OverlayRenderer.tsx`
- Device selector: query param `?device=cpu|gpu` on `/v1/analyze`
- Logging: Python logging with JSON formatter
- CI: Phase 8 guardrail script + schema/usage checks

---

## 5. Success Criteria

- All Phase 8 acceptance checklist items green
- CI green, no regressions
- Metrics available and queryable via DuckDB
- Normalisation enforced for all plugin outputs
- Overlays rendered via unified renderer
- FPS controls active and measurable
- Device selector functional with fallback
- Phase 8 Closure PR merged

---
```

---

### 

```md
# ⭐ Phase 8 Tasks — Granular Breakdown

## 1. Metrics & Observability (DuckDB)

- [ ] Create `server/app/observability/duckdb/` directory
- [ ] Add `PHASE_8_METRICS_SCHEMA.sql`
- [ ] Initialise `metrics.db` using schema
- [ ] Implement `metrics_writer.py`
- [ ] Implement `metrics_reader.py`
- [ ] Wire job pipeline to write job metrics
- [ ] Wire plugin wrapper to write plugin metrics
- [ ] Wire overlay renderer to write overlay metrics
- [ ] Wire device selector to write device usage metrics
- [ ] Add basic analysis queries (job summary, plugin duration, device usage)

---

## 2. Structured Logging

- [ ] Add JSON formatter to Python logging config
- [ ] Replace `print()` calls in server with structured logs
- [ ] Add correlation IDs (job_id, plugin, device) to logs
- [ ] Add plugin-side logging for inference steps
- [ ] Add error-path logging for failed jobs and plugins

---

## 3. Normalisation Layer

- [ ] Create `server/app/schemas/normalisation.py`
- [ ] Define canonical result schema (boxes, labels, scores, frames)
- [ ] Implement normalisation functions per plugin type
- [ ] Add schema validation tests
- [ ] Wire job pipeline to pass plugin outputs through normalisation
- [ ] Add CI check: all results must pass normalisation

---

## 4. Overlay Renderer

- [ ] Create `web-ui/src/components/OverlayRenderer.tsx`
- [ ] Implement bounding box rendering
- [ ] Implement track ID rendering
- [ ] Implement pitch line rendering
- [ ] Implement radar rendering
- [ ] Add overlay toggles (players, ball, pitch, radar)
- [ ] Refactor VideoTracker to delegate to `OverlayRenderer`

---

## 5. FPS & Performance Controls

- [ ] Add FPS throttling to overlay rendering
- [ ] Add frame skipping for slow devices
- [ ] Add performance metrics (render time, FPS) to metrics layer
- [ ] Add regression tests for FPS stability
- [ ] Add UI indicators for performance state (optional)

---

## 6. Device Selector Logic

- [ ] Add CPU/GPU selector to Web-UI
- [ ] Pass `?device=cpu|gpu` to `/v1/analyze`
- [ ] Update server to accept and propagate device preference
- [ ] Add plugin-side device guardrails
- [ ] Implement GPU→CPU fallback logic
- [ ] Log device usage to DuckDB

---

## 7. Governance & CI

- [ ] Add `phase8_guardrails.sh` to CI
- [ ] Enforce no raw `print()` in server/plugins
- [ ] Enforce presence of DuckDB metrics schema + DB
- [ ] Enforce normalisation usage
- [ ] Enforce manifest validity
- [ ] Enforce no legacy `/run` paths
- [ ] Update `.ampcode/PROJECT_RECOVERY` docs with Phase 8 state

---
```

---

### 

```md
# ⭐ Phase 8 Timeline — Sequenced Execution Plan

## Phase 8 Order of Operations

The goal is to minimise rework and maximise observability while building overlays and performance features.

---

## Step 1 — Metrics & Logging Foundation

1.1 Metrics (DuckDB)
- [ ] Create DuckDB schema + `metrics.db`
- [ ] Implement `metrics_writer.py`
- [ ] Implement `metrics_reader.py`
- [ ] Wire job pipeline + plugin wrapper to write metrics

1.2 Structured Logging
- [ ] Add JSON logging config
- [ ] Replace `print()` with structured logs
- [ ] Add correlation IDs to logs

**Exit criteria:**  
- Metrics written for jobs + plugins  
- Logs structured and correlated with job_id  

---

## Step 2 — Normalisation Layer

- [ ] Implement `normalisation.py`
- [ ] Define canonical schema
- [ ] Wire pipeline to normalise all plugin outputs
- [ ] Add schema validation tests

**Exit criteria:**  
- All plugin outputs pass through normalisation  
- Tests green  

---

## Step 3 — Overlay Renderer

- [ ] Implement `OverlayRenderer.tsx`
- [ ] Wire VideoTracker to use `OverlayRenderer`
- [ ] Add overlay toggles
- [ ] Log overlay performance metrics

**Exit criteria:**  
- Overlays rendered via unified renderer  
- Overlay metrics visible in DuckDB  

---

## Step 4 — FPS & Performance Controls

- [ ] Add FPS throttling + frame skipping
- [ ] Add performance metrics to metrics layer
- [ ] Add regression tests for FPS

**Exit criteria:**  
- Stable FPS under expected load  
- No major regressions  

---

## Step 5 — Device Selector

- [ ] Add device selector to UI
- [ ] Wire `?device=cpu|gpu` to `/v1/analyze`
- [ ] Implement plugin-side guardrails + fallback
- [ ] Log device usage

**Exit criteria:**  
- Device selection works end-to-end  
- Fallback behaviour validated  

---

## Step 6 — Governance & Closure

- [ ] Finalise Phase 8 CI guardrails
- [ ] Run full acceptance checklist
- [ ] Prepare Phase 8 Closure PR
- [ ] Update epic + ISSUES_LIST with Phase 8 closed
- [ ] Confirm Phase 9 prerequisites met

**Exit criteria:**  
- Phase 8 Closure PR merged  
- Phase 9 unblocked  

---
```

