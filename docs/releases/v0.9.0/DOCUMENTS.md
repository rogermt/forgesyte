# 📦 v0.9.0 COMPLETE DOCUMENTATION — OPTION A (CORRECTED) — FINAL

---

# 📋 1. OVERVIEW — v0.9.0

## **v0.9.0 — Video Upload Feature (Option A: Use Existing Infrastructure)**

### **Purpose**
v0.9.0 delivers **video upload functionality to the Web UI** by **completing the Phase 16 async job system using existing pipeline infrastructure**. This is a **focused, two-part release** that replaces the broken Phase 17 delivery.

### **What Came Before**

| Version | Name | Status | Summary |
|---------|------|--------|---------|
| v0.8.0 | Phase 15 | ✅ Stable | Synchronous batch video processing (YOLO + OCR pipeline) |
| v0.8.1 | Phase 16 | ⚠️ Partial | Async job system (incomplete, no frontend wiring) |
| ❌ Phase 17 | Phase 17 | ❌ Rejected | Broken delivery with regressions, experimental code, architectural drift |

### **What Phase 16 Left Incomplete**
- ⚠️ `/v1/video/submit` exists but requires `pipeline_id` parameter
- ⚠️ No default pipeline configured
- ⚠️ YOLO plugin has unpickling error ("unpickling stack underflow")
- ⚠️ No frontend wiring for video upload

### **What Already Works (Phase 16)**
- ✅ `VideoFilePipelineService` (from Phase 15)
- ✅ `DagPipelineService` (JSON-driven pipeline execution)
- ✅ Plugin registry (discovers and loads plugins)
- ✅ Worker process (dequeues and executes jobs)
- ✅ Job database (stores job state and results)
- ✅ Object storage (stores uploaded videos)

### **What v0.9.0 Delivers**

**v0.9.0 has TWO release stages:**

#### **v0.9.0-alpha (OCR-Only Pipeline)**
✅ Fix `/v1/video/submit` to work without `pipeline_id`  
✅ Add `ocr_only` pipeline definition (JSON)  
✅ Temporarily disable YOLO (due to unpickling bug)  
✅ Wire video upload UI to backend  
✅ End-to-end video upload → OCR results working  

#### **v0.9.0-beta (Full YOLO + OCR Pipeline)**
✅ Fix YOLO unpickling error  
✅ Add `yolo_ocr` pipeline definition (JSON)  
✅ Display YOLO detections in UI  
✅ Full video analysis working  

### **What v0.9.0 Does NOT Change**
- ✅ Plugin selector remains intact
- ✅ Tool selector remains intact
- ✅ Image upload remains intact
- ✅ `VideoFilePipelineService` unchanged (reused)
- ✅ `DagPipelineService` unchanged (reused)
- ✅ Phase 16 job queue/worker unchanged
- ✅ No experimental code added
- ✅ No architectural changes
- ✅ No breaking changes

### **Key Principle**
> **v0.9.0 = Use Existing Infrastructure + Add Video Upload UI. Zero New Services. Zero Regressions.**

---

# 🏗️ 2. HIGH-LEVEL DESIGN (HLD) — v0.9.0

## **System Architecture (v0.9.0)**

