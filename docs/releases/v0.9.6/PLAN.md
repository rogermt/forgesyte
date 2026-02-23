# v0.9.6 — Video Job Progress Tracking Implementation Plan

## Overview
This plan implements real-time progress tracking for video-based jobs across the entire stack: database, worker, plugin system, API, and Web-UI.

## Architecture Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| OpenCV Dependency | Use `cv2.VideoCapture` | Fast metadata-only frame count extraction |
| Progress Update Frequency | Throttle to every 5% | Balance accuracy vs DB write volume |
| Plugin Callback Interface | `progress_callback(current_frame, total_frames)` | Worker calculates percentage, plugin stays simple |
| Web-UI Polling | Keep 2 seconds | Good balance of responsiveness and server load |
| Backward Compatibility | Return `progress: null` for old jobs | Clear distinction between "no progress" and "0% progress" |

---

## Phase 1: Database Migration & Model Update

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`server/tests/migrations/test_006_add_progress_column.py`:**
```python
"""TDD tests for v0.9.6 progress column migration."""

import pytest
import sqlalchemy as sa


def test_progress_column_exists(db_engine):
    """RED: Verify progress column will exist after migration."""
    insp = sa.inspect(db_engine)
    columns = [c["name"] for c in insp.get_columns("jobs")]
    assert "progress" in columns, "progress column missing from jobs table"


def test_progress_column_is_nullable(db_engine):
    """RED: Verify progress column is nullable for backward compatibility."""
    insp = sa.inspect(db_engine)
    columns = {c["name"]: c for c in insp.get_columns("jobs")}
    progress_col = columns.get("progress")
    assert progress_col is not None, "progress column not found"
    assert progress_col["nullable"] is True, "progress column should be nullable"


def test_progress_column_is_integer(db_engine):
    """RED: Verify progress column is Integer type."""
    insp = sa.inspect(db_engine)
    columns = {c["name"]: c for c in insp.get_columns("jobs")}
    progress_col = columns.get("progress")
    assert progress_col is not None, "progress column not found"
    assert "int" in str(progress_col["type"]).lower(), "progress should be Integer"
```

**`server/tests/models/test_job_progress.py`:**
```python
"""TDD tests for Job model progress field."""

from app.models.job import Job, JobStatus


def test_job_model_accepts_progress_field(session):
    """RED: Verify Job model can store progress value."""
    job = Job(
        plugin_id="test-plugin",
        tool="test-tool",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=50,  # Should accept progress value
    )
    session.add(job)
    session.commit()
    
    # Verify progress was stored
    assert job.progress == 50


def test_job_model_allows_null_progress(session):
    """RED: Verify Job model allows null progress (backward compatibility)."""
    job = Job(
        plugin_id="test-plugin",
        tool="test-tool",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=None,  # Should allow null
    )
    session.add(job)
    session.commit()
    
    # Verify progress is null
    assert job.progress is None
```

### Files to Create/Edit
- `server/app/migrations/versions/006_add_progress_column.py` (NEW)
- `server/app/models/job.py` (EDIT)

### Implementation Details (GREEN Phase - After Tests Fail)

**Migration 006_add_progress_column.py:**
```python
"""Add progress column to jobs table for v0.9.6 video progress tracking.

Adds integer progress column (0-100) to track video processing progress.
Backfills existing jobs with NULL for backward compatibility.

Revision ID: 006
Revises: 005
Create Date: 2026-02-20 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    """Add progress column as nullable for backward compatibility."""
    op.add_column(
        "jobs",
        sa.Column("progress", sa.Integer(), nullable=True),
    )
    
    # Create index for efficient progress lookups
    op.create_index("ix_jobs_progress", "jobs", ["progress"])


def downgrade():
    """Remove progress column."""
    op.drop_index("ix_jobs_progress", table_name="jobs")
    op.drop_column("jobs", "progress")
```

**Job Model Update (server/app/models/job.py):**
Add after `updated_at` column:
```python
progress = Column(
    Integer,
    nullable=True,  # NULL for jobs created before v0.9.6
    default=None,
)
```

### Tests Required
- Migration test: Verify column exists and is nullable
- Model test: Verify Job model accepts progress field

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
# Create logs directory
mkdir -p logs/v0.9.6

# Run TDD tests (expect RED/failures)
cd server && uv run pytest tests/migrations/test_006_add_progress_column.py tests/models/test_job_progress.py -v > ../logs/v0.9.6/phase1-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement migration and model, then verify tests pass
```bash
# After implementing migration and model updates...

# Run pre-commit tests and save logs (MUST PASS)
uv run pre-commit run --all-files > logs/v0.9.6/phase1-pre-commit.log 2>&1
cd server && uv run pytest tests/migrations/test_006_add_progress_column.py tests/models/test_job_progress.py -v > ../logs/v0.9.6/phase1-pytest.log 2>&1
python scripts/scan_execution_violations.py > logs/v0.9.6/phase1-governance.log 2>&1

# Verify all GREEN
echo "=== Phase 1 Test Results ==="
grep -E "(PASSED|FAILED|ERROR)" logs/v0.9.6/phase1-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
# Add log files to git
git add logs/v0.9.6/phase1-*.log
git add server/app/migrations/versions/006_add_progress_column.py
git add server/app/models/job.py
git commit -m "feat(db): add progress column to jobs table for video progress tracking"
```

