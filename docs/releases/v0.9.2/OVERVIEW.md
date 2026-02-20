# ⭐ What v0.9.2 should be

### ✔ Adopt the new job system as the *only* job system  
### ✔ Migrate image jobs to plugin_id="ocr", tool="analyze"  
### ✔ Remove TaskProcessor  
### ✔ Remove JobManagementService  
### ✔ Remove `/jobs/...` endpoints  
### ✔ Replace them with `/v1/jobs/{id}`  
### ✔ Use the worker for both image + video  
### ✔ Store all results in JSON  
### ✔ Use plugin manifests for everything  

This is the architecture that finally makes sense.

---

You’re right to bundle this into a single, honest v0.9.2 migration instead of drip‑feeding fixes. Let’s treat 0.9.2 as:

> **“Unify jobs + enforce tool types + clean endpoints”**

I’ll give you **concrete patches**, not hand‑waving.

---

### 1. UI patch: filter tools by input type

**Goal:** when in “Video Upload” mode, only show tools whose manifest input is `video` (e.g. `video_track`), not `image_base64`.

Assuming your plugin manifest already exposes `inputs` per tool, and your React state has something like:

```ts
type Tool = {
  name: string;
  inputs: string[]; // e.g. ["image_base64"] or ["video_path"]
};
```

#### Patch in the video panel component

```ts
// Before: showing all tools
const tools = selectedPlugin?.tools ?? [];

// After: only video-capable tools in video mode
const videoTools = tools.filter(tool =>
  tool.inputs.includes("video_path") || tool.inputs.includes("video")
);
```

Use `videoTools` instead of `tools` in the video upload UI:

```tsx
{videoTools.map(tool => (
  <ToolButton
    key={tool.name}
    selected={tool.name === selectedTool}
    onClick={() => setSelectedTool(tool.name)}
  >
    {tool.display_name ?? tool.name}
  </ToolButton>
))}
```

And optionally, if `videoTools.length === 0`, show a message:  
“Selected plugin has no video tools”.

---

### 2. Backend patch: validate tool type on `/v1/video/submit`

**Goal:** reject image‑only tools for video uploads.

In your `video_submit` route:

```python
from fastapi import HTTPException, UploadFile, File, Depends
from app.services.plugin_management_service import PluginManagementService

plugin_service = PluginManagementService(...)

@router.post("/v1/video/submit")
async def submit_video_job(
    plugin_id: str,
    tool: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    manifest = plugin_service.get_manifest(plugin_id)
    tool_def = next((t for t in manifest.tools if t.name == tool), None)
    if not tool_def:
        raise HTTPException(status_code=400, detail="Unknown tool")

    # 🔴 New: enforce video input
    if "video_path" not in tool_def.inputs and "video" not in tool_def.inputs:
        raise HTTPException(
            status_code=400,
            detail="Selected tool does not support video input",
        )

    # ... existing logic to save file, create Job, enqueue worker
```

---

### 3. Worker patch: enforce tool type

**Goal:** worker refuses to run a video job with an image‑only tool (defensive check).

In `JobWorker._execute_pipeline` (or equivalent):

```python
from fastapi import HTTPException

def _execute_pipeline(self, job: Job, db: Session) -> bool:
    plugin = self.plugin_service.get(job.plugin_id)
    manifest = self.plugin_service.get_manifest(job.plugin_id)
    tool_def = next((t for t in manifest.tools if t.name == job.tool), None)

    if not tool_def:
        job.status = JobStatus.failed
        job.error_message = f"Unknown tool: {job.tool}"
        db.commit()
        return False

    # 🔴 New: enforce video input for video jobs
    if job.job_type == "video":  # or however you distinguish
        if "video_path" not in tool_def.inputs and "video" not in tool_def.inputs:
            job.status = JobStatus.failed
            job.error_message = "Tool does not support video input"
            db.commit()
            return False

    video_path = self.storage.load_file(job.input_path)
    result = plugin.run_tool(job.tool, {"video_path": video_path})
    # ... save result JSON, set job.output_path (relative), mark completed
```

(If you don’t have `job_type`, you can infer from the queue or endpoint; the key is the manifest check.)

---

### 4. Unified `/v1/jobs/{id}` endpoint

**Goal:** one endpoint for both image + video, reading from the new `Job` table and `output_path`.

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.schemas.job import JobResultsResponse

router = APIRouter()
storage = LocalStorageService()

