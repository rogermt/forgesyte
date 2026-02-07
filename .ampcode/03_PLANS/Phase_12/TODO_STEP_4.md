# Step 4 Implementation Plan - API Route Layer

## Overview

Step 4 focuses on enhancing the API route layer for analysis execution. HTTP requests are translated into service calls and responses are formatted.

## Current Status (After Step 3)

**Files Already Created:**
- `server/app/services/execution/__init__.py` ✓
- `server/app/services/execution/plugin_execution_service.py` ✓
- `server/app/services/execution/job_execution_service.py` ✓
- `server/app/services/execution/analysis_execution_service.py` ✓

**Tests Already Created:**
- `server/tests/execution/test_plugin_execution_service.py` ✓ (9 tests)
- `server/tests/execution/test_job_execution_service.py` ✓ (20 tests)

**Existing Route File:**
- `server/app/api_routes/routes/execution.py` - Already exists with basic `POST /v1/analyze-execution`

---

## Step 4 Deliverables

### Files to Modify

1. **`server/app/api_routes/routes/execution.py`** - Enhance existing route file
   - POST `/v1/analyze-execution` - Synchronous analysis (already exists)
   - POST `/v1/analyze-execution/async` - Asynchronous analysis submission
   - GET `/v1/analyze-execution/jobs/{job_id}` - Get job status
   - GET `/v1/analyze-execution/jobs/{job_id}/result` - Get job result
   - GET `/v1/analyze-execution/jobs` - List jobs
   - DELETE `/v1/analyze-execution/jobs/{job_id}` - Cancel job

2. **`server/tests/execution/test_analysis_execution_endpoint.py`** - API endpoint tests (CREATE NEW)

---

## Implementation Checklist

### Step 4.1: Enhance execution.py Route File
- [ ] Add Pydantic request models
- [ ] Implement POST `/v1/analyze-execution/async` - Asynchronous analysis
- [ ] Implement GET `/v1/analyze-execution/jobs/{job_id}` - Get job status
- [ ] Implement GET `/v1/analyze-execution/jobs/{job_id}/result` - Get job result
- [ ] Implement GET `/v1/analyze-execution/jobs` - List jobs with optional filtering
- [ ] Implement DELETE `/v1/analyze-execution/jobs/{job_id}` - Cancel job
- [ ] Add authentication dependency to all endpoints

### Step 4.2: Modify main.py to Mount Router
- [ ] Import router from `server.app.api_routes.routes.execution`
- [ ] Add `app.include_router(router)` in main.py

### Step 4.3: Create API Endpoint Tests
- [ ] Create `tests/execution/test_analysis_execution_endpoint.py`
- [ ] Test POST `/v1/analyze-execution` - Valid request returns 200
- [ ] Test POST `/v1/analyze-execution` - Invalid request returns 400
- [ ] Test POST `/v1/analyze-execution/async` - Returns job_id and queued status
- [ ] Test GET `/v1/analyze-execution/jobs/{job_id}` - Returns job status
- [ ] Test GET `/v1/analyze-execution/jobs/{job_id}/result` - Returns job result
- [ ] Test GET `/v1/analyze-execution/jobs` - Returns list of jobs
- [ ] Test DELETE `/v1/analyze-execution/jobs/{job_id}` - Cancels job
- [ ] Test 404 for non-existent job
- [ ] Test 409 for conflict states (job running/completed)
- [ ] Test async workflow (submit → poll → get result)

---

## File Structure After Step 4

```
server/app/
├── api_routes/
│   ├── routes/
│   │   └── execution.py  ← MODIFIED
│   └── __init__.py
├── main.py  ← MODIFIED: include router
└── services/
    └── execution/
        ├── __init__.py
        ├── plugin_execution_service.py
        ├── job_execution_service.py
        └── analysis_execution_service.py

tests/execution/
├── test_plugin_execution_service.py
├── test_job_execution_service.py
├── test_analysis_execution_endpoint.py  ← NEW
└── test_registry_metrics.py
```

---

## Route Specifications

### 1. POST `/v1/analyze-execution`

**Purpose:** Synchronous analysis execution - waits for completion and returns result.

**Request Body:**
```json
{
  "plugin": "yolo_football",
  "image": "<base64 encoded image>",
  "mime_type": "image/png"
}
```