---

## Phase 2: Worker Progress Tracking

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`server/tests/app/workers/test_worker_progress.py`:**
```python
"""TDD tests for worker progress tracking."""

import pytest
from unittest.mock import MagicMock, patch
from app.workers.worker import JobWorker
from app.models.job import Job, JobStatus


def test_worker_get_total_frames_with_opencv():
    """RED: Verify _get_total_frames returns correct frame count."""
    worker = JobWorker()
    
    # Mock video file
    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.get.return_value = 1000  # 1000 frames
        mock_instance.release = MagicMock()
        mock_cap.return_value = mock_instance
        
        result = worker._get_total_frames("/tmp/test.mp4")
        assert result == 1000


def test_worker_get_total_frames_fallback():
    """RED: Verify _get_total_frames falls back to 100 on error."""
    worker = JobWorker()
    
    with patch("cv2.VideoCapture", side_effect=Exception("OpenCV error")):
        result = worker._get_total_frames("/tmp/test.mp4")
        assert result == 100  # Fallback heuristic


def test_worker_update_progress_throttled(session):
    """RED: Verify progress updates are throttled to every 5%."""
    worker = JobWorker()
    job = Job(
        job_id="test-job-id",
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
    )
    session.add(job)
    session.commit()
    
    # Update at 1% (should update - first frame)
    worker._update_job_progress("test-job-id", 1, 100, session)
    assert job.progress == 1
    
    # Update at 2% (should NOT update - not 5% boundary)
    worker._update_job_progress("test-job-id", 2, 100, session)
    # Progress should still be 1 (not updated)
    
    # Update at 5% (should update - 5% boundary)
    worker._update_job_progress("test-job-id", 5, 100, session)
    assert job.progress == 5


def test_worker_executes_video_job_with_progress_callback(session, mock_plugin_service):
    """RED: Verify worker passes progress_callback for video jobs."""
    worker = JobWorker(
        plugin_service=mock_plugin_service,
        storage=MagicMock(),
    )
    
    job = Job(
        job_id="test-job-id",
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
    )
    session.add(job)
    session.commit()
    
    # Mock storage to return video path
    worker._storage.load_file.return_value = "/tmp/test.mp4"
    
    # Execute pipeline
    with patch.object(worker, "_get_total_frames", return_value=100):
        worker._execute_pipeline(job, session)
    
    # Verify plugin service was called with progress_callback
    call_args = mock_plugin_service.run_plugin_tool.call_args
    assert "progress_callback" in call_args.kwargs["args"]


def test_worker_sets_100_percent_on_completion(session, mock_plugin_service):
    """RED: Verify worker sets progress to 100% on job completion."""
    worker = JobWorker(
        plugin_service=mock_plugin_service,
        storage=MagicMock(),
    )
    
    job = Job(
        job_id="test-job-id",
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=95,
    )
    session.add(job)
    session.commit()
    
    # Mock successful execution
    mock_plugin_service.run_plugin_tool.return_value = {"detections": []}
    worker._storage.load_file.return_value = "/tmp/test.mp4"
    worker._storage.save_file.return_value = "video/output/test-job-id.json"
    
    # Execute pipeline
    with patch.object(worker, "_get_total_frames", return_value=100):
        worker._execute_pipeline(job, session)
    
    # Verify progress is 100%
    assert job.progress == 100
    assert job.status == JobStatus.completed
```

### Files to Edit
- `server/app/workers/worker.py`

### Implementation Details (GREEN Phase - After Tests Fail)

**Add OpenCV helper method to JobWorker class:**
```python
@staticmethod
def _get_total_frames(video_path: str) -> int:
    """Get total frame count from video metadata using OpenCV.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Total frame count, or 100 as fallback heuristic
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return total if total > 0 else 100
    except Exception:
        return 100  # Fallback heuristic
```

**Add progress update helper:**
```python
def _update_job_progress(self, job_id, current_frame: int, total_frames: int, db) -> None:
    """Update job progress in database, throttled to every 5%.
    
    Args:
        job_id: Job UUID
        current_frame: Current frame being processed
        total_frames: Total frames in video
        db: Database session
    """
    if total_frames <= 0:
        return
        
    percent = int((current_frame / total_frames) * 100)
    percent = max(0, min(100, percent))
    
    # Throttle: only update every 5% to reduce DB writes
    # Also update on first frame (0%) and last frame (100%)
    if current_frame == 1 or current_frame == total_frames or percent % 5 == 0:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.progress = percent
            db.commit()
```

