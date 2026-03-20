"""Tests for JobWorker."""

import json
from unittest.mock import ANY, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
from app.models.job_tool import JobTool
from app.workers.worker import JobWorker


@pytest.mark.unit
def test_worker_init(test_engine):
    """Test worker initialization."""
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(session_factory=Session)

    assert worker is not None
    assert worker._running is True


@pytest.mark.unit
def test_worker_run_once_no_pending_jobs(test_engine):
    """Test run_once returns False when no pending jobs in DB."""
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(session_factory=Session)

    result = worker.run_once()

    assert result is False


@pytest.mark.unit
def test_worker_run_once_marks_job_running(test_engine, session):
    """Test run_once marks job as running."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create a pending job in the database
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    # Add tool to job_tools table
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = []

    # Run worker
    result = worker.run_once()

    assert result is True

    # Verify job is now COMPLETED (with mocked services)
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job is not None
    assert updated_job.status == JobStatus.completed


@pytest.mark.unit
def test_worker_run_once_no_matching_job(test_engine, session):
    """Test run_once returns False when only non-pending jobs exist."""
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(session_factory=Session)

    # Create a job that is already completed (not pending)
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="test_plugin",
        input_path="test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Run worker — should find nothing pending
    result = worker.run_once()

    assert result is False


@pytest.mark.unit
def test_worker_multiple_run_once_calls(test_engine, session):
    """Test running worker multiple times."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create multiple pending jobs
    job_ids = [str(uuid4()) for _ in range(3)]
    for job_id in job_ids:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test_plugin",
            input_path="video/input/test.mp4",
            job_type="video",
        )
        session.add(job)
        session.flush()
        # Add tool to job_tools table
        job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
        session.add(job_tool)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = []

    # Process all jobs
    for _ in range(3):
        result = worker.run_once()
        assert result is True

    # No more pending jobs
    assert worker.run_once() is False

    # All jobs should be COMPLETED
    session.expire_all()
    for job_id in job_ids:
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job.status == JobStatus.completed


# COMMIT 6: Pipeline Execution Tests


@pytest.mark.unit
def test_worker_run_once_executes_pipeline(test_engine, session):
    """Test run_once executes pipeline on input file."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
        {"frame_index": 1, "result": {"detections": []}},
    ]

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify plugin service was called with correct args
    # Note: video jobs include progress_callback parameter
    mock_plugin_service.run_plugin_tool.assert_called_once_with(
        "test_plugin",
        "test_tool",
        {"video_path": "/data/jobs/video/input/test.mp4"},
        progress_callback=ANY,
    )


@pytest.mark.unit
def test_worker_run_once_saves_results_to_storage(test_engine, session):
    """Test run_once saves pipeline results as JSON."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Setup mock behaviors
    test_results = [
        {"frame_index": 0, "result": {"detections": [{"id": 1}]}},
    ]
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = test_results

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify save_file was called with JSON results
    mock_storage.save_file.assert_called_once()
    call_args = mock_storage.save_file.call_args
    saved_content = (
        call_args[0][0].read() if hasattr(call_args[0][0], "read") else call_args[0][0]
    )
    if isinstance(saved_content, bytes):
        saved_json = json.loads(saved_content.decode())
    else:
        saved_json = json.loads(saved_content)
    # v0.10.0: Flattened video output format for VideoResultsViewer
    assert "job_id" in saved_json
    assert "status" in saved_json
    assert saved_json["status"] == "completed"
    # Frontend expects total_frames and frames at top level
    assert "total_frames" in saved_json
    assert "frames" in saved_json
    assert isinstance(saved_json["frames"], list)
    assert len(saved_json["frames"]) == 1


@pytest.mark.unit
def test_worker_run_once_updates_job_completed(test_engine, session):
    """Test run_once marks job as completed with output_path."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
    ]

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify job is now COMPLETED with output_path
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.completed
    assert updated_job.output_path == "video/output/test.json"
    assert updated_job.error_message is None


@pytest.mark.unit
def test_worker_run_once_handles_pipeline_error(test_engine, session):
    """Test run_once marks job as failed on pipeline error."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Setup mock to raise error
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.side_effect = ValueError("Plugin error")

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED with error_message
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "Plugin error" in updated_job.error_message


