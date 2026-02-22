# 📦 v0.9.1 COMPLETE DOCUMENTATION — UI COMPLETION + MULTI-TOOL ENHANCEMENT

---

# 📋 1. OVERVIEW — v0.9.1

## **v0.9.1 — Video UI + Multi-Tool Image Analysis (Built on v0.9.0)**

### **Purpose**
v0.9.1 is a **UI completion + multi-tool enhancement** release that builds on the delivered v0.9.0 backend. It delivers:

1. **Full video analysis UI** (what v0.9.0 backend enabled but UI didn't wire)
2. **Multi-tool image analysis** (run OCR + YOLO in one request)
3. **Combined JSON contract** for multi-tool results

### **What v0.9.0 Delivered (Backend Only)**
| Component | Status | What Works |
|-----------|--------|------------|
| `/v1/video/submit` | ✅ | Accepts MP4, creates job, returns job_id |
| `/v1/video/status/{job_id}` | ✅ | Returns job status |
| `/v1/video/results/{job_id}` | ✅ | Returns OCR/YOLO results |
| `VideoFilePipelineService` | ✅ | Processes video frames |
| `DagPipelineService` | ✅ | Executes pipelines |
| Worker | ✅ | Dequeues and processes jobs |
| **Frontend** | ❌ | **NOT WIRED** |

### **What v0.9.0 Left Incomplete**
- ❌ No video upload UI
- ❌ No video preview player
- ❌ No job status polling UI
- ❌ No results display UI
- ❌ Single-tool image analysis only (no multi-tool)

### **What v0.9.1 Delivers**

#### **1. Video Analysis UI (New)**
✅ Video upload form with file selection  
✅ HTML5 `<video>` preview player  
✅ Upload progress indicator  
✅ Job submission to `/v1/video/submit`  
✅ Real-time status polling  
✅ Results display (OCR + YOLO when enabled)  

#### **2. Multi-Tool Image Analysis (New)**
✅ New endpoint: `/v1/image/analyze-multi`  
✅ Run multiple tools (OCR + YOLO) in one request  
✅ Combined JSON response format  
✅ UI for selecting tools and viewing combined results  

#### **3. Combined JSON Contract**
All multi-tool results follow:

```json
{
  "tools": {
    "ocr": { "text": "...", "confidence": 0.95 },
    "yolo-tracker": { "detections": [...] }
  }
}
```

### **What v0.9.1 Does NOT Change**
- ✅ Existing single-tool image endpoint unchanged
- ✅ Existing plugin selector unchanged
- ✅ v0.9.0 video backend unchanged
- ✅ No new executor services
- ✅ No architectural changes
- ✅ No breaking changes

### **Key Principle**
> **v0.9.1 = Complete the UI. Add multi-tool. Zero backend rewrites.**

---

# 🏗️ 2. HIGH-LEVEL DESIGN (HLD) — v0.9.1

## **System Architecture (v0.9.1)**

```
┌─────────────────────────────────────────────────────────────┐
│                        WEB UI                                │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (v0.9.0)          NEW (v0.9.1)                     │
│  - Plugin Selector          - VideoUpload                    │
│  - Tool Selector            - VideoJobStatus                 │
│  - Image Upload (single)    - VideoResults                   │
│                             - ImageMultiToolForm             │
│                             - ImageMultiToolResults          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (v0.9.0)              NEW (v0.9.1)                 │
│  /v1/video/submit              /v1/image/analyze-multi       │
│  /v1/video/status/{job_id}     (OCR + YOLO in one request)  │
│  /v1/video/results/{job_id}                                  │
│  /v1/image/analyze (single)                                  │
│  /v1/plugins                                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  REUSED (v0.9.0)                NEW (v0.9.1)                 │
│  Job Manager                    Multi-Tool Orchestrator      │
│  VideoFilePipelineService       - Run OCR plugin             │
│  DagPipelineService             - Run YOLO plugin            │
│  Pipeline Definitions:          - Merge results              │
│    - ocr_only                   - Return combined JSON       │
│    - yolo_ocr                                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               EXECUTION LAYER (UNCHANGED)                    │
├─────────────────────────────────────────────────────────────┤
│  Worker Process                 Plugin Registry              │
│  - Dequeue video jobs          - ocr                         │
│  - Run VideoFilePipelineService - yolo-tracker               │
│  - Save results                                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               PERSISTENCE LAYER (UNCHANGED)                  │
├─────────────────────────────────────────────────────────────┤
│  Database: job state + results                               │
│  Object storage: video/image files                           │
│  Queue: Redis/in-memory                                      │
└─────────────────────────────────────────────────────────────┘
```

## **What's New in v0.9.1**

### **1. Video Upload UI Flow**

```
User → VideoUpload Component
  → Select MP4 file
  → See video preview in <video> player
  → Click "Upload"
  → POST /v1/video/submit
    → Backend creates job
    → Returns job_id
  → VideoJobStatus Component
    → Poll /v1/video/status/{job_id} every 2s
    → When status = "done"
      → Fetch /v1/video/results/{job_id}
  → VideoResults Component
    → Display OCR text
    → Display YOLO detections (if pipeline=yolo_ocr)
```

### **2. Multi-Tool Image Analysis Flow**

```
User → ImageMultiToolForm Component
  → Select image file
  → Check tools: [OCR, YOLO]
  → Click "Analyze"
  → POST /v1/image/analyze-multi
      Body: { file, tools: ["ocr", "yolo-tracker"] }
    → Multi-Tool Orchestrator
      → Run ocr_plugin.run(image_bytes)
      → Run yolo_plugin.run(image_bytes)
      → Merge results
      → Return combined JSON:
        {
          "tools": {
            "ocr": { "text": "..." },
            "yolo-tracker": { "detections": [...] }
          }
        }
  → ImageMultiToolResults Component
    → Display combined JSON
    → Pretty-print each tool's results
```

### **3. Backend: Multi-Tool Orchestrator**

**Location:** `/server/api/routes/image.py` (new endpoint)

**Responsibilities:**
- Accept image file + list of tool names
- For each tool:
  - Resolve plugin from registry
  - Run plugin on image
  - Collect result
- Return combined JSON with `tools` key

**Why not a new service:**
- This is simple orchestration (for loop + dict merge)
- No need for `MultiToolExecutor` service
- Keeps code in API layer where it belongs

---

## **Data Flow Diagrams**

### **Video Upload → Results (Complete Flow)**

```
┌──────────────┐
│ User Selects │
│   MP4 File   │
└──────┬───────┘
       │
       ↓
┌──────────────────────┐
│ <video> Preview      │
│ Shows Selected File  │
└──────┬───────────────┘
       │
       ↓ User Clicks "Upload"
┌──────────────────────┐
│ POST /v1/video/submit│
│ → job_id returned    │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────────┐
│ Poll /v1/video/status    │
│ every 2 seconds          │
│ until status = "done"    │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ GET /v1/video/results    │
│ → OCR + YOLO results     │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ Display Results in UI    │
│ - OCR text               │
│ - YOLO detections        │
└──────────────────────────┘
```

### **Multi-Tool Image Analysis**

```
┌──────────────┐
│ User Selects │
│  Image File  │
└──────┬───────┘
       │
       ↓
┌──────────────────────┐
│ User Checks Tools:   │
│ [x] OCR              │
│ [x] YOLO             │
└──────┬───────────────┘
       │
       ↓ User Clicks "Analyze"
┌──────────────────────────────┐
│ POST /v1/image/analyze-multi │
│ Body: { file, tools: [...] } │
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Backend Loop:                │
│ for tool in tools:           │
│   result = plugin.run(image) │
│   results[tool] = result     │
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Return Combined JSON:        │
│ {                            │
│   "tools": {                 │
│     "ocr": {...},            │
│     "yolo-tracker": {...}    │
│   }                          │
│ }                            │
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Display in UI                │
│ - OCR section                │
│ - YOLO section               │
└──────────────────────────────┘
```

---

# 📝 3. FUNCTIONAL REQUIREMENTS — v0.9.1

## **Video Analysis UI**

### **FR-V1: Video Upload Form**
**Description:** Web UI must display a video upload form.

**Acceptance Criteria:**
- ✅ User can select MP4 file via `<input type="file" accept="video/mp4">`
- ✅ Only MP4 files are accepted
- ✅ Clear error message for non-MP4 files

---

### **FR-V2: Video Preview Player**
**Description:** Web UI must show video preview before upload.

**Acceptance Criteria:**
- ✅ After file selection, `<video>` element renders with `src={URL.createObjectURL(file)}`
- ✅ Video plays locally (no backend dependency)
- ✅ Controls are visible (play, pause, seek)
- ✅ User can confirm it's the correct video before uploading

---

### **FR-V3: Video Submission**
**Description:** Web UI must submit video to backend.

**Acceptance Criteria:**
- ✅ "Upload" button sends `POST /v1/video/submit`
- ✅ Multipart/form-data with `file` field
- ✅ Optional `pipeline_id` parameter (defaults to `ocr_only`)
- ✅ Response contains `job_id`
- ✅ `job_id` is displayed to user

---

### **FR-V4: Upload Progress Indicator**
**Description:** Web UI must show upload progress.

**Acceptance Criteria:**
- ✅ Progress bar or percentage displayed during upload
- ✅ Uses XMLHttpRequest upload progress events
- ✅ Progress updates smoothly
- ✅ Progress disappears when upload completes

---

### **FR-V5: Video Job Status Polling**
**Description:** Web UI must poll job status until completion.

**Acceptance Criteria:**
- ✅ After submission, UI polls `GET /v1/video/status/{job_id}` every 2 seconds
- ✅ Status shows: `pending`, `running`, `done`, `error`
- ✅ Progress percentage displayed if available
- ✅ Polling stops when status is `done` or `error`
- ✅ Error message displayed if status is `error`

---

### **FR-V6: Video Results Display**
**Description:** Web UI must display job results when complete.

**Acceptance Criteria:**
- ✅ When status = `done`, UI fetches `GET /v1/video/results/{job_id}`
- ✅ OCR text is displayed (if present)
- ✅ YOLO detections are displayed (if present)
- ✅ Results are formatted for readability
- ✅ Frame-by-frame data is accessible

---

## **Multi-Tool Image Analysis**

### **FR-I1: Multi-Tool Endpoint**
**Description:** Backend must provide endpoint for multi-tool image analysis.

**Acceptance Criteria:**
- ✅ Endpoint: `POST /v1/image/analyze-multi`
- ✅ Accepts: `file` (image) + `tools` (list of tool names)
- ✅ Returns combined JSON with `tools` key
- ✅ Each tool's result is under `tools[tool_name]`

---

### **FR-I2: Combined JSON Contract**
**Description:** Multi-tool results must follow combined JSON format.

**Acceptance Criteria:**
- ✅ Response structure:
  ```json
  {
    "tools": {
      "ocr": { "text": "...", "confidence": 0.95 },
      "yolo-tracker": { "detections": [...] }
    }
  }
  ```
- ✅ Each tool's result is isolated
- ✅ Result format matches single-tool format for that tool

---

### **FR-I3: Multi-Tool UI**
**Description:** Web UI must provide interface for multi-tool image analysis.

**Acceptance Criteria:**
- ✅ User can select image file
- ✅ User can select tools via checkboxes (OCR, YOLO)
- ✅ "Analyze" button sends request to `/v1/image/analyze-multi`
- ✅ Results are displayed in structured format
- ✅ Each tool's results are clearly separated

---

### **FR-I4: Tool Execution**
**Description:** Backend must execute all requested tools.

**Acceptance Criteria:**
- ✅ For each tool in request:
  - Resolve plugin from registry
  - Run plugin on image
  - Collect result
- ✅ All tools run successfully or entire request fails
- ✅ Error message indicates which tool failed

---

### **FR-I5: Backward Compatibility**
**Description:** Existing single-tool endpoint must remain unchanged.

**Acceptance Criteria:**
- ✅ `POST /v1/image/analyze` still works
- ✅ Single-tool response format unchanged
- ✅ Existing UI for single-tool analysis still works
- ✅ No breaking changes

---

## **General Requirements**

### **FR-G1: No New Executor Services**
**Description:** All video processing must use existing infrastructure.

**Acceptance Criteria:**
- ✅ Worker uses `VideoFilePipelineService.run_on_file()`
- ✅ `VideoFilePipelineService` uses `DagPipelineService`
- ✅ `DagPipelineService` uses pipeline JSON definitions
- ✅ No new "PipelineExecutor" or "MultiToolExecutor" services

---

### **FR-G2: Logging & Observability**
**Description:** Video and multi-tool flows must be observable.

**Acceptance Criteria:**
- ✅ Log on video submit: file path, job_id, pipeline_id
- ✅ Log on worker start: job_id, pipeline_id
- ✅ Log on worker completion: job_id, frame count, duration
- ✅ Log on multi-tool request: tools requested
- ✅ Log on multi-tool completion: tools executed, duration

---

# 📝 4. NON-FUNCTIONAL REQUIREMENTS — v0.9.1

### **NFR-1: Backward Compatibility**
**Description:** v0.9.1 must not break v0.9.0 functionality.

**Acceptance Criteria:**
- ✅ All v0.9.0 backend endpoints unchanged
- ✅ All v0.9.0 tests pass
- ✅ Existing single-tool image analysis works
- ✅ Plugin selector works
- ✅ Tool selector works

---

### **NFR-2: Performance**
**Description:** Video and multi-tool analysis must be performant.

**Acceptance Criteria:**
- ✅ Video processing handles:
  - 3-minute MP4 (~5400 frames at 30 FPS)
  - Completes in reasonable time (< 10 minutes for OCR-only)
- ✅ Multi-tool image analysis:
  - Runs tools in sequence (for now)
  - Total time = sum of individual tool times
  - Future optimization: parallel execution (v1.1.0+)

---

### **NFR-3: User Experience**
**Description:** UI must be clear, responsive, and informative.

**Acceptance Criteria:**
- ✅ Video preview renders immediately after file selection
- ✅ Upload progress updates smoothly
- ✅ Status polling updates are visible
- ✅ Error messages are clear and actionable
- ✅ Results are formatted for readability

---

### **NFR-4: Code Quality**
**Description:** All code must pass CI workflows.

**Acceptance Criteria:**
- ✅ All existing CI workflows pass:
  - Vocabulary validation
  - Video batch validation
  - Governance CI
  - Execution CI
  - Main CI
- ✅ No linting errors
- ✅ No type errors (TypeScript)

---

### **NFR-5: Test Coverage**
**Description:** All new functionality must be tested.

**Acceptance Criteria:**
- ✅ Integration test: video upload → job → status → results
- ✅ Integration test: multi-tool image analysis (OCR + YOLO)
- ✅ Unit test: multi-tool orchestrator
- ✅ UI component tests (VideoUpload, VideoJobStatus, VideoResults)
- ✅ UI component tests (ImageMultiToolForm, ImageMultiToolResults)

---

### **NFR-6: No Architectural Drift**
**Description:** v0.9.1 must not introduce new architectural patterns.

**Acceptance Criteria:**
- ✅ No new top-level services
- ✅ No "PipelineExecutor" service
- ✅ No "MultiToolExecutor" service
- ✅ Orchestration stays in API layer
- ✅ No Phase-17-style streaming experiments

---

# 👤 5. USER STORIES — v0.9.1

## **Video Player & Analyzer**

### **US-V1: Preview Video Before Upload**
**As a user**  
I want to see my selected video play in the browser before uploading  
So that I can confirm it's the correct file.

**Acceptance Criteria:**
- ✅ After file selection, video renders in `<video>` player
- ✅ Video plays locally (no upload required)
- ✅ Controls work (play, pause, seek)

---

### **US-V2: Upload Video for Analysis**
**As a user**  
I want to upload a video and receive a job ID  
So that I can track the processing status.

**Acceptance Criteria:**
- ✅ "Upload" button submits video
- ✅ Upload progress is visible
- ✅ Job ID is displayed after successful upload

---

### **US-V3: Monitor Video Processing**
**As a user**  
I want to see real-time status updates for my video processing job  
So that I know when it's complete.

**Acceptance Criteria:**
- ✅ Status updates automatically (every 2 seconds)
- ✅ Status shows: pending, running, completed, or failed
- ✅ Progress percentage displayed (if available)
- ✅ Clear error message if job fails

---

### **US-V4: View OCR Results**
**As a user**  
I want to see the OCR text extracted from my video  
So that I can use it for downstream analysis.

**Acceptance Criteria:**
- ✅ OCR text is displayed when job completes
- ✅ Text is formatted for readability
- ✅ I can copy the text

---

### **US-V5: View YOLO + OCR Results**
**As a user**  
I want to see both object detections and OCR text from my video  
So that I can analyze both visual and textual content.

**Acceptance Criteria:**
- ✅ YOLO detections displayed (when `yolo_ocr` pipeline used)
- ✅ Bounding boxes, labels, confidence scores shown
- ✅ OCR text displayed alongside detections
- ✅ Frame-by-frame results accessible

---

## **Multi-Tool Image Analyzer**

### **US-I1: Run Multiple Tools on One Image**
**As a user**  
I want to run OCR and YOLO on a single image in one request  
So that I don't have to make separate API calls.

**Acceptance Criteria:**
- ✅ I can select an image file
- ✅ I can check "OCR" and "YOLO" boxes
- ✅ Clicking "Analyze" runs both tools

---

### **US-I2: Receive Combined Results**
**As a user**  
I want to receive a single JSON response containing all tool results  
So that I can easily parse and use the data.

**Acceptance Criteria:**
- ✅ Response structure is:
  ```json
  {
    "tools": {
      "ocr": { ... },
      "yolo-tracker": { ... }
    }
  }
  ```
- ✅ Each tool's result is clearly separated
- ✅ Results match single-tool format for each tool

---

### **US-I3: View Structured Results**
**As a user**  
I want to see multi-tool results in a clear, structured format  
So that I can understand what each tool found.

**Acceptance Criteria:**
- ✅ Results are pretty-printed
- ✅ Each tool's section is clearly labeled
- ✅ OCR text is readable
- ✅ YOLO detections are formatted

---

### **US-I4: Preserve Single-Tool Workflow**
**As a user**  
I want to still use the single-tool endpoint when I only need one tool  
So that I have a simpler workflow for simple tasks.

**Acceptance Criteria:**
- ✅ Existing single-tool UI still works
- ✅ Single-tool response format unchanged
- ✅ No breaking changes to existing workflow

---

## **Developer Stories**

### **US-D1: Reuse Existing Infrastructure**
**As a developer**  
I want v0.9.1 to use existing services and pipelines  
So that I don't introduce new complexity or maintenance burden.

**Acceptance Criteria:**
- ✅ Worker uses `VideoFilePipelineService`
- ✅ `VideoFilePipelineService` uses `DagPipelineService`
- ✅ Multi-tool orchestration is simple (for loop + dict merge)
- ✅ No new executor services

---

### **US-D2: Clear Separation of Concerns**
**As a developer**  
I want UI logic separate from backend logic  
So that I can test and maintain each independently.

**Acceptance Criteria:**
- ✅ UI components handle presentation only
- ✅ Backend handles business logic only
- ✅ API contracts are stable and documented
- ✅ No business logic in UI components

---

### **US-D3: Observable Video Processing**
**As a developer**  
I want to see logs for each step of video processing  
So that I can debug issues quickly.

**Acceptance Criteria:**
- ✅ Log on video submit
- ✅ Log on worker start
- ✅ Log on pipeline execution
- ✅ Log on worker completion
- ✅ All logs include job_id

---

# 🛠️ 6. DEVELOPMENT PLAN — v0.9.1

## **Guiding Principles**
1. **UI first, backend second** (backend already works, just add one endpoint)
2. **One component per commit**
3. **Every commit is testable**
4. **Every commit is reviewable**
5. **No breaking changes**
6. **No regressions**
7. **No new services**

---

**Last Updated:** 2026-02-18
**Status:** Ready for Implementation

---

### **Before Commit (Mandatory)**

Every commit in v0.9.0 must satisfy:

1. Run all GitHub workflows locally  
2. Fix all errors  
3. Ensure repo is GREEN  
4. Only then commit  


### **CI Tests**
- Run all GitHub workflows locally  
/home/rogermt/forgesyte/.github/workflows/ci.yml
/home/rogermt/forgesyte/.github/workflows/execution-ci.yml
/home/rogermt/forgesyte/.github/workflows/governance-ci.yml
/home/rogermt/forgesyte/.github/workflows/video_batch_validation.yml
/home/rogermt/forgesyte/.github/workflows/vocabulary_validation.yml

This applies to:

- Backend commits  
- Frontend commits  
- Integration commits  
- Documentation commits  

---


## **PHASE 1: Backend (Multi-Tool Endpoint)**

### **Commit B1: Add `/v1/image/analyze-multi` Endpoint**

**What:** Create new endpoint for multi-tool image analysis.

**Why:** Enable running OCR + YOLO in one request.

**Files Added:**
- None (add to existing `/server/api/routes/image.py`)

**Files Changed:**
- `/server/api/routes/image.py`

**Code:**
```python
from fastapi import APIRouter, UploadFile, File, Body
from typing import List, Dict, Any
from server.core.plugin_management_service import plugin_manager

router = APIRouter()

async def run_tool_on_image(tool_name: str, image_bytes: bytes) -> Any:
    """Run a single tool on image bytes."""
    plugin = plugin_manager.get_plugin(tool_name)
    if not plugin:
        raise ValueError(f"Unknown tool: {tool_name}")
    return await plugin.run(image_bytes=image_bytes)

@router.post("/v1/image/analyze-multi")
async def analyze_image_multi(
    file: UploadFile = File(...),
    tools: List[str] = Body(..., embed=True),
) -> Dict[str, Any]:
    """
    Run multiple tools on a single image.
    
    Returns combined JSON:
    {
      "tools": {
        "ocr": { ... },
        "yolo-tracker": { ... }
      }
    }
    """
    image_bytes = await file.read()
    results: Dict[str, Any] = {"tools": {}}
    
    for tool in tools:
        try:
            result = await run_tool_on_image(tool, image_bytes)
            results["tools"][tool] = result
        except Exception as e:
            results["tools"][tool] = {"error": str(e)}
    
    return results
```

**Tests:**
- ✅ Request with `tools=["ocr"]` returns OCR result
- ✅ Request with `tools=["ocr", "yolo-tracker"]` returns both
- ✅ Unknown tool returns error in result
- ✅ Response structure matches combined JSON contract

**Acceptance Criteria:**
```bash
curl -F "file=@image.jpg" \
     -F 'tools=["ocr", "yolo-tracker"]' \
     http://localhost:8000/v1/image/analyze-multi
→ 200 OK
→ {"tools": {"ocr": {...}, "yolo-tracker": {...}}}
```

---

### **Commit B2: Add Logging to Multi-Tool Endpoint**

**What:** Log multi-tool requests for observability.

**Why:** Debug and monitor multi-tool usage.

**Files Changed:**
- `/server/api/routes/image.py`

**Code:**
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/v1/image/analyze-multi")
async def analyze_image_multi(...):
    logger.info(f"Multi-tool request: tools={tools}, file={file.filename}")
    
    # ... existing code ...
    
    logger.info(f"Multi-tool completed: tools={tools}, duration={duration}s")
    return results
```

**Tests:**
- ✅ Logs appear in server output
- ✅ Logs include tools requested
- ✅ Logs include duration

**Acceptance Criteria:**
- ✅ Logs visible when endpoint called
- ✅ Logs help debug issues

---

### **Commit B3: Add Integration Test for Multi-Tool**

**What:** Test full multi-tool flow.

**Why:** Ensure endpoint works end-to-end.

**Files Added:**
- `/server/tests/integration/test_multi_tool_image.py`

**Code:**
```python
import pytest
from fastapi.testclient import TestClient

def test_multi_tool_image_analysis():
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr", "yolo-tracker"]}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tools" in data
    assert "ocr" in data["tools"]
    assert "yolo-tracker" in data["tools"]
    assert "text" in data["tools"]["ocr"]
    assert "detections" in data["tools"]["yolo-tracker"]
```

**Tests:**
- ✅ Test passes
- ✅ Full flow works

**Acceptance Criteria:**
- ✅ Integration test added to test suite
- ✅ Test runs in CI

---

## **PHASE 2: Frontend (Video Upload UI)**

### **Commit F1: Add `submitVideo` API Helper**

**What:** Create API service method for video upload.

**Why:** Centralize API logic.

**Files Changed:**
- `/web-ui/services/api.ts`

**Code:**
```typescript
export async function submitVideo(
  file: File,
  pipelineId?: string,
  onProgress?: (percent: number) => void
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  if (pipelineId) {
    formData.append("pipeline_id", pipelineId);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/v1/video/submit");

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress((e.loaded / e.total) * 100);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(formData);
  });
}