**Modify _execute_pipeline for video jobs:**
In the video job branch (`elif job.job_type == "video":`), add:
```python
# Calculate total frames for progress tracking
video_path = self._storage.load_file(job.input_path)
total_frames = self._get_total_frames(str(video_path))

# Create progress callback
def progress_callback(current_frame: int, total: int = total_frames) -> None:
    self._update_job_progress(job.job_id, current_frame, total, db)

# Add progress_callback to args
args = {
    "video_path": str(video_path),
    "progress_callback": progress_callback,
}
```

**Ensure 100% on completion:**
In the success block after tool execution:
```python
# Mark job as completed with 100% progress
job.status = JobStatus.completed
job.output_path = output_path
job.error_message = None
job.progress = 100  # Ensure 100% on completion
db.commit()
```

### Tests Required
- Worker test: Verify progress updates during video processing
- Worker test: Verify throttling (only updates every 5%)
- Worker test: Verify 100% on completion
- Worker test: Verify fallback to 100 frames when OpenCV fails

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
cd server && uv run pytest tests/app/workers/test_worker_progress.py -v > ../logs/v0.9.6/phase2-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement worker changes, then verify all tests pass
```bash
# Run pre-commit tests and save logs (MUST PASS)
uv run pre-commit run --all-files > logs/v0.9.6/phase2-pre-commit.log 2>&1
cd server && uv run pytest tests/app/workers/test_worker_progress.py -v > ../logs/v0.9.6/phase2-pytest.log 2>&1
python scripts/scan_execution_violations.py > logs/v0.9.6/phase2-governance.log 2>&1

# Verify all GREEN
echo "=== Phase 2 Test Results ==="
grep -E "(PASSED|FAILED|ERROR)" logs/v0.9.6/phase2-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
git add logs/v0.9.6/phase2-*.log
git add server/app/workers/worker.py
git commit -m "feat(worker): implement frame-level progress updates for video jobs"
```

---

## Phase 3: Plugin Progress Callback Support

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`server/tests/services/test_plugin_progress_callback.py`:**
```python
"""TDD tests for plugin progress callback support."""

import pytest
from unittest.mock import MagicMock
from app.services.plugin_management_service import PluginManagementService


def test_run_plugin_tool_accepts_progress_callback(mock_registry):
    """RED: Verify run_plugin_tool accepts progress_callback parameter."""
    service = PluginManagementService(mock_registry)
    
    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_registry.get.return_value = mock_plugin
    
    # Define progress callback
    def progress_callback(current: int, total: int) -> None:
        pass
    
    # Should not raise when progress_callback is provided
    result = service.run_plugin_tool(
        plugin_id="test-plugin",
        tool_name="detect",
        args={"video_path": "/tmp/test.mp4"},
        progress_callback=progress_callback,
    )
    
    # Verify plugin was called
    mock_plugin.run_tool.assert_called_once()


def test_run_plugin_tool_without_callback_backward_compatible(mock_registry):
    """RED: Verify run_plugin_tool works without progress_callback."""
    service = PluginManagementService(mock_registry)
    
    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_registry.get.return_value = mock_plugin
    
    # Should work without progress_callback (backward compatible)
    result = service.run_plugin_tool(
        plugin_id="test-plugin",
        tool_name="detect",
        args={"video_path": "/tmp/test.mp4"},
        # No progress_callback
    )
    
    # Verify plugin was called
    mock_plugin.run_tool.assert_called_once()


def test_progress_callback_passed_to_tool_function(mock_registry):
    """RED: Verify progress_callback is passed to tool function."""
    service = PluginManagementService(mock_registry)
    
    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_registry.get.return_value = mock_plugin
    
    # Define progress callback
    def progress_callback(current: int, total: int) -> None:
        pass
    
    # Run tool with callback
    service.run_plugin_tool(
        plugin_id="test-plugin",
        tool_name="detect",
        args={"video_path": "/tmp/test.mp4"},
        progress_callback=progress_callback,
    )
    
    # Verify run_tool was called with progress_callback in kwargs
    call_kwargs = mock_plugin.run_tool.call_args[1]
    assert "progress_callback" in call_kwargs
```

### Files to Edit
- `server/app/services/plugin_management_service.py`

### Implementation Details (GREEN Phase - After Tests Fail)

**Modify run_plugin_tool method signature:**
```python
def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
```

**Pass progress_callback to tool function:**
In the tool execution section, modify the sandbox call:
```python
# Filter out progress_callback from args if present
tool_args = {k: v for k, v in args.items() if k != "progress_callback"}

# Execute tool in sandbox
sandbox_result = run_plugin_sandboxed(
    tool_func,
    **tool_args,
)

# Note: progress_callback is handled separately by the plugin tool itself
# The plugin tool receives it via args and calls it during processing
```

