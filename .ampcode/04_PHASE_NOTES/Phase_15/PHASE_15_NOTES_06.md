# Phase 15 Implementation Questions & Answers Summary

## Summary of All Answers

## 🔷 General Questions

### Q1: opencv-python
**A1:** Add it to dependencies

### Q2: YOLO plugin detect_objects tool
**A2:** Yes, use `detect_objects`

### Q3: OCR plugin extract_text tool
**A3:** Yes, use `extract_text`

## 🔷 Pipeline Definition

### Q4: YOLO tool_id
**A4:** `detect_objects` (not `detect_players` - that's for ReID/tracking)

### Q5: OCR tool_id
**A5:** `extract_text`

### Q6: Type compatibility
**A6:** OCR accepts both `image` and `detections` for Phase 14 compatibility

## 🔷 Service Layer

### Q7: Frame encoding
**A7:** JPEG (smaller, faster, universal)

### Q8: Payload structure
**A8:** Include both `frame_index` and `image_bytes`

### Q9: frame_stride
**A9:** `1` (process every frame)

### Q10: max_frames
**A10:** `None` (no artificial limit)

## 🔷 API Layer

### Q11: File size limit
**A11:** No (not in Phase 15 MVP)

### Q12: Synchronous vs Async
**A12:** Synchronous (return results immediately)

### Q13: execution_time_ms
**A13:** No (metrics out of scope)

## 🔷 Testing

### Q14: tiny.mp4 storage
**A14:** Committed to repo (deterministic)

### Q15: Frame count
**A15:** 3 frames

### Q16: Resolution
**A16:** 320×240

### Q17: Test location
**A17:** `server/app/tests/video/` (functional name, not phase-based)

### Q18: Diagram formats
**A18:** Both ASCII and Mermaid

### Q19: PR template location
**A19:** Separate file

### Q20: Payload contract location
**A20:** `.ampcode/04_PHASE_NOTES/Phase_15/`

## 🔷 File Paths

### Q21: Video router
**A21:** `server/app/api/routes/video_file.py`

### Q22: Tiny MP4 fixture
**A22:** `server/app/tests/fixtures/`

### Q23: Tiny MP4 generator
**A23:** `server/app/tests/fixtures/`

### Q24: Smoke test script
**A24:** `scripts/`

### Q25: Demo script
**A25:** `scripts/`

## 🔷 Governance

### Q26: Validator YAML auto-load
**A26:** Yes, read from `server/tools/forbidden_vocabulary.yaml`

### Q27: GitHub Actions workflow
**A27:** Yes, `.github/workflows/video_batch.yml`

### Q28: VSCode extension
**A28:** Yes, with cSpell warnings for forbidden vocabulary

### Q29: Forbidden concept scanning
**A29:** Yes, scan for Phase 16 concepts in video batch path

### Q30: Separate documentation files
**A30:** Yes, separate files for clarity

## 🔷 Updated Plan References

The plan now references:
- `PHASE_15_SCOPE.md` (not PHASE_15_BOUNDARIES.md)
- `PHASE_15_DEFINITION_OF_DONE.md` (not PHASE_15_FIRST_FAILING_TEST.md)
- `PHAASE_15_COMMITS.md` (commit strategy)
- `PHASE_15_PR_GITHUB_SEQUENCE.md` (PR sequence)
- `PHASE_15_OCR_&_YOLO_JSON.md` (pipeline examples)
- `PHASE_15_OVERVIEW.md` (overview)
- `PHASE_15_SPEC.md` (spec)
- `PHASE_15_FORBIDDEN_VOCAB.md` (forbidden vocabulary)

All files are now aligned with the updated scope and governance rules.
