"""E2E test for v0.9.2 unified job system.

Tests the complete flow:
1. Submit OCR image job via /v1/image/submit
2. Submit YOLO video job via /v1/video/submit
3. Run worker to process both jobs
4. Fetch results via unified /v1/jobs/{id}
5. Verify JSON output format
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.local_storage import LocalStorageService
from app.workers.worker import JobWorker


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def storage():
    """Create a storage service."""
    return LocalStorageService()


@pytest.fixture
def plugin_service():
    """Create a plugin service."""
    plugin_manager = PluginRegistry()
    plugin_manager.load_plugins()
    return PluginManagementService(plugin_manager)


def run_worker_once(storage, plugin_service):
    """Run worker once to process all pending jobs."""
    db = SessionLocal()
    worker = JobWorker(
        session_factory=SessionLocal,
        storage=storage,
        pipeline_service=None,  # Not used in v0.9.2 worker
    )
    # Process all pending jobs
    jobs = db.query(Job).filter(Job.status == JobStatus.pending).all()
    for job in jobs:
        worker._execute_pipeline(job, db)
    db.close()


def test_e2e_ocr_image_and_yolo_video(client, storage, plugin_service):
    """Test end-to-end flow: OCR image + YOLO video via unified /v1/jobs/{id}."""
    # 1) Submit OCR image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    image_job_id = resp.json()["job_id"]

    # 2) Submit YOLO video job
    fake_mp4 = b"ftyp" + b"\x00" * 100
    with BytesIO(fake_mp4) as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert resp.status_code == 200
    video_job_id = resp.json()["job_id"]

    # 3) Run worker to process both jobs
    run_worker_once(storage, plugin_service)

    # 4) Fetch results via unified /v1/jobs/{id}

    # OCR image job
    resp = client.get(f"/v1/jobs/{image_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == image_job_id
    assert data["results"] is not None
    assert "results" in data["results"]  # Nested results structure

    # YOLO video job
    resp = client.get(f"/v1/jobs/{video_job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == video_job_id
    assert data["results"] is not None
    assert "results" in data["results"]  # Nested results structure


def test_e2e_image_job_storage_paths(client, storage):
    """Test that image jobs use correct storage paths."""
    # Submit image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Run worker
    from app.plugin_loader import PluginRegistry
    from app.services.plugin_management_service import PluginManagementService

    plugin_manager = PluginRegistry()
    plugin_manager.load_plugins()
    plugin_service = PluginManagementService(plugin_manager)
    run_worker_once(storage, plugin_service)

    # Verify storage paths
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.input_path.startswith("image/input/")
    assert job.output_path.startswith("image/output/")
    db.close()


def test_e2e_video_job_storage_paths(client, storage):
    """Test that video jobs use correct storage paths."""
    # Submit video job
    fake_mp4 = b"ftyp" + b"\x00" * 100
    with BytesIO(fake_mp4) as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Run worker
    from app.plugin_loader import PluginRegistry
    from app.services.plugin_management_service import PluginManagementService

    plugin_manager = PluginRegistry()
    plugin_manager.load_plugins()
    plugin_service = PluginManagementService(plugin_manager)
    run_worker_once(storage, plugin_service)

    # Verify storage paths
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.input_path.startswith("video/input/")
    assert job.output_path.startswith("video/output/")
    db.close()


def test_e2e_unified_endpoint_returns_null_for_pending(client):
    """Test that unified endpoint returns None for results when job is pending."""
    # Submit image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Fetch results immediately (should be pending)
    resp = client.get(f"/v1/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["results"] is None  # Pending jobs return None for results


def test_e2e_tool_validation_prevents_wrong_type(client):
    """Test that tool validation prevents using image tools on video jobs."""
    # Try to submit a video job with an image-only tool
    fake_mp4 = b"ftyp" + b"\x00" * 100
    with BytesIO(fake_mp4) as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=ocr&tool=extract_text",  # OCR is image-only
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    # This should fail at the endpoint level or worker level
    # For now, the endpoint doesn't validate, but the worker will fail
    assert resp.status_code == 200  # Endpoint accepts it

    job_id = resp.json()["job_id"]

    # Run worker
    from app.plugin_loader import PluginRegistry
    from app.services.plugin_management_service import PluginManagementService

    plugin_manager = PluginRegistry()
    plugin_manager.load_plugins()
    plugin_service = PluginManagementService(plugin_manager)
    run_worker_once(storage, plugin_service)

    # Fetch results (should be failed)
    resp = client.get(f"/v1/jobs/{job_id}")
    assert resp.status_code == 200
    # Job should have failed
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    assert job.status == JobStatus.failed
    assert "does not support video input" in job.error_message.lower()
    db.close()