**Update args handling to include progress_callback:**
```python
# 3. Get tool function via BasePlugin contract dispatcher
def tool_func(**kw):
    # Inject progress_callback if provided
    if progress_callback:
        kw["progress_callback"] = progress_callback
    return plugin.run_tool(tool_name, kw)
```

### Tests Required
- Plugin service test: Verify progress_callback is passed to tool
- Plugin service test: Verify tool execution works without progress_callback (backward compatibility)

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
cd server && uv run pytest tests/services/test_plugin_progress_callback.py -v > ../logs/v0.9.6/phase3-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement plugin service changes, then verify all tests pass
```bash
# Run pre-commit tests and save logs (MUST PASS)
uv run pre-commit run --all-files > logs/v0.9.6/phase3-pre-commit.log 2>&1
cd server && uv run pytest tests/services/test_plugin_progress_callback.py -v > ../logs/v0.9.6/phase3-pytest.log 2>&1
python scripts/scan_execution_violations.py > logs/v0.9.6/phase3-governance.log 2>&1

# Verify all GREEN
echo "=== Phase 3 Test Results ==="
grep -E "(PASSED|FAILED|ERROR)" logs/v0.9.6/phase3-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
git add logs/v0.9.6/phase3-*.log
git add server/app/services/plugin_management_service.py
git commit -m "feat(plugin): add progress_callback support to plugin tool execution"
```

---

## Phase 4: API Status Endpoint Update

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`server/tests/app/api/test_job_status_progress.py`:**
```python
"""TDD tests for job status endpoint with progress."""

import pytest
from datetime import datetime
from app.models.job import Job, JobStatus


def test_get_job_status_returns_progress_for_v096_jobs(client, session):
    """RED: Verify /v1/video/status returns progress for v0.9.6+ jobs."""
    # Create job with progress
    job = Job(
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=75,
    )
    session.add(job)
    session.commit()
    
    # Query status endpoint
    response = client.get(f"/v1/video/status/{job.job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "progress" in data
    assert data["progress"] == 75.0


def test_get_job_status_returns_null_for_old_jobs(client, session):
    """RED: Verify /v1/video/status returns null for pre-v0.9.6 jobs."""
    # Create job without progress (simulating old job)
    job = Job(
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=None,  # No progress data
    )
    session.add(job)
    session.commit()
    
    # Query status endpoint
    response = client.get(f"/v1/video/status/{job.job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "progress" in data
    assert data["progress"] is None


def test_get_job_status_returns_100_for_completed_jobs(client, session):
    """RED: Verify /v1/video/status returns 100 for completed jobs."""
    job = Job(
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.completed,
        progress=100,
    )
    session.add(job)
    session.commit()
    
    # Query status endpoint
    response = client.get(f"/v1/video/status/{job.job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    assert data["progress"] == 100.0
```

### Files to Edit
- `server/app/api_routes/routes/job_status.py`
- `server/app/schemas/job.py` (verify/update)

### Implementation Details (GREEN Phase - After Tests Fail)

**Update _calculate_progress function:**
```python
def _calculate_progress(job: Job) -> Optional[float]:
    """Calculate progress based on job status and stored progress.
    
    Args:
        job: Job model instance
        
    Returns:
        Progress float (0.0-100.0) or None if not available
    """
    # v0.9.6: Return actual progress from database if available
    if job.progress is not None:
        return float(job.progress)
    
    # Fallback for jobs created before v0.9.6
    if job.status == JobStatus.pending:
        return 0.0
    elif job.status == JobStatus.running:
        return 0.5  # Indeterminate progress
    else:  # completed or failed
        return 1.0
```

**Update get_job_status endpoint:**
```python
@router.get(
    "/v1/video/status/{job_id}", response_model=JobStatusResponse, deprecated=True
)
async def get_job_status(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobStatusResponse:
    """Get status of a job.

    DEPRECATED: Use /v1/jobs/{job_id} instead. TODO: Remove in v1.0.0

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        JobStatusResponse with status, progress, timestamps

    Raises:
        HTTPException: 404 if job not found
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = _calculate_progress(job)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
```

**Verify JobStatusResponse schema (server/app/schemas/job.py):**
Ensure it accepts Optional[float] for progress:
```python
class JobStatusResponse(BaseModel):
    """Response for GET /video/status/{job_id}."""
    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    progress: Optional[float]  # None for pre-v0.9.6 jobs
    created_at: datetime
    updated_at: datetime
```

