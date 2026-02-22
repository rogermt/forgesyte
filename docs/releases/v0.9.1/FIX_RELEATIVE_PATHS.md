
Great question — and it’s one of those subtle architectural choices that can save you from a whole class of bugs later on. Let me break it down in a way that’s practical and grounded in how your system actually works.

---

# 🎯 Why patching the worker to store **relative paths** is better than storing full paths

Right now, your worker writes:

```
data/video_jobs/output/<job_id>.json
```

And stores **that full path** in `job.output_path`.

Your results endpoint then tries to do:

```python
file_path = storage.load_file(results_path)
```

But `storage.load_file()` expects a **relative path**, so it prepends its own base directory.  
That’s how you ended up with:

```
data/video_jobs/data/video_jobs/output/<job_id>.json
```

Which doesn’t exist → 404.

You fixed the endpoint by bypassing `storage.load_file()`, which works — but it’s a workaround, not a clean architecture.

---

# 🧠 The deeper reason: **full paths break portability**

Storing absolute or semi‑absolute paths in the database causes problems:

### 1. **Environment differences**
Dev, staging, prod, Docker, Kaggle, local — all have different base directories.

If you store:

```
/kaggle/working/forgesyte/server/data/video_jobs/output/123.json
```

That path is meaningless in:

- Docker container  
- Local dev  
- GitHub Actions  
- Production server  

Relative paths avoid this entirely.

---

### 2. **Storage backends**
Right now you use `LocalStorageService`, but later you might use:

- S3  
- Azure Blob  
- GCS  
- MinIO  

Those don’t have “paths” — they have keys.

If you store:

```
data/video_jobs/output/123.json
```

That can map cleanly to:

```
bucket/key = "video_jobs/output/123.json"
```

But if you store a full filesystem path, you can’t map it cleanly.

---

### 3. **Storage service abstraction becomes useless**
If you store full paths, then:

- `storage.load_file()` becomes pointless  
- You bypass the storage layer  
- You break the abstraction  

The whole point of `StorageService` is:

```
save_file(relative_path) → returns relative_path
load_file(relative_path) → returns absolute_path
```

But storing absolute paths in the DB breaks that contract.

---

### 4. **Security**
Storing absolute paths in the DB can leak:

- Server directory structure  
- Container filesystem layout  
- Deployment environment details  

Relative paths avoid this.

---

# 🛠️ The clean fix: Worker stores **relative paths only**

Instead of:

```python
output_path = self._storage.save_file(output_bytes, f"output/{job.job_id}.json")
job.output_path = output_path
```

Make sure `save_file()` returns **only**:

```
output/<job_id>.json
```

Then the endpoint does:

```python
file_path = storage.load_file(job.output_path)
```

And everything works everywhere.

---

# 🧼 Summary: Why relative paths are the right choice

| Issue | Full Path | Relative Path |
|-------|-----------|---------------|
| Works across environments | ❌ No | ✅ Yes |
| Works with S3 / cloud storage | ❌ No | ✅ Yes |
| Keeps storage abstraction clean | ❌ No | ✅ Yes |
| Avoids leaking filesystem structure | ❌ No | ✅ Yes |
| Works with `storage.load_file()` | ❌ No | ✅ Yes |

---

# ✔️ Final recommendation

**Yes — patch the worker to store relative paths only.**  
It’s the correct architectural choice and prevents future breakage.

If you want, I can generate:

- The exact worker patch  
- The corrected `LocalStorageService`  
- A migration to clean old absolute paths  
- A regression test to ensure only relative paths are stored  

Just tell me what you want next.
Below is everything you asked for:

- **The exact worker patch** (store relative paths only)  
- **The corrected LocalStorageService**  
- **A migration to clean old absolute paths**  
- **A regression test to ensure only relative paths are stored**

All written cleanly and ready to paste.

---

# ✅ 1. Worker Patch — Store **relative paths only**

### Before (buggy)
```python
output_path = self._storage.save_file(
    output_bytes,
    f"output/{job.job_id}.json",
)
job.output_path = output_path
```

If `save_file()` returns a full path, the DB stores a full path.

