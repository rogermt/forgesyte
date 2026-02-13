Roger, you’re about to get a **fully‑governed, contributor‑friendly Phase 15 delivery pipeline**.  
These four pieces—PR sequence, CI workflow, final‑merge checklist, and retrospective template—are the last structural elements needed to make Phase 15 airtight.

I’ll give you everything in a clean, drop‑in format.

---

# ⭐ 1. GitHub PR Sequence (10 PRs, one per commit)

This sequence mirrors the **atomic commit strategy** we defined earlier.  
Each PR is small, reviewable, and governance‑aligned.

### **PR 1 — Add `yolo_ocr` pipeline definition**
```
phase15: add yolo_ocr pipeline definition (YOLO → OCR)
```
- Adds `server/app/pipelines/yolo_ocr.json`
- Ensures pipeline validator passes

---

### **PR 2 — Define YOLO/OCR payload contract**
```
phase15: define payload contract for yolo+ocr multi-frame execution
```
- Adds `docs/payloads/yolo_ocr_payload.md`

---

### **PR 3 — Add tiny MP4 fixture + generator**
```
phase15: add tiny mp4 fixture and generator script
```
- Adds `generate_tiny_mp4.py`
- Commits `tiny.mp4`

---

### **PR 4 — Add VideoFilePipelineService**
```
phase15: implement VideoFilePipelineService for MP4 frame extraction
```
- Adds `video_file_pipeline_service.py`

---

### **PR 5 — Add /video/upload-and-run endpoint**
```
phase15: add /video/upload-and-run endpoint for batch mp4 processing
```
- Adds `video_file.py` router
- Wires into `main.py`

---

### **PR 6 — Add Phase‑15 integration tests**
```
phase15: add integration tests for mp4 → yolo_ocr pipeline
```
- Adds `tests/phase15/`

---

### **PR 7 — Add Phase‑15 smoke test script**
```
phase15: add smoke test script for mp4 batch execution
```
- Adds `scripts/smoke_test_phase15.sh`

---

### **PR 8 — Add Phase‑15 documentation**
```
phase15: add overview, migration guide, governance, onboarding docs
```
- Adds all Phase‑15 docs

---

### **PR 9 — Add Phase‑15 architecture diagrams**
```
phase15: add architecture diagrams (ASCII + Mermaid)
```
- Adds `.txt` and `.mmd` diagrams

---

### **PR 10 — Add Phase‑15 release notes**
```
phase15: add release notes for mp4 batch execution (YOLO + OCR)
```
- Adds `PHASE_15_RELEASE_NOTES.md`

---

# ⭐ 2. GitHub Actions CI Workflow for Phase 15

Save as:

```
.github/workflows/phase15.yml
```

```yaml
name: Phase 15 CI

on:
  pull_request:
    branches: [ main ]
    paths:
      - "server/**"
      - "scripts/**"
      - ".ampcode/**"
      - ".github/workflows/phase15.yml"

jobs:
  phase15-ci:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Validate plugins
        run: uv run python server/tools/validate_plugins.py

      - name: Validate pipelines
        run: uv run python server/tools/validate_pipelines.py

      - name: Run Phase 15 tests only
        run: uv run pytest server/app/tests/phase15 -q --disable-warnings --maxfail=1

      - name: Run full test suite
        run: uv run pytest -q --disable-warnings --maxfail=1
```

This workflow enforces:

- Plugin validation  
- Pipeline validation  
- Phase‑15 tests  
- Full test suite  

Exactly what your governance requires.

---

# ⭐ 3. Phase‑15 “Final Checklist” for Merging to Main

Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_FINAL_CHECKLIST.md
```

```markdown
# Phase 15 Final Checklist (YOLO + OCR Edition)

## Pipeline
- [ ] `yolo_ocr.json` validates
- [ ] No ReID, no Viz, no tracking
- [ ] No new DAG semantics introduced

## Backend
- [ ] `/video/upload-and-run` endpoint implemented
- [ ] `VideoFilePipelineService` extracts frames correctly
- [ ] Payload contract respected (image_bytes + frame_index)
- [ ] DAG executes YOLO → OCR per frame
- [ ] Results aggregated correctly

## Tests
- [ ] Tiny MP4 fixture exists
- [ ] Integration tests pass
- [ ] Invalid file tests pass
- [ ] Invalid pipeline tests pass
- [ ] Smoke test passes

## Governance
- [ ] No job queue
- [ ] No async workers
- [ ] No persistence
- [ ] No state across frames
- [ ] No tracking
- [ ] No ReID
- [ ] No Viz
- [ ] No metrics
- [ ] No history

## Documentation
- [ ] Overview updated
- [ ] Migration guide added
- [ ] Governance doc added
- [ ] Onboarding doc added
- [ ] Architecture diagrams added
- [ ] Release notes added

## CI
- [ ] Phase‑15 GitHub Actions workflow passing
- [ ] Full test suite passing

## Approval
- [ ] All PRs reviewed
- [ ] No scope creep detected
- [ ] Ready to merge to main
```

This ensures Phase‑15 is **locked, governed, and complete**.

---

# ⭐ 4. Phase‑15 Retrospective Template

Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RETRO.md
```

```markdown
# Phase 15 Retrospective  
**MP4 → Multi-Frame DAG Execution (YOLO + OCR)**

## What Went Well
- 
- 
- 

## What Was Hard
- 
- 
- 

## What We Learned
- 
- 
- 

## What Surprised Us
- 
- 
- 

## Governance Review
- [ ] Scope remained intact
- [ ] No job queue introduced
- [ ] No persistence added
- [ ] No tracking/ReID/Viz added
- [ ] No new DAG semantics introduced

## Testing Review
- [ ] Integration tests effective
- [ ] Tiny MP4 fixture reliable
- [ ] Smoke test caught regressions

## Documentation Review
- [ ] Contributors onboarded smoothly
- [ ] Architecture clear
- [ ] Payload contract stable

## What We Should Improve in Phase 16
- 
- 
- 

## Final Summary
A concise summary of Phase 15 outcomes and readiness for Phase 16.
```

This gives you a clean, repeatable process for closing the phase.

---

# ⭐ Roger, with these four pieces, Phase 15 is now fully operational  
You now have:

- A **10‑PR sequence**  
- A **CI workflow**  
- A **final merge checklist**  
- A **retrospective template**  

This is the exact structure used in high‑governance engineering orgs.

