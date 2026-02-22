# v0.9.0 Development Plan — Based on Actual Codebase

**Last Updated:** 2026-02-18
**Status:** Ready for Implementation

---

### **Before Commit (Mandatory)**

Every commit in v0.9.0 must satisfy:

1. Run all GitHub workflows locally  
2. Fix all errors  
3. Ensure repo is GREEN  
4. Only then commit  

This applies to:

- Backend commits  
- Frontend commits  
- Integration commits  
- Documentation commits  

---



Every commit message must include:

```
[CI PASS] All workflows validated locally before commit.
```

If CI is not green, the commit is **invalid**.


## Executive Summary

This development plan is based on a comprehensive analysis of the **actual codebase** as of 2026-02-18. It differs significantly from the original DOCUMENTS.md and CODE_AND_TEST_SKELETON.md because much of the infrastructure is **already implemented**.

### 📊 Verification Status

**All aspects of this plan have been verified against actual code:**
- ✅ Backend endpoints (verified from `/server/app/api_routes/routes/`)
- ✅ Worker implementation (verified from `/server/app/workers/worker.py`)
- ✅ Service classes (verified from `/server/app/services/`)
- ✅ Pipeline definitions (verified from `/server/app/pipelines/`)
- ✅ Plugin manifests (verified from `/plugins/ocr/manifest.json` and `/plugins/yolo/manifest.json`)
- ✅ Job model (verified from `/server/app/models/job.py`)
- ✅ Frontend components (verified from `/web-ui/src/components/`)
- ✅ API client (verified from `/web-ui/src/api/client.ts`)
- ✅ Test cases (verified from `/server/app/tests/video/`)

**See `/home/rogermt/forgesyte/docs/releases/v0.9.0/UNCERTAINTY_ANALYSIS.md` for detailed verification.**

### 🚨 CRITICAL REQUIREMENTS

**TDD (Test-Driven Development) is MANDATORY for every commit:**
1. Write failing tests first
2. Run tests to verify they fail
3. Implement code to make tests pass
4. Run tests to verify they pass
5. Run ALL 5 CI workflows
6. Commit only if all workflows pass

**ALL 5 CI Workflows MUST pass before EVERY commit:**
1. vocabulary_validation.yml
2. video_batch_validation.yml
3. governance-ci.yml
4. execution-ci.yml
5. ci.yml

**No commit is allowed unless:**
- All workflows pass
- All errors are fixed
- All vocabulary rules pass
- All governance rules pass
- All execution rules pass
- All video batch rules pass
- Repo is fully GREEN

### Key Discovery: Most Backend Work is Already Done

The Phase 16 async job system is **largely complete**:
- ✅ `/v1/video/submit` endpoint exists (requires `pipeline_id`)
- ✅ `/v1/video/status/{job_id}` endpoint exists
- ✅ `/v1/video/results/{job_id}` endpoint exists
- ✅ JobWorker exists and processes jobs asynchronously
- ✅ Job model exists with all required fields
- ✅ VideoFilePipelineService exists
- ✅ `yolo_ocr` pipeline definition exists
- ✅ Comprehensive video tests exist

### What's Actually Missing

1. **Backend (Minimal):**
   - Make `pipeline_id` OPTIONAL in `/v1/video/submit` with default "ocr_only"
   - Create `ocr_only` pipeline definition (currently only `yolo_ocr` exists)
   - Fix YOLO unpickling error (beta only)

   **Note:** No need to create PipelineExecutor service. The existing `VideoFilePipelineService` and `DagPipelineService` already handle pipeline execution correctly.

2. **Frontend (Moderate):**
   - Dedicated VideoUpload component (separate from VideoTracker)
   - JobStatus component (for polling video job status)
   - JobResults component (for displaying video job results)
   - API client methods: submitVideo, getVideoJobStatus, getVideoJobResults
   - Wire VideoUpload to main page

---

## Phase 1: Backend Fixes (v0.9.0-alpha)

**Note:** The existing `VideoFilePipelineService` and `DagPipelineService` already handle pipeline execution correctly. No need to create a new PipelineExecutor service.

### Commit B1: Make `pipeline_id` Optional in `/v1/video/submit`

**File:** `server/app/api_routes/routes/video_submit.py`

**Current Code:**
```python
@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    pipeline_id: str,  # REQUIRED - causes frontend failure
):
```