@pytest.mark.unit
def test_worker_run_once_handles_storage_error(test_engine, session):
    """Test run_once marks job as failed on storage error."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        input_path="video/input/missing.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="test_tool", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Setup mock to raise file not found
    mock_storage.load_file.side_effect = FileNotFoundError("File not found")
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "test_tool", "input_types": ["video"]}]
    }

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "File not found" in updated_job.error_message


@pytest.mark.unit
def test_worker_flattens_video_results_for_ui(test_engine, session):
    """Test v0.10.0: Video results are flattened for VideoResultsViewer.

    Frontend expects { total_frames, frames } at top level,
    not wrapped in { results: [{ tool, output }] }.
    """
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create pending video job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="yolo",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="video_player_tracking", tool_order=0)
    session.add(job_tool)
    session.commit()
    # Mock returns dict with frames and total_frames (like YOLO plugin)
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "video_player_tracking", "input_types": ["video"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = {
        "total_frames": 100,
        "frames": [
            {"frame_index": 0, "detections": {"tracked_objects": []}},
            {"frame_index": 1, "detections": {"tracked_objects": []}},
        ],
    }

    # Execute
    result = worker.run_once()

    assert result is True

    # Verify saved JSON is flattened for UI
    saved_content = mock_storage.save_file.call_args[0][0]
    # saved_content is a BytesIO object
    if hasattr(saved_content, "read"):
        saved_content.seek(0)
        saved_json = json.loads(saved_content.read().decode())
    elif isinstance(saved_content, bytes):
        saved_json = json.loads(saved_content.decode())
    else:
        saved_json = json.loads(saved_content)

    # v0.10.0: Flattened format for VideoResultsViewer
    assert saved_json["job_id"] == job_id
    assert saved_json["status"] == "completed"
    assert "total_frames" in saved_json
    assert saved_json["total_frames"] == 100
    assert "frames" in saved_json
    assert isinstance(saved_json["frames"], list)
    assert len(saved_json["frames"]) == 2

    # Should NOT have wrapped results array
    assert "results" not in saved_json or not isinstance(
        saved_json.get("results"), list
    )


# Issue #304: Test that sync mode fallback loads plugins


@pytest.mark.unit
def test_worker_sync_mode_loads_plugins(test_engine, session):
    """Test that sync mode fallback loads plugins when plugin_service is None.

    Issue #304: When JobWorker is created without a plugin_service (common in
    production), it falls back to creating a PluginRegistry in _execute_pipeline.
    This fallback must call load_plugins() or the registry remains empty.

    This test creates a worker WITHOUT injecting a mock plugin_service,
    testing the real fallback code path.
    """
    import tempfile
    from importlib.metadata import entry_points

    from PIL import Image

    # Skip if OCR plugin entry point is not available (clean CI environments)
    eps = entry_points(group="forgesyte.plugins")
    ocr_available = any(ep.name == "ocr" for ep in eps)
    if not ocr_available:
        pytest.skip("OCR plugin entry point not available - requires forgesyte-plugins")

    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()

    # Create worker WITHOUT plugin_service - triggers fallback code path
    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=None,  # Explicitly None to trigger fallback
    )

    # Create a real test image file for OCR
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        test_image_path = f.name
        # Create a simple white image
        img = Image.new("RGB", (100, 50), color="white")
        img.save(f, format="PNG")

    # Create a pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="ocr",  # Use a known plugin
        input_path="image/input/test.png",
        job_type="image",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(
        job_id=job_id, tool_id="analyze", tool_order=0
    )  # OCR plugin's tool name
    session.add(job_tool)
    session.commit()
    # Setup storage mock to return real temp file
    mock_storage.load_file.return_value = test_image_path
    mock_storage.save_file.return_value = "image/output/test.json"

    # Execute - this will fail if load_plugins() is missing
    result = worker.run_once()

    # Check job state for diagnostics
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()

    # Cleanup temp file
    import os

    os.unlink(test_image_path)

    # If load_plugins() was NOT called, result would be False (plugin not found)
    # If load_plugins() WAS called, the OCR plugin should be found
    assert result is True, (
        f"Worker failed: result={result}, "
        f"job_status={updated_job.status if updated_job else 'None'}, "
        f"error_message={updated_job.error_message if updated_job else 'None'}. "
        f"Sync mode fallback may have forgotten to call plugin_manager.load_plugins()"
    )

    # Verify job completed
    assert updated_job.status == JobStatus.completed


# Discussion #354: Pre-computed summary for /v1/jobs hot path
@pytest.mark.unit
def test_worker_stores_summary_on_completion(test_engine, session):
    """Test worker computes and stores summary when job completes.

    Discussion #354: Summary should be computed once during worker finalization
    and stored in job.summary column to avoid loading full artifacts on /v1/jobs.
    """
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    # Create a pending video job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.flush()
    job_tool = JobTool(job_id=job_id, tool_id="detect", tool_order=0)
    session.add(job_tool)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/jobs/video/input/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "detect", "input_types": ["video"]}]
    }
    # Return video results with frames and detections
    mock_plugin_service.run_plugin_tool.return_value = {
        "total_frames": 10,
        "frames": [
            {"frame_idx": i, "detections": [{"class": "person"}, {"class": "car"}]}
            for i in range(10)
        ],
    }

    # Run worker
    result = worker.run_once()

    assert result is True

    # Verify job completed
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.completed

    # Discussion #354: Summary should be stored
    assert updated_job.summary is not None, "Worker should compute and store summary"

    # Verify summary content
    summary = json.loads(updated_job.summary)
    assert "frame_count" in summary
    assert "detection_count" in summary
    assert "classes" in summary
    # 10 frames * 2 detections each = 20 total
    assert summary["detection_count"] == 20
    assert set(summary["classes"]) == {"person", "car"}