**Response (200):**
```json
{
  "plugin": "yolo_football",
  "result": {...}
}
```

**Response (400):** Invalid request parameters (structured error envelope)

### 2. POST `/v1/analyze-execution/async`

**Purpose:** Asynchronous submission - returns immediately with job_id.

**Request Body:** Same as synchronous

**Response (200):**
```json
{
  "job_id": "uuid"
}
```

### 3. GET `/v1/analyze-execution/jobs/{job_id}`

**Purpose:** Poll for job status.

**Response (200):**
```json
{
  "job": {
    "id": "uuid",
    "plugin": "yolo_football",
    "status": "RUNNING",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:01Z"
  }
}
```

**Response (404):** Job not found

### 4. GET `/v1/analyze-execution/jobs/{job_id}/result`

**Purpose:** Get completed job result.

**Response (200):**
```json
{
  "job_id": "uuid",
  "plugin": "yolo_football",
  "status": "SUCCESS",
  "result": {...},
  "error": null
}
```

**Response (404):** Job not found
**Response (409):** Job still running

### 5. GET `/v1/analyze-execution/jobs`

**Purpose:** List jobs with optional filtering.

**Query Parameters:**
- `plugin` (optional): Filter by plugin name
- `status` (optional): Filter by status (QUEUED, RUNNING, SUCCESS, FAILED)

**Response (200):**
```json
{
  "jobs": [...]
}
```

### 6. DELETE `/v1/analyze-execution/jobs/{job_id}`

**Purpose:** Cancel a queued job.

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "FAILED",
  "cancelled": true
}
```

**Response (404):** Job not found
**Response (409):** Job already completed

---

## Dependencies to Import

```python
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.auth import require_auth
from app.services.execution.analysis_execution_service import AnalysisExecutionService
```

---

## Response Models (Pydantic)

```python
class AnalyzeExecutionRequest(BaseModel):
    """Request model for analysis execution."""
    plugin: str = "default"
    image: str
    mime_type: str = "image/png"


class AnalyzeExecutionResponse(BaseModel):
    """Response model for analysis execution."""
    plugin: str
    result: Dict[str, Any]


class JobStatus(BaseModel):
    """Job status model."""
    id: str
    plugin: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response for job status endpoint."""
    job: JobStatus


class JobResultResponse(BaseModel):
    """Response for job result endpoint."""
    job_id: str
    plugin: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Response for job list endpoint."""
    jobs: List[JobStatus]


class JobCancelResponse(BaseModel):
    """Response for job cancellation endpoint."""
    job_id: str
    status: str
    cancelled: bool
```

---

## Testing Commands

```bash
# Run the new endpoint tests
pytest tests/execution/test_analysis_execution_endpoint.py -v

# Run all execution tests
pytest tests/execution/ -v

# Verify Phase 11 still passes
pytest tests/phase_11 -v
```

---

## Key Design Decisions

1. **Use existing route file** - `server/app/api_routes/routes/execution.py` already exists

2. **Same authentication** - Use existing `require_auth` dependency for consistency

3. **Response models** - Pydantic models for request/response validation

4. **Error handling** - Return 400 for validation, 404 for not found, 409 for conflict, never 500

5. **Backward compatibility** - Does NOT modify existing `/analyze` or `/jobs` endpoints in api.py

---

## Execution Flow

```
HTTP Request (POST /v1/analyze-execution)
  ↓
execution.py router
  ↓
AnalysisExecutionService.analyze()
  ↓
JobExecutionService.create_job() + run_job()
  ↓
PluginExecutionService.execute()
  ↓
ToolRunner.run()
  ├─ validate_input_payload()
  ├─ plugin.run() [ONLY PLACE]
  ├─ validate_plugin_output()
  ├─ try/except → error_envelope()
  └─ finally: registry.update_execution_metrics()
  ↓
Return result/error to router
  ↓
HTTP Response (200 or 400)
```

---

## Success Criteria for Step 4

- [ ] Enhanced route file at `server/app/api_routes/routes/execution.py`
- [ ] All 6 endpoints implemented (1 existing + 5 new)
- [ ] Router properly mounted in main.py
- [ ] Tests created at `tests/execution/test_analysis_execution_endpoint.py`
- [ ] All endpoint tests pass
- [ ] Phase 11 tests still pass (no regressions)
- [ ] Ruff lint clean
- [ ] Mypy type check clean