### Tests Required
- API test: Verify progress returned for v0.9.6+ jobs
- API test: Verify fallback behavior for pre-v0.9.6 jobs
- API test: Verify progress is null for old jobs (not 0)

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
cd server && uv run pytest tests/app/api/test_job_status_progress.py -v > ../logs/v0.9.6/phase4-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement API changes, then verify all tests pass
```bash
# Run pre-commit tests and save logs (MUST PASS)
uv run pre-commit run --all-files > logs/v0.9.6/phase4-pre-commit.log 2>&1
cd server && uv run pytest tests/app/api/test_job_status_progress.py -v > ../logs/v0.9.6/phase4-pytest.log 2>&1
python scripts/scan_execution_violations.py > logs/v0.9.6/phase4-governance.log 2>&1

# Verify all GREEN
echo "=== Phase 4 Test Results ==="
grep -E "(PASSED|FAILED|ERROR)" logs/v0.9.6/phase4-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
git add logs/v0.9.6/phase4-*.log
git add server/app/api_routes/routes/job_status.py
git add server/app/schemas/job.py
git commit -m "feat(api): extend /v1/video/status to return actual progress from DB"
```

---

## Phase 5: Web-UI Progress Bar

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`web-ui/src/components/JobStatus.progress.test.tsx`:**
```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { JobStatus } from "./JobStatus";
import { apiClient } from "../api/client";

// Mock the API client
vi.mock("../api/client", () => ({
  apiClient: {
    getJob: vi.fn(),
  },
}));

describe("JobStatus Progress Bar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should display progress bar when job is running with progress", async () => {
    // RED: Test that progress bar appears
    vi.mocked(apiClient.getJob).mockResolvedValue({
      job_id: "test-job",
      status: "running",
      progress: 75,
      created_at: "2026-02-20T10:00:00Z",
    });

    render(<JobStatus jobId="test-job" />);

    await waitFor(() => {
      expect(screen.getByText("Status: running")).toBeInTheDocument();
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
      expect(screen.getByText("75%")).toBeInTheDocument();
    });
  });

  it("should show indeterminate message when progress is null", async () => {
    // RED: Test handling of null progress (pre-v0.9.6 jobs)
    vi.mocked(apiClient.getJob).mockResolvedValue({
      job_id: "test-job",
      status: "running",
      progress: null,
      created_at: "2026-02-20T10:00:00Z",
    });

    render(<JobStatus jobId="test-job" />);

    await waitFor(() => {
      expect(screen.getByText("Status: running")).toBeInTheDocument();
      expect(screen.getByText(/progress not available/i)).toBeInTheDocument();
    });
  });

  it("should not show progress bar when job is pending", async () => {
    // RED: Test no progress bar for pending jobs
    vi.mocked(apiClient.getJob).mockResolvedValue({
      job_id: "test-job",
      status: "pending",
      progress: 0,
      created_at: "2026-02-20T10:00:00Z",
    });

    render(<JobStatus jobId="test-job" />);

    await waitFor(() => {
      expect(screen.getByText("Status: pending")).toBeInTheDocument();
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });

  it("should continue polling while job is running", async () => {
    // RED: Test polling continues for running jobs
    vi.mocked(apiClient.getJob)
      .mockResolvedValueOnce({
        job_id: "test-job",
        status: "running",
        progress: 50,
        created_at: "2026-02-20T10:00:00Z",
      })
      .mockResolvedValueOnce({
        job_id: "test-job",
        status: "running",
        progress: 75,
        created_at: "2026-02-20T10:00:00Z",
      });

    render(<JobStatus jobId="test-job" />);

    // First poll
    await waitFor(() => {
      expect(screen.getByText("50%")).toBeInTheDocument();
    });

    // Second poll (after interval)
    await waitFor(() => {
      expect(screen.getByText("75%")).toBeInTheDocument();
    });
  });
});
```

### Files to Edit
- `web-ui/src/components/JobStatus.tsx`
- `web-ui/src/components/JobStatus.test.tsx` (update existing)

### Implementation Details (GREEN Phase - After Tests Fail)

**Update JobStatus.tsx:**
```typescript
import React, { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { JobResults } from "./JobResults";
import { ProgressBar } from "./ProgressBar"; // Import ProgressBar component

type Props = {
  jobId: string;
};

type Status = "pending" | "running" | "completed" | "failed";

type VideoJobResults = {
  job_id: string;
  results: {
    text?: string;
    detections?: Array<{
      label: string;
      confidence: number;
      bbox: number[];
    }>;
  } | null;
  created_at: string;
  updated_at: string;
};

export const JobStatus: React.FC<Props> = ({ jobId }) => {
  const [status, setStatus] = useState<Status>("pending");
  const [progress, setProgress] = useState<number | null>(null); // Add progress state
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<VideoJobResults | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    const poll = async () => {
      try {
        const job = await apiClient.getJob(jobId);
        setStatus(job.status as Status);
        setProgress(job.progress ?? null); // Update progress from API

        if (job.status === "completed" && job.results) {
          setResults(job.results as VideoJobResults);
          return;
        }

        if (job.status === "failed") {
          setError(job.error_message || job.error || "Job failed.");
          return;
        }

        // Continue polling while job is running or pending
        if (job.status === "running" || job.status === "pending") {
          timer = window.setTimeout(poll, 2000);
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Status polling failed.");
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
      
      {/* Show progress bar when running and progress is available */}
      {status === "running" && progress !== null && (
        <div style={{ marginTop: "10px", marginBottom: "10px" }}>
          <ProgressBar progress={progress} max={100} showPercentage />
        </div>
      )}
      
      {/* Show indeterminate progress when running but no progress data yet */}
      {status === "running" && progress === null && (
        <div style={{ marginTop: "10px", marginBottom: "10px", color: "#666" }}>
          Processing... (progress not available)
        </div>
      )}
      
      {error && <div style={{ color: "red" }}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};
```

