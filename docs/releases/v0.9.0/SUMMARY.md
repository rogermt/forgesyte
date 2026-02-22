# v0.9.0 Release Summary

## Overview
v0.9.0 delivers **video upload functionality to the Web UI** by completing the Phase 16 async job system using existing infrastructure. This is a focused, two-stage release that replaces the broken Phase 17 delivery.

**Key Principle**: Use Existing Infrastructure + Add Video Upload UI. Zero New Services. Zero Regressions.

## Background

### Previous Releases
- **v0.8.0 (Phase 15)**: Stable synchronous batch video processing (YOLO + OCR pipeline)
- **v0.8.1 (Phase 16)**: Partial async job system (incomplete, missing pipeline registry)
- **Phase 17**: Rejected - broken delivery with regressions, experimental code, architectural drift

### Phase 16 Incompleteness
- `/v1/video/submit` exists but requires `pipeline_id` parameter (made optional in v0.9.0)
- No default pipeline configured (added `ocr_only` in v0.9.0-alpha)
- YOLO plugin has unpickling error ("unpickling stack underflow") (fixed in v0.9.0-beta)
- No frontend wiring for video upload (added in v0.9.0-alpha)

### Phase 17 Failures
- Removed plugin selector from UI
- Removed tool selector from UI
- Removed image upload from UI
- Introduced experimental streaming code
- Broke Gemini-CLI MCP extension
- Introduced architectural drift
- Broke UI → backend contract

## What v0.9.0 Delivers

### v0.9.0-alpha (OCR-Only Pipeline)
- Fix `/v1/video/submit` to work without `pipeline_id`
- Implement default `ocr_only` pipeline
- Temporarily disable YOLO (due to unpickling bug)
- Wire video upload UI to backend
- End-to-end video upload → OCR results working

### v0.9.0-beta (Full YOLO + OCR Pipeline)
- Fix YOLO unpickling error
- Implement full `yolo_ocr` pipeline
- Display YOLO detections in UI
- Full video analysis working

## What v0.9.0 Does NOT Change
- Plugin selector remains intact
- Tool selector remains intact
- Image upload remains intact
- Phase 15 video pipeline logic unchanged (reused by worker)
- Phase 16 job queue/worker unchanged
- No experimental code added
- No architectural changes
- No breaking changes

## Key Principle
> **v0.9.0 = Fix Async System + Add Video Upload UI. Zero Regressions. Zero Drift.**

## System Architecture

### Backend Changes (v0.9.0-alpha)

#### 1. Fixed: `/v1/video/submit` Endpoint
Made `pipeline_id` optional with default value `"ocr_only"` (backward compatible)

#### 2. New: Pipeline Definition Files (JSON)
Created `/server/pipelines/ocr_only.json` (declarative pipeline definition)

#### 3. Updated: Worker Uses Existing Services
Worker calls existing `VideoFilePipelineService.run_on_file()` (no new services)

### Backend Changes (v0.9.0-beta)

#### 4. Fixed: YOLO Unpickling Error
Root cause: corrupted/incompatible model checkpoint
- Replace model file with fresh YOLOv8 checkpoint
- No architecture changes, just model file swap

#### 5. New: YOLO + OCR Pipeline Definition
Created `/server/pipelines/yolo_ocr.json` (enables full object detection + OCR)

### Frontend Changes (All in v0.9.0-alpha)

#### 1. Video Upload UI Component
- File upload form with MP4 validation
- Submit to `/v1/video/submit`
- Display job_id
- Handle upload progress and errors

#### 2. Job Status Display Component
- Poll `/v1/video/status/{job_id}` every 2 seconds
- Display status (pending/running/completed/failed)
- Display progress percentage

#### 3. Job Results Display Component
- Fetch `/v1/video/results/{job_id}` when complete
- Display OCR text results (alpha)
- Display YOLO detections (beta)
- Format results for readability

## Development Plan

### v0.9.0-alpha (OCR-Only Pipeline)

**Backend Commits (5):**
1. Make pipeline_id optional in `/v1/video/submit`
2. Create ocr_only.json pipeline definition
3. Update worker to use VideoFilePipelineService
4. Add backend integration test
5. Update API documentation

**Frontend Commits (12):**
1. VideoUpload component skeleton
2. File upload form
3. Client-side validation
4. Wire to `/v1/video/submit`
5. Display job_id
6. JobStatus component
7. Status polling
8. JobResults component
9. Fetch and display results
10. Upload progress indicator
11. Error handling UI
12. Wire to main page

**Integration & Release (3 commits):**
13. Integration tests
14. Documentation update
15. Tag `v0.9.0-alpha`

### v0.9.0-beta (YOLO + OCR Pipeline)

**Backend Commits (2):**
1. Fix YOLO unpickling error (replace model file)
2. Create yolo_ocr.json pipeline definition

**Frontend Commits (1):**
1. Display YOLO detections in results

**Integration & Release (3 commits):**
2. Integration tests for YOLO + OCR
3. Documentation update
4. Tag `v0.9.0-beta`

## Key Features

### Functional Requirements
- FR-1: Video Upload Form
- FR-2: Video Submission (fixed in alpha)
- FR-3: Job Status Display
- FR-4: Job Results Display (alpha: OCR only, beta: YOLO + OCR)
- FR-5: Error Handling
- FR-6: No Breaking Changes
- FR-7: Backend Pipeline Execution
- FR-8: YOLO Fix (beta only)

### Non-Functional Requirements
- NFR-1: Backward Compatibility
- NFR-2: Performance
- NFR-3: User Experience
- NFR-4: Code Quality
- NFR-5: Test Coverage
- NFR-6: Phased Delivery

## User Stories
1. Upload Video for Processing (Alpha)
2. Monitor Video Processing Status
3. View OCR Results (Alpha)
4. View YOLO + OCR Results (Beta)
5. Handle Upload Errors
6. Continue Using Existing Features

## Data Flow

### v0.9.0-alpha Flow (OCR Only)
User → Web UI → POST /v1/video/submit (pipeline_id defaults to "ocr_only") → Job Manager → Worker → PipelineExecutor (OCR only) → Results → UI displays OCR text

### v0.9.0-beta Flow (YOLO + OCR)
Same as alpha, but pipeline_id can be "yolo_ocr" → PipelineExecutor runs both YOLO and OCR → UI displays detections + OCR text