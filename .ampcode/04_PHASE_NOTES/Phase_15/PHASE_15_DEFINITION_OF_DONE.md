
# ⭐ PHASE 15 — DEFINITION OF DONE  
Save as:

```
PHASE_15_DEFINITION_OF_DONE.md
```

```markdown
# Phase 15 — Definition of Done  
**YOLO + OCR Multi‑Frame MP4 Execution**

This document defines the exact criteria required for Phase 15 to be considered complete.

---

# 1. Functional Requirements

## 1.1 MP4 Upload
- [ ] `POST /video/upload-and-run` accepts MP4 files
- [ ] Rejects invalid file types
- [ ] Saves file to a temporary location

## 1.2 Frame Extraction
- [ ] OpenCV successfully opens MP4
- [ ] Frames extracted sequentially
- [ ] Optional `frame_stride` supported
- [ ] Optional `max_frames` supported

## 1.3 Per‑Frame DAG Execution
- [ ] Payload includes:
  - `image_bytes`
  - `frame_index`
- [ ] DAG engine executes `yolo_ocr` pipeline
- [ ] YOLO output feeds into OCR
- [ ] No state carried between frames

## 1.4 Aggregated Results
- [ ] Response contains:
```json
{
  "results": [
    { "frame_index": N, "result": {...} }
  ]
}
```
- [ ] Results ordered by frame index

---

# 2. Non‑Functional Requirements

## 2.1 Governance
- [ ] No job queue
- [ ] No async workers
- [ ] No persistence
- [ ] No tracking
- [ ] No ReID
- [ ] No Viz
- [ ] No streaming
- [ ] No new DAG semantics
- [ ] No state across frames

## 2.2 Code Quality
- [ ] All new code documented
- [ ] All new modules tested
- [ ] No dead code
- [ ] No unused imports
- [ ] No TODOs left behind

---

# 3. Testing Requirements

## 3.1 Tiny MP4 Fixture
- [ ] `tiny.mp4` exists in `tests/fixtures/`
- [ ] Generator script included

## 3.2 Integration Tests
- [ ] Valid MP4 → success
- [ ] Invalid file type → 400
- [ ] Invalid pipeline → 400/404
- [ ] At least one frame processed
- [ ] Result structure validated

## 3.3 Smoke Test
- [ ] `scripts/smoke_test_phase15.sh` passes

---

# 4. Documentation Requirements

- [ ] Phase‑15 Overview updated to new scope
- [ ] Phase‑15 Migration Guide added
- [ ] Phase‑15 Governance doc added
- [ ] Phase‑15 Architecture diagrams added
- [ ] Phase‑15 Onboarding doc added
- [ ] Phase‑15 Release Notes added
- [ ] PR Template added

---

# 5. CI Requirements

- [ ] Phase‑15 GitHub Actions workflow passing
- [ ] Full test suite passing
- [ ] Pipeline validator passing
- [ ] Plugin validator passing

---

# 6. Approval Requirements

- [ ] All PRs reviewed
- [ ] No scope creep detected
- [ ] All governance boundaries respected
- [ ] Maintainers approve merge to `main`

---

# ⭐ Phase 15 is Done When:

**“Upload MP4 → Extract Frames → Run YOLO → Run OCR → Return Per‑Frame Results”  
works end‑to‑end, is fully tested, fully documented, fully governed, and introduces no new semantics.”**
```

---

# ⭐ Roger, with these two documents, Phase 15 is now fully defined  
You now have:

- **Scope Document**  
- **Definition of Done**  
- **Migration Guide**  
- **Governance Checklist**  
- **Architecture Diagram**  
- **PR Sequence**  
- **CI Workflow**  
- **Smoke Test**  
- **Integration Tests**  
- **Release Notes**  
- **Onboarding Guide**

This is a *complete*, *governed*, *auditable* Phase‑15 package.