```
┌─────────────────────────────────────────────────────────────┐
│                        WEB UI                                │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (Unchanged)          NEW (v0.9.0)                  │
│  - Plugin Selector             - Video Upload Form           │
│  - Tool Selector               - Job ID Display              │
│  - Image Upload                - Job Status Display          │
│  - Pipeline Selection          - Job Results Display         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (Unchanged)          FIXED (v0.9.0-alpha)          │
│  /v1/image/analyze            /v1/video/submit ← FIXED       │
│  /v1/plugins                  (pipeline_id now optional)     │
│  /v1/jobs                                                    │
│                                                               │
│  UNCHANGED (Phase 16)                                        │
│  /v1/video/status/{job_id}                                   │
│  /v1/video/results/{job_id}                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER (REUSED)                   │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (Phase 16)           NEW (v0.9.0)                  │
│  Job Manager                   Pipeline Definitions          │
│  - Job Creation                - ocr_only.json (alpha)       │
│  - Status Tracking             - yolo_ocr.json (beta)        │
│  - Result Storage              - JSON-driven, declarative    │
│                                                               │
│  VideoFilePipelineService      DagPipelineService            │
│  (Phase 15 - REUSED)           (Phase 16 - REUSED)           │
│  - Opens MP4 files             - Loads pipeline JSON         │
│  - Extracts frames             - Resolves plugin names       │
│  - Calls DAG pipeline          - Executes plugin calls       │
│  - Aggregates results          - Returns results             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               EXECUTION LAYER (UNCHANGED)                    │
├─────────────────────────────────────────────────────────────┤
│  Worker Process (Phase 16)    Plugin Registry               │
│  - Dequeue Jobs               - ocr plugin                   │
│  - Call VideoFilePipelineService - yolo-tracker plugin      │
│  - Save Results               - Plugin discovery             │
│  - Update Status                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               PERSISTENCE LAYER (Unchanged)                  │
├─────────────────────────────────────────────────────────────┤
│  Database (Phase 16)          Object Storage (Phase 16)      │
│  - Job State                  - Video Files                  │
│  - Job Results                - Image Files                  │
│                                                               │
│  Queue (Phase 16)                                            │
│  - Job Queue (Redis/In-Memory)                               │
└─────────────────────────────────────────────────────────────┘
```

## **What's Changed in v0.9.0**

### **Backend Changes (v0.9.0-alpha)**

#### **1. Fixed: `/v1/video/submit` Endpoint**
**Before (Phase 16):**
```python
@router.post("/v1/video/submit")
async def submit_video(file: UploadFile, pipeline_id: str):  # REQUIRED
    ...
```

**After (v0.9.0-alpha):**
```python
DEFAULT_VIDEO_PIPELINE = "ocr_only"

@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    pipeline_id: str = Query(default=DEFAULT_VIDEO_PIPELINE)  # OPTIONAL
):
    video_path = await save_uploaded_file(file)
    job = await job_manager.create_job(
        input_path=video_path,
        pipeline_id=pipeline_id,
    )
    return {"job_id": job.id}
```

**Impact:**
- ✅ Frontend can submit videos without specifying `pipeline_id`
- ✅ Default pipeline is `ocr_only` (safe, working)
- ✅ Beta will add `yolo_ocr` option

---

#### **2. New: Pipeline Definition Files (JSON)**
**Location:** `/server/pipelines/`

**File:** `ocr_only.json` (v0.9.0-alpha)
```json
{
  "id": "ocr_only",
  "name": "OCR Only Video Pipeline",
  "description": "Extract text from video frames using OCR",
  "nodes": [
    {
      "id": "ocr",
      "plugin": "ocr",
      "type": "frame_processor"
    }
  ]
}
```

**File:** `yolo_ocr.json` (v0.9.0-beta)
```json
{
  "id": "yolo_ocr",
  "name": "YOLO + OCR Video Pipeline",
  "description": "Detect objects and extract text from video frames",
  "nodes": [
    {
      "id": "yolo",
      "plugin": "yolo-tracker",
      "type": "frame_processor"
    },
    {
      "id": "ocr",
      "plugin": "ocr",
      "type": "frame_processor"
    }
  ]
}
```

**Why JSON:**
- Declarative (plugin names only, no implementation)
- Easy to add new pipelines without code changes
- Aligns with existing `DagPipelineService` architecture
- No new "PipelineExecutor" service needed

---

#### **3. Updated: Worker Uses Existing Services**
**Location:** `/server/workers/video_worker.py`

**Before (Phase 16 - incomplete):**
```python
async def process_job(job_id: str):
    job = job_repo.get(job_id)
    # ... direct plugin calls (incomplete)
```

**After (v0.9.0-alpha):**
```python
from server.services.video_file_pipeline_service import VideoFilePipelineService

async def process_job(job_id: str):
    job = job_repo.get(job_id)
    
    try:
        # Ensure pipeline_id is set (backward compatibility)
        pipeline_id = getattr(job, "pipeline_id", DEFAULT_VIDEO_PIPELINE)
        
        # Use existing VideoFilePipelineService
        result = await VideoFilePipelineService.run_on_file(
            pipeline_id=pipeline_id,
            file_path=job.input_path,
        )
        
        job.result = result
        job.status = "done"
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
    finally:
        job_repo.save(job)
```

