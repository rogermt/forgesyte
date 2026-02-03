# ⭐ Phase 8 Acceptance Checklist

## 1. Metrics & Observability
- [ ] Metrics emitted for `/v1/analyze`
- [ ] Metrics emitted for job lifecycle (queued → running → done)
- [ ] Metrics emitted for plugin execution
- [ ] Correlation IDs added (job_id, request_id)
- [ ] Structured logging implemented (debug/info/warn/error)

## 2. Result Normalisation
- [ ] Canonical schema defined
- [ ] Bounding boxes normalised
- [ ] Class labels normalised
- [ ] Confidence scores normalised
- [ ] Multi-frame results normalised
- [ ] Schema validation tests added
- [ ] CI guardrail: normalisation required

## 3. Overlay System
- [ ] Unified overlay renderer implemented
- [ ] Bounding box renderer
- [ ] Track ID renderer
- [ ] Pitch line renderer
- [ ] Radar renderer
- [ ] Overlay toggles implemented
- [ ] Performance safeguards added

## 4. FPS & Performance
- [ ] FPS throttling implemented
- [ ] Frame skipping for slow devices
- [ ] Performance metrics surfaced
- [ ] Regression tests added

## 5. Device Selector
- [ ] CPU/GPU selector in UI
- [ ] Device preference passed to `/v1/analyze`
- [ ] Plugin-side device guardrails
- [ ] GPU→CPU fallback logic

## 6. Governance & CI
- [ ] CI: structured logging enforced
- [ ] CI: normalised results enforced
- [ ] CI: plugin manifest validity enforced
- [ ] CI: job lifecycle invariants enforced
- [ ] CI: no legacy `/run` paths

## 7. Documentation
- [ ] PHASE_8_README.md updated
- [ ] Phase 8 notes added
- [ ] Escalation template updated

## Final Gate
- [ ] All items above green
- [ ] CI green
- [ ] No regressions
- [ ] Phase 8 Closure PR approved
