"""Tests for JobWorker."""

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService
from app.workers.worker import JobWorker


@pytest.mark.unit
def test_worker_init(test_engine):
    """Test worker initialization."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    assert worker is not None
    assert worker._running is True


@pytest.mark.unit
def test_worker_run_once_empty_queue(test_engine):
    """Test run_once returns False when queue is empty."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    result = worker.run_once()

    assert result is False


@pytest.mark.unit
def test_worker_run_once_marks_job_running(test_engine, session):
    """Test run_once marks job as running."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(queue, Session, mock_storage, mock_pipeline_service)

    # Create a job in the database
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="test_pipeline",
        input_path="test.mp4",
    )
    session.add(job)
    session.commit()

    # Enqueue the job
    queue.enqueue(job_id)

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = []

    # Run worker
    result = worker.run_once()

    assert result is True

    # Verify job is now COMPLETED (with mocked services)
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job is not None
    assert updated_job.status == JobStatus.completed


@pytest.mark.unit
def test_worker_run_once_missing_job(test_engine):
    """Test run_once handles missing job gracefully."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    # Enqueue a job_id that doesn't exist in DB
    job_id = str(uuid4())
    queue.enqueue(job_id)

    # Run worker
    result = worker.run_once()

    # Should return False (job not found)
    assert result is False


@pytest.mark.unit
def test_worker_multiple_run_once_calls(test_engine, session):
    """Test running worker multiple times."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    worker = JobWorker(queue, Session, mock_storage, mock_pipeline_service)

    # Create multiple jobs
    job_ids = [str(uuid4()) for _ in range(3)]
    for job_id in job_ids:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            pipeline_id="test_pipeline",
            input_path="test.mp4",
        )
        session.add(job)
        queue.enqueue(job_id)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = []

    # Process all jobs
    for _ in range(3):
        result = worker.run_once()
        assert result is True

    # Queue should be empty now
    assert worker.run_once() is False

    # All jobs should be COMPLETED (with mocked services)
    for job_id in job_ids:
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job.status == JobStatus.completed


# COMMIT 6: Pipeline Execution Tests


@pytest.mark.unit
def test_worker_run_once_executes_pipeline(test_engine, session):
    """Test run_once executes pipeline on input file."""
    # Setup mocks
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    # Create job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="test_pipeline",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()
    queue.enqueue(job_id)

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
        {"frame_index": 1, "result": {"detections": []}},
    ]

    # Inject mocks into worker
    worker._storage = mock_storage
    worker._pipeline_service = mock_pipeline_service

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify pipeline was called with correct args
    mock_pipeline_service.run_on_file.assert_called_once()


@pytest.mark.unit
def test_worker_run_once_saves_results_to_storage(test_engine, session):
    """Test run_once saves pipeline results as JSON."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    # Create job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="test_pipeline",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()
    queue.enqueue(job_id)

    # Setup mock behaviors
    test_results = [
        {"frame_index": 0, "result": {"detections": [{"id": 1}]}},
    ]
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = test_results

    worker._storage = mock_storage
    worker._pipeline_service = mock_pipeline_service

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
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    # Create job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="test_pipeline",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()
    queue.enqueue(job_id)

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"
    mock_pipeline_service.run_on_file.return_value = [
        {"frame_index": 0, "result": {"detections": []}},
    ]

    worker._storage = mock_storage
    worker._pipeline_service = mock_pipeline_service

    # Execute
    result = worker.run_once()

    assert result is True
    # Verify job is now COMPLETED with output_path
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.completed
    assert updated_job.output_path == "/data/video_jobs/output/test.json"
    assert updated_job.error_message is None


@pytest.mark.unit
def test_worker_run_once_handles_pipeline_error(test_engine, session):
    """Test run_once marks job as failed on pipeline error."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    # Create job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="nonexistent_pipeline",
        input_path="input/test.mp4",
    )
    session.add(job)
    session.commit()
    queue.enqueue(job_id)

    # Setup mock to raise error
    mock_storage.load_file.return_value = "/data/video_jobs/input/test.mp4"
    mock_pipeline_service.run_on_file.side_effect = ValueError("Pipeline not found")

    worker._storage = mock_storage
    worker._pipeline_service = mock_pipeline_service

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED with error_message
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "Pipeline not found" in updated_job.error_message


@pytest.mark.unit
def test_worker_run_once_handles_storage_error(test_engine, session):
    """Test run_once marks job as failed on storage error."""
    queue = InMemoryQueueService()
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(queue, Session)

    mock_storage = MagicMock()
    mock_pipeline_service = MagicMock()

    # Create job
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id="test_pipeline",
        input_path="input/missing.mp4",
    )
    session.add(job)
    session.commit()
    queue.enqueue(job_id)

    # Setup mock to raise file not found
    mock_storage.load_file.side_effect = FileNotFoundError("File not found")

    worker._storage = mock_storage
    worker._pipeline_service = mock_pipeline_service

    # Execute
    result = worker.run_once()

    assert result is False
    # Verify job is now FAILED
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.failed
    assert "File not found" in updated_job.error_message
