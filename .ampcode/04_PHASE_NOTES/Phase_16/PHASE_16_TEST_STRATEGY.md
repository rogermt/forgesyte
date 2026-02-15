# Phase 16 Test Strategy

**Date**: 2026-2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution

---

## Overview

This guide documents how to test all Phase 16 functionality, including unit tests, integration tests, and system tests.

---

## Test Structure

```
server/app/tests/jobs/
├── test_job_model.py              # Job model tests
├── test_job_queue_service.py        # Queue service tests
├── test_worker.py                  # Worker logic tests
├── test_job_submission_endpoint.py  # Submit endpoint tests
├── test_job_status_endpoint.py      # Status endpoint tests
├── test_job_results_endpoint.py     # Results endpoint tests
└── test_worker_integration.py      # Worker integration tests
```

---

## Running Tests

### Prerequisites

```bash
cd server
uv sync  # Ensure dependencies are installed
```

### Run All Job Tests

```bash
cd server
uv run pytest app/tests/jobs -v
```

### Run Specific Test Suites

```bash
# Unit tests only
uv run pytest app/tests/jobs/test_job_model.py -v

# Integration tests only
uv run pytest app/tests/jobs/test_job_submission_endpoint.py -v

# Worker integration tests only
uv run pytest app/tests/jobs/test_worker_integration.py -v
```

---

## Test Descriptions

### Unit Tests (`test_job_model.py`)

Tests the Job model in isolation.

| Test | Description |
|------|-------------|
| `test_job_creation` | Job can be created with required fields |
| `test_job_status_transitions` | Status transitions work correctly |
| `test_job_timestamps` | Created/updated timestamps are set |
| `test_job_validation` | Invalid status values rejected |

### Unit Tests (`test_job_queue_service.py`)

Tests the queue service in isolation with mocked database.

| Test | Description |
|------|-------------|
| `test_enqueue_job` | Job can be enqueued |
| `test_dequeue_job` | Job can be dequeued |
| `test_queue_empty` | Empty queue returns None |
| `test_queue_fifo` | Queue is FIFO |

### Unit Tests (`test_worker.py`)

Tests the worker logic with mocked dependencies.

| Test | Description |
|------|-------------|
| `test_process_job_success` | Successful job processing |
| `test_process_job_failure` | Failed job handling |
| `test_process_job_updates_status` | Status updates during processing |
| `test_process_job_stores_results` | Results are stored correctly |

### Integration Tests (`test_job_submission_endpoint.py`)

Tests the submit endpoint with real database and queue.

| Test | Description |
|------|-------------|
| `test_submit_job_success` | Valid MP4 → job created and enqueued |
| `test_submit_job_invalid_file` | Invalid file type → 400 |
| `test_submit_job_queue_error` | Queue unavailable → 503 |
| `test_submit_job_db_error` | Database error → 503 |

### Integration Tests (`test_job_status_endpoint.py`)

Tests the status endpoint.

| Test | Description |
|------|-------------|
| `test_get_status_pending` | Pending job status |
| `test_get_status_running` | Running job status |
| `test_get_status_completed` | Completed job status |
| `test_get_status_failed` | Failed job status |
| `test_get_status_not_found` | Non-existent job → 404 |

### Integration Tests (`test_job_results_endpoint.py`)

Tests the results endpoint.

| Test | Description |
|------|-------------|
| `test_get_results_completed` | Completed job results |
| `test_get_results_pending` | Pending job → 404 |
| `test_get_results_not_found` | Non-existent job → 404 |
| `test_results_match_phase15_format` | Results match Phase 15 format |

### System Tests (`test_worker_integration.py`)

Tests full worker lifecycle.

| Test | Description |
|------|-------------|
| `test_worker_lifecycle` | Worker processes job end-to-end |
| `test_worker_error_handling` | Worker handles errors gracefully |
| `test_worker_status_updates` | Worker updates status correctly |
| `test_worker_retry_logic` | Worker retries on transient errors |

---

## Test Data

### Test MP4 File

```
server/app/tests/fixtures/job_test.mp4
```

3-frame test video for job processing tests.

### Test Queue Payload

```python
{
    "job_id": "550e8400-e29b-41d44-a716-446655440000"
}
```

### Test Job Record

```python
{
    "job_id": "550e8400-eonb-41d4-a716-446655440000",
    "status": "pending",
    "created_at": "2026-02-13T00:00:00Z",
    "updated_at": "2026-02-13T00:00:00Z",
    "input_path": "/uploads/job_test.mp4",
    "output_path": null,
    "error_message": null,
    "pipeline_id": "yolo_ocr",
    "frame_stride": 1,
    "max_frames": null
}
```

---

## Mocking Strategy

### Mock Queue Service

```python
from unittest.mock import Mock

def test_submit_job_success():
    mock_queue = Mock()
    mock_queue.enqueue.return_value = True
    
    # Test with mock queue
    result = submit_job(file, mock_queue)
    assert result.job_id is not None
```

### Mock Database

```python
from unittest.mock import Mock

def test_job_creation():
    mock_db = Mock()
    mock_db.create_job.return_value = job_record
    
    # Test with mock database
    result = create_job(mock_db)
    assert result.status == "pending"
```

### Mock VideoFilePipelineService

```python
from unittest.mock import Mock

def test_worker_process_job():
    mock_pipeline = Mock()
    mock_pipeline.run_on_file.return_value = results
    
    # Test with mock pipeline
    worker.process_job(job_id, mock_pipeline)
    assert job.status == "completed"
```

---

## Integration Test Setup

### Test Database

```python
import sqlite3

def setup_test_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            input_path TEXT NOT NULL,
            output_path TEXT,
            error_message TEXT,
            pipeline_id TEXT NOT NULL,
            frame_stride INTEGER DEFAULT 1,
            max_frames INTEGER
        )
    """)
    return conn
```

### Test Queue

```python
from collections import deque

def setup_test_queue():
    return deque()
```

---

## Test Execution Order

### Unit Tests (Fastest)

1. Job model tests
2. Queue service tests
3. Worker logic tests

### Integration Tests (Medium)

4. Submit endpoint tests
5. Status endpoint tests
6. Results endpoint tests

### System Tests (Slowest)

7. Worker integration tests
8. End-to-end job lifecycle tests

---

## Common Issues

### Issue: Tests fail with "Queue not found"

**Solution**: Ensure queue is initialized in test setup

### Issue: Tests fail with "Job not found"

**Solution**: Ensure job is created in test setup

### Issue: Worker tests timeout

**Solution**: Ensure worker is properly mocked or test is configured with timeout

---

## CI Integration

All tests run automatically in CI via:
- `.github/workflows/ci.yml` - Main CI workflow
- `.github/workflows/phase16_validation.yml` - Phase 16 governance workflow

Both workflows must pass before merging to `main`.

---

## See Also

- `PHASE_16_OVERVIEW.md` - Feature overview
- `PHASE_16_SCOPE.md` - What's in/out of scope
- `PHASE_16_DEFINITION_OF_DONE.md` - Completion criteria
- `PHASE_16_ARCHITECTURE.md` - System architecture
- `PHASE_16_ENDPOINTS.md` - API specification
- `PHASE_16_WORKER_LIFECYCLE.md` - Worker behavior
- `PHASE_16_GOVERNANCE_RULES.md` - Governance rules