"""TDD tests for worker progress tracking."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
from app.workers.worker import JobWorker


@pytest.mark.unit
def test_worker_get_total_frames_with_opencv(test_engine):
    """RED: Verify _get_total_frames returns correct frame count."""
    worker = JobWorker(session_factory=sessionmaker(bind=test_engine))

    # Mock video file
    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.get.return_value = 1000  # 1000 frames
        mock_instance.release = MagicMock()
        mock_cap.return_value = mock_instance

        result = worker._get_total_frames("/tmp/test.mp4")
        assert result == 1000


@pytest.mark.unit
def test_worker_get_total_frames_fallback(test_engine):
    """RED: Verify _get_total_frames falls back to 100 on error."""
    worker = JobWorker(session_factory=sessionmaker(bind=test_engine))

    with patch("cv2.VideoCapture", side_effect=Exception("OpenCV error")):
        result = worker._get_total_frames("/tmp/test.mp4")
        assert result == 100  # Fallback heuristic


@pytest.mark.unit
def test_worker_get_total_frames_zero_frames_fallback(test_engine):
    """RED: Verify _get_total_frames falls back when frame count is 0."""
    worker = JobWorker(session_factory=sessionmaker(bind=test_engine))

    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.get.return_value = 0  # Invalid frame count
        mock_instance.release = MagicMock()
        mock_cap.return_value = mock_instance

        result = worker._get_total_frames("/tmp/test.mp4")
        assert result == 100  # Fallback heuristic


@pytest.mark.unit
def test_worker_update_progress_throttled(test_engine, session):
    """RED: Verify progress updates are throttled to every 5%."""
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(session_factory=Session)

    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
    )
    session.add(job)
    session.commit()

    # Update at 1% (should update - first frame)
    worker._update_job_progress(job_id, 1, 100, session)
    session.expire_all()
    assert job.progress == 1

    # Update at 2% (should NOT update - not 5% boundary)
    worker._update_job_progress(job_id, 2, 100, session)
    session.expire_all()
    assert job.progress == 1  # Still 1, not updated

    # Update at 5% (should update - 5% boundary)
    worker._update_job_progress(job_id, 5, 100, session)
    session.expire_all()
    assert job.progress == 5

    # Update at 10% (should update - 5% boundary)
    worker._update_job_progress(job_id, 10, 100, session)
    session.expire_all()
    assert job.progress == 10


@pytest.mark.unit
def test_worker_update_progress_always_updates_last_frame(test_engine, session):
    """RED: Verify progress updates on the last frame (100%)."""
    Session = sessionmaker(bind=test_engine)
    worker = JobWorker(session_factory=Session)

    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=95,
    )
    session.add(job)
    session.commit()

    # Update at last frame (100%) - should update even if not 5% boundary
    worker._update_job_progress(job_id, 100, 100, session)
    session.expire_all()
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job.progress == 100


@pytest.mark.unit
def test_worker_sets_100_percent_on_completion(test_engine, session):
    """RED: Verify worker sets progress to 100% on job completion."""
    Session = sessionmaker(bind=test_engine)

    mock_storage = MagicMock()
    mock_plugin_service = MagicMock()

    worker = JobWorker(
        session_factory=Session,
        storage=mock_storage,
        plugin_service=mock_plugin_service,
    )

    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=95,
    )
    session.add(job)
    session.commit()

    # Setup mock behaviors
    mock_storage.load_file.return_value = "/tmp/test.mp4"
    mock_storage.save_file.return_value = "video/output/test.json"
    mock_plugin_service.get_plugin_manifest.return_value = {
        "tools": [{"id": "detect", "inputs": ["video_path"]}]
    }
    mock_plugin_service.run_plugin_tool.return_value = {"detections": []}

    # Execute pipeline
    with patch.object(worker, "_get_total_frames", return_value=100):
        result = worker._execute_pipeline(job, session)

    assert result is True
    session.expire_all()
    updated_job = session.query(Job).filter(Job.job_id == job_id).first()
    assert updated_job.status == JobStatus.completed
    assert updated_job.progress == 100
