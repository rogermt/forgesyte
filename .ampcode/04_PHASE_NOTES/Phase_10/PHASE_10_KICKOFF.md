Roger, let’s launch **Phase 10** with the same clarity, structure, and mechanical governance you’ve enforced since Phase 6.  
Phase 10 is the first phase that *builds on top of* the fully stabilized, typed, governed Phase 9 platform — which means this kickoff can be bold, but it must also respect the invariants you locked in.

Below is a **complete Phase 10 Kickoff**, written in the exact style of your Phase 6B/7/8/9 documents, ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_KICKOFF.md
```

---

# ⭐ **PHASE 10 — Kickoff Plan**  
### **Feature Expansion + Real‑Time Insights + Plugin Pipeline Upgrade**

Phase 10 introduces the next major functional milestone:  
**real‑time insights, richer plugin outputs, and a unified plugin pipeline** built on top of the stable Phase 9 API + UI foundation.

Phase 9 gave you typed responses, consistent UI controls, and DX infrastructure.  
Phase 10 uses that stability to expand capability.

---

# 1. Goals

## **1.1 Real‑Time Insights (New Feature)**
Introduce a lightweight, low‑latency insights channel:

- Real‑time overlay updates (subset of frames)
- Real‑time metrics (FPS, latency, plugin health)
- Real‑time device usage + fallback reporting
- WebSocket or SSE channel for streaming updates

**Outcome:**  
UI can show “live” overlays while the full job runs in the background.

---

## **1.2 Plugin Pipeline Upgrade**
Unify plugin execution into a consistent, typed, multi‑stage pipeline:

- Standard plugin interface:
  - `prepare()`
  - `process_frame()`
  - `finalize()`
- Typed plugin outputs (Phase 9 example outputs become canonical)
- Plugin metadata:
  - name
  - version
  - capabilities
  - latency budget
- Plugin health reporting

**Outcome:**  
Plugins become predictable, testable, and composable.

---

## **1.3 Enhanced Job Model**
Extend the Phase 9 typed job model with:

- job progress (0–100)
- plugin breakdown (per‑plugin timings)
- warnings + soft‑failures
- device fallback reasons
- real‑time status updates

**Outcome:**  
Jobs become observable and debuggable.

---

## **1.4 UI Enhancements**
Add UI support for the new real‑time + plugin features:

- Real‑time overlay stream
- Plugin inspector panel
- Job progress bar
- Plugin latency + health indicators
- Real‑time device usage indicator

**Outcome:**  
Users see what’s happening *as it happens*.

---

## **1.5 Developer Experience**
- Add Storybook stories for new real‑time components
- Add plugin test harness
- Add plugin example pack
- Add real‑time integration tests
- Add plugin metadata validator

**Outcome:**  
Contributors can build plugins without guessing.

---

# 2. TDD Strategy

Phase 10 follows the same RED → GREEN → REFACTOR discipline as Phases 6–9.

## **2.1 Real‑Time Insights**
**RED**
- Tests for WebSocket/SSE endpoint existence  
- Tests for real‑time frame streaming  
- Tests for real‑time metrics  

**GREEN**
- Minimal streaming implementation  
- Minimal metrics publisher  

**REFACTOR**
- Consolidate streaming layer  
- Add backpressure + throttling  

---

## **2.2 Plugin Pipeline Upgrade**
**RED**
- Tests for plugin interface  
- Tests for plugin metadata  
- Tests for plugin lifecycle  

**GREEN**
- Implement minimal plugin runner  
- Add metadata loader  

**REFACTOR**
- Extract plugin registry  
- Add plugin health reporting  

---

## **2.3 Enhanced Job Model**
**RED**
- Tests for job progress  
- Tests for plugin breakdown  
- Tests for warnings  

**GREEN**
- Add fields to typed models  
- Update job store  

**REFACTOR**
- Consolidate job lifecycle logic  

---

## **2.4 UI Enhancements**
**RED**
- Tests for real‑time overlay stream  
- Tests for plugin inspector panel  
- Tests for job progress bar  

**GREEN**
- Minimal UI components  
- Wire to real‑time channel  

**REFACTOR**
- Extract reusable real‑time hooks  

---

# 3. Deliverables

- Real‑time insights channel (WebSocket/SSE)
- Plugin pipeline v2 (typed, lifecycle‑based)
- Enhanced job model (progress, breakdown, warnings)
- Real‑time UI components
- Plugin inspector panel
- Job progress bar
- Device usage indicator
- Plugin metadata validator
- Real‑time integration tests
- Storybook stories for real‑time components

---

# 4. Exit Criteria

Phase 10 is complete when:

- Real‑time insights channel is functional and tested  
- Plugin pipeline v2 is implemented and typed  
- Job model includes progress + plugin breakdown  
- UI displays real‑time overlays + progress  
- Plugin inspector panel works  
- All Phase 10 RED tests are GREEN  
- All governance rules from Phase 9 remain intact  
- Schema drift baseline updated  
- Storybook builds with new components  
- Integration tests pass  

---

# 5. Notes

Phase 10 is the first “expansion” phase after the stabilization of Phase 9.  
It introduces new capabilities but **must not break**:

- typed API responses  
- required fields  
- UI control IDs  
- schema drift baseline  
- Storybook build  
- test/assertion count governance  

Phase 10 sets the stage for Phase 11, which will introduce **multi‑plugin orchestration** and **advanced analytics**.

---
