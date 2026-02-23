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

from app.core.database import get_db
from app.main import app
from app.models.job import Job, JobStatus
from app.plugin_loader import PluginRegistry
from app.services.plugin_management_service import PluginManagementService
from app.services.storage.local_storage import LocalStorageService
from app.workers.worker import JobWorker


def has_yolo_plugin():
    """Check if YOLO plugin is available (GPU-only, may not be present)."""
    try:
        registry = PluginRegistry()
        registry.load_plugins()
        return "yolo" in registry.plugins
    except Exception:
        return False


requires_yolo = pytest.mark.skipif(
    not has_yolo_plugin(), reason="YOLO plugin not available (GPU-only)"
)


@pytest.fixture
def client(session):
    """Create a test client with dependency overrides for database session."""

    # Override get_db dependency to use test session
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Don't close test session, fixture handles it

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Clean up dependency overrides
    app.dependency_overrides.clear()


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


def run_worker_once(storage, plugin_service, session):
    """Run worker once to process all pending jobs."""
    worker = JobWorker(
        session_factory=lambda: session,
        storage=storage,
        plugin_service=plugin_service,
    )
    # Process all pending jobs
    jobs = session.query(Job).filter(Job.status == JobStatus.pending).all()
    for job in jobs:
        worker._execute_pipeline(job, session)
    session.commit()


@requires_yolo
def test_e2e_ocr_image_and_yolo_video(client, storage, plugin_service, session):
    """Test end-to-end flow: OCR image + YOLO video via unified /v1/jobs/{id}."""
    # 1) Submit OCR image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
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
    run_worker_once(storage, plugin_service, session)

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


def test_e2e_image_job_storage_paths(client, storage, plugin_service, session):
    """Test that image jobs use correct storage paths."""
    # Submit image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", f, "image/png")},
        )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Run worker
    run_worker_once(storage, plugin_service, session)

    # Verify storage paths
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.input_path.startswith("image/input/")
    assert job.output_path.startswith("image/output/")


@requires_yolo
def test_e2e_video_job_storage_paths(client, storage, plugin_service, session):
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
    run_worker_once(storage, plugin_service, session)

    # Verify storage paths
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.input_path.startswith("video/input/")
    assert job.output_path.startswith("video/output/")


def test_e2e_unified_endpoint_returns_null_for_pending(client, session):
    """Test that unified endpoint returns None for results when job is pending."""
    # Submit image job
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with BytesIO(fake_png) as f:
        resp = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
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


def test_e2e_tool_validation_prevents_wrong_type(
    client, storage, plugin_service, session
):
    """Test that tool validation prevents using image tools on video jobs.

    v0.9.5: Endpoint now validates input_types and rejects video jobs with
    image-only tools at the API level (returns 400).
    """
    # Try to submit a video job with an image-only tool
    fake_mp4 = b"ftyp" + b"\x00" * 100
    with BytesIO(fake_mp4) as f:
        resp = client.post(
            "/v1/video/submit?plugin_id=ocr&tool=analyze",  # OCR is image-only
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    # v0.9.5: Endpoint validates input_types and rejects with 400
    assert resp.status_code == 400
    assert "does not support video input" in resp.json()["detail"].lower()
