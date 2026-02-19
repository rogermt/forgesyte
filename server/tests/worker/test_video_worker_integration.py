"""Integration test for video_worker - tests end-to-end pipeline with real ocr_only."""

from types import SimpleNamespace

import pytest

from server.app.workers.video_worker import process_job


class FakeJobRepo:
    """Minimal fake job repository for testing."""

    def __init__(self):
        self.jobs = {}

    def get(self, job_id):
        if job_id not in self.jobs:
            raise KeyError(f"Job {job_id} not found")
        return self.jobs[job_id]

    def save(self, job):
        self.jobs[job.id] = job


@pytest.fixture
def job_repo(monkeypatch):
    """Inject fake job repo into worker module."""
    repo = FakeJobRepo()
    monkeypatch.setattr("server.app.workers.video_worker.job_repo", repo)
    return repo


@pytest.mark.asyncio
async def test_worker_end_to_end_with_ocr_only(monkeypatch, job_repo, tmp_path):
    """
    End-to-end test: Create job -> worker processes -> updates status.
    Uses mock ocr_only pipeline (no YOLO, no GPU required).
    """
    # Create fake MP4 file
    mp4_path = tmp_path / "test_video.mp4"
    mp4_path.write_bytes(b"fake mp4 data")

    job_id = "e2e_job_123"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(mp4_path),
        pipeline_id="ocr_only",
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    # Mock ocr_only pipeline result
    async def fake_ocr_only_pipeline(pipeline_id, file_path):
        # Simulate ocr_only returning frames with OCR data
        return {
            "frames": [
                {
                    "frame_number": 0,
                    "timestamp": 0.0,
                    "text": "Detected text from frame 0",
                }
            ],
            "text": "Detected text from frame 0",
        }

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_ocr_only_pipeline,
    )

    # Run worker
    await process_job(job_id)

    # Verify job completed
    completed_job = job_repo.get(job_id)
    assert completed_job.status == "done"
    assert "frames" in completed_job.result
    assert "text" in completed_job.result
    assert completed_job.result["text"] == "Detected text from frame 0"


@pytest.mark.asyncio
async def test_worker_handles_missing_pipeline_id(monkeypatch, job_repo, tmp_path):
    """Verify worker handles jobs without pipeline_id gracefully."""
    mp4_path = tmp_path / "test_video.mp4"
    mp4_path.write_bytes(b"fake mp4")

    job_id = "missing_pipeline"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(mp4_path),
        pipeline_id=None,  # Missing!
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    called = {}

    async def fake_pipeline(pipeline_id, file_path):
        called["pipeline_id"] = pipeline_id
        return {"status": "ok"}

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_pipeline,
    )

    await process_job(job_id)

    # Should use default pipeline
    processed_job = job_repo.get(job_id)
    assert processed_job.status == "done"
