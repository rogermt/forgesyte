Good — this is a real release spec now, not a story. I’ll give you **concrete, repo-shaped artifacts** you can actually implement.

I’ll assume paths consistent with your doc:

- Backend root: `server/`
- Frontend root: `web-ui/`

---

## 1. Backend code diffs (v0.9.0‑alpha)

### 1.1 Make `pipeline_id` optional in `/v1/video/submit`

**File:** `server/api/routes/video.py`

```diff
@@
-@router.post("/v1/video/submit")
-async def submit_video(
-    file: UploadFile = File(...),
-    pipeline_id: str = Query(..., description="Pipeline ID"),
-):
+DEFAULT_VIDEO_PIPELINE = "ocr_only"
+
+@router.post("/v1/video/submit")
+async def submit_video(
+    file: UploadFile = File(...),
+    pipeline_id: str = Query(
+        default=DEFAULT_VIDEO_PIPELINE,
+        description="Pipeline ID (optional, defaults to ocr_only)",
+    ),
+):
@@
-    job = await job_manager.create_job(
-        plugin=plugin_name,
-        input_path=video_path,
-        pipeline_id=pipeline_id,
-    )
+    job = await job_manager.create_job(
+        input_path=video_path,
+        pipeline_id=pipeline_id,
+    )
```

*(Adjust `job_manager.create_job` signature to match your real code.)*

---

# ✅ **UPDATED IN YOUR ORIGINAL FORMAT**

## **1.2 Add `PipelineExecutor` service**

**File:** `server/services/pipeline_executor.py` (REMOVED)

```python
# ❌ REMOVED — NOT NEEDED

"""
DEPRECATED — DO NOT USE.

Pipeline execution is handled by:
- VideoFilePipelineService
- DagPipelineService
- Plugin registry

This file remains only to avoid import errors during refactoring.
It will be fully removed in v1.0.0.
"""

# Intentionally empty.
```

---

## **1.3 Wire `PipelineExecutor` into worker**  
*(Corrected to use VideoFilePipelineService instead)*

**File:** `server/workers/video_worker.py`

```diff
-from server.plugins.yolo_tracker import yolo_plugin
-from server.plugins.ocr import ocr_plugin
-from server.utils.video import extract_frames
+from server.services.video_file_pipeline_service import VideoFilePipelineService

 async def process_job(job_id: str):
     job = job_repo.get(job_id)

     try:
-        frames = extract_frames(job.input_path)
-        # Old direct plugin calls (Phase 15 / Phase 16 style)
-        yolo_results = await yolo_plugin.run(frames)
-        ocr_results = await ocr_plugin.run(frames)
-
-        job.result = {
-            "detections": yolo_results,
-            "text": ocr_results,
-        }
+        # Ensure pipeline_id exists (backward compatibility with older jobs)
+        pipeline_id = getattr(job, "pipeline_id", "ocr_only")
+
+        # Use the existing Phase 16 pipeline execution system
+        # This handles:
+        # - opening MP4
+        # - extracting frames
+        # - running DAG pipeline per frame
+        # - aggregating results
+        result = await VideoFilePipelineService.run_on_file(
+            pipeline_id=pipeline_id,
+            file_path=job.input_path,
+        )
+
+        job.result = result
         job.status = "done"

     except Exception as e:
         job.status = "error"
         job.error = str(e)

     job_repo.save(job)
```

*(If `job.pipeline_id` doesn’t exist yet, add it to the job model with default `"ocr_only"`.)*

---





### 1.4 Restore `/v1/video/process` (sync endpoint)

**File:** `server/api/routes/video.py`

```diff
+@router.post("/v1/video/process")
+async def process_video(file: UploadFile = File(...)):
+    # Save uploaded file
+    video_path = await save_uploaded_file(file)  # reuse existing helper
+
+    # For v0.9.0-alpha, reuse ocr_only pipeline
+    result = await execute_pipeline("ocr_only", video_path)
+
+    return result
```

---

### 1.5 Restore `/v1/image/process`

**File:** `server/api/routes/image.py` (new or restored)

```python
from fastapi import APIRouter, UploadFile, File, Query

from server.plugins.ocr import ocr_plugin
from server.plugins.yolo_tracker import yolo_plugin  # used in beta

router = APIRouter()


@router.post("/v1/image/process")
async def process_image(
    file: UploadFile = File(...),
    mode: str = Query(default="ocr", regex="^(ocr|yolo)$"),
):
    image_bytes = await file.read()

    if mode == "ocr":
        text = await ocr_plugin.run([image_bytes])
        return {"mode": "ocr", "text": text}

    # v0.9.0-beta: enable YOLO here
    detections = await yolo_plugin.run([image_bytes])
    return {"mode": "yolo", "detections": detections}
```

And mount it in your main router:

**File:** `server/api/routes/__init__.py`

```diff
-from . import video
+from . import video, image
@@
-api.include_router(video.router)
+api.include_router(video.router)
+api.include_router(image.router)
```

---

## 2. Frontend component skeletons (v0.9.0‑alpha)

