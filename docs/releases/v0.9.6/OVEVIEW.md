# ⭐ **v0.9.6 — PR DESCRIPTION (FINAL)**

## **Title:**  
v0.9.6 — Video Job Progress Tracking (DB, Worker, API, UI)

## **Summary**  
This release introduces **real‑time progress tracking** for video‑based jobs.  
Users can now see a live progress bar in the Web‑UI while video processing is running.

This feature required coordinated updates across:

- Database (new `progress` column)
- Worker (frame‑level progress updates)
- Plugin (progress callback support)
- API (`/v1/video/status` now returns `progress`)
- Web‑UI (progress bar + polling)

## **Motivation**  
Previously, video jobs remained in `"running"` state with no visibility into progress.  
This caused uncertainty for long videos and made debugging difficult.

v0.9.6 solves this by exposing accurate progress based on total frame count.

## **Key Features**
- Accurate frame‑based progress using OpenCV `CAP_PROP_FRAME_COUNT`
- Worker updates DB every frame (or throttled)
- Status endpoint returns `{ status, progress }`
- Web‑UI shows a determinate progress bar
- Plugin supports `progress_callback` for streaming inference

## **Breaking Changes**
None.  
Existing image jobs and tools are unaffected.

## **Testing**
- Added migration test to ensure `progress` column exists
- Updated smoke test to assert `progress` is present and valid
- Manual Web‑UI verification with sample MP4

## **Next Steps (v0.9.7)**
- WebSocket live progress streaming  
- Multi‑tool video pipelines  
- Annotated video output

---

# ⭐ **COMMIT MESSAGE SET (FINAL)**

### **Commit 1 — DB Migration**
```
feat(db): add progress column to jobs table for video progress tracking

- Adds integer progress column (0–100)
- Updates Job model with default=0
- Includes Alembic migration script
```

### **Commit 2 — Worker Progress Updates**
```
feat(worker): implement frame-level progress updates for video jobs

- Adds OpenCV total frame detection
- Worker updates job.progress during processing
- Ensures 100% on completion
- Adds progress_callback wiring to plugin tools
```

### **Commit 3 — Plugin Progress Callback**
```
feat(plugin): add progress_callback support to video_player_detection

- Accepts progress_callback parameter
- Calls callback every frame
- Integrates with YOLO streaming inference
```

### **Commit 4 — API Status Endpoint**
```
feat(api): extend /v1/video/status to include progress field

- Returns { job_id, status, progress }
- Backward compatible with existing clients
```

### **Commit 5 — Web-UI Progress Bar**
```
feat(ui): add determinate progress bar for running video jobs

- Polls status endpoint for progress
- Renders MUI LinearProgress with percentage
- Shows progress text under bar
```

### **Commit 6 — Tests**
```
test: add migration test and update smoke test for progress support

- Verifies progress column exists
- Smoke test asserts progress is returned
- Ensures progress is between 0 and 100
```

---

# ⭐ **MIGRATION TEST (FINAL)**  
Place in: `server/tests/migrations/test_progress_column.py`

```python
def test_progress_column_exists(engine):
    insp = sa.inspect(engine)
    cols = [c["name"] for c in insp.get_columns("jobs")]
    assert "progress" in cols, "progress column missing from jobs table"
```

If your test harness uses fixtures:

```python
def test_progress_column_exists(db_engine):
    insp = sa.inspect(db_engine)
    assert "progress" in [c["name"] for c in insp.get_columns("jobs")]
```

---

# ⭐ **SMOKE TEST UPDATE (FINAL)**  
Update `scripts/smoke_test.py` → `test_job_status` and `test_job_results`.

### **Patch for `test_job_status`**

```diff
 required_fields = ["job_id", "status"]
+required_fields.append("progress")
```

Add validation:

```diff
 progress = data.get("progress")
 assert isinstance(progress, int)
 assert 0 <= progress <= 100
```

### **Patch for `test_job_results`**

No change needed — results endpoint doesn’t include progress.

---