**Update JobStatus.test.tsx:**
Add tests for:
- Progress bar displayed when status is running and progress is available
- Progress bar shows correct percentage
- No progress bar when job is pending
- No progress bar when job is completed

### Tests Required
- Component test: Verify ProgressBar renders when running with progress
- Component test: Verify correct progress value displayed
- Component test: Verify polling continues while running
- Component test: Verify no progress bar for pre-v0.9.6 jobs (progress=null)

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
cd web-ui && npm run test -- --run -t "JobStatus" > ../logs/v0.9.6/phase5-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement Web-UI changes, then verify all tests pass
```bash
# Run ALL THREE required checks and save logs (MUST PASS)
cd web-ui && npm run lint > ../logs/v0.9.6/phase5-lint.log 2>&1
cd web-ui && npm run type-check > ../logs/v0.9.6/phase5-typecheck.log 2>&1
cd web-ui && npm run test -- --run -t "JobStatus" > ../logs/v0.9.6/phase5-test.log 2>&1

# Verify all GREEN
echo "=== Phase 5 Test Results ==="
grep -E "(PASS|FAIL|Error)" logs/v0.9.6/phase5-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
git add logs/v0.9.6/phase5-*.log
git add web-ui/src/components/JobStatus.tsx
git add web-ui/src/components/JobStatus.progress.test.tsx
git commit -m "feat(ui): add determinate progress bar for running video jobs"
```

---

## Phase 6: Integration Tests & Smoke Test

### TDD Tests (Write First - RED Phase)
Create these test files BEFORE implementing:

**`server/tests/integration/test_video_progress_e2e.py`:**
```python
"""TDD end-to-end test for video progress tracking."""

import pytest


def test_video_job_reports_progress_during_processing(client):
    """RED: Verify video job reports progress during processing."""
    # Submit video job
    with open("fixtures/test_video.mp4", "rb") as f:
        response = client.post(
            "/v1/video/submit?plugin_id=yolo&tool=detect",
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Poll status and verify progress increases
    progress_values = []
    for _ in range(10):  # Poll 10 times
        status_resp = client.get(f"/v1/video/status/{job_id}")
        data = status_resp.json()
        
        if data.get("progress") is not None:
            progress_values.append(data["progress"])
        
        if data["status"] in ("completed", "failed"):
            break
    
    # Verify progress was reported
    assert len(progress_values) > 0, "No progress values reported"
    assert progress_values[-1] == 100 or data["status"] == "completed"


def test_smoke_test_validates_progress_field(client):
    """RED: Verify smoke test checks progress field."""
    # Create a job
    from app.models.job import Job, JobStatus
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    job = Job(
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=50,
    )
    db.add(job)
    db.commit()
    
    # Query status
    response = client.get(f"/v1/video/status/{job.job_id}")
    data = response.json()
    
    # Verify progress field exists and is valid
    assert "progress" in data, "Response missing 'progress' field"
    assert isinstance(data["progress"], (int, float)), "Progress should be numeric"
    assert 0 <= data["progress"] <= 100, "Progress should be 0-100"
```

**Update `scripts/smoke_test.py`:**
Add to `test_job_status` function:
```python
# v0.9.6: Verify progress field is present
assert "progress" in data, "Response missing 'progress' field"

# v0.9.6: Verify progress is valid if present
progress = data.get("progress")
if progress is not None:
    assert isinstance(progress, (int, float)), f"Progress should be number, got {type(progress)}"
    assert 0 <= progress <= 100, f"Progress should be 0-100, got {progress}"
```

### Files to Create/Edit
- `server/tests/integration/test_video_progress_e2e.py` (NEW)
- `scripts/smoke_test.py` (EDIT - update test_job_status)

### Implementation Details (GREEN Phase - After Tests Fail)

