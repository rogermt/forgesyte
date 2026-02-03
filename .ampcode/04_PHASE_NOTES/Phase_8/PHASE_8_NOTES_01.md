# ⭐ Phase 8 Notes

These notes track day‑to‑day findings, architectural clarifications, regressions, and decisions made during Phase 8.  
This file is a working log and supplements the formal milestone checklist.

---

## Note 01 — Metrics Layer Boundaries
- Metrics must be emitted at three layers:
  1. Server (`/v1/analyze`, job lifecycle)
  2. Plugin (execution duration, success/failure)
  3. Job pipeline (queued → running → done)
- All metrics must include correlation IDs (`job_id`, `request_id`).

---

---

## Note 02 — Metrics Emission Strategy
Metrics must be emitted at three layers:
1. Server (`/v1/analyze`, job lifecycle)
2. Plugin execution (duration, success/failure)
3. Job pipeline (queued → running → done)

All metrics must include correlation IDs:
- `job_id`
- `request_id`
- `plugin`
- `tool` (if applicable)

Metrics must be structured, not free‑form.

---

## Note 03 — Normalisation Canonical Schema
All plugin outputs must conform to a single canonical schema.

Normalisation rules:
- Bounding boxes → `{x1, y1, x2, y2}`
- Confidence scores → float
- Class labels → string
- Multi-frame results → include `frame_index`
- Radar/pitch overlays → normalised coordinate space

Schema validation tests required before Phase 8 closure.

---

## Note 04 — Overlay Rendering Architecture
Overlay system must be unified across:
- players
- ball
- pitch
- radar
- track IDs

Rendering must be:
- decoupled from plugin output format
- deterministic
- performant (virtualisation + throttling)

Overlay toggles must be consistent across all modes.

---

## Note 05 — FPS & Performance Controls
FPS throttling required for video overlays.

Performance safeguards:
- frame skipping for slow devices
- throttled redraws
- GPU/CPU mode indicator (optional)
- performance metrics surfaced in UI

Regression tests required for FPS stability.

---

## Note 06 — Device Selector Logic
UI must allow CPU/GPU selection.

Server must accept device preference:
- `?device=cpu`
- `?device=gpu`

Plugin must enforce device guardrails:
- GPU unavailable → fallback to CPU
- GPU errors → fallback to CPU

Device mismatch warnings required.

---

## Note 07 — Structured Logging Requirements
Replace all `print()` statements with structured logging.

Logging must include:
- timestamp
- job_id
- plugin
- tool
- duration
- error (if any)

Plugin-side logging required for inference steps.

---

## Note 08 — Job Lifecycle Invariants
Every job must reach a terminal state:
- `queued`
- `running`
- `done`
- `error`

CI must enforce:
- no stuck jobs
- no missing terminal states
- no legacy `/run` paths

Job progress reporting optional but recommended.

---

## Note 09 — Manifest Validation Rules
Every plugin must expose a manifest.

Manifest must include:
- plugin name
- version
- tools
- input schema
- output schema

CI must validate:
- manifest exists
- manifest is valid JSON
- manifest matches plugin implementation

---

## Note 10 — Phase 8 Closure Requirements
Before Phase 8 can close:
- all acceptance checklist items must be green
- CI must be green
- no regressions allowed
- structured logging must be complete
- normalisation layer must be stable
- overlay system must be functional
- FPS controls must be implemented
- device selector must be operational

Phase 8 Closure PR required.

---