### After (correct)
```python
relative_path = f"output/{job.job_id}.json"

self._storage.save_file(
    output_bytes,
    relative_path,
)

job.output_path = relative_path
```

### Full patched worker snippet

```python
# Save results (store RELATIVE path only)
relative_path = f"output/{job.job_id}.json"

self._storage.save_file(
    output_bytes,
    relative_path,
)

job.output_path = relative_path
job.status = JobStatus.completed
job.error_message = None
db.commit()
```

This ensures:

- DB stores: `output/<id>.json`
- Storage layer resolves it to an absolute path
- Results endpoint works everywhere

---

# ✅ 2. Corrected LocalStorageService

Your storage service should:

- Accept **relative paths**
- Save to `base_dir / relative_path`
- Return **absolute path** only when loading

### Correct implementation

```python
import os
from pathlib import Path
from io import BytesIO

class LocalStorageService:
    def __init__(self, base_dir: str = "data/video_jobs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, src: BytesIO, dest_path: str) -> str:
        """Save file using a RELATIVE path."""
        full_path = self.base_dir / dest_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(src.read())

        # Return RELATIVE path only
        return dest_path

    def load_file(self, relative_path: str) -> str:
        """Return ABSOLUTE path for reading."""
        full_path = self.base_dir / relative_path
        return str(full_path)
```

This restores the intended abstraction:

- Worker stores relative paths  
- Storage resolves them  
- Endpoints use `storage.load_file()`  

---

# ✅ 3. Migration to clean old absolute paths

This migration:

- Detects absolute paths (starting with `/` or containing `data/video_jobs`)
- Converts them to relative paths
- Leaves already-correct rows untouched

### Alembic migration

```python
from alembic import op
import sqlalchemy as sa

revision = "fix_output_paths_relative"
down_revision = "xxxx_previous"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Fetch all jobs with output_path
    rows = conn.execute(sa.text("SELECT job_id, output_path FROM jobs")).fetchall()

    for job_id, output_path in rows:
        if not output_path:
            continue

        # If path is absolute or contains data/video_jobs, convert it
        if output_path.startswith("/") or "video_jobs" in output_path:
            # Extract relative part
            rel = output_path.split("video_jobs/")[-1]
            conn.execute(
                sa.text("UPDATE jobs SET output_path = :rel WHERE job_id = :id"),
                {"rel": rel, "id": job_id},
            )


def downgrade():
    # No-op: cannot restore absolute paths
    pass
```

This ensures your DB is clean and consistent.

---

# ✅ 4. Regression Test — Ensure worker stores **relative paths only**

Place this in `tests/video/test_worker_output_paths.py`:

```python
from io import BytesIO
from unittest.mock import MagicMock

from app.worker.worker import JobWorker
from app.models.job import Job, JobStatus


class FakeSession:
    def commit(self): pass
    def close(self): pass


def test_worker_stores_relative_output_path(tmp_path):
    storage = MagicMock()

    # Simulate save_file returning RELATIVE path
    storage.save_file.side_effect = lambda src, dest: dest
    storage.load_file.side_effect = lambda rel: str(tmp_path / rel)

    plugin_service = MagicMock()
    plugin_service.run_video_tool.return_value = {"ok": True}

    worker = JobWorker(
        session_factory=lambda: FakeSession(),
        storage=storage,
        plugin_service=plugin_service,
    )

    job = Job(
        job_id="abc",
        status=JobStatus.running,
        plugin_id="yolo-tracker",
        tool="video_track",
        input_path="video.mp4",
    )

    worker._execute_pipeline(job, FakeSession())

    # Assert relative path
    assert job.output_path == "output/abc.json"
    assert not job.output_path.startswith("/")
    assert "video_jobs" not in job.output_path
```

This test ensures:

- Worker stores **relative** paths  
- No absolute paths  
- No environment-specific prefixes  

---

# 🎉 Final result

With these four pieces:

- Worker patch  
- Corrected storage service  
- Migration  
- Regression test  

Your system becomes:

- Portable  
- Storage-agnostic  
- Consistent  
- Future-proof  
- Free from the “double prefix” bug forever  
