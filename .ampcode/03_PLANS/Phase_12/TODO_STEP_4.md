# Step 4 Implementation Plan - API Route Layer

## Overview

Step 4 focuses on creating the API route layer for analysis execution. This is where HTTP requests are translated into service calls and responses are formatted.

## Current Status (After Step 3)

**Files Already Created:**
- `server/app/services/execution/__init__.py` ✓
- `server/app/services/execution/plugin_execution_service.py` ✓
- `server/app/services/execution/job_execution_service.py` ✓
- `server/app/services/execution/analysis_execution_service.py` ✓

**Tests Already Created:**
- `server/tests/execution/test_plugin_execution_service.py` ✓ (9 tests)
- `server/tests/execution/test_job_execution_service.py` ✓ (20 tests)

---

## Step 4 Deliverables

### Files to Create

1. **`server/app/api/routes/analysis_execution.py`** - API route handlers
   - POST `/v1/analyze-execution` - Synchronous analysis execution
   - POST `/v1/analyze-execution/async` - Asynchronous analysis submission
   - GET `/v1/analyze-execution/jobs/{job_id}` - Get job status
   - GET `/v1/analyze-execution/jobs/{job_id}/result` - Get job result
   - GET `/v1/analyze-execution/jobs` - List jobs
   - DELETE `/v1/analyze-execution/jobs/{job_id}` - Cancel job

2. **`server/tests/execution/test_analysis_execution_endpoint.py`** - API endpoint tests
   - Test request validation
   - Test response formatting
   - Test error handling (400, 404)
   - Test async workflow

---

## Implementation Checklist

### Step 4.1: Create API Routes Directory Structure
- [ ] Create `server/app/api/routes/` directory (if not exists)
- [ ] Create `server/app/api/routes/__init__.py`

### Step 4.2: Create analysis_execution.py Route File
- [ ] Import FastAPI components (APIRouter, HTTPException, Depends, status)
- [ ] Import AnalysisExecutionService
- [ ] Import authentication dependencies
- [ ] Create router: `router = APIRouter(prefix="/analyze-execution", tags=["analysis-execution"])`
- [ ] Implement POST `/` - Synchronous analysis
- [ ] Implement POST `/async` - Asynchronous analysis
- [ ] Implement GET `/jobs/{job_id}` - Get job status
- [ ] Implement GET `/jobs/{job_id}/result` - Get job result
- [ ] Implement GET `/jobs` - List jobs with optional filtering
- [ ] Implement DELETE `/jobs/{job_id}` - Cancel job
- [ ] Add proper response models

### Step 4.3: Modify main.py to Mount Router
- [ ] Import AnalysisExecutionRouter from `server.app.api.routes.analysis_execution`
- [ ] Add `app.include_router(analysis_execution_router, prefix=settings.api_prefix)`
- [ ] Add AnalysisExecutionService to app.state in lifespan

### Step 4.4: Create API Endpoint Tests
- [ ] Create `tests/execution/test_analysis_execution_endpoint.py`
- [ ] Test POST `/` - Valid request returns 200
- [ ] Test POST `/` - Invalid request returns 400
- [ ] Test POST `/async` - Returns job_id and queued status
- [ ] Test GET `/jobs/{job_id}` - Returns job status
- [ ] Test GET `/jobs/{job_id}/result` - Returns job result
- [ ] Test GET `/jobs` - Returns list of jobs
- [ ] Test DELETE `/jobs/{job_id}` - Cancels job
- [ ] Test 404 for non-existent job
- [ ] Test async workflow (submit → poll → get result)

---

## File Structure After Step 4

```
server/app/
├── api/
│   ├── routes/
│   │   ├── __init__.py
│   │   └── analysis_execution.py  ← NEW
│   └── main.py [MODIFIED: include router, add service to state]
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
  "plugin_name": "yolo_football",
  "tool_name": "detect",
  "args": {
    "frame_base64": "<base64 encoded image>",
    "device": "cpu",
    "confidence": 0.5
  },
  "mime_type": "image/png"
}
```

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "success",
  "result": {...},
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:00:01Z"
}
```

**Response (400):** Invalid request parameters

### 2. POST `/v1/analyze-execution/async`

**Purpose:** Asynchronous submission - returns immediately with job_id.

**Request Body:** Same as synchronous

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 3. GET `/v1/analyze-execution/jobs/{job_id}`

**Purpose:** Poll for job status.

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "running",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 4. GET `/v1/analyze-execution/jobs/{job_id}/result`

**Purpose:** Get completed job result.

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "success",
  "result": {...},
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:00:01Z"
}
```

### 5. GET `/v1/analyze-execution/jobs`

**Purpose:** List jobs with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (queued, running, success, failed)
- `limit` (optional): Max results (default 50, max 200)

**Response (200):**
```json
{
  "jobs": [...],
  "count": 10
}
```

### 6. DELETE `/v1/analyze-execution/jobs/{job_id}`

**Purpose:** Cancel a queued job.

**Response (200):**
```json
{
  "job_id": "uuid",
  "status": "cancelled"
}
```

---

## Dependencies to Import

```python
# In analysis_execution.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import require_auth
from app.services.execution.analysis_execution_service import AnalysisExecutionService
from app.models import JobStatus
```

---

## Response Models (Pydantic)

```python
class AnalysisExecutionRequest(BaseModel):
    """Request model for analysis execution."""
    plugin_name: str = Field(..., description="Name of the plugin to execute")
    tool_name: str = Field(..., description="Name of the tool to run")
    args: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific arguments")
    mime_type: str = Field(default="image/png", description="MIME type of input")


class AnalysisExecutionResponse(BaseModel):
    """Response model for analysis execution."""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None


class AsyncJobResponse(BaseModel):
    """Response model for async job submission."""
    job_id: str
    status: str
    created_at: str


class JobListResponse(BaseModel):
    """Response model for job listing."""
    jobs: List[Dict[str, Any]]
    count: int
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

1. **Separate router file** - `analysis_execution.py` keeps Phase 12 routes separate from Phase 11 routes in `api.py`

2. **Same authentication** - Use existing `require_auth` dependency for consistency

3. **Response models** - Pydantic models for request/response validation

4. **Error handling** - Return 400 for validation errors, 404 for not found, never 500 (all errors structured)

5. **Backward compatibility** - Does NOT modify existing `/analyze` or `/jobs` endpoints

---

## Execution Flow

```
HTTP Request (POST /v1/analyze-execution)
  ↓
analysis_execution.py router
  ↓
AnalysisExecutionService.submit_analysis()
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

- [ ] API route file created at `server/app/api/routes/analysis_execution.py`
- [ ] Router mounted in `main.py`
- [ ] AnalysisExecutionService added to app.state
- [ ] All 6 endpoints implemented
- [ ] Response models defined
- [ ] Tests created at `tests/execution/test_analysis_execution_endpoint.py`
- [ ] All endpoint tests pass
- [ ] Phase 11 tests still pass (no regressions)
- [ ] Ruff lint clean
- [ ] Mypy type check clean

