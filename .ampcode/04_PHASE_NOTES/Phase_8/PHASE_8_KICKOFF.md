# ⭐ **Milestone 9 — Phase 8 Kickoff (System Metrics, Logging, Normalisation, Overlays)**  
*(Phase 7 closed; Phase 8 now unblocked)*

### 📌 Phase 8 Transition Note  
Phase 7 (CSS Modules Migration) is officially closed.  
All Tier 1 migrations complete, Tier 2–4 audited and confirmed N/A, CI + guardrails validated.  
The system is stable, predictable, and ready for forward development.  
Phase 8 now begins.

---

## **1. Metrics & Observability Foundation**
- [ ] Add structured metrics for `/v1/analyze` (duration, plugin, tool, success/failure)  
- [ ] Add per-frame metrics for YOLO tracker (optional)  
- [ ] Add job lifecycle metrics (queued → running → done)  
- [ ] Add logging correlation IDs (job_id, request_id)  
- [ ] Add plugin-level logging wrappers  
- [ ] Add error-path logging for invalid inputs  

---

## **2. Logging Modernisation**
- [ ] Replace ad‑hoc `print()` with structured logging  
- [ ] Add log levels (debug/info/warn/error)  
- [ ] Add plugin‑side logging for inference steps  
- [ ] Add server‑side logging for job creation + completion  
- [ ] Add logging for manifest load + validation  
- [ ] Add logging for plugin discovery  

---

## **3. Result Normalisation Layer**
- [ ] Create canonical result schema for all plugins  
- [ ] Normalise bounding boxes (x1,y1,x2,y2)  
- [ ] Normalise class labels  
- [ ] Normalise confidence scores  
- [ ] Normalise multi-frame outputs (YOLO tracker)  
- [ ] Add schema validation tests  
- [ ] Add CI guardrail: all results must pass normalisation  

---

## **4. UI Overlay System (Unified Rendering Layer)**
- [ ] Create unified overlay renderer (players, ball, pitch, radar)  
- [ ] Add bounding box renderer  
- [ ] Add track ID renderer  
- [ ] Add radar view renderer  
- [ ] Add pitch line renderer  
- [ ] Add overlay toggles (players, ball, pitch, radar)  
- [ ] Add performance safeguards (virtualisation, throttling)  

---

## **5. FPS & Performance Controls**
- [ ] Add FPS throttling for video overlays  
- [ ] Add frame skipping for slow devices  
- [ ] Add performance metrics to UI  
- [ ] Add GPU/CPU mode indicator (optional)  
- [ ] Add performance regression tests  

---

## **6. Device Selector Logic**
- [ ] Add device selector (CPU/GPU) to UI  
- [ ] Add device preference to `/v1/analyze`  
- [ ] Add plugin‑side device selection guardrails  
- [ ] Add fallback logic (GPU → CPU)  
- [ ] Add device mismatch warnings  

---

## **7. Governance & Guardrails (Phase 8)**
- [ ] CI: enforce structured logging  
- [ ] CI: enforce normalised results  
- [ ] CI: enforce plugin manifest validity  
- [ ] CI: enforce job lifecycle invariants  
- [ ] CI: enforce no legacy `/run` code paths  
- [ ] Add Phase 8 escalation template  

---

### 📘 Phase 8 Kickoff Footer  
Phase 8 is now active.  
The system is stable after Phase 7, and forward development can proceed without architectural risk.  
This milestone focuses on observability, normalisation, overlays, and performance — the foundation for a production‑grade vision platform.

---

