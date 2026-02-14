"""Tests for JobWorker."""

import pytest
from uuid import uuid4
from sqlalchemy.orm import sessionmaker
from app.workers.worker import JobWorker
from app.services.queue.memory_queue import InMemoryQueueService
from app.models.job import Job, JobStatus


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
    worker = JobWorker(queue, Session)

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

    # Run worker
    result = worker.run_once()

    assert result is True

    # Verify job is now RUNNING
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job is not None
    assert updated_job.status == JobStatus.running


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
    worker = JobWorker(queue, Session)

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

    # Process all jobs
    for _ in range(3):
        result = worker.run_once()
        assert result is True

    # Queue should be empty now
    assert worker.run_once() is False

    # All jobs should be RUNNING
    for job_id in job_ids:
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job.status == JobStatus.running