**Migration Test (server/tests/migrations/test_progress_column.py):**
```python
"""Test for v0.9.6 progress column migration."""

import pytest
import sqlalchemy as sa


def test_progress_column_exists(db_engine):
    """Verify progress column exists in jobs table after migration."""
    insp = sa.inspect(db_engine)
    columns = [c["name"] for c in insp.get_columns("jobs")]
    assert "progress" in columns, "progress column missing from jobs table"


def test_progress_column_is_nullable(db_engine):
    """Verify progress column is nullable for backward compatibility."""
    insp = sa.inspect(db_engine)
    columns = {c["name"]: c for c in insp.get_columns("jobs")}
    progress_col = columns.get("progress")
    assert progress_col is not None, "progress column not found"
    assert progress_col["nullable"] is True, "progress column should be nullable for backward compatibility"


def test_progress_column_type(db_engine):
    """Verify progress column is Integer type."""
    insp = sa.inspect(db_engine)
    columns = {c["name"]: c for c in insp.get_columns("jobs")}
    progress_col = columns.get("progress")
    assert progress_col is not None, "progress column not found"
    # Check it's an integer type (could be INTEGER or BigInteger depending on DB)
    assert "int" in str(progress_col["type"]).lower(), "progress column should be Integer type"
```

**Smoke Test Update (scripts/smoke_test.py):**
In `test_job_status` function, add:
```python
# v0.9.6: Verify progress field is present
assert "progress" in data, "Response missing 'progress' field"

# v0.9.6: Verify progress is valid if present
progress = data.get("progress")
if progress is not None:
    assert isinstance(progress, (int, float)), f"Progress should be number, got {type(progress)}"
    assert 0 <= progress <= 100, f"Progress should be 0-100, got {progress}"
```

### TDD Workflow (RED → GREEN → COMMIT)

**Step 1: RED** - Write tests first (tests will fail)
```bash
cd server && uv run pytest tests/integration/test_video_progress_e2e.py -v > ../logs/v0.9.6/phase6-tdd-red.log 2>&1
```

**Step 2: GREEN** - Implement integration tests and smoke test updates, then verify all tests pass
```bash
# Run pre-commit tests and save logs (MUST PASS)
uv run pre-commit run --all-files > logs/v0.9.6/phase6-pre-commit.log 2>&1
cd server && uv run pytest tests/integration/test_video_progress_e2e.py -v > ../logs/v0.9.6/phase6-pytest.log 2>&1
python scripts/scan_execution_violations.py > logs/v0.9.6/phase6-governance.log 2>&1

# Run smoke test and save logs
python scripts/smoke_test.py > logs/v0.9.6/phase6-smoke-test.log 2>&1

# Verify all GREEN
echo "=== Phase 6 Test Results ==="
grep -E "(PASSED|FAILED|ERROR)" logs/v0.9.6/phase6-*.log
```

**Step 3: COMMIT** - Only commit when all tests are GREEN
```bash
git add logs/v0.9.6/phase6-*.log
git add server/tests/integration/test_video_progress_e2e.py
git add scripts/smoke_test.py
git commit -m "test: add migration test and update smoke test for progress support"
```

---

## Final Validation (All Phases Complete)

### Complete Test Suite with Log Files
```bash
# Create logs directory
mkdir -p logs/v0.9.6

# FORGESYTE repo - Python tests
# 1. Pre-commit (black/ruff/mypy)
uv run pre-commit run --all-files > logs/v0.9.6/final-pre-commit.log 2>&1

# 2. All Python tests
cd server && uv run pytest tests/ -v > ../logs/v0.9.6/final-pytest.log 2>&1

# 3. Governance check
python scripts/scan_execution_violations.py > logs/v0.9.6/final-governance.log 2>&1

# Web-UI - TypeScript tests (ALL THREE REQUIRED)
cd web-ui
# 4. ESLint
npm run lint > ../logs/v0.9.6/final-webui-lint.log 2>&1
# 5. TypeScript type check (MANDATORY)
npm run type-check > ../logs/v0.9.6/final-webui-typecheck.log 2>&1
# 6. Vitest tests
npm run test -- --run > ../logs/v0.9.6/final-webui-test.log 2>&1

# 7. Smoke test
python scripts/smoke_test.py > logs/v0.9.6/final-smoke-test.log 2>&1

# Verify all tests passed (check for failures in logs)
echo "=== Checking for test failures ==="
grep -i "failed\|error\|FAIL" logs/v0.9.6/final-*.log || echo "All tests PASSED (GREEN)"
```

### TDD Test File Summary

| Phase | Test File | Purpose |
|-------|-----------|---------|
| 1 | `tests/migrations/test_006_add_progress_column.py` | Verify DB migration |
| 1 | `tests/models/test_job_progress.py` | Verify Job model |
| 2 | `tests/app/workers/test_worker_progress.py` | Verify worker progress tracking |
| 3 | `tests/services/test_plugin_progress_callback.py` | Verify plugin callback |
| 4 | `tests/app/api/test_job_status_progress.py` | Verify API returns progress |
| 5 | `src/components/JobStatus.progress.test.tsx` | Verify Web-UI progress bar |
| 6 | `tests/integration/test_video_progress_e2e.py` | Verify end-to-end flow |