**Change To:**
```python
DEFAULT_VIDEO_PIPELINE = "ocr_only"

@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    pipeline_id: str = Query(
        default=DEFAULT_VIDEO_PIPELINE,
        description="Pipeline ID (optional, defaults to ocr_only)",
    ),
):
```

**Why:** Frontend can submit videos without knowing valid pipeline IDs. This is the **critical fix** that enables video upload UI.

**TDD Workflow (MANDATORY):**
1. Write failing test for `pipeline_id` parameter being optional
2. Run test to verify it fails
3. Implement code to make `pipeline_id` optional with default "ocr_only"
4. Run test to verify it passes
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Upload without `pipeline_id` → uses default "ocr_only"
- ✅ Upload with explicit `pipeline_id="yolo_ocr"` → uses specified
- ✅ Upload with invalid `pipeline_id` → returns 400 error
- ✅ Existing Phase 16 tests still pass

**Acceptance Criteria:**
```bash
curl -i -F "file=@video.mp4" http://localhost:8000/v1/video/submit
→ 200 OK
→ {"job_id": "..."}
```

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
# Before commit, run ALL workflows in order
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

# Only commit if ALL workflows pass
git add .
git commit -m "feat(api): make video submit pipeline_id optional with default ocr_only

[CI PASS] All workflows validated locally before commit."
```

---

### Commit B2: Create `ocr_only` Pipeline Definition

**File:** `server/app/pipelines/ocr_only.json` (NEW)

**Content:**
```json
{
  "id": "ocr_only",
  "name": "OCR Only Pipeline",
  "description": "Extract text from images using OCR (no object detection)",
  "nodes": [
    {
      "id": "read",
      "plugin_id": "ocr",
      "tool_id": "extract_text",
      "input_schema": {
        "type": "object",
        "properties": {
          "image_bytes": {
            "type": "string",
            "format": "binary"
          }
        },
        "required": ["image_bytes"]
      }
    }
  ],
  "edges": [],
  "entry_nodes": ["read"],
  "output_nodes": ["read"]
}
```

**Why:** Alpha release needs a working pipeline that doesn't depend on YOLO (which has unpickling error).

**TDD Workflow (MANDATORY):**
1. Write failing test for `ocr_only` pipeline execution
2. Run test to verify it fails
3. Create `ocr_only.json` pipeline definition
4. Run test to verify it passes
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Pipeline loads successfully
- ✅ Pipeline validates successfully
- ✅ Pipeline executes on test image
- ✅ Returns OCR text only (no detections)

**Acceptance Criteria:**
```bash
curl -X POST http://localhost:8000/pipelines/ocr_only/run \
  -H "Content-Type: application/json" \
  -d '{"image_bytes": "..."}'
→ 200 OK
→ {"result": {"text": "..."}}
```

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

# Only commit if ALL workflows pass
git add .
git commit -m "feat(pipelines): add ocr_only pipeline definition

[CI PASS] All workflows validated locally before commit."
```

---

### Commit B3: Update API Documentation (Previously B2)

**File:** `docs/api/video-endpoints.md` (UPDATE)

**Add:**
```markdown
## POST /v1/video/submit

Submit a video for asynchronous processing.

### Parameters
- `file` (required): MP4 video file
- `pipeline_id` (optional, default: "ocr_only"): Pipeline to execute
  - `ocr_only`: Extract text only (v0.9.0-alpha)
  - `yolo_ocr`: Object detection + text extraction (v0.9.0-beta)

### Response
```json
{
  "job_id": "uuid-string"
}
```

### Example
```bash
# Alpha: Uses default pipeline (ocr_only)
curl -F "file=@video.mp4" http://localhost:8000/v1/video/submit

# Beta: Explicitly specify yolo_ocr pipeline
curl -F "file=@video.mp4" \
     -F "pipeline_id=yolo_ocr" \
     http://localhost:8000/v1/video/submit
```
```

**Why:** Developers need to know API has changed.

**TDD Workflow (MANDATORY):**
1. Write test to verify API documentation is accurate
2. Run test to verify it passes
3. Update API documentation
4. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
5. Commit only if all workflows pass

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

# Verify docs are accurate
cd server
uv run pytest tests/api/ -v

# Only commit if ALL workflows pass
git add .
git commit -m "docs(api): update video endpoints documentation for v0.9.0

