You’re right to zoom in on the **commit strategy**, because Phase‑15 is only “complete” when the commit history tells a clean, reviewable, auditable story.  
And since we **changed the scope of Phase 15** (from job‑queue/async/persistence → to MP4 batch execution only), the commit plan must reflect the *new* boundaries.

Below is the **updated, correct, Phase‑15 commit strategy**, aligned with:

- The new Phase‑15 scope  
- Your governance rules  
- Your Phase‑14 → Phase‑15 transition  
- Your preference for atomic, reviewable commits  
- Your repo’s structure and conventions  

This is the commit history you want reviewers to see.

---

# ⭐ Updated Phase‑15 Commit Strategy  
### *10 small, atomic, reviewable commits — matching the new Phase‑15 scope*

This commit plan is **governance‑aligned**, **Phase‑14‑compatible**, and **Phase‑15‑accurate**.

---

# ✅ **Commit 1 — Add `yolo_ocr.json` pipeline**
**Message:**
```
phase15: add yolo_ocr pipeline definition (YOLO → OCR)
```

**Changes:**
- Add `server/app/pipelines/yolo_ocr.json`
- Validate with `validate_pipelines.py`

This establishes the Phase‑15 pipeline.

---

# ✅ **Commit 2 — Define YOLO/OCR payload contract**
**Message:**
```
phase15: define payload contract for yolo+ocr multi-frame execution
```

**Changes:**
- Add `docs/payloads/yolo_ocr_payload.md`
- Document:
  - `image_bytes`
  - `frame_index`
  - YOLO output → OCR input

This locks the interface.

---

# ✅ **Commit 3 — Add tiny MP4 fixture + generator**
**Message:**
```
phase15: add tiny mp4 fixture and generator script
```

**Changes:**
- Add `tests/fixtures/generate_tiny_mp4.py`
- Commit `tests/fixtures/tiny.mp4`

This enables integration tests.

---

# ✅ **Commit 4 — Add VideoFilePipelineService**
**Message:**
```
phase15: implement VideoFilePipelineService for MP4 frame extraction
```

**Changes:**
- Add `server/app/services/video_file_pipeline_service.py`
- Add unit tests (optional)

This is the core of Phase‑15.

---

# ✅ **Commit 5 — Add /video/upload-and-run endpoint**
**Message:**
```
phase15: add /video/upload-and-run endpoint for batch mp4 processing
```

**Changes:**
- Add `server/app/api/routes/video_file.py`
- Wire into `main.py`

This exposes Phase‑15 functionality.

---

# ✅ **Commit 6 — Add Phase‑15 integration tests**
**Message:**
```
phase15: add integration tests for mp4 → yolo_ocr pipeline
```

**Changes:**
- Add `tests/phase15/test_phase15_integration.py`
- Add invalid file/pipeline tests

This ensures correctness.

---

# ✅ **Commit 7 — Add Phase‑15 smoke test script**
**Message:**
```
phase15: add smoke test script for mp4 batch execution
```

**Changes:**
- Add `scripts/smoke_test_phase15.sh`

This gives you a one‑command verifier.

---

# ✅ **Commit 8 — Add Phase‑15 documentation**
**Message:**
```
phase15: add overview, migration guide, governance, onboarding docs
```

**Changes:**
- Add:
  - `PHASE_15_OVERVIEW.md`
  - `PHASE_15_MIGRATION_GUIDE.md`
  - `PHASE_15_GOVERNANCE.md`
  - `PHASE_15_ONBOARDING.md`

This documents the new scope.

---

# ✅ **Commit 9 — Add Phase‑15 architecture diagrams**
**Message:**
```
phase15: add architecture diagrams (ASCII + Mermaid)
```

**Changes:**
- Add:
  - `PHASE_15_ARCHITECTURE.txt`
  - `PHASE_15_ARCHITECTURE.mmd`

This clarifies the system.

---

# ✅ **Commit 10 — Add Phase‑15 release notes**
**Message:**
```
phase15: add release notes for mp4 batch execution (YOLO + OCR)
```

**Changes:**
- Add `PHASE_15_RELEASE_NOTES.md`

This finalizes the phase.

---

# ⭐ Why this commit strategy is correct  
Because it:

### ✔ Matches the **new Phase‑15 scope**  
(no job queue, no async, no persistence, no tracking)

### ✔ Keeps commits **atomic and reviewable**  
(each commit introduces one conceptual unit)

### ✔ Aligns with your **governance rules**  
(no hidden behavior, no implicit state, no scope creep)

### ✔ Mirrors your **Phase‑14 commit structure**  
so the repo stays consistent

### ✔ Produces a clean, auditable history  
that future contributors can understand

---

