
---

# ⭐ **PHASE‑15 USER STORY INDEX**  
### *Mapped 1:1 to the 10‑Commit Delivery Plan*

```
PHASE 15 — USER STORY INDEX
───────────────────────────────────────────────
Story 1  → Pipeline Definition
Story 2  → Payload Contract & Scope Boundaries
Story 3  → OpenCV Dependency + Test Fixtures + Corrupt Harness
Story 4  → VideoFilePipelineService + Mock DAG + Pure Unit Tests
Story 5  → Router + App Wiring + Registration Test
Story 6  → Integration Tests + Full Error Coverage
Story 7  → Schema Regression Guard + Golden Snapshot
Story 8  → Stress + Fuzz Test Suites
Story 9  → Governance Tooling + CI + Smoke Test
Story 10 → Documentation + Demo Script + Rollback Plan
───────────────────────────────────────────────
```

Each story is atomic, testable, and mapped to a single commit.  
This index is the table of contents for the entire phase.

---

# ⭐ **PHASE‑15 PR REVIEW CHECKLIST (Derived Directly From User Stories)**  
### *A mechanical, reviewer‑proof checklist — if every box is checked, the PR is safe.*

```
PHASE 15 — PR REVIEW CHECKLIST
──────────────────────────────────────────────────────────────

GENERAL GOVERNANCE
[ ] No phase‑named files in server/app/** or server/tools/**
[ ] No forbidden vocabulary (job_id, queue, redis, tracking, websocket, etc.)
[ ] No Phase‑16 concepts (async workers, persistence, streaming, job queues)
[ ] All new files are in allowed directories

COMMIT 1 — PIPELINE DEFINITION
[ ] yolo_ocr.json exists
[ ] Nodes: detect → read
[ ] Entry/output nodes correct
[ ] validate_pipelines.py passes

COMMIT 2 — PAYLOAD CONTRACT & SCOPE
[ ] Payload doc defines exactly: frame_index, image_bytes
[ ] No base64
[ ] Response schema frozen
[ ] Scope doc contains all forbidden items
[ ] Overview rewritten to batch‑only

COMMIT 3 — FIXTURES & CORRUPT HARNESS
[ ] tiny.mp4 committed (3 frames, 320×240)
[ ] generate_tiny_mp4.py correct
[ ] corrupt_mp4_generator deterministic
[ ] OpenCV dependency added

COMMIT 4 — SERVICE + UNIT TESTS
[ ] VideoFilePipelineService implemented
[ ] JPEG encoding via cv2.imencode
[ ] Stride + max_frames logic correct
[ ] Mock DAG service implemented
[ ] Pure unit tests pass

COMMIT 5 — ROUTER + WIRING
[ ] /video/upload-and-run implemented
[ ] Temp file cleanup in finally
[ ] Router included in main.py
[ ] Registration test passes

COMMIT 6 — INTEGRATION + ERROR TESTS
[ ] Success path test passes
[ ] 422 tests for missing fields
[ ] 400 tests for invalid/empty/corrupt MP4
[ ] 404 for missing pipeline

COMMIT 7 — SCHEMA REGRESSION + GOLDEN SNAPSHOT
[ ] Schema regression test freezes keys
[ ] golden_output.json committed
[ ] Golden snapshot test passes

COMMIT 8 — STRESS + FUZZ
[ ] 1000‑frame stress test passes
[ ] Fuzz tests handle malformed MP4s safely

COMMIT 9 — GOVERNANCE + SMOKE TEST
[ ] forbidden_vocabulary.yaml correct
[ ] validate_video_batch_path.py passes
[ ] CI workflow added
[ ] smoke_test_video_batch.sh runs all 4 steps

COMMIT 10 — DOCUMENTATION + ROLLBACK
[ ] Demo script executable
[ ] Rollback plan complete
[ ] Testing guide complete
[ ] All Phase‑15 docs updated and clean

──────────────────────────────────────────────────────────────
If every box is checked, the PR is Phase‑15 compliant.
```

This checklist is mechanically derived from your user stories — nothing added, nothing removed.

---