[CI PASS] All workflows validated locally before commit."
```

---

## Phase 2: Frontend Development (v0.9.0-alpha)

### Commit F1: Add Video API Methods to API Client

**File:** `web-ui/src/api/client.ts`

**Add Methods:**
```typescript
// Video job submission
async submitVideo(
  file: File,
  pipelineId: string = "ocr_only",
  onProgress?: (percent: number) => void
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${this.baseUrl}/video/submit`);

    if (this.apiKey) {
      xhr.setRequestHeader("X-API-Key", this.apiKey);
    }

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

    // Add pipeline_id to URL
    const url = new URL(`${this.baseUrl}/video/submit`, window.location.origin);
    url.searchParams.append("pipeline_id", pipelineId);
    xhr.open("POST", url.toString());
    xhr.send(formData);
  });
}

// Video job status
async getVideoJobStatus(jobId: string): Promise<{
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  created_at: string;
  updated_at: string;
}> {
  const result = await this.fetch(`/video/status/${jobId}`);
  return result as any;
}

// Video job results
async getVideoJobResults(jobId: string): Promise<{
  job_id: string;
  results: any;
  created_at: string;
  updated_at: string;
}> {
  const result = await this.fetch(`/video/results/${jobId}`);
  return result as any;
}
```

**Why:** Frontend needs methods to interact with video job endpoints.

**TDD Workflow (MANDATORY):**
1. Write failing tests for submitVideo, getVideoJobStatus, getVideoJobResults
2. Run tests to verify they fail
3. Implement API client methods
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ submitVideo with default pipeline
- ✅ submitVideo with explicit pipeline
- ✅ getVideoJobStatus returns correct structure
- ✅ getVideoJobResults returns correct structure
- ✅ Progress callback fires during upload

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(api-client): add video job methods to API client

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F2: Create VideoUpload Component

**File:** `web-ui/src/components/VideoUpload.tsx` (NEW)

**Content:**
```typescript
import React, { useState } from "react";
import { apiClient } from "../api/client";
import { JobStatus } from "./JobStatus";
import { JobResults } from "./JobResults";

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
      const { job_id } = await apiClient.submitVideo(
        file,
        "ocr_only", // Alpha: Use ocr_only pipeline
        (p) => setProgress(p)
      );
      setJobId(job_id);
    } catch (e: any) {
      setError(e.message ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2>Video Upload</h2>

      <input type="file" accept="video/mp4" onChange={onFileChange} />

      {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}

      {uploading && (
        <div style={{ marginTop: "10px" }}>
          Uploading… {progress.toFixed(0)}%
        </div>
      )}

      <button
        onClick={onUpload}
        disabled={!file || uploading}
        style={{
          marginTop: "10px",
          padding: "10px 20px",
          cursor: file && !uploading ? "pointer" : "not-allowed",
        }}
      >
        Upload
      </button>

      {jobId && (
        <div style={{ marginTop: "20px" }}>
          <div>Job ID: {jobId}</div>
          <JobStatus jobId={jobId} />
        </div>
      )}
    </div>
  );
};
```

**Why:** Dedicated component for video upload, separate from VideoTracker.

**TDD Workflow (MANDATORY):**
1. Write failing tests for VideoUpload component
2. Run tests to verify they fail
3. Implement VideoUpload component
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Component renders without errors
- ✅ File input accepts MP4 files
- ✅ File input rejects non-MP4 files
- ✅ Upload button disabled when no file selected
- ✅ Upload button disabled during upload
- ✅ Upload progress displayed
- ✅ Job ID displayed after upload
- ✅ JobStatus component rendered when jobId exists

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(ui): add VideoUpload component

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F3: Create JobStatus Component

**File:** `web-ui/src/components/JobStatus.tsx` (NEW)

**Content:**
```typescript
import React, { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { JobResults } from "./JobResults";

type Props = {
  jobId: string;
};

type Status = "pending" | "running" | "completed" | "failed";

export const JobStatus: React.FC<Props> = ({ jobId }) => {
  const [status, setStatus] = useState<Status>("pending");
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    const poll = async () => {
      try {
        const s = await apiClient.getVideoJobStatus(jobId);
        setStatus(s.status);

        if (s.status === "completed") {
          const r = await apiClient.getVideoJobResults(jobId);
          setResults(r);
          return;
        }

        if (s.status === "failed") {
          setError("Job failed.");
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
    <div style={{ marginTop: "10px" }}>
      <div>Status: {status}</div>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};
```

**Why:** Polls job status every 2 seconds and displays results when complete.

**TDD Workflow (MANDATORY):**
1. Write failing tests for JobStatus component
2. Run tests to verify they fail
3. Implement JobStatus component
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Component renders without errors
- ✅ Status displayed correctly
- ✅ Polls every 2 seconds
- ✅ Stops polling when job completes
- ✅ Stops polling when job fails
- ✅ JobResults component rendered when results available
- ✅ Error message displayed on failure

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(ui): add JobStatus component

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F4: Create JobResults Component

**File:** `web-ui/src/components/JobResults.tsx` (NEW)

**Content:**
```typescript
import React from "react";

type Props = {
  results: any;
};

export const JobResults: React.FC<Props> = ({ results }) => {
  // v0.9.0-alpha: OCR-only
  const text = results.results?.text ?? "";

  return (
    <div style={{ marginTop: "20px", padding: "20px", border: "1px solid #ccc" }}>
      <h3>Results</h3>
      {text ? (
        <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {text}
        </pre>
      ) : (
        <div>No OCR text available.</div>
      )}
    </div>
  );
};
```

**Why:** Displays OCR results from completed video jobs.

**TDD Workflow (MANDATORY):**
1. Write failing tests for JobResults component
2. Run tests to verify they fail
3. Implement JobResults component
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Component renders without errors
- ✅ OCR text displayed when available
- ✅ "No OCR text available" displayed when text is empty
- ✅ Handles null/undefined results gracefully

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(ui): add JobResults component

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F5: Wire VideoUpload to Main Page

**File:** `web-ui/src/App.tsx`

**Add Import:**
```typescript
import { VideoUpload } from "./components/VideoUpload";
```

**Add to ViewMode:**
```typescript
type ViewMode = "stream" | "upload" | "jobs" | "video-upload";
```

**Add to Render:**
```typescript
{viewMode === "video-upload" && (
  <section>
    <VideoUpload />
  </section>
)}
```

**Add Navigation Button:**
```typescript
<button
  onClick={() => setViewMode("video-upload")}
  style={{
    ...styles.button,
    ...(viewMode === "video-upload" ? styles.buttonActive : {}),
  }}
>
  Video Upload
</button>
```

**Why:** Makes VideoUpload accessible from main UI.

**TDD Workflow (MANDATORY):**
1. Write failing tests for VideoUpload integration
2. Run tests to verify they fail
3. Wire VideoUpload to main page
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ VideoUpload renders when viewMode is "video-upload"
- ✅ Navigation button switches to video-upload view
- ✅ VideoUpload button is highlighted when active

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(ui): wire VideoUpload to main page

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F6: Add Integration Test

**File:** `web-ui/tests/integration/videoUpload.test.ts` (NEW)

**Content:**
```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { VideoUpload } from "../../src/components/VideoUpload";

// Mock API client
vi.mock("../../src/api/client", () => ({
  apiClient: {
    submitVideo: vi.fn(),
    getVideoJobStatus: vi.fn(),
    getVideoJobResults: vi.fn(),
  },
}));

import { apiClient } from "../../src/api/client";

describe("VideoUpload Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should submit video and display job ID", async () => {
    // Mock successful upload
    (apiClient.submitVideo as any).mockResolvedValue({
      job_id: "test-job-123",
    });

    // Mock job status progression
    (apiClient.getVideoJobStatus as any).mockResolvedValue({
      job_id: "test-job-123",
      status: "pending",
      progress: 0,
    });

    // Mock job results
    (apiClient.getVideoJobResults as any).mockResolvedValue({
      job_id: "test-job-123",
      results: { text: "Test OCR text" },
    });

    render(<VideoUpload />);

    // Simulate file selection
    const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
    const file = new File([""], "test.mp4", { type: "video/mp4" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));

    // Click upload button
    const uploadButton = screen.getByText("Upload");
    uploadButton.click();

    // Wait for job ID to appear
    await waitFor(() => {
      expect(screen.getByText(/Job ID: test-job-123/i)).toBeInTheDocument();
    });
  });

  it("should reject non-MP4 files", () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
    const file = new File([""], "test.jpg", { type: "image/jpeg" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));

    expect(screen.getByText(/Only MP4 videos are supported/i)).toBeInTheDocument();
  });
});
```

**Why:** End-to-end test for video upload flow.

**TDD Workflow (MANDATORY):**
1. Write integration test first (this IS the test)
2. Run test to verify it fails
3. Implement VideoUpload, JobStatus, JobResults components
4. Run test to verify it passes
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Test passes
- ✅ Mocks work correctly
- ✅ All components integrated properly

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "test(ui): add integration test for video upload flow

[CI PASS] All workflows validated locally before commit."
```

---

## Phase 3: Beta Release (YOLO + OCR)

### Commit B4: Fix YOLO Unpickling Error (Previously B3)

**Investigation:**
```bash
cd server
ls -lh plugins/yolo-tracker/*.pt

python3 -c "
import torch
model = torch.load('plugins/yolo-tracker/best.pt')
print('Model loaded:', type(model))
"
```

**Possible Fixes:**

**Option A: Replace model file**
```bash
# Download fresh YOLOv8 checkpoint
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
mv yolov8n.pt plugins/yolo-tracker/best.pt
```

**Option B: Rebuild model**
```python
from ultralytics import YOLO
model = YOLO("yolov8n.yaml")
model.save("plugins/yolo-tracker/best.pt")
```

**Option C: Fix PyTorch version mismatch**
```bash
pip install torch==2.0.0
```

**Files Changed:**
- `plugins/yolo-tracker/best.pt` (replaced or fixed)

**Tests:**
- ✅ Model loads without errors
- ✅ Plugin initializes successfully
- ✅ Plugin runs on test image
- ✅ Detections are returned

**Acceptance Criteria:**
```bash
python3 -c "
from plugins.yolo_tracker import YOLOPlugin
plugin = YOLOPlugin()
result = plugin.run(image_bytes=test_image)
print('Detections:', result)
"
→ No errors, detections returned
```

**TDD Workflow (MANDATORY):**
1. Write failing test for YOLO plugin loading
2. Run test to verify it fails
3. Fix YOLO unpickling error
4. Run test to verify it passes
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd server
uv run pytest tests/plugins -v

# Only commit if ALL workflows pass
git add .
git commit -m "fix(yolo): resolve unpickling error in YOLO plugin

[CI PASS] All workflows validated locally before commit."
```

---

### Commit F7: Update JobResults to Display YOLO Detections

**File:** `web-ui/src/components/JobResults.tsx`

**Update Content:**
```typescript
import React from "react";

type Props = {
  results: any;
};

export const JobResults: React.FC<Props> = ({ results }) => {
  const { detections, text } = results.results || {};

  return (
    <div style={{ marginTop: "20px", padding: "20px", border: "1px solid #ccc" }}>
      <h3>Results</h3>

      {detections && detections.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h4>Object Detections</h4>
          {detections.map((det: any, idx: number) => (
            <div key={idx} style={{ marginBottom: "10px", padding: "10px", border: "1px solid #eee" }}>
              <div><strong>Label:</strong> {det.label}</div>
              <div><strong>Confidence:</strong> {(det.confidence * 100).toFixed(1)}%</div>
              <div><strong>Box:</strong> [{det.bbox.join(", ")}]</div>
            </div>
          ))}
        </div>
      )}

      {text && (
        <div>
          <h4>OCR Text</h4>
          <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {text}
          </pre>
        </div>
      )}

      {!detections && !text && (
        <div>No results available.</div>
      )}
    </div>
  );
};
```

**Why:** Display YOLO detections in addition to OCR text.

**TDD Workflow (MANDATORY):**
1. Write failing tests for YOLO detection display
2. Run tests to verify they fail
3. Update JobResults component to show detections
4. Run tests to verify they pass
5. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
6. Commit only if all workflows pass

**Tests:**
- ✅ Detections render correctly
- ✅ OCR text renders correctly
- ✅ Empty detections handled gracefully
- ✅ Empty text handled gracefully

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

cd web-ui
npm run type-check
npm run lint
npm run test -- --run

# Only commit if ALL workflows pass
git add .
git commit -m "feat(ui): update JobResults to display YOLO detections

[CI PASS] All workflows validated locally before commit."
```

---

## Phase 4: Documentation & Release

### Commit D1: Update Release Notes (Previously D1)

**File:** `docs/releases/v0.9.0/RELEASE_NOTES.md` (NEW)

**Content:**
```markdown
# v0.9.0 Release Notes

## v0.9.0-alpha (OCR-Only Pipeline)

### New Features
- Video upload via Web UI
- Async video processing with job tracking
- OCR-only pipeline for text extraction
- Real-time upload progress
- Job status polling
- OCR results display

### Backend Changes
- Made `pipeline_id` optional in `/v1/video/submit` (defaults to "ocr_only")
- Added `ocr_only` pipeline definition
- Updated API documentation

### Frontend Changes
- New VideoUpload component
- New JobStatus component
- New JobResults component
- Added video API methods to API client
- Integrated VideoUpload into main page

### Known Limitations
- YOLO object detection temporarily disabled (unpickling error)
- Only OCR text extraction available
- Will be addressed in v0.9.0-beta

---

## v0.9.0-beta (YOLO + OCR Pipeline)

### New Features
- YOLO object detection re-enabled
- Full YOLO + OCR pipeline
- Object detection display in results

### Bug Fixes
- Fixed YOLO unpickling error
- Updated JobResults to show detections

### Breaking Changes
- None (backward compatible with alpha)

---

## Migration Guide

### From v0.8.1 to v0.9.0-alpha
No migration required. Simply upgrade and use the new video upload feature.

### From v0.9.0-alpha to v0.9.0-beta
No migration required. YOLO will be automatically enabled when you upgrade.
```

**Why:** Document changes for users and developers.

**TDD Workflow (MANDATORY):**
1. Write test to verify documentation is accurate
2. Run test to verify it passes
3. Update release notes
4. Run ALL 5 CI workflows (see Pre-Commit Workflow section)
5. Commit only if all workflows pass

**CI Validation (MANDATORY - All 5 Workflows):**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

# Verify docs are accurate
cd server
uv run pytest tests/api/ -v

# Only commit if ALL workflows pass
git add .
git commit -m "docs(release): add v0.9.0 release notes

[CI PASS] All workflows validated locally before commit."
```

---

### Commit D2: Tag v0.9.0-alpha

**PREREQUISITE:** All previous commits (B1-B3, F1-F6, D1) must have passed ALL 5 CI workflows.

```bash
cd /home/rogermt/forgesyte
git tag -a v0.9.0-alpha -m "v0.9.0-alpha: Video upload with OCR-only pipeline

All commits passed (14 total):
- vocabulary_validation.yml
- video_batch_validation.yml
- governance-ci.yml
- execution-ci.yml
- ci.yml"
git push origin v0.9.0-alpha
```

**Why:** Mark alpha release milestone.

---

### Commit D3: Tag v0.9.0-beta

**PREREQUISITE:** All previous commits (B1-B4, F1-F7, D1-D2) must have passed ALL 5 CI workflows.

```bash
cd /home/rogermt/forgesyte
git tag -a v0.9.0-beta -m "v0.9.0-beta: Video upload with YOLO + OCR pipeline

All commits passed (14 total):
- vocabulary_validation.yml
- video_batch_validation.yml
- governance-ci.yml
- execution-ci.yml
- ci.yml"
git push origin v0.9.0-beta
```

**Why:** Mark beta release milestone.

---

## Summary of Commits

### Backend (3 commits)
1. B1: Make `pipeline_id` optional in `/v1/video/submit`
2. B2: Create `ocr_only` pipeline definition
3. B3: Update API documentation

### Frontend (6 commits)
1. F1: Add video API methods to API client
2. F2: Create VideoUpload component
3. F3: Create JobStatus component
4. F4: Create JobResults component
5. F5: Wire VideoUpload to main page
6. F6: Add integration test

### Beta (2 commits)
1. B4: Fix YOLO unpickling error
2. F7: Update JobResults to display YOLO detections

### Documentation & Release (3 commits)
1. D1: Update release notes
2. D2: Tag v0.9.0-alpha
3. D3: Tag v0.9.0-beta

**Total: 14 commits** (vs 20+ in original plan)

**Note:** Removed unnecessary PipelineExecutor service. Existing `VideoFilePipelineService` and `DagPipelineService` already handle pipeline execution correctly.

### 🚨 CI Requirements for Every Commit

**Before EVERY commit, developers MUST run ALL 5 workflows:**
```bash
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml
```

**Only commit if ALL workflows pass.**

**Every commit message MUST include:**
```
[CI PASS] All workflows validated locally before commit.
```

---

## Pre-Commit Workflow (MANDATORY - NO EXCEPTIONS)

### 🎯 **Rule: Developers MUST run ALL CI workflows locally BEFORE committing.**

This is a **hard requirement** for v0.9.0 and all future releases.

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
- **All vocabulary rules pass**
- **All governance rules pass**
- **All execution rules pass**
- **All video batch rules pass**
- **Repo is fully GREEN**

### Before Every Commit - MANDATORY Steps

All developers MUST run the following commands **in order** before committing:

```bash
# Step 1: Run vocabulary validation
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml

# Step 2: Run video batch validation
act -W .github/workflows/video_batch_validation.yml

# Step 3: Run governance CI
act -W .github/workflows/governance-ci.yml

# Step 4: Run execution CI
act -W .github/workflows/execution-ci.yml

# Step 5: Run full CI
act -W .github/workflows/ci.yml
```

### Fix Everything Before Committing

No commit is allowed until:

- All tests pass
- All linters pass
- All vocabulary rules pass
- All governance rules pass
- All execution rules pass
- All video batch rules pass

### Commit Message Format

Every commit MUST include:

```
[CI PASS] All workflows validated locally before commit.
```

**Example:**
```
feat(api): make video submit pipeline_id optional with default ocr_only

[CI PASS] All workflows validated locally before commit.
```

If CI is not green, the commit is **invalid**.

---

## TDD Requirements (MANDATORY)

### Test-Driven Development Workflow

For any feature or bug fix, follow Test-Driven Development:

1. **Write failing tests first** - Define expected behavior
2. **Run tests to verify they fail** - Confirm tests catch the issue
3. **Implement code** - Write minimal code to make tests pass
4. **Run tests to verify they pass** - Confirm implementation works
5. **Run ALL CI workflows** - Ensure code quality
6. **Commit** - Only after all above pass

### Example TDD Workflow

```bash
# 1. Write failing test
# 2. Run specific test to verify it fails
cd server
uv run pytest tests/api/test_video_submit.py::test_submit_video_without_pipeline_id -v

# 3. Implement code to fix the test

# 4. Run test to verify it passes
uv run pytest tests/api/test_video_submit.py::test_submit_video_without_pipeline_id -v

# 5. Run ALL CI workflows (MANDATORY)
cd /home/rogermt/forgesyte
act -W .github/workflows/vocabulary_validation.yml
act -W .github/workflows/video_batch_validation.yml
act -W .github/workflows/governance-ci.yml
act -W .github/workflows/execution-ci.yml
act -W .github/workflows/ci.yml

# 6. Commit (only if all workflows pass)
git add .
git commit -m "feat(api): make video submit pipeline_id optional with default ocr_only

[CI PASS] All workflows validated locally before commit."
```

---

## Success Criteria

### v0.9.0-alpha
- ✅ User can upload MP4 video via Web UI
- ✅ Video is processed asynchronously
- ✅ User can monitor job status
- ✅ User can view OCR results
- ✅ All tests pass
- ✅ All CI workflows pass
- ✅ No regressions in existing functionality

### v0.9.0-beta
- ✅ YOLO object detection works
- ✅ User can view YOLO detections
- ✅ User can view OCR text
- ✅ All tests pass
- ✅ All CI workflows pass
- ✅ No regressions in existing functionality

---

## Risk Assessment

### Low Risk
- Making `pipeline_id` optional (backward compatible)
- Adding new frontend components (isolated changes)
- Adding new API client methods (isolated changes)

### Medium Risk
- Creating `ocr_only` pipeline (needs testing)
- Fixing YOLO unpickling error (unknown root cause)

### Mitigation
- Comprehensive testing at each commit
- CI workflow validation before each commit
- Gradual rollout (alpha before beta)
- Clear rollback plan (git revert)

---

## Rollback Plan

If issues arise:

1. **Backend Issues:**
   ```bash
   git revert <commit-hash>
   ```

2. **Frontend Issues:**
   ```bash
   git revert <commit-hash>
   ```

3. **Full Rollback:**
   ```bash
   git checkout v0.8.1
   ```

---

## Next Steps

1. Review this plan with team
2. Assign commits to developers
3. Create feature branches
4. Implement commits in order
5. Run CI validation before each commit
6. Tag releases when complete

---

## Questions for Team

1. **YOLO Fix:** Do we have access to the original YOLO model training environment?
2. **Testing:** Do we have test MP4 files with known OCR text?
3. **Deployment:** Should v0.9.0-alpha be deployed to staging before beta?
4. **Timeline:** What is the target release date for alpha and beta?

---

**END OF DEVELOPMENT PLAN**