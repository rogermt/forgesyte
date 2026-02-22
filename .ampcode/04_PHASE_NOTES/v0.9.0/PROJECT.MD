# ⭐ COMPLETE DOCUMENTATION PACKAGE — v0.9.0 + v1.0.0

---

# 📦 PART 1: v0.9.0 DOCUMENTATION

---

# 📋 1. OVERVIEW — v0.9.0

## **v0.9.0 — Video Upload Feature (Replaces Broken Phase 17)**

### **Purpose**
v0.9.0 delivers **video upload functionality to the Web UI**, building on the stable Phase 16 async job system. This is a **focused, single-feature release** that replaces the broken Phase 17 delivery.

### **What Came Before**

| Version | Name | Status | Summary |
|---------|------|--------|---------|
| v0.8.0 | Phase 15 | ✅ Stable | Synchronous batch video processing (YOLO + OCR pipeline) |
| v0.8.1 | Phase 16 | ✅ Stable | Async job system (queue, workers, persistence, object storage) |
| ❌ Phase 17 | Phase 17 | ❌ Rejected | Broken delivery with regressions, experimental code, architectural drift |

### **What Phase 17 Did Wrong**
- ❌ Removed plugin selector from UI
- ❌ Removed tool selector from UI  
- ❌ Removed image upload from UI
- ❌ Introduced experimental streaming code
- ❌ Broke Gemini-CLI MCP extension
- ❌ Introduced architectural drift
- ❌ Broke UI → backend contract

### **What v0.9.0 Delivers**
v0.9.0 is a **clean, focused delivery** that adds **one feature only**:

✅ **Video Upload to Web UI**
- User can upload MP4 video via Web UI
- Video is submitted to `/v1/video/submit` (Phase 16 endpoint)
- Job ID is returned and displayed
- User can check status via `/v1/video/status/{job_id}`
- User can retrieve results via `/v1/video/results/{job_id}`
- Full integration with Phase 16 async job system
- Full integration with Phase 15 video processing pipeline

### **What v0.9.0 Does NOT Change**
- ✅ Plugin selector remains intact
- ✅ Tool selector remains intact
- ✅ Image upload remains intact
- ✅ Phase 15 video pipeline unchanged
- ✅ Phase 16 async job system unchanged
- ✅ No experimental code added
- ✅ No architectural changes
- ✅ No breaking changes

### **Key Principle**
> **v0.9.0 = One Feature. Zero Regressions. Zero Drift.**

---

# 🏗️ 2. HIGH-LEVEL DESIGN (HLD) — v0.9.0

## **System Architecture (v0.9.0)**

```
┌─────────────────────────────────────────────────────────────┐
│                        WEB UI (NEW)                          │
├─────────────────────────────────────────────────────────────┤
│  EXISTING (Unchanged)          NEW (v0.9.0)                  │
│  - Plugin Selector             - Video Upload Form           │
│  - Tool Selector               - Job ID Display              │
│  - Image Upload                - Job Status Display          │
│  - Pipeline Selection          - Job Results Display         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (Unchanged)                     │
├─────────────────────────────────────────────────────────────┤
│  /v1/image/analyze            (existing)                     │
│  /v1/video/submit             (Phase 16 - existing)          │
│  /v1/video/status/{job_id}    (Phase 16 - existing)          │
│  /v1/video/results/{job_id}   (Phase 16 - existing)          │
│  /v1/plugins                  (existing)                     │
│  /v1/pipelines                (existing)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER (Unchanged)                │
├─────────────────────────────────────────────────────────────┤
│  Job Manager (Phase 16)       Pipeline Registry              │
│  - Job Creation               - Phase 15 Video               │
│  - Status Tracking            - Image Pipelines              │
│  - Result Storage             - Tool Mapping                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               EXECUTION LAYER (Unchanged)                    │
├─────────────────────────────────────────────────────────────┤
│  Worker Process (Phase 16)    VideoFilePipelineService       │
│  - Dequeue Jobs               (Phase 15)                     │
│  - Execute Phase 15 Pipeline  - Frame Extraction             │
│  - Save Results               - YOLO Detection               │
│  - Update Status              - OCR Processing               │
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

## **What's New in v0.9.0**

### **1. Video Upload UI Component**
- **Location:** `/web-ui/components/VideoUpload.tsx`
- **Responsibilities:**
  - Display file upload form
  - Validate MP4 format
  - Submit video to `/v1/video/submit`
  - Display returned job_id
  - Poll `/v1/video/status/{job_id}` for status updates
  - Display results from `/v1/video/results/{job_id}` when complete

### **2. Job Status Display Component**
- **Location:** `/web-ui/components/JobStatus.tsx`
- **Responsibilities:**
  - Display current job status (pending, running, completed, failed)
  - Display progress percentage
  - Display error messages if failed
  - Auto-refresh status until job completes

### **3. Job Results Display Component**
- **Location:** `/web-ui/components/JobResults.tsx`
- **Responsibilities:**
  - Display YOLO detection results
  - Display OCR text results
  - Display frame-by-frame analysis
  - Display video metadata

## **Data Flow (v0.9.0 Video Upload)**

```
User → Web UI Video Upload Form
  → Select MP4 file
  → Click "Upload"
  → POST /v1/video/submit (multipart/form-data)
    → Phase 16 Job Manager
      → Validate MP4
      → Save to Object Storage
      → Create Job Row in DB (status: pending)
      → Enqueue job_id
      → Return job_id
  → Web UI displays job_id
  → Web UI polls GET /v1/video/status/{job_id}
    → Returns: { status: "running", progress: 45 }
  → Worker Process (Phase 16)
    → Dequeue job_id
    → Download MP4 from Object Storage
    → Execute Phase 15 VideoFilePipelineService
      → Extract frames
      → Run YOLO
      → Run OCR
      → Assemble results
    → Save results to DB
    → Update job status to "completed"
  → Web UI polls GET /v1/video/status/{job_id}
    → Returns: { status: "completed" }
  → Web UI calls GET /v1/video/results/{job_id}
    → Returns: { detections: [...], ocr: [...], frames: [...] }
  → Web UI displays results
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