### 2.1 Directory structure

```text
web-ui/
  components/
    VideoUpload.tsx
    VideoUpload.module.css
    JobStatus.tsx
    JobStatus.module.css
    JobResults.tsx
    JobResults.module.css
  services/
    api.ts
  pages/
    index.tsx
  tests/
    integration/
      videoUpload.test.ts
```

---

### 2.2 `VideoUpload` skeleton

**File:** `web-ui/components/VideoUpload.tsx`

```tsx
import React, { useState } from "react";
import styles from "./VideoUpload.module.css";
import { submitVideo } from "../services/api";
import { JobStatus } from "./JobStatus";

export const VideoUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setError(null);
    setJobId(null);
    setProgress(0);

    if (!f) {
      setFile(null);
      return;
    }

    if (f.type !== "video/mp4") {
      setError("Only MP4 videos are supported.");
      setFile(null);
      return;
    }

    setFile(f);
  };

  const onUpload = async () => {
    if (!file) return;
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const { job_id } = await submitVideo(file, (p) => setProgress(p));
      setJobId(job_id);
    } catch (e: any) {
      setError(e.message ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2>Video Upload</h2>

      <input type="file" accept="video/mp4" onChange={onFileChange} />

      {error && <div className={styles.error}>{error}</div>}

      {uploading && (
        <div className={styles.progress}>
          Uploading… {progress.toFixed(0)}%
        </div>
      )}

      <button
        onClick={onUpload}
        disabled={!file || uploading}
        className={styles.button}
      >
        Upload
      </button>

      {jobId && (
        <div className={styles.jobSection}>
          <div className={styles.jobId}>Job ID: {jobId}</div>
          <JobStatus jobId={jobId} />
        </div>
      )}
    </div>
  );
};
```

---

### 2.3 `JobStatus` skeleton

**File:** `web-ui/components/JobStatus.tsx`

```tsx
import React, { useEffect, useState } from "react";
import styles from "./JobStatus.module.css";
import { getJobStatus, getJobResults } from "../services/api";
import { JobResults } from "./JobResults";

type Props = {
  jobId: string;
};

type Status = "pending" | "running" | "done" | "error";

export const JobStatus: React.FC<Props> = ({ jobId }) => {
  const [status, setStatus] = useState<Status>("pending");
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    const poll = async () => {
      try {
        const s = await getJobStatus(jobId);
        setStatus(s.status);

        if (s.status === "done") {
          const r = await getJobResults(jobId);
          setResults(r);
          return;
        }

        if (s.status === "error") {
          setError(s.error ?? "Job failed.");
          return;
        }

        timer = window.setTimeout(poll, 2000);
      } catch (e: any) {
        setError(e.message ?? "Status polling failed.");
      }
    };

    poll();

    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  return (
    <div className={styles.container}>
      <div>Status: {status}</div>
      {error && <div className={styles.error}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};
```

---

### 2.4 `JobResults` skeleton (alpha: OCR only)

**File:** `web-ui/components/JobResults.tsx`

```tsx
import React from "react";
import styles from "./JobResults.module.css";

type Props = {
  results: any;
};

export const JobResults: React.FC<Props> = ({ results }) => {
  // v0.9.0-alpha: OCR-only
  const text = results.text ?? results.ocr ?? "";

  return (
    <div className={styles.container}>
      <h3>Results</h3>
      {text ? (
        <pre className={styles.text}>{text}</pre>
      ) : (
        <div>No OCR text available.</div>
      )}
    </div>
  );
};
```

*(v0.9.0‑beta: extend to show `results.detections`.)*

---

### 2.5 API service functions

**File:** `web-ui/services/api.ts`

```ts
const BASE_URL = "http://localhost:8000";

export async function submitVideo(
  file: File,
  onProgress?: (percent: number) => void
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE_URL}/v1/video/submit`);

    xhr.upload.onprogress = (event) => {
      if (!onProgress || !event.lengthComputable) return;
      const percent = (event.loaded / event.total) * 100;
      onProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (e) {
          reject(new Error("Invalid server response."));
        }
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}.`));
      }
    };

    xhr.onerror = () => reject(new Error("Network error during upload."));

    xhr.send(formData);
  });
}

export async function getJobStatus(jobId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/v1/video/status/${jobId}`);
  if (!res.ok) throw new Error(`Status failed: ${res.status}`);
  return res.json();
}