**Impact:**
- ✅ Reuses existing `VideoFilePipelineService` (no new code)
- ✅ Reuses existing `DagPipelineService` (no new code)
- ✅ No "PipelineExecutor" service needed
- ✅ Worker is simpler and more maintainable

---

#### **4. How It Works (Call Stack)**

**End-to-end flow:**

1. **User uploads video** → `/v1/video/submit`
2. **API creates job** → saves to DB with `pipeline_id = "ocr_only"`
3. **Worker picks up job**
4. **Worker calls:**
   ```python
   VideoFilePipelineService.run_on_file(
       pipeline_id="ocr_only",
       file_path="/path/to/video.mp4"
   )
   ```
5. **VideoFilePipelineService:**
   - Opens MP4 file
   - Extracts frames
   - For each frame, calls:
     ```python
     DagPipelineService.execute(
         pipeline_id="ocr_only",
         frame_data=frame
     )
     ```
6. **DagPipelineService:**
   - Loads `ocr_only.json`
   - Resolves plugin name `"ocr"` → `ocr_plugin` instance
   - Calls:
     ```python
     ocr_plugin.run(image_bytes=frame)
     ```
   - Returns OCR result
7. **VideoFilePipelineService:**
   - Aggregates results from all frames
   - Returns:
     ```json
     {
       "results": [
         {"frame_index": 0, "result": {"text": "...", ...}},
         {"frame_index": 1, "result": {"text": "...", ...}},
         ...
       ]
     }
     ```
8. **Worker:**
   - Saves result to `job.result`
   - Sets `job.status = "done"`

**No new services. Just wiring existing ones.**

---

### **Backend Changes (v0.9.0-beta)**

#### **5. Fixed: YOLO Unpickling Error**
**Root cause:** Corrupted or incompatible model checkpoint

**Fix:** Replace model file with fresh YOLOv8 checkpoint

**Verification:**
```bash
python3 -c "
import torch
model = torch.load('plugins/yolo-tracker/best.pt')
print('✅ Model loads successfully')
"
```

---

#### **6. Added: `yolo_ocr.json` Pipeline Definition**
See JSON above. No code changes needed in services — just add the file.

---

### **Frontend Changes (All in v0.9.0-alpha)**

#### **1. New: Video Upload UI Component**
- **Location:** `/web-ui/components/VideoUpload.tsx`
- **Responsibilities:**
  - Display file upload form
  - Validate MP4 format
  - Submit video to `/v1/video/submit`
  - Display returned job_id
  - Handle upload progress
  - Handle errors

#### **2. New: Job Status Display Component**
- **Location:** `/web-ui/components/JobStatus.tsx`
- **Responsibilities:**
  - Poll `/v1/video/status/{job_id}` every 2 seconds
  - Display status (pending/running/completed/failed)
  - Display progress percentage
  - Stop polling when job completes or fails

#### **3. New: Job Results Display Component**
- **Location:** `/web-ui/components/JobResults.tsx`
- **Responsibilities:**
  - Fetch `/v1/video/results/{job_id}` when complete
  - Display OCR text results (alpha)
  - Display YOLO detections (beta)
  - Display frame-by-frame analysis
  - Format results for readability

---

## **Data Flow (v0.9.0)**

### **v0.9.0-alpha Flow (OCR Only)**

```
User → Web UI Video Upload Form
  → Select MP4 file
  → Click "Upload"
  → POST /v1/video/submit
      (no pipeline_id → defaults to "ocr_only")
    → Job Manager
      → Validate MP4
      → Save to Object Storage
      → Create Job (status: pending, pipeline_id: "ocr_only")
      → Enqueue job_id
      → Return job_id
  
  → UI displays job_id
  → UI polls GET /v1/video/status/{job_id} every 2s
  
  → Worker Process
    → Dequeue job_id
    → Load job metadata
    → Call VideoFilePipelineService.run_on_file("ocr_only", video_path)
      → Extract frames
      → For each frame:
        → Call DagPipelineService.execute("ocr_only", frame)
          → Load ocr_only.json
          → Resolve plugin "ocr"
          → Call ocr_plugin.run(frame)
          → Return OCR result
      → Aggregate frame results
      → Return full result
    → Save results to DB
    → Update job status: completed
  
  → UI detects status: completed
  → UI calls GET /v1/video/results/{job_id}
  → UI displays OCR text results
```