**TDD Workflow for Each Phase:**
1. **RED**: Write test file first (tests will fail) → Save to `logs/v0.9.6/phase{N}-tdd-red.log`
2. **GREEN**: Implement feature → Run all pre-commit tests → Save to `logs/v0.9.6/phase{N}-*.log`
3. **REFACTOR**: Clean up while keeping tests green
4. **VERIFY**: Check all logs show GREEN (no failures)
5. **COMMIT**: Commit with test logs attached

**Required Pre-Commit Tests (MUST BE GREEN):**

**FORGESYTE repo (Python):**
- `uv run pre-commit run --all-files` (black/ruff/mypy)
- `cd server && uv run pytest tests/ -v` (all tests)
- `python scripts/scan_execution_violations.py` (governance)

**Web-UI (TypeScript) - ALL THREE REQUIRED:**
- `npm run lint` (eslint)
- `npm run type-check` (tsc --noEmit - MANDATORY)
- `npm run test -- --run` (vitest)

**Note:** Each phase commit must include the corresponding test log files to verify all tests passed (GREEN). No code should be committed until all pre-commit tests pass and logs are saved.

---

## Commit Messages

### Commit 1 — Database Migration
```
feat(db): add progress column to jobs table for video progress tracking

- Adds Alembic migration 006_add_progress_column.py
- Updates Job model with progress field (Integer, nullable)
- Creates index on progress column for efficient lookups
- Migration is backward compatible (nullable column)
- Includes migration tests
```

### Commit 2 — Worker Progress Updates
```
feat(worker): implement frame-level progress updates for video jobs

- Adds OpenCV get_total_frames() helper using CAP_PROP_FRAME_COUNT
- Implements _update_job_progress() with 5% throttling
- Worker passes progress_callback to plugin tools for video jobs
- Ensures 100% progress on job completion
- Handles OpenCV failures gracefully with fallback to 100 frames
```

### Commit 3 — Plugin Progress Callback
```
feat(plugin): add progress_callback support to plugin tool execution

- PluginManagementService.run_plugin_tool accepts progress_callback
- Callback signature: (current_frame: int, total_frames: int)
- Maintains backward compatibility (callback is optional)
- Progress callback passed through to plugin tools
```

### Commit 4 — API Status Endpoint
```
feat(api): extend /v1/video/status to return actual progress from DB

- _calculate_progress() returns real progress value when available
- Returns null for pre-v0.9.6 jobs (backward compatible)
- Falls back to status-based progress (0.0/0.5/1.0) for old jobs
- Updated JobStatusResponse schema accepts Optional[float]
```

### Commit 5 — Web-UI Progress Bar
```
feat(ui): add determinate progress bar for running video jobs

- JobStatus component displays ProgressBar when running
- Shows percentage text under progress bar
- Handles null progress gracefully (shows "progress not available")
- Continues polling while job is running or pending
- Uses existing ProgressBar component from components/
```

### Commit 6 — Tests & Smoke Test
```
test: add migration test and update smoke test for progress support

- Adds test_progress_column_exists migration test
- Verifies progress column is nullable for backward compatibility
- Updates smoke test to validate progress field
- Ensures progress is between 0 and 100 when present
- All tests pass (Python + TypeScript)
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OpenCV not installed | Low | High | Add opencv-python to requirements, graceful fallback to 100 frames |
| High DB write volume | Low | Medium | Throttled to every 5%, negligible impact |
| Plugin doesn't support callback | Medium | High | Callback is optional, plugins work without it |
| Breaking API change | Low | High | Progress is nullable, old clients unaffected |
| Web-UI type errors | Low | Medium | Full type-check before commit, optional chaining |

---

## Success Criteria

- [ ] Database migration runs successfully
- [ ] Job model accepts progress field
- [ ] Worker updates progress during video processing
- [ ] Progress updates are throttled to every 5%
- [ ] API returns actual progress from database
- [ ] API returns null for pre-v0.9.6 jobs
- [ ] Web-UI displays progress bar when running
- [ ] Web-UI shows percentage text
- [ ] All pre-commit tests pass (black/ruff/mypy)
- [ ] All Python tests pass
- [ ] All TypeScript tests pass
- [ ] Smoke test validates progress field
- [ ] Governance scan passes
- [ ] No breaking changes to existing functionality

---

## Notes

- OpenCV is used for fast metadata-only frame count extraction
- Progress is nullable to distinguish "no progress data" from "0% complete"
- Throttling at 5% reduces DB writes by 95% vs per-frame updates
- All changes are backward compatible with existing jobs and clients
