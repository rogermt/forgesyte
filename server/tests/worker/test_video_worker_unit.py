"""Unit tests for video_worker.py - tests worker logic without model loading."""

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
async def test_worker_calls_pipeline(monkeypatch, job_repo, tmp_path):
    """Verify worker calls VideoFilePipelineService.run_on_file()."""
    job_id = "test_123"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(tmp_path / "video.mp4"),
        pipeline_id="ocr_only",
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    # Mock pipeline service
    called = {}

    async def fake_run_on_file(pipeline_id, file_path):
        called["pipeline_id"] = pipeline_id
        called["file_path"] = file_path
        return {"frames": [], "text": "detected text"}

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_run_on_file,
    )

    # Run worker
    await process_job(job_id)

    # Verify job was processed
    processed_job = job_repo.get(job_id)
    assert processed_job.status == "done"
    assert processed_job.result == {"frames": [], "text": "detected text"}
    assert called["pipeline_id"] == "ocr_only"
    assert called["file_path"] == job.input_path


@pytest.mark.asyncio
async def test_worker_handles_exceptions(monkeypatch, job_repo, tmp_path):
    """Verify worker handles exceptions and marks job as error."""
    job_id = "error_job"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(tmp_path / "video.mp4"),
        pipeline_id="ocr_only",
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    async def fake_fail(*args, **kwargs):
        raise RuntimeError("Pipeline execution failed: boom")

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_fail,
    )

    # Run worker
    await process_job(job_id)

    # Verify job error state
    error_job = job_repo.get(job_id)
    assert error_job.status == "error"
    assert "boom" in error_job.error


@pytest.mark.asyncio
async def test_worker_respects_pipeline_id(monkeypatch, job_repo, tmp_path):
    """Verify worker uses job's pipeline_id."""
    job_id = "pipeline_test"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(tmp_path / "video.mp4"),
        pipeline_id="custom_pipeline",
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    called = {}

    async def fake_run_on_file(pipeline_id, file_path):
        called["pipeline_id"] = pipeline_id
        return {}

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_run_on_file,
    )

    await process_job(job_id)

    assert called["pipeline_id"] == "custom_pipeline"


@pytest.mark.asyncio
async def test_worker_saves_job_after_processing(monkeypatch, job_repo, tmp_path):
    """Verify worker saves job to repo after processing."""
    job_id = "save_test"
    job = SimpleNamespace(
        id=job_id,
        input_path=str(tmp_path / "video.mp4"),
        pipeline_id="ocr_only",
        status="pending",
        result=None,
        error=None,
    )
    job_repo.jobs[job_id] = job

    async def fake_run_on_file(pipeline_id, file_path):
        return {"success": True}

    from server.app.services import video_file_pipeline_service

    monkeypatch.setattr(
        video_file_pipeline_service.VideoFilePipelineService,
        "run_on_file",
        fake_run_on_file,
    )

    await process_job(job_id)

    # Verify job was persisted
    saved_job = job_repo.get(job_id)
    assert saved_job.status == "done"
    assert saved_job.result == {"success": True}