### **v0.9.0-beta Flow (YOLO + OCR)**

```
(Same as alpha, but:)
  
  → User optionally selects pipeline_id: "yolo_ocr"
  
  → Worker calls VideoFilePipelineService.run_on_file("yolo_ocr", video_path)
    → DagPipelineService loads yolo_ocr.json
    → For each frame:
      → Call yolo_plugin.run(frame) ← NOW WORKING
      → Call ocr_plugin.run(frame)
      → Return combined result
  
  → UI displays:
      - YOLO bounding boxes
      - Object labels
      - Confidence scores
      - OCR text
```

---

# 📝 3. FUNCTIONAL REQUIREMENTS — v0.9.0

## **FR-1: Video Upload Form**
**Description:** Web UI must display a video upload form.

**Acceptance Criteria:**
- ✅ Form accepts MP4 files
- ✅ Form validates file format client-side
- ✅ Form displays upload progress
- ✅ Form handles upload errors gracefully

---

## **FR-2: Video Submission (Fixed in Alpha)**
**Description:** Web UI must submit video to `/v1/video/submit` without requiring `pipeline_id`.

**Acceptance Criteria:**
- ✅ Video is sent as multipart/form-data
- ✅ `pipeline_id` is optional (defaults to `ocr_only`)
- ✅ Response includes job_id
- ✅ job_id is displayed to user

---

## **FR-3: Job Status Display**
**Description:** Web UI must display job status.

**Acceptance Criteria:**
- ✅ Status is polled every 2 seconds
- ✅ Status shows: pending, running, completed, failed
- ✅ Progress percentage is displayed (if available)
- ✅ Polling stops when job completes or fails

---

## **FR-4: Job Results Display**
**Description:** Web UI must display job results when complete.

**Acceptance Criteria (Alpha):**
- ✅ Results include OCR text
- ✅ OCR text is formatted for readability
- ✅ Frame-by-frame results are accessible

**Acceptance Criteria (Beta):**
- ✅ Results include YOLO detections
- ✅ Detections show bounding boxes
- ✅ Detections show object labels
- ✅ Detections show confidence scores
- ✅ Results include OCR text
- ✅ Results include frame-by-frame data

---

## **FR-5: Error Handling**
**Description:** Web UI must handle all error cases.

**Acceptance Criteria:**
- ✅ Invalid file format shows error message
- ✅ Upload failure shows error message
- ✅ Job failure shows error message
- ✅ Network errors show error message

---

## **FR-6: No Breaking Changes**
**Description:** Existing UI functionality must remain intact.

**Acceptance Criteria:**
- ✅ Plugin selector still works
- ✅ Tool selector still works
- ✅ Image upload still works
- ✅ All existing tests pass

---

## **FR-7: Backend Uses Existing Services (New)**
**Description:** Backend must use existing `VideoFilePipelineService` and `DagPipelineService`.

**Acceptance Criteria (Alpha):**
- ✅ Worker calls `VideoFilePipelineService.run_on_file()`
- ✅ `VideoFilePipelineService` calls `DagPipelineService.execute()`
- ✅ `DagPipelineService` loads `ocr_only.json`
- ✅ No new "PipelineExecutor" service is created

**Acceptance Criteria (Beta):**
- ✅ `DagPipelineService` loads `yolo_ocr.json`
- ✅ YOLO + OCR both execute via existing plugin registry

---

## **FR-8: Pipeline Definitions Are JSON (New)**
**Description:** Pipelines must be defined in JSON files, not Python code.

**Acceptance Criteria:**
- ✅ `ocr_only.json` exists and is valid
- ✅ `yolo_ocr.json` exists and is valid (beta)
- ✅ JSON follows existing DAG pipeline schema
- ✅ No hardcoded plugin calls in worker