export async function getJobResults(jobId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/v1/video/results/${jobId}`);
  if (!res.ok) throw new Error(`Results failed: ${res.status}`);
  return res.json();
}
```

---

### 2.6 Wire `VideoUpload` into main page

**File:** `web-ui/pages/index.tsx`

```tsx
import React from "react";
import { VideoUpload } from "../components/VideoUpload";
// import existing components (image upload, plugin selector, etc.)

const HomePage: React.FC = () => {
  return (
    <main>
      <h1>ForgerSyte</h1>

      {/* existing image upload + tools UI here */}

      <section>
        <VideoUpload />
      </section>
    </main>
  );
};

export default HomePage;
```

---

## 3. Test cases (high‑level)

### 3.1 Backend tests

**File:** `server/tests/test_video_submit.py`

- **Test 1:** `POST /v1/video/submit` with MP4 → 200, returns `job_id`.
- **Test 2:** `POST /v1/video/submit` without `pipeline_id` → uses `"ocr_only"`.
- **Test 3:** Worker processes job with `pipeline_id="ocr_only"` → `job.result.text` present.

**File:** `server/tests/test_video_process.py`

- **Test 4:** `POST /v1/video/process` with MP4 → 200, JSON with `text`.

**File:** `server/tests/test_image_process.py`

- **Test 5:** `POST /v1/image/process` with image, `mode=ocr` → 200, `text`.
- **Test 6:** `POST /v1/image/process` with image, `mode=yolo` (beta) → 200, `detections`.

---

### 3.2 Frontend integration test

**File:** `web-ui/tests/integration/videoUpload.test.ts`

- **Test 1:**  
  - Render `VideoUpload`.  
  - Mock `submitVideo` → returns `{ job_id: "123" }`.  
  - Mock `getJobStatus` → `pending` → `running` → `done`.  
  - Mock `getJobResults` → `{ text: "hello world" }`.  
  - Assert:
    - file input accepts MP4  
    - upload button enabled when file selected  
    - job_id displayed  
    - status transitions  
    - results text rendered  

---


# 🧩 **v0.9.0 — Mandatory Pre‑Commit Workflow Enforcement**

## 🎯 **Rule: Developers MUST run all CI workflows locally BEFORE committing.**

This is now a **hard requirement** for v0.9.0 and all future releases.

### **Why?**
- Phase 16 broke because regressions slipped through.
- Phase 17 broke because nothing was tested.
- You start from a **GREEN** repo.
- You want to **stay GREEN** forever.
- Your workflows are your governance system.

### **What this means:**
Before *every commit*, the developer must manually run and fix **all** workflows:

```
/home/rogermt/forgesyte/.github/workflows/vocabulary_validation.yml
/home/rogermt/forgesyte/.github/workflows/video_batch_validation.yml
/home/rogermt/forgesyte/.github/workflows/governance-ci.yml
/home/rogermt/forgesyte/.github/workflows/execution-ci.yml
/home/rogermt/forgesyte/.github/workflows/ci.yml
```

No commit is allowed unless:

- **All workflows pass**
- **All errors are fixed**
- **Repo is fully GREEN**

This rule is now part of the v0.9.0 contract.

---

# 🛠️ **How Developers Must Run Workflows Locally**

### **Step 1 — Run vocabulary validation**
```bash
act -W .github/workflows/vocabulary_validation.yml
```

### **Step 2 — Run video batch validation**
```bash
act -W .github/workflows/video_batch_validation.yml
```

### **Step 3 — Run governance CI**
```bash
act -W .github/workflows/governance-ci.yml
```

### **Step 4 — Run execution CI**
```bash
act -W .github/workflows/execution-ci.yml
```

### **Step 5 — Run full CI**
```bash
act -W .github/workflows/ci.yml
```

### **Step 6 — Fix everything**
No commit is allowed until:

- All tests pass  
- All linters pass  
- All vocabulary rules pass  
- All governance rules pass  
- All execution rules pass  
- All video batch rules pass  

---

# 📌 **Add This to v0.9.0 Release Notes**

## **Developer Requirements (New in v0.9.0)**

Before committing, developers MUST run and pass all CI workflows:

- `vocabulary_validation.yml`
- `video_batch_validation.yml`
- `governance-ci.yml`
- `execution-ci.yml`
- `ci.yml`

**No commit is allowed unless the repository is fully GREEN.**

This rule prevents regressions and ensures the stability of the v0.9.0 release.

---


## 4. Commit messages (suggested)

**Backend (alpha):**

1. `feat(api): make video submit pipeline_id optional with default ocr_only`
2. `feat(core): add pipeline executor service for video pipelines`
3. `feat(worker): route video jobs through pipeline executor`
4. `feat(api): restore /v1/video/process synchronous endpoint`
5. `feat(api): restore /v1/image/process endpoint for ocr/yolo`

**Frontend (alpha):**

6. `feat(ui): add VideoUpload component skeleton`
7. `feat(ui): add video file upload form with mp4 validation`
8. `feat(ui): wire VideoUpload to /v1/video/submit`
9. `feat(ui): display job id after video submission`
10. `feat(ui): add JobStatus component with polling`
11. `feat(ui): add JobResults component for OCR results`
12. `feat(ui): show upload progress and error messages`
13. `feat(ui): render VideoUpload on main page`
14. `test(ui): add integration test for video upload flow`

**Release:**

15. `docs: document v0.9.0-alpha video upload feature`
16. `chore: bump version to v0.9.0-alpha`

---

If you want, next step we can do is **tighten the backend contracts** (exact JSON shapes for `/status` and `/results`) so the FE and BE are locked together with zero ambiguity.