## **FR-2: Video Submission**
**Description:** Web UI must submit video to `/v1/video/submit`.

**Acceptance Criteria:**
- ✅ Video is sent as multipart/form-data
- ✅ Request includes any selected pipeline_id
- ✅ Response includes job_id
- ✅ job_id is displayed to user

---

## **FR-3: Job Status Display**
**Description:** Web UI must display job status.

**Acceptance Criteria:**
- ✅ Status is polled every 2 seconds
- ✅ Status shows: pending, running, completed, failed
- ✅ Progress percentage is displayed
- ✅ Polling stops when job completes or fails

---

## **FR-4: Job Results Display**
**Description:** Web UI must display job results when complete.

**Acceptance Criteria:**
- ✅ Results include YOLO detections
- ✅ Results include OCR text
- ✅ Results include frame-by-frame data
- ✅ Results are formatted for readability

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

# 📝 4. NON-FUNCTIONAL REQUIREMENTS — v0.9.0

## **NFR-1: Backward Compatibility**
**Description:** v0.9.0 must not break any existing functionality.

**Acceptance Criteria:**
- ✅ All Phase 15 tests pass
- ✅ All Phase 16 tests pass
- ✅ Image upload still works
- ✅ Plugin/tool selection still works

---

## **NFR-2: Performance**
**Description:** Video upload must not degrade system performance.

**Acceptance Criteria:**
- ✅ Upload progress is smooth
- ✅ Status polling does not overload server
- ✅ Worker processes videos at Phase 15 speed
- ✅ UI remains responsive during upload

---

## **NFR-3: User Experience**
**Description:** Video upload flow must be intuitive.

**Acceptance Criteria:**
- ✅ Upload form is easy to use
- ✅ Status updates are clear
- ✅ Results are easy to read
- ✅ Errors are user-friendly

---

## **NFR-4: Code Quality**
**Description:** New code must follow project patterns.

**Acceptance Criteria:**
- ✅ Component structure matches existing patterns
- ✅ API calls use existing service layer
- ✅ Naming conventions are consistent
- ✅ No duplicate code

---

## **NFR-5: Test Coverage**
**Description:** All new functionality must be tested.

**Acceptance Criteria:**
- ✅ Unit tests for new components
- ✅ Integration tests for upload flow
- ✅ Integration tests for status polling
- ✅ Integration tests for results display

---

# 👤 5. USER STORIES — v0.9.0

## **US-1: Upload Video for Processing**
**As a user**  
I want to upload a video file via the Web UI  
So that I can process it with the video analysis pipeline.

**Acceptance Criteria:**
- ✅ I can select an MP4 file
- ✅ I can click "Upload" to submit it
- ✅ I see a job ID displayed
- ✅ I see upload progress

---

## **US-2: Monitor Video Processing Status**
**As a user**  
I want to see the status of my video processing job  
So that I know when it's complete.