---

## **FR-9: YOLO Fix (Beta Only)**
**Description:** YOLO unpickling error must be resolved.

**Acceptance Criteria:**
- ✅ YOLO model loads without errors
- ✅ YOLO plugin runs successfully
- ✅ Detections are returned
- ✅ No "unpickling stack underflow" errors

---

# 📝 4. NON-FUNCTIONAL REQUIREMENTS — v0.9.0

*(Unchanged from previous version)*

---

# 👤 5. USER STORIES — v0.9.0

*(Unchanged from previous version)*

---

# 🛠️ 6. DEVELOPMENT PLAN — v0.9.0 (CORRECTED)

## **Guiding Principles**
1. **Use existing infrastructure** (no new services)
2. **Backend before frontend** (establish stable API first)
3. **One component per commit**
4. **Every commit is testable**
5. **Every commit is reviewable**
6. **No breaking changes**
7. **No regressions**
8. **Alpha first, beta second**

---

## **PHASE: v0.9.0-alpha (OCR-Only Pipeline)**

### **BACKEND COMMITS (5 commits)**

---

## **Commit B1: Make pipeline_id Optional in `/v1/video/submit`**

**What:** Modify endpoint to accept optional `pipeline_id` with default value.

**Why:** Frontend can submit videos without knowing valid pipeline IDs.

**Files Changed:**
- `/server/api/routes/video.py`

**Code:**
```python
DEFAULT_VIDEO_PIPELINE = "ocr_only"

@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    pipeline_id: str = Query(default=DEFAULT_VIDEO_PIPELINE)
):
    video_path = await save_uploaded_file(file)
    job = await job_manager.create_job(
        input_path=video_path,
        pipeline_id=pipeline_id,
    )
    return {"job_id": job.id}
```

**Tests:**
- ✅ Upload without `pipeline_id` → uses default
- ✅ Upload with explicit `pipeline_id` → uses specified
- ✅ Invalid `pipeline_id` → returns 400 error
- ✅ Existing Phase 16 tests still pass

**Acceptance Criteria:**
```bash
curl -i -F "file=@video.mp4" http://localhost:8000/v1/video/submit
→ 200 OK
→ {"job_id": "..."}
```

---

## **Commit B2: Add `ocr_only.json` Pipeline Definition**

**What:** Create JSON pipeline definition for OCR-only processing.

**Why:** Define pipeline declaratively (no Python code).

**Files Added:**
- `/server/pipelines/ocr_only.json`

**Content:**
```json
{
  "id": "ocr_only",
  "name": "OCR Only Video Pipeline",
  "description": "Extract text from video frames using OCR",
  "nodes": [
    {
      "id": "ocr",
      "plugin": "ocr",
      "type": "frame_processor"
    }
  ]
}
```

**Tests:**
- ✅ JSON is valid
- ✅ `DagPipelineService` can load it
- ✅ Plugin name `"ocr"` resolves to OCR plugin

**Acceptance Criteria:**
- ✅ File exists and validates against schema
- ✅ Pipeline loads without errors
- ✅ No Python code changes needed

---

## **Commit B3: Wire Worker to Use Existing VideoFilePipelineService**

**What:** Update worker to call `VideoFilePipelineService.run_on_file()`.

**Why:** Reuse existing infrastructure; no new services.

**Files Changed:**
- `/server/workers/video_worker.py`

**Code:**
```python
from server.services.video_file_pipeline_service import VideoFilePipelineService

DEFAULT_VIDEO_PIPELINE = "ocr_only"

async def process_job(job_id: str):
    job = job_repo.get(job_id)
    
    try:
        pipeline_id = getattr(job, "pipeline_id", DEFAULT_VIDEO_PIPELINE)
        
        result = await VideoFilePipelineService.run_on_file(
            pipeline_id=pipeline_id,
            file_path=job.input_path,
        )
        
        job.result = result
        job.status = "done"
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
    finally:
        job_repo.save(job)
```

**Tests:**
- ✅ Worker dequeues job
- ✅ Worker calls `VideoFilePipelineService.run_on_file()`
- ✅ Worker saves results
- ✅ Worker updates status
- ✅ Worker handles errors