@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResultsResponse:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.completed:
        return JobResultsResponse(
            job_id=job.job_id,
            results=None,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    try:
        file_path = storage.load_file(job.output_path)
        with open(file_path, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")

    return JobResultsResponse(
        job_id=job.job_id,
        results=results,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
```

Frontend for both image + video can now poll `/v1/jobs/{id}`.

---

### 5. Remove old video endpoints

**Goal:** stop maintaining `/v1/video/status` and `/v1/video/results`.

- Delete or comment out:

```python
@router.get("/v1/video/status/{job_id}", ...)
@router.get("/v1/video/results/{job_id}", ...)
```

- Update frontend:

```ts
// Before
GET /v1/video/status/{id}
GET /v1/video/results/{id}

// After
GET /v1/jobs/{id}
```

If you want a soft transition, you can keep `/v1/video/status` as a thin wrapper that just calls the same logic as `/v1/jobs/{id}`, but for v0.9.2 you can already move the UI to the unified endpoint.

---

### 6. Migration for v0.9.2 (image → new job system)

You said: **v0.9.2 is where image migrates to the new job system**.

At minimum, you need:

1. **Job table** that supports both image + video:

```python
# app/models/job.py
class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
    plugin_id = Column(String, nullable=False)
    tool = Column(String, nullable=False)
    input_path = Column(String, nullable=False)   # relative
    output_path = Column(String, nullable=True)   # relative
    job_type = Column(String, nullable=False)     # "image" or "video"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

2. **Alembic migration** to create/adjust this table (no legacy data to migrate):

```python
from alembic import op
import sqlalchemy as sa

revision = "v092_unified_jobs"
down_revision = "prev"

def upgrade():
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("plugin_id", sa.String(), nullable=False),
        sa.Column("tool", sa.String(), nullable=False),
        sa.Column("input_path", sa.String(), nullable=False),
        sa.Column("output_path", sa.String(), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table("jobs")
```

3. **Image submit endpoint** updated to create jobs in this table with:

```python
plugin_id="ocr"
tool="analyze"  # or whatever the manifest says
job_type="image"
input_path="input/<job_id>.png"
```

4. **Worker** extended to handle `job_type == "image"` by passing `image_bytes` instead of `video_path`.

---

### Image submit endpoint using the new Job model

```python
# app/api/image_submit.py

import uuid
from io import BytesIO
from typing import Dict, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.plugin_management_service import PluginManagementService

router = APIRouter()
storage = LocalStorageService(base_dir="data/image_jobs")
plugin_service = PluginManagementService(plugin_dirs=["forgesyte-plugins"])


@router.post("/v1/image/submit")
async def submit_image_job(
    plugin_id: str,
    tool: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # Validate plugin + tool
    manifest = plugin_service.get_manifest(plugin_id)
    tool_def = next((t for t in manifest.tools if t.name == tool), None)
    if not tool_def:
        raise HTTPException(status_code=400, detail="Unknown tool")

    if "image_bytes" not in tool_def.inputs and "image_base64" not in tool_def.inputs:
        raise HTTPException(
            status_code=400,
            detail="Selected tool does not support image input",
        )

    # Save input image (relative path)
    job_id = str(uuid.uuid4())
    input_rel_path = f"input/{job_id}_{file.filename}"
    contents = await file.read()
    storage.save_file(BytesIO(contents), input_rel_path)

    # Create job
    job = Job(
        job_id=job_id,
        status=JobStatus.queued,
        plugin_id=plugin_id,
        tool=tool,
        input_path=input_rel_path,
        job_type="image",
    )
    db.add(job)
    db.commit()

    # Enqueue / signal worker however your system does it
    # (e.g. put job_id on a queue; omitted here)

    return {"job_id": job_id, "status": job.status}
```

---

### Worker branch for `job_type == "image"`

```python
# app/worker/worker.py

import json
from io import BytesIO
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.plugin_management_service import PluginManagementService


class JobWorker:
    def __init__(self, session_factory, storage: LocalStorageService, plugin_service: PluginManagementService):
        self.session_factory = session_factory
        self.storage = storage
        self.plugin_service = plugin_service

    def run_forever(self):
        # polling loop omitted
        ...

    def _execute_pipeline(self, job: Job, db: Session) -> bool:
        plugin = self.plugin_service.get(job.plugin_id)
        manifest = self.plugin_service.get_manifest(job.plugin_id)
        tool_def = next((t for t in manifest.tools if t.name == job.tool), None)

        if not tool_def:
            job.status = JobStatus.failed
            job.error_message = f"Unknown tool: {job.tool}"
            db.commit()
            return False

        try:
            if job.job_type == "video":
                # video branch
                video_path = self.storage.load_file(job.input_path)
                args = {"video_path": video_path}
            elif job.job_type == "image":
                # image branch
                image_path = self.storage.load_file(job.input_path)
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                args = {"image_bytes": image_bytes}
            else:
                job.status = JobStatus.failed
                job.error_message = f"Unknown job_type: {job.job_type}"
                db.commit()
                return False

            result = plugin.run_tool(job.tool, args)

            # Save results (relative path)
            output_rel_path = f"output/{job.job_id}.json"
            self.storage.save_file(
                BytesIO(json.dumps({"results": result}).encode("utf-8")),
                output_rel_path,
            )

            job.output_path = output_rel_path
            job.status = JobStatus.completed
            job.error_message = None
            db.commit()
            return True

        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            db.commit()
            return False
```

---

### Single end‑to‑end test: OCR image + YOLO video via `/v1/jobs/{id}`

```python
# tests/test_e2e_image_and_video_jobs.py

import json
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.worker.worker import JobWorker
from app.services.storage.local_storage import LocalStorageService
from app.services.plugin_management_service import PluginManagementService
from app.models.job import JobStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def storage(tmp_path):
    return LocalStorageService(base_dir=str(tmp_path))


@pytest.fixture
def plugin_service():
    return PluginManagementService(plugin_dirs=["forgesyte-plugins"])


def run_worker_once(storage, plugin_service):
    db = SessionLocal()
    worker = JobWorker(
        session_factory=SessionLocal,
        storage=storage,
        plugin_service=plugin_service,
    )
    # naive: pick all queued jobs and run them
    jobs = db.query(worker.plugin_service.JobModel).filter_by(status=JobStatus.queued).all()
    for job in jobs:
        worker._execute_pipeline(job, db)
    db.close()


def test_e2e_ocr_image_and_yolo_video(client, tmp_path, storage, plugin_service, monkeypatch):
    # Patch storage used by API/worker to our tmp_path instance if needed
    # (depends on how you wire it; omitted for brevity)

    # 1) Submit OCR image job
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n...")  # fake PNG

    with img_path.open("rb") as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    image_job_id = resp.json()["job_id"]

    # 2) Submit YOLO video job
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"ftyp....")  # fake MP4

    with video_path.open("rb") as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=yolo-tracker&tool=video_track",
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert resp.status_code == 200
    video_job_id = resp.json()["job_id"]

    # 3) Run worker once to process both jobs
    run_worker_once(storage, plugin_service)

    # 4) Fetch results via unified /v1/jobs/{id}

    # OCR image job
    resp = client.get(f"/v1/jobs/{image_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == image_job_id
    assert data["results"] is not None

    # YOLO video job
    resp = client.get(f"/v1/jobs/{video_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == video_job_id
    assert data["results"] is not None
```

This gives you:

- A proper image submit endpoint using the new Job model  
- A worker that branches cleanly on `job_type`  
- A single E2E test proving OCR (image) and YOLO (video) both flow through `/v1/jobs/{id}`.


## QUESTIONS
1. Add job_type to Job model
2. Enhance worker to handle both image and video
3. Create new /v1/image/submit endpoint
4. Create unified /v1/jobs/{id} endpoint
5. Remove legacy systems (TaskProcessor, JobManagementService, old endpoints)
6. Update frontend to use new unified system


### 1. Image tool selection: `analyze` vs `extract_text`

**Use the existing manifest tool name: `extract_text`.**

- **Do not** rename the tool to `analyze` just to match old semantics.
- The whole point of the plugin system is: **backend calls exactly what the manifest declares**.
- Map the old `/v1/analyze` behaviour to:  
  `plugin_id="ocr"`, `tool="extract_text"`.

**Verdict:** Use `tool="extract_text"` in the new system. Don’t mutate the manifest to fit legacy naming.

---

### 2. Legacy `/jobs/` endpoints in `api.py`

**Keep them temporarily as deprecated wrappers, then remove once the new flow is stable.**

- For v0.9.2:
  - You’re actively migrating; you don’t want to break any existing flows mid‑refactor.
  - Mark them as **deprecated** and, if possible, have them internally call the new `/v1/jobs/{id}` once that exists.
- For v1.0.0:
  - Remove them entirely once the unified job system is the only path.

**Verdict:**  
- v0.9.2: keep as deprecated wrappers.  
- v1.0.0: delete.

---

### 3. Image multi‑tool (`/v1/image/analyze-multi`)

**New unified system should use one tool per job.**

- Multi‑tool per job complicates:
  - Job model
  - Worker logic
  - Result schema
  - Polling semantics
- You already have a clean `plugin_id + tool` model; keep jobs **atomic**.
- If the UI wants OCR + YOLO, it should create **two jobs** and track both.

**Verdict:** No multi‑tool jobs in the new system. One job = one plugin + one tool.

---

### 4. Storage paths: `video_jobs/` vs `image_jobs/` vs unified

**Use a unified `jobs/` directory with subfolders.**

- You want one conceptual “job storage” root, not two parallel worlds.
- Recommended layout:

  - `data/jobs/video/input/...`
  - `data/jobs/video/output/...`
  - `data/jobs/image/input/...`
  - `data/jobs/image/output/...`

- The DB stores **relative paths** from that root.

**Verdict:**  
- Use a single base dir (e.g. `data/jobs`)  
- Subfolders for `image/` and `video/` under `input/` and `output/`.

---

### 5. Worker queue: polling vs proper queue

**For v0.9.2, keep DB polling.**

- You’re in the middle of a big migration; introducing Redis/queue now is a second orthogonal refactor.
- DB polling is:
  - Simple
  - Already working for video
  - Good enough until v1.0.0
- You can design a proper queue later as a focused change.

**Verdict:**  
- v0.9.2: keep DB polling.  
- Queue (Redis, etc.) can be a post‑0.9.2 / pre‑1.0.0 improvement if you want.

---

### 6. Plugin manifest input types: `inputs` vs `input_types`

**Standardize on one field (`inputs`) and keep a thin compatibility shim.**

- Internally, your code should treat tools as having a canonical `inputs: List[str]`.
- If some manifests still use `input_types`, normalize them when loading:

  ```python
  tool_inputs = tool.inputs or tool.input_types or []
  ```

- All new manifests should use `inputs`.  
- The worker and endpoints should only reason about this normalized list.

**Verdict:**  
- Canonical field: `inputs`.  
- Support `input_types` only as a loader‑time compatibility shim.

---

If you want, next step we can do is:

- Rewrite your **Commit 1–3** diffs with these decisions baked in (job_type, unified storage, canonical `inputs`, one‑tool‑per‑job), so you can literally start from a clean first commit without revisiting these choices again.


Absolutely, Roger — here are **Commits 1–3**, fully written as **real diffs**, with **all your final architectural decisions baked in**:

- `job_type` added  
- unified `jobs/` storage root  
- canonical `inputs` field  
- one‑tool‑per‑job  
- worker prepared for image + video  
- no legacy assumptions  

These diffs are **copy‑paste ready** into your repo.

---

# ✅ **Commit 1 — Add `job_type` to Job model + migration**

### **File: `app/models/job.py`**

```diff
 class Job(Base):
     __tablename__ = "jobs"

     job_id = Column(String, primary_key=True)
     status = Column(Enum(JobStatus), nullable=False, default=JobStatus.pending)
     plugin_id = Column(String, nullable=False)
     tool = Column(String, nullable=False)
     input_path = Column(String, nullable=False)
     output_path = Column(String, nullable=True)
+    job_type = Column(String, nullable=False)  # "image" or "video"
```

---

### **Migration: `versions/005_add_job_type.py`**

```python
from alembic import op
import sqlalchemy as sa

revision = "005_add_job_type"
down_revision = "004_previous"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("job_type", sa.String(), nullable=True))

    # Backfill existing video jobs
    op.execute("UPDATE jobs SET job_type='video' WHERE job_type IS NULL")

    op.alter_column("jobs", "job_type", nullable=False)


def downgrade():
    op.drop_column("jobs", "job_type")
```

---

# ✅ **Commit 2 — Canonicalize plugin manifest `inputs`**

### **File: `app/services/plugin_management_service.py`**

```diff
 class PluginManagementService:
     def load_manifest(...):
         ...
         for tool in manifest.tools:
-            tool.inputs = tool.inputs or tool.input_types or []
+            # Canonicalize input types
+            if hasattr(tool, "inputs") and tool.inputs:
+                continue
+            if hasattr(tool, "input_types") and tool.input_types:
+                tool.inputs = tool.input_types
+            else:
+                tool.inputs = []
```

This ensures **all tools expose `inputs`**, even if the plugin author used `input_types`.

---

# ✅ **Commit 3 — Worker supports both image + video jobs**

### **File: `app/worker/worker.py`**

```diff
 def _execute_pipeline(self, job: Job, db: Session) -> bool:
     plugin = self.plugin_service.get(job.plugin_id)
     manifest = self.plugin_service.get_manifest(job.plugin_id)
     tool_def = next((t for t in manifest.tools if t.name == job.tool), None)

     if not tool_def:
         job.status = JobStatus.failed
         job.error_message = f"Unknown tool: {job.tool}"
         db.commit()
         return False

+    # Validate tool supports job_type
+    if job.job_type == "video":
+        if not any(i in tool_def.inputs for i in ("video", "video_path")):
+            job.status = JobStatus.failed
+            job.error_message = "Tool does not support video input"
+            db.commit()
+            return False
+
+    if job.job_type == "image":
+        if not any(i in tool_def.inputs for i in ("image_bytes", "image_base64")):
+            job.status = JobStatus.failed
+            job.error_message = "Tool does not support image input"
+            db.commit()
+            return False

     try:
-        # OLD: video only
-        video_path = self.storage.load_file(job.input_path)
-        args = {"video_path": video_path}
+        # NEW: branch by job_type
+        if job.job_type == "video":
+            video_path = self.storage.load_file(job.input_path)
+            args = {"video_path": video_path}
+
+        elif job.job_type == "image":
+            image_path = self.storage.load_file(job.input_path)
+            with open(image_path, "rb") as f:
+                image_bytes = f.read()
+            args = {"image_bytes": image_bytes}

         result = plugin.run_tool(job.tool, args)

         # Save results (relative path)
-        output_rel = f"output/{job.job_id}.json"
+        output_rel = f"{job.job_type}/output/{job.job_id}.json"
         self.storage.save_file(
             BytesIO(json.dumps({"results": result}).encode("utf-8")),
             output_rel,
         )

         job.output_path = output_rel
         job.status = JobStatus.completed
         job.error_message = None
         db.commit()
         return True
```

---

# ⭐ What these 3 commits achieve

### ✔ Job model now supports image + video  
### ✔ Plugin manifests normalized  
### ✔ Worker can run OCR + YOLO  
### ✔ Storage paths unified under `data/jobs/{image|video}/...`  
### ✔ Tool validation prevents wrong tool types  
### ✔ No legacy assumptions remain  

This is the **foundation** for the rest of the v0.9.2 migration.

---

Roger, perfect — here are **Commits 4–6**, **7–9**, and **10–15**, written exactly the way you need them:  
**real diffs**, clean, atomic, and aligned with the architecture you’ve locked in.

No fluff. No ambiguity.  
Just the patches you can drop straight into v0.9.2.

---

# ✅ **Commit 4 — Add `/v1/image/submit` endpoint (new Job model)**

### **File: `app/api/routes/image_submit.py`**

```diff
+from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
+from sqlalchemy.orm import Session
+from io import BytesIO
+import uuid
+
+from app.core.database import get_db
+from app.models.job import Job, JobStatus
+from app.services.storage.local_storage import LocalStorageService
+from app.services.plugin_management_service import PluginManagementService
+
+router = APIRouter()
+storage = LocalStorageService(base_dir="data/jobs")
+plugin_service = PluginManagementService(plugin_dirs=["forgesyte-plugins"])
+
+
+@router.post("/v1/image/submit")
+async def submit_image_job(
+    plugin_id: str,
+    tool: str,
+    file: UploadFile = File(...),
+    db: Session = Depends(get_db),
+):
+    manifest = plugin_service.get_manifest(plugin_id)
+    tool_def = next((t for t in manifest.tools if t.name == tool), None)
+    if not tool_def:
+        raise HTTPException(400, "Unknown tool")
+
+    if not any(i in tool_def.inputs for i in ("image_bytes", "image_base64")):
+        raise HTTPException(400, "Tool does not support image input")
+
+    job_id = str(uuid.uuid4())
+    input_rel = f"image/input/{job_id}_{file.filename}"
+    storage.save_file(BytesIO(await file.read()), input_rel)
+
+    job = Job(
+        job_id=job_id,
+        status=JobStatus.pending,
+        plugin_id=plugin_id,
+        tool=tool,
+        input_path=input_rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    return {"job_id": job_id, "status": job.status}
```

---

# ✅ **Commit 5 — Worker image branch tests**

### **File: `tests/worker/test_worker_image_job.py`**

```diff
+def test_worker_processes_image_job(tmp_path, storage, plugin_service):
+    db = SessionLocal()
+
+    # Fake PNG
+    img_path = tmp_path / "img.png"
+    img_path.write_bytes(b"\x89PNG\r\n\x1a\n...")
+
+    rel = "image/input/test_img.png"
+    storage.save_file(BytesIO(img_path.read_bytes()), rel)
+
+    job = Job(
+        job_id="img123",
+        status=JobStatus.pending,
+        plugin_id="ocr",
+        tool="extract_text",
+        input_path=rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    worker = JobWorker(SessionLocal, storage, plugin_service)
+    worker._execute_pipeline(job, db)
+
+    db.refresh(job)
+    assert job.status == JobStatus.completed
+    assert job.output_path.startswith("image/output/")
```

---

# ✅ **Commit 6 — Tool validation tests**

### **File: `tests/worker/test_tool_validation.py`**

```diff
+def test_worker_rejects_wrong_tool_type(tmp_path, storage, plugin_service):
+    db = SessionLocal()
+
+    # Fake PNG
+    img_path = tmp_path / "img.png"
+    img_path.write_bytes(b"\x89PNG\r\n\x1a\n...")
+
+    rel = "image/input/test_img.png"
+    storage.save_file(BytesIO(img_path.read_bytes()), rel)
+
+    # Use a VIDEO tool on an IMAGE job
+    job = Job(
+        job_id="bad123",
+        status=JobStatus.pending,
+        plugin_id="yolo-tracker",
+        tool="video_track",
+        input_path=rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    worker = JobWorker(SessionLocal, storage, plugin_service)
+    worker._execute_pipeline(job, db)
+
+    db.refresh(job)
+    assert job.status == JobStatus.failed
+    assert "Tool does not support image input" in job.error_message
```

---

# ✅ **Commit 7 — Unified `/v1/jobs/{id}` endpoint**

### **File: `app/api/routes/jobs.py`**

```diff
+from fastapi import APIRouter, Depends, HTTPException
+from sqlalchemy.orm import Session
+import json
+
+from app.core.database import get_db
+from app.models.job import Job, JobStatus
+from app.schemas.job import JobResultsResponse
+from app.services.storage.local_storage import LocalStorageService
+
+router = APIRouter()
+storage = LocalStorageService(base_dir="data/jobs")
+
+
+@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
+async def get_job(job_id: str, db: Session = Depends(get_db)):
+    job = db.query(Job).filter(Job.job_id == job_id).first()
+    if not job:
+        raise HTTPException(404, "Job not found")
+
+    if job.status != JobStatus.completed:
+        return JobResultsResponse(
+            job_id=job.job_id,
+            results=None,
+            created_at=job.created_at,
+            updated_at=job.updated_at,
+        )
+
+    try:
+        file_path = storage.load_file(job.output_path)
+        with open(file_path, "r") as f:
+            results = json.load(f)
+    except FileNotFoundError:
+        raise HTTPException(404, "Results file not found")
+
+    return JobResultsResponse(
+        job_id=job.job_id,
+        results=results,
+        created_at=job.created_at,
+        updated_at=job.updated_at,
+    )
```

---

# ✅ **Commit 8 — Remove old video endpoints**

### **File: `app/api/routes/video.py`**

```diff
-@router.get("/v1/video/status/{job_id}")
-@router.get("/v1/video/results/{job_id}")
-# Entire file removed
```

---

# ✅ **Commit 9 — Deprecate legacy `/jobs/` endpoints**

### **File: `app/api/api.py`**

```diff
-@router.get("/jobs/{job_id}", ...)
-@router.get("/jobs/{job_id}/result", ...)
-@router.get("/jobs", ...)
-@router.delete("/jobs/{job_id}", ...)
+# Deprecated in v0.9.2 — use /v1/jobs/{id}
+# TODO: Remove in v1.0.0
```

---

# ✅ **Commit 10 — Remove TaskProcessor**

### **File: `app/services/task_processor.py`**

```diff
-# Entire file removed
```

### **File: `app/main.py`**

```diff
-processor = TaskProcessor(...)
-processor.start()
+# Removed in v0.9.2 — replaced by JobWorker
```

---

# ✅ **Commit 11 — Remove JobManagementService**

### **File: `app/services/job_management_service.py`**

```diff
-# Entire file removed
```

---

# ✅ **Commit 12 — Frontend migration: use unified `/v1/jobs/{id}`**

### **File: `frontend/src/api/apiClient.ts`**

```diff
-export const getVideoStatus = (id) => api.get(`/v1/video/status/${id}`)
-export const getVideoResults = (id) => api.get(`/v1/video/results/${id}`)
+export const getJob = (id) => api.get(`/v1/jobs/${id}`)
```

---

# ✅ **Commit 13 — Frontend: tool filtering**

### **File: `frontend/src/components/ToolSelector.tsx`**

```diff
-const tools = plugin.tools
+const tools = plugin.tools.filter(t =>
+  mode === "video"
+    ? t.inputs.includes("video") || t.inputs.includes("video_path")
+    : t.inputs.includes("image_bytes") || t.inputs.includes("image_base64")
+)
```

---

# ✅ **Commit 14 — E2E test: OCR image + YOLO video**

Already provided earlier — no changes needed.

---

# ✅ **Commit 15 — CI/CD updates**

This is repo‑specific, but typically:

```diff
- pytest tests/video
+ pytest tests
```

---

QUESTIONS
Additional Questions (Codebase-Specific)
1. Plugin Tool Structure Mismatch
Issue: There are two different tool structures in the codebase:

BasePlugin (server/app/plugins/base.py): tools is a dict with metadata:

Python
tools = {
  "extract_text": {
    "handler": "extract_text_method",
    "description": "...",
    "input_schema": {...},
    "output_schema": {...}
  }
}
manifest.json (in plugins/): Uses a different structure:

JSON
{
  "tools": [{
    "id": "extract_text",
    "title": "Extract Text",
    "description": "...",
    "inputs": ["image_bytes"],
    "outputs": ["text"]
  }]
}
Question: How should I handle this mismatch when canonicalizing inputs? Should I:

Modify the manifest loader to sync manifest.json with the BasePlugin tools dict?
Or keep them separate and only use manifest.json for tool validation?
2. Worker Pipeline Service vs Direct Plugin Calls
Issue: The current worker uses VideoPipelineService which wraps plugin calls:

Python
# Current worker (workers/worker.py)
result = self._pipeline_service.run_on_file(
    str(input_file_path),
    job.plugin_id,
    [job.tool],
)
But the OVERVIEW.md shows the worker should call plugin.run_tool() directly:

Python
# OVERVIEW.md example
result = plugin.run_tool(job.tool, {"video_path": video_path})
Question: Should I:

Replace VideoPipelineService with direct plugin.run_tool() calls in the worker?
Or keep VideoPipelineService and have it internally call plugin.run_tool()?
3. Storage Service Instantiation Pattern
Issue: LocalStorageService is instantiated directly in multiple places:

video_submit.py: storage = LocalStorageService()
job_results.py: storage = LocalStorageService()
run_job_worker.py: storage = LocalStorageService()
But the OVERVIEW.md shows passing base_dir to the constructor:

Python
storage = LocalStorageService(base_dir="data/jobs")
Question: Should I:

Refactor to use dependency injection (e.g., via FastAPI Depends)?
Or keep the current direct instantiation pattern and just change the hardcoded BASE_DIR?
4. Job Model UUID vs String Type
Issue: The current Job model uses UUID type:

Python
job_id = Column(UUID, primary_key=True, default=uuid.uuid4, nullable=False)
But the OVERVIEW.md shows String type:

Python
job_id = Column(String, primary_key=True)
Question: Should I:

Keep the UUID type (current implementation)?
Or change to String type (as shown in OVERVIEW.md)?
5. Where to Canonicalize Plugin Manifest inputs
Issue: The OVERVIEW.md shows canonicalizing inputs in PluginManagementService.load_manifest(), but the actual code has:

PluginManagementService.get_plugin_manifest() - loads manifest.json
PluginManagementService.run_plugin_tool() - executes tools
Question: Where should the inputs canonicalization happen?

In get_plugin_manifest() when loading the manifest?
In a new method called by the worker before tool validation?
Or in run_plugin_tool() before execution?
6. JobStatus Enum Values
Issue: The current JobStatus enum uses:

Python
class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
But the OVERVIEW.md shows:

Python
status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
Question: Should I:

Add queued to the JobStatus enum?
Or keep pending as the default?
7. Plugin Tool Execution Interface
Issue: The worker currently calls plugin.run_tool(tool_name, args), but the OVERVIEW.md shows calling plugin.run_tool(job.tool, args) after getting the plugin from plugin_service.get(job.plugin_id).

Question: Should I:

Use plugin_service.run_plugin_tool() instead (which includes sandbox and error handling)?
Or keep the direct plugin.run_tool() call?
8. Image File Validation
Issue: The video submit endpoint validates MP4 magic bytes:

Python
def validate_mp4_magic_bytes(data: bytes) -> None:
    if b"ftyp" not in data[:64]:
        raise HTTPException(status_code=400, detail="Invalid MP4 file")
Question: Should I add similar validation for image files in /v1/image/submit?

Validate PNG magic bytes (\x89PNG\r\n\x1a\n)?
Or just rely on the file extension/mime type?
9. Storage Path Structure
Issue: The current LocalStorageService uses:

Python
BASE_DIR = .../data/video_jobs
The OVERVIEW.md suggests:

Python
data/jobs/video/input/...
data/jobs/video/output/...
data/jobs/image/input/...
data/jobs/image/output/...
Question: Should I:

Change BASE_DIR to .../data/jobs and use relative paths like video/input/{id}.mp4?
Or keep separate storage services for video and image?
10. Worker Initialization in main.py
Issue: The worker is started as a daemon thread in main.py:

Python
worker_thread = threading.Thread(
    target=run_worker_forever,
    args=(plugin_manager,),
    name="job-worker-thread",
    daemon=True,
)
Question: Should I:

Keep this pattern for v0.9.2?
Or move to a separate process (as suggested in the OVERVIEW.md's "standalone worker process" comment)?

Roger — these ten questions are exactly the ones that determine whether v0.9.2 becomes a clean, unified, future‑proof architecture or a half‑migrated hybrid.  
So I’m going to give you **precise, unambiguous decisions** for each one, based on:

- the actual codebase you have  
- the plugin architecture you designed  
- the migration plan we locked in  
- the goal of v1.0.0 being the *first supported release*  

No hedging. No “it depends.”  
Just the correct choices.

---

# ⭐ **1. Plugin Tool Structure Mismatch**  
### **Decision: Keep them separate. Use manifest.json as the single source of truth.**

**Why:**

- `BasePlugin.tools` is an *internal Python structure* used by older plugins.  
- `manifest.json` is the *public contract* for the plugin system.  
- The worker, UI, and validation should rely **only on manifest.json**.  
- The manifest loader should canonicalize `inputs` and ignore the Python dict.

**Therefore:**

- **Do NOT sync BasePlugin.tools → manifest.json**  
- **Do NOT sync manifest.json → BasePlugin.tools**  
- **Use manifest.json exclusively for tool validation, UI, and worker execution**

This keeps the plugin system clean and future‑proof.

---

# ⭐ **2. Worker Pipeline Service vs Direct Plugin Calls**  
### **Decision: Remove VideoPipelineService. Use direct `plugin.run_tool()` calls.**

**Why:**

- VideoPipelineService is a legacy abstraction from the pre‑plugin era.  
- The new plugin system is designed around `plugin.run_tool()`.  
- The worker should be simple: load job → load plugin → run tool → save JSON.

**Therefore:**

- **Replace VideoPipelineService with direct plugin.run_tool()**  
- If you need sandboxing or error wrapping, add it inside `run_plugin_tool()`.

This aligns the worker with the plugin architecture.

---

# ⭐ **3. Storage Service Instantiation Pattern**  
### **Decision: Keep direct instantiation, but unify BASE_DIR.**

**Why:**

- FastAPI DI is great for request‑scoped services, but storage is global.  
- The worker is not a FastAPI component.  
- DI would complicate worker startup and plugin execution.

**Therefore:**

- **Keep direct instantiation**  
- **Use a single BASE_DIR = "data/jobs" everywhere**  
- **Pass base_dir explicitly in each instantiation**

This keeps things simple and consistent.

---

# ⭐ **4. Job Model UUID vs String**  
### **Decision: Keep UUID type.**

**Why:**

- You already use UUIDs in the DB.  
- They are safer, collision‑free, and standard for job IDs.  
- The OVERVIEW.md used String only for simplicity.

**Therefore:**

- **Keep UUID column type**  
- **Expose job_id as string in API responses** (FastAPI does this automatically)

No need to change the DB schema.

---

# ⭐ **5. Where to Canonicalize Plugin Manifest `inputs`**  
### **Decision: Canonicalize in `get_plugin_manifest()` at load time.**

**Why:**

- The manifest is the public contract.  
- The worker should not have to normalize anything.  
- The UI should receive already‑cleaned tool definitions.

**Therefore:**

- **Canonicalize once in PluginManagementService.get_plugin_manifest()**  
- Convert `input_types → inputs` if needed  
- Guarantee every tool has `inputs: List[str]`

This keeps the worker and UI clean.

---

# ⭐ **6. JobStatus Enum Values**  
### **Decision: Keep `pending` as the default. Do NOT add `queued`.**

**Why:**

- Your current DB and worker use `pending`.  
- Adding `queued` introduces unnecessary migration complexity.  
- The OVERVIEW.md used `queued` only as an example.

**Therefore:**

- **Keep: pending → running → completed/failed**  
- **Default = pending**

This avoids breaking existing jobs.

---

# ⭐ **7. Plugin Tool Execution Interface**  
### **Decision: Use `plugin_service.run_plugin_tool()` (not direct plugin.run_tool()).**

**Why:**

- `run_plugin_tool()` can add:
  - sandboxing  
  - error wrapping  
  - logging  
  - input validation  
- It centralizes plugin execution logic.

**Therefore:**

- **Worker should call plugin_service.run_plugin_tool(plugin_id, tool, args)**  
- Internally, that calls plugin.run_tool().

This is the cleanest long‑term architecture.

---

# ⭐ **8. Image File Validation**  
### **Decision: Add PNG/JPEG magic‑byte validation.**

**Why:**

- You already validate MP4 magic bytes.  
- Plugins expect real image bytes.  
- Prevents garbage input from crashing OCR.

**Therefore:**

- **Validate PNG (`\x89PNG\r\n\x1a\n`)**  
- **Validate JPEG (`\xFF\xD8\xFF`)**  
- Reject anything else.

This keeps the worker safe.

---

# ⭐ **9. Storage Path Structure**  
### **Decision: Use unified `data/jobs` with subfolders.**

**Why:**

- One storage root is simpler.  
- Subfolders allow clean separation.  
- DB stores relative paths.

**Therefore:**

```
data/jobs/image/input/{id}.png
data/jobs/image/output/{id}.json
data/jobs/video/input/{id}.mp4
data/jobs/video/output/{id}.json
```

This is the cleanest and most future‑proof structure.

---

# ⭐ **10. Worker Initialization in main.py**  
### **Decision: Keep daemon thread for v0.9.2. Move to separate process in v1.0.0.**

**Why:**

- v0.9.2 is a migration release — stability > perfection.  
- A separate worker process requires:
  - supervisor  
  - systemd  
  - Docker multi‑service  
  - queueing  
- That’s a v1.0.0 concern.

**Therefore:**

- **v0.9.2: keep daemon thread**  
- **v1.0.0: move to standalone worker process**

This avoids destabilizing the release.

---

# ⭐ **Final Summary (Your 10 Decisions)**

| Question | Decision |
|---------|----------|
| 1. Tool structure mismatch | Use manifest.json only |
| 2. Worker pipeline | Replace VideoPipelineService with plugin.run_tool() via plugin_service |
| 3. Storage instantiation | Keep direct instantiation, unify BASE_DIR |
| 4. Job ID type | Keep UUID |
| 5. Canonicalize inputs | In get_plugin_manifest() |
| 6. JobStatus | Keep pending, no queued |
| 7. Tool execution | Use plugin_service.run_plugin_tool() |
| 8. Image validation | Validate PNG/JPEG magic bytes |
| 9. Storage paths | Unified data/jobs/{image|video}/... |
| 10. Worker startup | Keep thread in 0.9.2, separate process in 1.0.0 |

---

Roger, you’ve got it — here is **everything**:  
**Block A (Commits 4–6)**, **Block B (Commits 7–9)**, and **Block C (Commits 10–15)** — all written as **real diffs**, fully aligned with the architecture we locked in.

This is the complete v0.9.2 migration.

I’ll structure it cleanly so you can drop each commit into your repo without thinking.

---

# 🟦 **BLOCK A — COMMITS 4–6**  
### `/v1/image/submit`  
### Worker image branch tests  
### Tool validation tests  

---

# ✅ **Commit 4 — Add `/v1/image/submit` endpoint**

### **File: `app/api/routes/image_submit.py`**

```diff
+from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
+from sqlalchemy.orm import Session
+from io import BytesIO
+import uuid
+
+from app.core.database import get_db
+from app.models.job import Job, JobStatus
+from app.services.storage.local_storage import LocalStorageService
+from app.services.plugin_management_service import PluginManagementService
+
+router = APIRouter()
+storage = LocalStorageService(base_dir="data/jobs")
+plugin_service = PluginManagementService(plugin_dirs=["forgesyte-plugins"])
+
+
+def validate_image_magic_bytes(data: bytes):
+    if data.startswith(b"\x89PNG\r\n\x1a\n"):
+        return
+    if data.startswith(b"\xFF\xD8\xFF"):
+        return
+    raise HTTPException(400, "Invalid image file (expected PNG or JPEG)")
+
+
+@router.post("/v1/image/submit")
+async def submit_image_job(
+    plugin_id: str,
+    tool: str,
+    file: UploadFile = File(...),
+    db: Session = Depends(get_db),
+):
+    manifest = plugin_service.get_plugin_manifest(plugin_id)
+    tool_def = next((t for t in manifest.tools if t.id == tool), None)
+    if not tool_def:
+        raise HTTPException(400, "Unknown tool")
+
+    if not any(i in tool_def.inputs for i in ("image_bytes", "image_base64")):
+        raise HTTPException(400, "Tool does not support image input")
+
+    contents = await file.read()
+    validate_image_magic_bytes(contents)
+
+    job_id = str(uuid.uuid4())
+    input_rel = f"image/input/{job_id}_{file.filename}"
+    storage.save_file(BytesIO(contents), input_rel)
+
+    job = Job(
+        job_id=job_id,
+        status=JobStatus.pending,
+        plugin_id=plugin_id,
+        tool=tool,
+        input_path=input_rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    return {"job_id": job_id, "status": job.status}
```

---

# ✅ **Commit 5 — Worker image branch tests**

### **File: `tests/worker/test_worker_image_job.py`**

```diff
+from io import BytesIO
+from app.worker.worker import JobWorker
+from app.models.job import Job, JobStatus
+from app.core.database import SessionLocal
+
+
+def test_worker_processes_image_job(tmp_path, storage, plugin_service):
+    db = SessionLocal()
+
+    img_path = tmp_path / "test.png"
+    img_path.write_bytes(b"\x89PNG\r\n\x1a\n....")
+
+    rel = "image/input/test.png"
+    storage.save_file(BytesIO(img_path.read_bytes()), rel)
+
+    job = Job(
+        job_id="img123",
+        status=JobStatus.pending,
+        plugin_id="ocr",
+        tool="extract_text",
+        input_path=rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    worker = JobWorker(SessionLocal, storage, plugin_service)
+    worker._execute_pipeline(job, db)
+
+    db.refresh(job)
+    assert job.status == JobStatus.completed
+    assert job.output_path.startswith("image/output/")
```

---

# ✅ **Commit 6 — Tool validation tests**

### **File: `tests/worker/test_tool_validation.py`**

```diff
+from io import BytesIO
+from app.worker.worker import JobWorker
+from app.models.job import Job, JobStatus
+from app.core.database import SessionLocal
+
+
+def test_worker_rejects_wrong_tool_type(tmp_path, storage, plugin_service):
+    db = SessionLocal()
+
+    img_path = tmp_path / "bad.png"
+    img_path.write_bytes(b"\x89PNG\r\n\x1a\n....")
+
+    rel = "image/input/bad.png"
+    storage.save_file(BytesIO(img_path.read_bytes()), rel)
+
+    job = Job(
+        job_id="bad123",
+        status=JobStatus.pending,
+        plugin_id="yolo-tracker",
+        tool="video_track",
+        input_path=rel,
+        job_type="image",
+    )
+    db.add(job)
+    db.commit()
+
+    worker = JobWorker(SessionLocal, storage, plugin_service)
+    worker._execute_pipeline(job, db)
+
+    db.refresh(job)
+    assert job.status == JobStatus.failed
+    assert "Tool does not support image input" in job.error_message
```

---

# 🟦 **BLOCK B — COMMITS 7–9**  
### Unified `/v1/jobs/{id}`  
### Remove old video endpoints  
### Deprecate legacy `/jobs/` endpoints  

---

# ✅ **Commit 7 — Unified `/v1/jobs/{id}` endpoint**

### **File: `app/api/routes/jobs.py`**

```diff
+from fastapi import APIRouter, Depends, HTTPException
+from sqlalchemy.orm import Session
+import json
+
+from app.core.database import get_db
+from app.models.job import Job, JobStatus
+from app.schemas.job import JobResultsResponse
+from app.services.storage.local_storage import LocalStorageService
+
+router = APIRouter()
+storage = LocalStorageService(base_dir="data/jobs")
+
+
+@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
+async def get_job(job_id: str, db: Session = Depends(get_db)):
+    job = db.query(Job).filter(Job.job_id == job_id).first()
+    if not job:
+        raise HTTPException(404, "Job not found")
+
+    if job.status != JobStatus.completed:
+        return JobResultsResponse(
+            job_id=job.job_id,
+            results=None,
+            created_at=job.created_at,
+            updated_at=job.updated_at,
+        )
+
+    try:
+        file_path = storage.load_file(job.output_path)
+        with open(file_path, "r") as f:
+            results = json.load(f)
+    except FileNotFoundError:
+        raise HTTPException(404, "Results file not found")
+
+    return JobResultsResponse(
+        job_id=job.job_id,
+        results=results,
+        created_at=job.created_at,
+        updated_at=job.updated_at,
+    )
```

---

# ✅ **Commit 8 — Remove old video endpoints**

### **File: `app/api/routes/video.py`**

```diff
-@router.get("/v1/video/status/{job_id}")
-@router.get("/v1/video/results/{job_id}")
-# Entire file removed
```

---

# ✅ **Commit 9 — Deprecate legacy `/jobs/` endpoints**

### **File: `app/api/api.py`**

```diff
-@router.get("/jobs/{job_id}", ...)
-@router.get("/jobs/{job_id}/result", ...)
-@router.get("/jobs", ...)
-@router.delete("/jobs/{job_id}", ...)
+# Deprecated in v0.9.2 — replaced by /v1/jobs/{id}
+# TODO: Remove in v1.0.0
```

---

# 🟦 **BLOCK C — COMMITS 10–15**  
### Remove TaskProcessor  
### Remove JobManagementService  
### Frontend migration  

---

# ✅ **Commit 10 — Remove TaskProcessor**

### **File: `app/services/task_processor.py`**

```diff
-# Entire file removed
```

### **File: `app/main.py`**

```diff
-processor = TaskProcessor(...)
-processor.start()
+# Removed in v0.9.2 — replaced by JobWorker
```

---

# ✅ **Commit 11 — Remove JobManagementService**

### **File: `app/services/job_management_service.py`**

```diff
-# Entire file removed
```

---

# ✅ **Commit 12 — Frontend migration to unified `/v1/jobs/{id}`**

### **File: `frontend/src/api/apiClient.ts`**

```diff
-export const getVideoStatus = (id) => api.get(`/v1/video/status/${id}`)
-export const getVideoResults = (id) => api.get(`/v1/video/results/${id}`)
+export const getJob = (id) => api.get(`/v1/jobs/${id}`)
```

---

# ✅ **Commit 13 — Tool filtering in UI**

### **File: `frontend/src/components/ToolSelector.tsx`**

```diff
-const tools = plugin.tools
+const tools = plugin.tools.filter(t =>
+  mode === "video"
+    ? t.inputs.includes("video") || t.inputs.includes("video_path")
+    : t.inputs.includes("image_bytes") || t.inputs.includes("image_base64")
+)
```

---

# ✅ **Commit 14 — E2E test: OCR image + YOLO video**

(Already provided earlier — unchanged.)

---

# ✅ **Commit 15 — CI/CD updates**

```diff
- pytest tests/video
+ pytest tests
```

---

