"""Tests for JobWorker."""

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
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
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create a pending job in the database
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        tool="test_tool",
        input_path="test.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = []

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
        tool="test_tool",
        input_path="test.mp4",
    )
    session.add(job)
    session.commit()

    # Run worker — should find nothing pending
    result = worker.run_once()

    assert result is False


@pytest.mark.unit
def test_worker_multiple_run_once_calls(test_engine, session):
    """Test running worker multiple times."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create multiple pending jobs
    job_ids = [str(uuid4()) for _ in range(3)]
    for job_id in job_ids:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test_plugin",
            tool="test_tool",
            input_path="test.mp4",
        )
        session.add(job)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = []

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
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        tool="test_tool",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
        {"frame_index": 1, "result": {"detections": []}},
    ]

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify pipeline was called with correct args
    mock_pipeline_service.run_on_file.assert_called_once_with(
        "/data/video_jobs/input/test.mp4",
        "test_plugin",
        ["test_tool"],
    )


@pytest.mark.unit
def test_worker_run_once_saves_results_to_storage(test_engine, session):
    """Test run_once saves pipeline results as JSON."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        tool="test_tool",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock behaviors
    test_results = [
        {"frame_index": 0, "result": {"detections": [{"id": 1}]}},
    ]
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = test_results

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
    assert "results" in saved_json
    assert saved_json["results"] == test_results


@pytest.mark.unit
def test_worker_run_once_updates_job_completed(test_engine, session):
    """Test run_once marks job as completed with output_path."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        tool="test_tool",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
    ]

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify job is now COMPLETED with output_path
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.completed
    assert updated_job.output_path == "/data/video_jobs/output/test.json"
    assert updated_job.error_message is None


@pytest.mark.unit
def test_worker_run_once_handles_pipeline_error(test_engine, session):
    """Test run_once marks job as failed on pipeline error."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="nonexistent_plugin",
        tool="test_tool",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock to raise error
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_pipeline_service.run_on_file.side_effect = ValueError("Plugin not found")

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED with error_message
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "Plugin not found" in updated_job.error_message


@pytest.mark.unit
def test_worker_run_once_handles_storage_error(test_engine, session):
    """Test run_once marks job as failed on storage error."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        pipeline_service=mock_pipeline_service,
    )

    # Create pending job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="test_plugin",
        tool="test_tool",
        input_path="input/missing.mp4",
    )
    session.add(job)
    session.commit()

    # Setup mock to raise file not found
    mock_storage.load_file.side_effect = FileNotFoundError("File not found")

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "File not found" in updated_job.error_message