**Acceptance Criteria:**
- ✅ I see current status (pending/running/completed)
- ✅ I see progress percentage
- ✅ Status updates automatically
- ✅ I know when processing is done

---

## **US-3: View Video Processing Results**
**As a user**  
I want to see the results of my video processing  
So that I can use the detected objects and text.

**Acceptance Criteria:**
- ✅ I see YOLO detections
- ✅ I see OCR text
- ✅ I see frame-by-frame data
- ✅ Results are easy to read

---

## **US-4: Handle Upload Errors**
**As a user**  
I want to see clear error messages if upload fails  
So that I know what went wrong.

**Acceptance Criteria:**
- ✅ Invalid file format shows error
- ✅ Upload failure shows error
- ✅ Processing failure shows error
- ✅ Errors are clear and actionable

---

## **US-5: Continue Using Existing Features**
**As a user**  
I want all existing features to still work  
So that I can continue using image upload and plugin selection.

**Acceptance Criteria:**
- ✅ Image upload still works
- ✅ Plugin selector still works
- ✅ Tool selector still works
- ✅ No features are removed

---

# 🛠️ 6. DEVELOPMENT PLAN — v0.9.0

## **Guiding Principles**
1. **One component per commit**
2. **Every commit is testable**
3. **Every commit is reviewable**
4. **No breaking changes**
5. **No regressions**

---

## **Commit 1: Create VideoUpload Component Skeleton**
**What:** Create basic VideoUpload component structure.  
**Why:** Foundation for video upload UI.

**Files Added:**
- `/web-ui/components/VideoUpload.tsx`
- `/web-ui/components/VideoUpload.module.css`