**Acceptance Criteria:**
- ✅ End-to-end: submit → worker → results works
- ✅ Existing Phase 16 worker tests pass
- ✅ No new "PipelineExecutor" service exists

---

## **Commit B4: Add Backend Integration Test**

**What:** Add test for full video submission → processing → results flow.

**Why:** Ensure backend is stable before frontend work.

**Files Added:**
- `/server/tests/integration/test_video_pipeline_alpha.py`

**Code:**
```python
import pytest
from fastapi.testclient import TestClient

def test_video_submission_ocr_only():
    # Upload video
    with open("test_video.mp4", "rb") as f:
        response = client.post("/v1/video/submit", files={"file": f})
    
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Wait for completion (or mock worker)
    # ...
    
    # Get results
    results = client.get(f"/v1/video/results/{job_id}")
    assert results.status_code == 200
    data = results.json()
    
    assert "results" in data
    assert len(data["results"]) > 0
    assert "text" in data["results"][0]["result"]
```

**Tests:**
- ✅ Full flow works end-to-end
- ✅ OCR results are returned
- ✅ Result format matches Phase 15 format

**Acceptance Criteria:**
- ✅ Test passes
- ✅ No manual intervention needed
- ✅ Repeatable

---

## **Commit B5: Update API Documentation**

**What:** Document changes to `/v1/video/submit` endpoint.

**Why:** Developers need to know API has changed.

**Files Changed:**
- `/docs/api/video-endpoints.md`

**Content:**
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
curl -F "file=@video.mp4" http://localhost:8000/v1/video/submit
```

### Backend Implementation
Uses existing `VideoFilePipelineService` and `DagPipelineService`.
No new services. Pipelines defined in JSON files under `/server/pipelines/`.
```

**Tests:**
- ✅ Documentation is accurate
- ✅ Examples work

**Acceptance Criteria:**
- ✅ Docs updated
- ✅ Changelog updated

---

### **FRONTEND COMMITS (12 commits - UNCHANGED)**

*(Frontend commits 1-12 remain identical to original plan)*

**Commit F1:** VideoUpload component skeleton  
**Commit F2:** File upload form  
**Commit F3:** Client-side validation  
**Commit F4:** Wire to `/v1/video/submit`  
**Commit F5:** Display job_id  
**Commit F6:** JobStatus component  
**Commit F7:** Status polling  
**Commit F8:** JobResults component  
**Commit F9:** Fetch and display results  
**Commit F10:** Upload progress indicator  
**Commit F11:** Error handling UI  
**Commit F12:** Wire to main page  

---

### **INTEGRATION & RELEASE (3 commits)**

**Commit 13:** Integration tests  
**Commit 14:** Documentation update  
**Commit 15:** Tag `v0.9.0-alpha`

---

## **PHASE: v0.9.0-beta (YOLO + OCR Pipeline)**

### **BACKEND COMMITS (2 commits)**

---

## **Commit B6: Fix YOLO Unpickling Error**

**What:** Resolve "unpickling stack underflow" in YOLO plugin.

**Why:** Enable object detection.

**Fix:**
```bash
# Download fresh YOLOv8 checkpoint
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
mv yolov8n.pt plugins/yolo-tracker/best.pt
```

**Files Changed:**
- `/plugins/yolo-tracker/best.pt` (replaced)

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

---

## **Commit B7: Add `yolo_ocr.json` Pipeline Definition**

**What:** Create JSON pipeline definition for YOLO + OCR processing.

**Why:** Enable full video analysis.

**Files Added:**
- `/server/pipelines/yolo_ocr.json`

**Content:**
```json
{
  "id": "yolo_ocr",
  "name": "YOLO + OCR Video Pipeline",
  "description": "Detect objects and extract text from video frames",
  "nodes": [
    {
      "id": "yolo",
      "plugin": "yolo-tracker",
      "type": "frame_processor"
    },
    {
      "id": "ocr",
      "plugin": "ocr",
      "type": "frame_processor"
    }
  ]
}
```

**Tests:**
- ✅ JSON is valid
- ✅ `DagPipelineService` can load it
- ✅ Both plugins execute correctly