export async function getVideoStatus(jobId: string) {
  const res = await fetch(`/v1/video/status/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function getVideoResults(jobId: string) {
  const res = await fetch(`/v1/video/results/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch results");
  return res.json();
}
```

**Tests:**
- ✅ Mock test: `submitVideo()` returns job_id
- ✅ Mock test: `getVideoStatus()` returns status
- ✅ Mock test: `getVideoResults()` returns results

**Acceptance Criteria:**
- ✅ API helpers implemented
- ✅ Tests pass

---

### **Commit F2: Create `VideoUpload` Component**

**What:** Create video upload component with preview.

**Why:** Enable users to select and preview video.

**Files Added:**
- `/web-ui/components/VideoUpload.tsx`
- `/web-ui/components/VideoUpload.module.css`

**Code:**
```typescript
import React, { useState } from "react";
import { submitVideo } from "../services/api";
import { VideoJobStatus } from "./VideoJobStatus";
import styles from "./VideoUpload.module.css";

export const VideoUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    setError(null);
    setJobId(null);
    setProgress(0);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (selectedFile.type !== "video/mp4") {
      setError("Only MP4 videos are supported.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const onUpload = async () => {
    if (!file) return;
    
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const { job_id } = await submitVideo(file, undefined, setProgress);
      setJobId(job_id);
    } catch (e: any) {
      setError(e.message ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2>Video Analyzer</h2>

      <input
        type="file"
        accept="video/mp4"
        onChange={onFileChange}
        className={styles.fileInput}
      />

      {file && (
        <video
          src={URL.createObjectURL(file)}
          controls
          className={styles.videoPreview}
        />
      )}

      {error && <div className={styles.error}>{error}</div>}

      {uploading && (
        <div className={styles.progress}>
          Uploading… {progress.toFixed(0)}%
        </div>
      )}

      <button
        onClick={onUpload}
        disabled={!file || uploading}
        className={styles.uploadButton}
      >
        Upload
      </button>

      {jobId && <VideoJobStatus jobId={jobId} />}
    </div>
  );
};
```

**Tests:**
- ✅ Component renders
- ✅ File input works
- ✅ Video preview shows after selection
- ✅ Upload button disabled when no file
- ✅ Error shows for non-MP4 files

**Acceptance Criteria:**
- ✅ Component works end-to-end
- ✅ Video preview renders correctly

---

### **Commit F3: Create `VideoJobStatus` Component**

**What:** Create component to poll and display job status.

**Why:** Users need to see processing progress.

**Files Added:**
- `/web-ui/components/VideoJobStatus.tsx`
- `/web-ui/components/VideoJobStatus.module.css`

**Code:**
```typescript
import React, { useEffect, useState } from "react";
import { getVideoStatus, getVideoResults } from "../services/api";
import { VideoResults } from "./VideoResults";
import styles from "./VideoJobStatus.module.css";

export const VideoJobStatus: React.FC<{ jobId: string }> = ({ jobId }) => {
  const [status, setStatus] = useState<string>("pending");
  const [progress, setProgress] = useState<number>(0);
  const [results, setResults] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: number;

    const poll = async () => {
      try {
        const statusData = await getVideoStatus(jobId);
        setStatus(statusData.status);
        setProgress(statusData.progress || 0);

        if (statusData.status === "done") {
          const resultsData = await getVideoResults(jobId);
          setResults(resultsData);
          return; // Stop polling
        }

        if (statusData.status === "error") {
          setError(statusData.error ?? "Job failed");
          return; // Stop polling
        }

        // Continue polling
        timer = window.setTimeout(poll, 2000);
      } catch (e: any) {
        setError(e.message ?? "Status polling failed");
      }
    };

    poll();

    return () => window.clearTimeout(timer);
  }, [jobId]);

  return (
    <div className={styles.container}>
      <div className={styles.status}>
        <strong>Status:</strong> {status}
      </div>

      {progress > 0 && (
        <div className={styles.progress}>
          Progress: {progress.toFixed(0)}%
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}

      {results && <VideoResults results={results} />}
    </div>
  );
};
```

**Tests:**
- ✅ Component renders
- ✅ Polling starts on mount
- ✅ Polling stops when status = "done"
- ✅ Polling stops when status = "error"
- ✅ Results fetched when job completes

**Acceptance Criteria:**
- ✅ Status updates automatically
- ✅ Polling works correctly

---

### **Commit F4: Create `VideoResults` Component**

**What:** Create component to display video analysis results.

**Why:** Users need to see OCR and YOLO results.

**Files Added:**
- `/web-ui/components/VideoResults.tsx`
- `/web-ui/components/VideoResults.module.css`

**Code:**
```typescript
import React from "react";
import styles from "./VideoResults.module.css";

interface VideoResultsProps {
  results: any;
}

export const VideoResults: React.FC<VideoResultsProps> = ({ results }) => {
  const frames = results.results || [];

  return (
    <div className={styles.container}>
      <h3>Results</h3>

      {frames.length === 0 && <p>No results available.</p>}

      {frames.map((frame: any, idx: number) => (
        <div key={idx} className={styles.frame}>
          <h4>Frame {frame.frame_index}</h4>

          {frame.result.text && (
            <div className={styles.ocr}>
              <h5>OCR Text</h5>
              <pre>{frame.result.text}</pre>
            </div>
          )}

          {frame.result.detections && frame.result.detections.length > 0 && (
            <div className={styles.yolo}>
              <h5>YOLO Detections</h5>
              {frame.result.detections.map((det: any, i: number) => (
                <div key={i} className={styles.detection}>
                  <span className={styles.label}>{det.label}</span>
                  <span className={styles.confidence}>
                    {(det.confidence * 100).toFixed(1)}%
                  </span>
                  <span className={styles.bbox}>
                    [{det.bbox.join(", ")}]
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

**Tests:**
- ✅ Component renders
- ✅ OCR text displayed correctly
- ✅ YOLO detections displayed correctly
- ✅ Empty results handled gracefully

**Acceptance Criteria:**
- ✅ Results display correctly
- ✅ Layout is readable

---

## **PHASE 3: Frontend (Multi-Tool Image UI)**

### **Commit F5: Add `analyzeImageMulti` API Helper**

**What:** Create API service method for multi-tool image analysis.

**Why:** Centralize API logic.

**Files Changed:**
- `/web-ui/services/api.ts`

**Code:**
```typescript
export async function analyzeImageMulti(
  file: File,
  tools: string[]
): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tools", JSON.stringify(tools));

  const res = await fetch("/v1/image/analyze-multi", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Multi-tool analysis failed: ${res.status}`);
  }

  return res.json();
}
```

**Tests:**
- ✅ Mock test: returns combined JSON

**Acceptance Criteria:**
- ✅ API helper implemented
- ✅ Test passes

---

### **Commit F6: Create `ImageMultiToolForm` Component**

**What:** Create UI for multi-tool image analysis.

**Why:** Enable users to run OCR + YOLO on images.

**Files Added:**
- `/web-ui/components/ImageMultiToolForm.tsx`
- `/web-ui/components/ImageMultiToolForm.module.css`

**Code:**
```typescript
import React, { useState } from "react";
import { analyzeImageMulti } from "../services/api";
import { ImageMultiToolResults } from "./ImageMultiToolResults";
import styles from "./ImageMultiToolForm.module.css";

export const ImageMultiToolForm: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [useOcr, setUseOcr] = useState(true);
  const [useYolo, setUseYolo] = useState(true);
  const [results, setResults] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const onSubmit = async () => {
    if (!file) return;

    setError(null);
    setResults(null);
    setAnalyzing(true);

    const tools: string[] = [];
    if (useOcr) tools.push("ocr");
    if (useYolo) tools.push("yolo-tracker");

    try {
      const resultsData = await analyzeImageMulti(file, tools);
      setResults(resultsData);
    } catch (e: any) {
      setError(e.message ?? "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2>Image Multi-Tool Analyzer</h2>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className={styles.fileInput}
      />

      <div className={styles.toolSelection}>
        <label>
          <input
            type="checkbox"
            checked={useOcr}
            onChange={(e) => setUseOcr(e.target.checked)}
          />
          OCR
        </label>
        <label>
          <input
            type="checkbox"
            checked={useYolo}
            onChange={(e) => setUseYolo(e.target.checked)}
          />
          YOLO
        </label>
      </div>

      <button
        onClick={onSubmit}
        disabled={!file || analyzing || (!useOcr && !useYolo)}
        className={styles.analyzeButton}
      >
        Analyze
      </button>

      {error && <div className={styles.error}>{error}</div>}

      {results && <ImageMultiToolResults results={results} />}
    </div>
  );
};
```

**Tests:**
- ✅ Component renders
- ✅ File input works
- ✅ Tool checkboxes work
- ✅ Analyze button disabled when no tools selected

**Acceptance Criteria:**
- ✅ Component works end-to-end
- ✅ UI is intuitive

---

### **Commit F7: Create `ImageMultiToolResults` Component**

**What:** Create component to display multi-tool results.

**Why:** Users need to see structured results.

**Files Added:**
- `/web-ui/components/ImageMultiToolResults.tsx`
- `/web-ui/components/ImageMultiToolResults.module.css`

**Code:**
```typescript
import React from "react";
import styles from "./ImageMultiToolResults.module.css";

interface ImageMultiToolResultsProps {
  results: any;
}

export const ImageMultiToolResults: React.FC<ImageMultiToolResultsProps> = ({
  results,
}) => {
  const tools = results.tools || {};

  return (
    <div className={styles.container}>
      <h3>Results</h3>

      {Object.keys(tools).map((toolName) => (
        <div key={toolName} className={styles.toolResult}>
          <h4>{toolName}</h4>
          <pre>{JSON.stringify(tools[toolName], null, 2)}</pre>
        </div>
      ))}
    </div>
  );
};
```

**Tests:**
- ✅ Component renders
- ✅ Results display correctly
- ✅ Each tool's results are separated

**Acceptance Criteria:**
- ✅ Results are readable
- ✅ Layout is clean

---

## **PHASE 4: Integration & Release**

### **Commit F8: Wire Components to Main UI**

**What:** Add video and multi-tool UIs to main page.

**Why:** Make features discoverable.

**Files Changed:**
- `/web-ui/pages/index.tsx`

**Code:**
```typescript
import { VideoUpload } from "../components/VideoUpload";
import { ImageMultiToolForm } from "../components/ImageMultiToolForm";

export default function HomePage() {
  return (
    <div>
      <h1>Vision Processing System</h1>

      <section>
        <VideoUpload />
      </section>

      <section>
        <ImageMultiToolForm />
      </section>

      {/* Existing components remain */}
    </div>
  );
}
```

**Tests:**
- ✅ Page renders
- ✅ All components visible
- ✅ No layout issues

**Acceptance Criteria:**
- ✅ Features accessible from main page
- ✅ No regressions

---

### **Commit 9: Add Integration Tests**

**What:** Add end-to-end tests for video and multi-tool flows.

**Why:** Ensure full flows work.

**Files Added:**
- `/web-ui/tests/integration/videoUpload.test.ts`
- `/web-ui/tests/integration/multiToolImage.test.ts`

**Tests:**
- ✅ Video: upload → status → results
- ✅ Multi-tool: analyze → combined JSON

**Acceptance Criteria:**
- ✅ All integration tests pass
- ✅ Tests run in CI

---

### **Commit 10: Update Documentation**

**What:** Document v0.9.1 features.

**Why:** Users and developers need docs.

**Files Changed:**
- `/docs/v0.9.1/video-upload-ui.md`
- `/docs/v0.9.1/multi-tool-image.md`
- `/CHANGELOG.md`
- `/README.md`

**Tests:**
- ✅ Documentation is accurate
- ✅ Examples work

**Acceptance Criteria:**
- ✅ All features documented
- ✅ CHANGELOG updated

---

### **Commit 11: Tag v0.9.1 Release**

**What:** Tag final release.

**Why:** Official release.

**Files Changed:**
- Version bump

**Tests:**
- ✅ All tests pass
- ✅ All features work
- ✅ No regressions

**Acceptance Criteria:**
- ✅ v0.9.1 is ready for production

---

# 🔄 7. PULL REQUEST TEMPLATE — v0.9.1

```markdown
## PR Title
[v0.9.1 / Commit N] Brief description

## Component
- [ ] Backend
- [ ] Frontend
- [ ] Documentation
- [ ] Tests

## Commit Number
Commit N of 11

## Description
What does this PR do?

## Why
Why is this change necessary?

## Files Changed
- `/path/to/file1.py`
- `/path/to/file2.tsx`

## Tests Added/Modified
- ✅ Test 1 description
- ✅ Test 2 description

## Acceptance Criteria
- ✅ Criterion 1
- ✅ Criterion 2

## Regression Check
- ✅ All v0.9.0 tests pass
- ✅ Existing single-tool image analysis works
- ✅ Plugin selector works
- ✅ Tool selector works

## Backend Stability Check (if backend commit)
- ✅ `/v1/image/analyze-multi` works
- ✅ Combined JSON format correct
- ✅ Backward compatible

## Frontend Check (if frontend commit)
- ✅ Video preview renders
- ✅ Upload works
- ✅ Status polling works
- ✅ Results display correctly

## Screenshots
[If UI commit, add screenshots]

## Related Issues
Part of v0.9.1 video UI + multi-tool release

## Checklist
- [ ] Code follows project patterns
- [ ] Tests added/updated
- [ ] Documentation added/updated
- [ ] CHANGELOG updated (if final commit)
- [ ] No breaking changes
- [ ] All CI checks pass
- [ ] Ready for review
```

---

# ✅ SUMMARY

## **v0.9.1 Deliverables**

### **Backend (3 commits)**
1. Add `/v1/image/analyze-multi` endpoint
2. Add logging
3. Add integration test

### **Frontend (8 commits)**
4. Add `submitVideo` API helper
5. Create `VideoUpload` component
6. Create `VideoJobStatus` component
7. Create `VideoResults` component
8. Add `analyzeImageMulti` API helper
9. Create `ImageMultiToolForm` component
10. Create `ImageMultiToolResults` component
11. Wire to main UI

### **Integration & Release (3 commits)**
9. Add integration tests
10. Update documentation
11. Tag v0.9.1

## **Total: 11 Commits**

| Phase | Backend | Frontend | Integration | Total |
|-------|---------|----------|-------------|-------|
| **v0.9.1** | 3 | 6 | 2 | **11** |

---

**Roger, this is the complete v0.9.1 documentation:**
- ✅ Built on v0.9.0 backend (no changes needed)
- ✅ Adds video upload UI (what PM forgot)
- ✅ Adds multi-tool image analysis
- ✅ Uses existing infrastructure (no new services)
- ✅ 11 clean, atomic commits
- ✅ Full test coverage
- ✅ Complete documentation

**Ready for implementation.**