**Files Changed:**
- `/web-ui/pages/index.tsx` (import component, don't render yet)

**Tests:**
- ✅ Component renders
- ✅ No errors in console
- ✅ Existing tests still pass

**Acceptance Criteria:**
- ✅ Component exists
- ✅ Component is importable
- ✅ No regressions

---

## **Commit 2: Add File Upload Form**
**What:** Add file input and upload button.  
**Why:** User needs to select video file.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`

**Tests:**
- ✅ File input renders
- ✅ Upload button renders
- ✅ Button is disabled when no file selected
- ✅ Button is enabled when file selected

**Acceptance Criteria:**
- ✅ User can select file
- ✅ User can click upload button
- ✅ Form validates file format

---

## **Commit 3: Add Client-Side File Validation**
**What:** Validate MP4 format before upload.  
**Why:** Prevent invalid uploads.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`

**Tests:**
- ✅ MP4 files are accepted
- ✅ Non-MP4 files show error
- ✅ Error message is displayed
- ✅ Upload button is disabled for invalid files

**Acceptance Criteria:**
- ✅ Only MP4 files can be uploaded
- ✅ Clear error message for invalid files

---

## **Commit 4: Implement Video Upload API Call**
**What:** Wire upload button to `/v1/video/submit`.  
**Why:** Submit video to backend.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`
- `/web-ui/services/api.ts` (add `submitVideo()` method)

**Tests:**
- ✅ Upload button calls API
- ✅ Multipart/form-data is sent correctly
- ✅ job_id is returned
- ✅ Error handling works

**Acceptance Criteria:**
- ✅ Video is uploaded to backend
- ✅ job_id is received
- ✅ Errors are handled

---

## **Commit 5: Display Job ID**
**What:** Show returned job_id in UI.  
**Why:** User needs to know job was submitted.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`

**Tests:**
- ✅ job_id is displayed after upload
- ✅ job_id is copyable
- ✅ job_id format is validated

**Acceptance Criteria:**
- ✅ User sees job_id
- ✅ job_id is clearly labeled

---

## **Commit 6: Create JobStatus Component**
**What:** Create component to display job status.  
**Why:** User needs to see processing status.

**Files Added:**
- `/web-ui/components/JobStatus.tsx`
- `/web-ui/components/JobStatus.module.css`

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx` (import JobStatus)

**Tests:**
- ✅ Component renders
- ✅ Component accepts job_id prop
- ✅ Component displays status

**Acceptance Criteria:**
- ✅ Component exists
- ✅ Component is wired to VideoUpload

---

## **Commit 7: Implement Status Polling**
**What:** Poll `/v1/video/status/{job_id}` every 2 seconds.  
**Why:** User needs live status updates.

**Files Changed:**
- `/web-ui/components/JobStatus.tsx`
- `/web-ui/services/api.ts` (add `getJobStatus()` method)

**Tests:**
- ✅ Polling starts when job_id is set
- ✅ Polling stops when job completes
- ✅ Polling stops when job fails
- ✅ Status is displayed
- ✅ Progress is displayed

**Acceptance Criteria:**
- ✅ Status updates every 2 seconds
- ✅ Polling stops on completion/failure
- ✅ Status is human-readable

---

## **Commit 8: Create JobResults Component**
**What:** Create component to display job results.  
**Why:** User needs to see processing results.

**Files Added:**
- `/web-ui/components/JobResults.tsx`
- `/web-ui/components/JobResults.module.css`

**Files Changed:**
- `/web-ui/components/JobStatus.tsx` (import JobResults)

**Tests:**
- ✅ Component renders
- ✅ Component accepts results prop
- ✅ Component displays detections
- ✅ Component displays OCR text

**Acceptance Criteria:**
- ✅ Component exists
- ✅ Component is wired to JobStatus

---

## **Commit 9: Fetch and Display Results**
**What:** Call `/v1/video/results/{job_id}` when job completes.  
**Why:** User needs to see final results.

**Files Changed:**
- `/web-ui/components/JobStatus.tsx`
- `/web-ui/services/api.ts` (add `getJobResults()` method)

**Tests:**
- ✅ Results are fetched on completion
- ✅ Results are passed to JobResults
- ✅ Results are displayed correctly
- ✅ Error handling works

**Acceptance Criteria:**
- ✅ Results load automatically
- ✅ Results are complete
- ✅ Results are readable

---

## **Commit 10: Add Upload Progress Indicator**
**What:** Show upload progress bar.  
**Why:** User needs feedback during upload.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`

**Tests:**
- ✅ Progress bar appears during upload
- ✅ Progress percentage updates
- ✅ Progress bar disappears on completion

**Acceptance Criteria:**
- ✅ User sees upload progress
- ✅ Progress is accurate

---

## **Commit 11: Add Error Handling UI**
**What:** Display user-friendly error messages.  
**Why:** User needs to know what went wrong.

**Files Changed:**
- `/web-ui/components/VideoUpload.tsx`
- `/web-ui/components/JobStatus.tsx`

**Tests:**
- ✅ Upload errors are displayed
- ✅ Job errors are displayed
- ✅ Network errors are displayed
- ✅ Error messages are clear

**Acceptance Criteria:**
- ✅ All error cases are handled
- ✅ Errors are user-friendly

---

## **Commit 12: Wire VideoUpload to Main Page**
**What:** Add VideoUpload component to main UI.  
**Why:** Make feature accessible to users.

**Files Changed:**
- `/web-ui/pages/index.tsx`

**Tests:**
- ✅ VideoUpload renders on main page
- ✅ Existing components still render
- ✅ Layout is correct

**Acceptance Criteria:**
- ✅ Video upload is visible
- ✅ No layout issues
- ✅ No regressions

---

## **Commit 13: Add Integration Tests**
**What:** Add end-to-end tests for video upload flow.  
**Why:** Ensure complete functionality.

**Files Added:**
- `/web-ui/tests/integration/videoUpload.test.ts`

**Tests:**
- ✅ Upload → job_id → status → results flow works
- ✅ Error cases are handled
- ✅ UI updates correctly

**Acceptance Criteria:**
- ✅ All integration tests pass
- ✅ Full flow is tested

---

## **Commit 14: Update Documentation**
**What:** Document video upload feature.  
**Why:** Users and developers need documentation.

**Files Changed:**
- `/docs/v0.9.0/video-upload.md`
- `/CHANGELOG.md`
- `/README.md`

**Tests:**
- ✅ Documentation is accurate
- ✅ Documentation is complete

**Acceptance Criteria:**
- ✅ Feature is documented
- ✅ CHANGELOG is updated

---

## **Commit 15: v0.9.0 Release**
**What:** Tag v0.9.0 release.  
**Why:** Official release.

**Files Changed:**
- Version bump
- Release notes

**Tests:**
- ✅ All tests pass
- ✅ All features work
- ✅ No regressions

**Acceptance Criteria:**
- ✅ v0.9.0 is ready for production

---

# 🔄 7. PULL REQUEST TEMPLATE — v0.9.0

```markdown
## PR Title
[v0.9.0 / Commit N] Brief description

## Feature
Video Upload to Web UI

## Commit Number
Commit N of 15

## Description
What does this PR do?

## Why
Why is this change necessary?

## Files Changed
- `/path/to/file1.tsx`
- `/path/to/file2.ts`

## Tests Added/Modified
- ✅ Test 1 description
- ✅ Test 2 description

## Acceptance Criteria
- ✅ Criterion 1
- ✅ Criterion 2

## Regression Check
- ✅ Plugin selector still works
- ✅ Tool selector still works
- ✅ Image upload still works
- ✅ All Phase 15/16 tests pass

## Screenshots
[Add screenshots here]

## Related Issues
Part of v0.9.0 video upload feature

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

---

# 📦 PART 2: v1.0.0 DOCUMENTATION

---

# 📋 1. OVERVIEW — v1.0.0

## **v1.0.0 — First Stable Release (MCP Integration + Stabilization)**

### **Purpose**
v1.0.0 is the **first stable, production-ready release** of the Vision Processing System. This release delivers **MCP (Model Context Protocol) integration** to enable Gemini-CLI extension support, plus **architectural stabilization** and **governance enforcement**.

### **What Came Before**

| Version | Name | Status | Summary |
|---------|------|--------|---------|
| v0.8.0 | Phase 15 | ✅ Stable | Synchronous batch video processing |
| v0.8.1 | Phase 16 | ✅ Stable | Async job system |
| v0.9.0 | Video Upload | ✅ Stable | Video upload to Web UI |

### **What v1.0.0 Delivers**

✅ **MCP Server Implementation**
- MCP-compliant server
- Tool discovery endpoint
- Tool execution endpoint
- Schema definition endpoint

✅ **Gemini-CLI Extension**
- MCP client for Gemini CLI
- Tool discovery
- Image analysis via Gemini
- Video processing via Gemini
- Full integration with backend

✅ **Architecture Stabilization**
- Plugin architecture cleanup
- Pipeline registry cleanup
- Folder structure normalization
- Code pattern enforcement

✅ **Governance Enforcement**
- Naming convention validation
- Folder structure validation
- Forbidden vocabulary prevention
- Contributor guidelines

✅ **Documentation**
- Complete API documentation
- Complete MCP documentation
- Complete governance documentation
- Migration guides

### **What v1.0.0 Does NOT Change**
- ✅ Phase 15 video pipeline unchanged
- ✅ Phase 16 async job system unchanged
- ✅ v0.9.0 video upload unchanged
- ✅ Image analysis unchanged
- ✅ Web UI unchanged (except minor fixes)

### **Key Principle**
> **v1.0.0 = MCP + Stabilization. Production Ready.**

---

# 🏗️ 2. HIGH-LEVEL DESIGN (HLD) — v1.0.0

## **System Architecture (v1.0.0)**

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Web UI (v0.9.0)              Gemini-CLI (NEW)               │
│  - Plugin Selector            - MCP Client                   │
│  - Tool Selector              - Tool Discovery               │
│  - Image Upload               - Image Analysis               │
│  - Video Upload               - Video Processing             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       API LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  REST API (Existing)          MCP API (NEW)                  │
│  - /v1/image/analyze          - /mcp/tools                   │
│  - /v1/video/submit           - /mcp/schema                  │
│  - /v1/video/status           - /mcp/execute/{tool}          │
│  - /v1/video/results                                         │
│  - /v1/plugins                                               │
│  - /v1/pipelines                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (NEW)             Pipeline Registry (CLEANED)    │
│  - Tool Registry              - Phase 15 Video               │
│  - Schema Generator           - Image Pipelines              │
│  - Tool Executor              - Tool Mapping                 │
│                                                               │
│  Plugin Manager (CLEANED)     Job Manager (Existing)         │
│  - Plugin Discovery           - Job Creation                 │
│  - Manifest Validation        - Status Tracking              │
│  - Type Validation            - Result Storage               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER (Unchanged)                │
├─────────────────────────────────────────────────────────────┤
│  Worker Process               VideoFilePipelineService       │
│  - Dequeue Jobs               - Frame Extraction             │
│  - Execute Pipelines          - YOLO Detection               │
│  - Save Results               - OCR Processing               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                PERSISTENCE LAYER (Unchanged)                 │
├─────────────────────────────────────────────────────────────┤
│  Database                     Object Storage                 │
│  Queue                                                        │
└─────────────────────────────────────────────────────────────┘
```

## **New Components in v1.0.0**

### **1. MCP Server**
- **Location:** `/mcp/server.py`
- **Responsibilities:**
  - Serve MCP schema
  - Serve tool list
  - Execute tools
  - Map tools to pipelines
  - Map tools to plugins

### **2. Tool Registry**
- **Location:** `/mcp/tool_registry.py`
- **Responsibilities:**
  - Discover available tools
  - Validate tool definitions
  - Map tools to backend pipelines

### **3. Schema Generator**
- **Location:** `/mcp/schema_generator.py`
- **Responsibilities:**
  - Generate MCP schema from tool definitions
  - Validate schema
  - Serve schema via `/mcp/schema`

### **4. Tool Executor**
- **Location:** `/mcp/executor.py`
- **Responsibilities:**
  - Execute tools via plugins
  - Execute tools via pipelines
  - Handle tool parameters
  - Return tool results

### **5. Gemini-CLI MCP Extension**
- **Location:** `/gemini-cli-extension/`
- **Responsibilities:**
  - MCP client implementation
  - Connect to MCP server
  - Discover tools
  - Execute tools from Gemini CLI
  - Display results in Gemini

## **MCP Data Flow**

```
Gemini CLI
  → Gemini-CLI MCP Extension (MCP Client)
    → GET /mcp/tools
      → Tool Registry
        → Returns: [
            { name: "analyze_image", description: "...", parameters: {...} },
            { name: "process_video", description: "...", parameters: {...} }
          ]
    → User selects "analyze_image"
    → POST /mcp/execute/analyze_image
        Body: { image_base64: "...", pipeline_id: "yolo_ocr" }
      → Tool Executor
        → Load pipeline "yolo_ocr"
        → Execute via Plugin Manager
        → Return results
      → Gemini-CLI displays results
```

---

# 📝 3. FUNCTIONAL REQUIREMENTS — v1.0.0

## **FR-1: MCP Server Must Serve Tools**
**Description:** MCP server must expose available tools via `/mcp/tools`.

**Acceptance Criteria:**
- ✅ `/mcp/tools` returns valid tool list
- ✅ Each tool includes name, description, parameters
- ✅ Tool list is discoverable by MCP clients

---

## **FR-2: MCP Server Must Serve Schema**
**Description:** MCP server must expose MCP schema via `/mcp/schema`.

**Acceptance Criteria:**
- ✅ `/mcp/schema` returns valid JSON schema
- ✅ Schema describes all tools
- ✅ Schema validates against MCP spec

---

## **FR-3: MCP Server Must Execute Tools**
**Description:** MCP server must execute tools via `/mcp/execute/{tool}`.

**Acceptance Criteria:**
- ✅ Tool execution works for image analysis
- ✅ Tool execution works for video processing
- ✅ Tool parameters are validated
- ✅ Tool results are returned

---

## **FR-4: Gemini-CLI Extension Must Connect**
**Description:** Gemini-CLI extension must connect to MCP server.

**Acceptance Criteria:**
- ✅ Extension discovers MCP server
- ✅ Extension fetches tool list
- ✅ Extension fetches schema
- ✅ Extension is ready to execute tools

---

## **FR-5: Gemini-CLI Extension Must Execute Tools**
**Description:** Gemini-CLI extension must execute tools from Gemini.

**Acceptance Criteria:**
- ✅ User can analyze images from Gemini
- ✅ User can process videos from Gemini
- ✅ Results are displayed in Gemini
- ✅ Errors are displayed in Gemini

---

## **FR-6: Plugin Architecture Must Be Consistent**
**Description:** All plugins must follow same structure.

**Acceptance Criteria:**
- ✅ All manifests are valid
- ✅ All plugin types are correct
- ✅ All tool definitions are correct
- ✅ All run() signatures are consistent

---

## **FR-7: Pipeline Registry Must Be Clean**
**Description:** Pipeline registry must be rebuilt and validated.

**Acceptance Criteria:**
- ✅ All pipelines load correctly
- ✅ All pipeline configs are valid
- ✅ Tools map correctly to pipelines

---

## **FR-8: Governance Rules Must Be Enforced**
**Description:** CI must validate governance rules.

**Acceptance Criteria:**
- ✅ Folder structure is validated
- ✅ Naming conventions are validated
- ✅ Forbidden vocabulary is prevented
- ✅ All PRs pass governance checks

---

# 📝 4. NON-FUNCTIONAL REQUIREMENTS — v1.0.0

## **NFR-1: Backward Compatibility**
**Description:** v1.0.0 must not break existing functionality.

**Acceptance Criteria:**
- ✅ All Phase 15 tests pass
- ✅ All Phase 16 tests pass
- ✅ All v0.9.0 tests pass
- ✅ Web UI still works
- ✅ REST API still works

---

## **NFR-2: MCP Compliance**
**Description:** MCP implementation must follow MCP spec.

**Acceptance Criteria:**
- ✅ Schema is MCP-compliant
- ✅ Tool definitions are MCP-compliant
- ✅ Tool execution is MCP-compliant

---

## **NFR-3: Performance**
**Description:** v1.0.0 must not degrade performance.

**Acceptance Criteria:**
- ✅ Image analysis latency unchanged
- ✅ Video processing latency unchanged
- ✅ MCP tool execution is fast (<1s overhead)

---

## **NFR-4: Code Quality**
**Description:** Codebase must be clean and maintainable.

**Acceptance Criteria:**
- ✅ No dead code
- ✅ No duplicate code
- ✅ Consistent naming
- ✅ Consistent structure

---

## **NFR-5: Documentation**
**Description:** All features must be documented.

**Acceptance Criteria:**
- ✅ MCP API documented
- ✅ Tool definitions documented
- ✅ Gemini-CLI usage documented
- ✅ Governance rules documented

---

## **NFR-6: Test Coverage**
**Description:** All new functionality must be tested.

**Acceptance Criteria:**
- ✅ MCP server has unit tests
- ✅ MCP server has integration tests
- ✅ Gemini-CLI has integration tests
- ✅ Governance has validation tests

---

# 👤 5. USER STORIES — v1.0.0

## **US-1: Analyze Images via Gemini**
**As a user**  
I want to analyze images using Gemini CLI  
So that I can get YOLO + OCR results without leaving Gemini.

**Acceptance Criteria:**
- ✅ I can use Gemini to analyze images
- ✅ I receive YOLO detections
- ✅ I receive OCR text
- ✅ Results appear in Gemini

---

## **US-2: Process Videos via Gemini**
**As a user**  
I want to process videos using Gemini CLI  
So that I can get video analysis results without leaving Gemini.

**Acceptance Criteria:**
- ✅ I can submit videos via Gemini
- ✅ I receive job_id
- ✅ I can check status via Gemini
- ✅ I receive results via Gemini

---

## **US-3: Discover Available Tools**
**As a developer**  
I want to discover available MCP tools  
So that I know what the system can do.

**Acceptance Criteria:**
- ✅ I can call `/mcp/tools`
- ✅ I receive tool list
- ✅ Each tool has clear description
- ✅ Each tool has parameter schema

---

## **US-4: Consistent Plugin Architecture**
**As a developer**  
I want all plugins to follow the same structure  
So that I can maintain and extend them easily.

**Acceptance Criteria:**
- ✅ All plugins have valid manifests
- ✅ All plugins follow naming conventions
- ✅ All plugins implement correct signatures

---

## **US-5: Enforce Governance Rules**
**As a maintainer**  
I want CI to enforce governance rules  
So that code quality remains high.

**Acceptance Criteria:**
- ✅ CI validates folder structure
- ✅ CI validates naming conventions
- ✅ CI prevents forbidden vocabulary
- ✅ PRs cannot merge if governance fails

---

# 🛠️ 6. DEVELOPMENT PLAN — v1.0.0

## **Epic 1: MCP Server Implementation (8 commits)**

### **Commit 1: Create MCP Server Skeleton**
**Files Added:**
- `/mcp/server.py`
- `/mcp/__init__.py`

**Tests:**
- ✅ Server starts
- ✅ Server responds to `/mcp/health`

---

### **Commit 2: Implement Tool Registry**
**Files Added:**
- `/mcp/tool_registry.py`

**Tests:**
- ✅ Tool registry discovers tools
- ✅ Tool registry validates tool definitions

---

### **Commit 3: Implement Schema Generator**
**Files Added:**
- `/mcp/schema_generator.py`

**Tests:**
- ✅ Schema is generated correctly
- ✅ Schema is MCP-compliant

---

### **Commit 4: Implement /mcp/tools Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint returns tool list
- ✅ Tool list is correct

---

### **Commit 5: Implement /mcp/schema Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint returns schema
- ✅ Schema is valid

---

### **Commit 6: Implement Tool Executor**
**Files Added:**
- `/mcp/executor.py`

**Tests:**
- ✅ Executor runs tools
- ✅ Executor validates parameters
- ✅ Executor returns results

---

### **Commit 7: Implement /mcp/execute/{tool} Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint executes tools
- ✅ Image analysis works
- ✅ Video processing works

---

### **Commit 8: Add MCP Integration Tests**
**Files Added:**
- `/tests/mcp/test_server.py`
- `/tests/mcp/test_tools.py`

**Tests:**
- ✅ Full MCP flow works
- ✅ All tools work

---

## **Epic 2: Gemini-CLI Extension (5 commits)**

### **Commit 9: Create Extension Skeleton**
**Files Added:**
- `/gemini-cli-extension/mcp_client.py`
- `/gemini-cli-extension/__init__.py`

**Tests:**
- ✅ Extension initializes

---

### **Commit 10: Implement MCP Client**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Client connects to server
- ✅ Client fetches tools
- ✅ Client fetches schema

---

### **Commit 11: Implement Tool Discovery**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Extension discovers tools
- ✅ Tools are listed correctly

---

### **Commit 12: Implement Tool Execution**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Extension executes tools
- ✅ Image analysis works
- ✅ Video processing works

---

### **Commit 13: Add Extension Integration Tests**
**Files Added:**
- `/gemini-cli-extension/tests/test_integration.py`

**Tests:**
- ✅ Full Gemini → MCP → Backend flow works

---

## **Epic 3: Architecture Cleanup (6 commits)**

### **Commit 14: Fix Plugin Manifests**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All manifests validate

---

### **Commit 15: Fix Plugin Types**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All plugin types are correct

---

### **Commit 16: Fix Tool Definitions**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All tool definitions are correct

---

### **Commit 17: Fix Plugin run() Signatures**
**Files Changed:**
- All `/plugins/*/__init__.py`

**Tests:**
- ✅ All signatures are consistent

---

### **Commit 18: Rebuild Pipeline Registry**
**Files Changed:**
- `/core/pipeline_registry.py`
- Pipeline configs

**Tests:**
- ✅ All pipelines load correctly

---

### **Commit 19: Normalize Folder Structure**
**Files Changed:**
- Move files to correct locations

**Tests:**
- ✅ All imports work
- ✅ All tests pass

---

## **Epic 4: Governance (4 commits)**

### **Commit 20: Add Folder Structure Validator**
**Files Added:**
- `/governance/validate_structure.py`
- `.github/workflows/governance.yml`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 21: Add Naming Convention Validator**
**Files Added:**
- `/governance/validate_naming.py`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 22: Add Forbidden Vocabulary Validator**
**Files Added:**
- `/governance/validate_vocabulary.py`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 23: Add Contributor Guidelines**
**Files Added:**
- `/CONTRIBUTING.md`
- `/GOVERNANCE.md`

**Tests:**
- ✅ Documentation is clear

---

## **Epic 5: Documentation (2 commits)**

### **Commit 24: Add MCP Documentation**
**Files Added:**
- `/docs/mcp/api.md`
- `/docs/mcp/tools.md`
- `/docs/mcp/gemini-cli.md`

**Tests:**
- ✅ Documentation is complete

---

### **Commit 25: Update CHANGELOG and Release**
**Files Changed:**
- `/CHANGELOG.md`
- Version bump

**Tests:**
- ✅ All tests pass
- ✅ All features work
- ✅ Ready for v1.0.0 release

---

# 🔄 7. PULL REQUEST TEMPLATE — v1.0.0

```markdown
## PR Title
[v1.0.0 / Epic N / Commit M] Brief description

## Epic
Epic N: Epic Name

## Commit Number
Commit M of 25

## Description
What does this PR do?

## Why
Why is this change necessary?

## Files Changed
- `/path/to/file1.py`
- `/path/to/file2.ts`

## Tests Added/Modified
- ✅ Test 1 description
- ✅ Test 2 description

## Acceptance Criteria
- ✅ Criterion 1
- ✅ Criterion 2

## Backward Compatibility Check
- ✅ Phase 15 tests pass
- ✅ Phase 16 tests pass
- ✅ v0.9.0 tests pass
- ✅ Web UI works
- ✅ REST API works

## Governance Check
- ✅ Folder structure valid
- ✅ Naming conventions followed
- ✅ No forbidden vocabulary

## Related Issues
Part of v1.0.0 MCP integration

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

# ✅ FINAL SUMMARY

## **v0.9.0 Deliverables**
- ✅ Video upload to Web UI
- ✅ Job status tracking
- ✅ Job results display
- ✅ Full integration with Phase 16 async system
- ✅ 15 atomic commits
- ✅ Zero regressions

## **v1.0.0 Deliverables**
- ✅ MCP server
- ✅ MCP schema
- ✅ Tool registry
- ✅ Tool executor
- ✅ Gemini-CLI MCP extension
- ✅ Plugin architecture cleanup
- ✅ Pipeline registry cleanup
- ✅ Governance enforcement
- ✅ Complete documentation
- ✅ 25 atomic commits
- ✅ Production ready

---

**Roger, this is the complete, production-ready documentation for both v0.9.0 and v1.0.0. Everything is grounded in reality, fully detailed, and ready to implement.**