**Acceptance Criteria:**
- ✅ File exists and validates
- ✅ Pipeline runs both YOLO and OCR
- ✅ No Python code changes needed

---

### **FRONTEND COMMITS (1 commit)**

---

## **Commit F13: Display YOLO Detections in Results**

**What:** Update JobResults component to display bounding boxes and labels.

**Why:** Users need to see object detections.

**Files Changed:**
- `/web-ui/components/JobResults.tsx`

**Code:**
```typescript
function JobResults({ results }: { results: any }) {
  return (
    <div>
      {results.results?.map((frameResult, idx) => (
        <div key={idx}>
          <h4>Frame {frameResult.frame_index}</h4>
          
          {frameResult.result.detections && (
            <div>
              <h5>Detections</h5>
              {frameResult.result.detections.map((det, i) => (
                <div key={i}>
                  <span>{det.label}</span>
                  <span>{(det.confidence * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}
          
          {frameResult.result.text && (
            <div>
              <h5>OCR Text</h5>
              <pre>{frameResult.result.text}</pre>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
```

**Tests:**
- ✅ Detections render correctly
- ✅ OCR text renders correctly
- ✅ Empty detections handled gracefully

**Acceptance Criteria:**
- ✅ User sees bounding boxes
- ✅ User sees labels and confidence
- ✅ User sees OCR text
- ✅ UI is responsive

---

### **INTEGRATION & RELEASE (3 commits)**

**Commit 14:** Integration tests for YOLO + OCR  
**Commit 15:** Documentation update  
**Commit 16:** Tag `v0.9.0-beta`

---

### **FINAL RELEASE (2 commits)**

**Commit 17:** Final integration tests (alpha + beta)  
**Commit 18:** Tag `v0.9.0` (final stable release)

---

# 🔄 7. PULL REQUEST TEMPLATE — v0.9.0

*(Unchanged from previous version)*

---

# ✅ SUMMARY OF CHANGES FROM PREVIOUS VERSION

## **What's CORRECTED:**

### **1. Removed PipelineExecutor Service**
- ❌ **REMOVED:** `PipelineExecutor` service (unnecessary)
- ✅ **USE:** Existing `VideoFilePipelineService` + `DagPipelineService`

### **2. Changed to JSON Pipeline Definitions**
- ❌ **REMOVED:** Hardcoded Python pipeline logic
- ✅ **USE:** JSON files (`ocr_only.json`, `yolo_ocr.json`)

### **3. Simplified Worker**
- **Before:** Worker created new `PipelineExecutor` and called methods
- **After:** Worker calls existing `VideoFilePipelineService.run_on_file()`

### **4. Updated HLD Diagram**
- Removed "Pipeline Executor" box
- Added "Pipeline Definitions (JSON)" box
- Clarified "REUSED" vs "NEW"

### **5. Updated Development Plan**
- **Commit B2:** Now adds JSON file, not Python service
- **Commit B3:** Now wires to existing service, not new one
- **Commit B7:** Now adds JSON file, not Python method

### **6. Updated Functional Requirements**
- **FR-7:** Now states "use existing services"
- **FR-8:** New requirement for JSON pipeline definitions

---

## **What's UNCHANGED:**

- ✅ All frontend commits (identical)
- ✅ All user stories
- ✅ All non-functional requirements
- ✅ Zero breaking changes principle
- ✅ Zero regressions principle
- ✅ Phased delivery (alpha → beta)

---

# 🎯 FINAL COMMIT COUNT

| Phase | Backend | Frontend | Integration | Total |
|-------|---------|----------|-------------|-------|
| **Alpha** | 5 | 12 | 3 | **20** |
| **Beta** | 2 | 1 | 3 | **6** |
| **Final** | 0 | 0 | 2 | **2** |
| **TOTAL** | **7** | **13** | **8** | **28** |

---

**Roger, this is the final, corrected v0.9.0 documentation following Option A with:**
- ✅ No PipelineExecutor (use existing VideoFilePipelineService)
- ✅ JSON pipeline definitions (declarative, not hardcoded)
- ✅ Simpler worker (just calls existing service)
- ✅ All backend work uses existing infrastructure

**Ready for implementation.**