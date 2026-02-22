"""Hybrid integration test — real storage in tmpdir, mocked plugins/DB."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage.local_storage import LocalStorageService

ROUTE = "app.api_routes.routes.image_submit"

FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
FAKE_MANIFEST = {
    "tools": {
        "analyze": {
            "inputs": ["image_bytes"],
        }
    }
}


@pytest.fixture
def tmp_storage(tmp_path):
    """Create a real LocalStorageService backed by a temp directory."""
    import app.services.storage.local_storage as storage_mod

    original_base = storage_mod.BASE_DIR
    storage_mod.BASE_DIR = tmp_path

    svc = LocalStorageService.__new__(LocalStorageService)
    yield svc, tmp_path

    storage_mod.BASE_DIR = original_base


@pytest.fixture
def client(tmp_storage):
    from app.api_routes.routes import image_submit

    svc, _ = tmp_storage
    mock_db = MagicMock()

    # Set up mock plugin and service
    mock_plugin = MagicMock()
    mock_plugin.tools = {
        "analyze": {"input_schema": {"image_bytes": {"type": "bytes"}}}
    }
    mock_plugin_manager = MagicMock()
    mock_plugin_manager.get.return_value = mock_plugin
    mock_plugin_service = MagicMock()
    mock_plugin_service.get_available_tools.return_value = ["analyze"]
    mock_plugin_service.get_plugin_manifest.return_value = FAKE_MANIFEST

    # Use dependency_overrides for FastAPI DI
    app.dependency_overrides[image_submit.get_plugin_manager] = (
        lambda: mock_plugin_manager
    )
    app.dependency_overrides[image_submit.get_plugin_service] = (
        lambda pm=None: mock_plugin_service
    )

    with (
        patch(f"{ROUTE}.storage", svc),
        patch(f"{ROUTE}.SessionLocal", return_value=mock_db),
    ):
        yield TestClient(app)

    app.dependency_overrides.clear()


class TestImageSubmitHybrid:
    """Tests that verify real file I/O in a temp directory."""

    def test_png_saves_file_to_disk(self, client, tmp_storage):
        _, tmp_path = tmp_storage

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
        )
        assert response.status_code == 200

        saved_files = list(tmp_path.rglob("*.png"))
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == FAKE_PNG

    def test_saved_file_path_includes_job_id(self, client, tmp_storage):
        _, tmp_path = tmp_storage

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("photo.png", BytesIO(FAKE_PNG), "image/png")},
        )
        job_id = response.json()["job_id"]

        saved_files = list(tmp_path.rglob("*.png"))
        assert len(saved_files) == 1
        assert job_id in saved_files[0].name

    def test_saved_under_image_input_subdir(self, client, tmp_storage):
        _, tmp_path = tmp_storage

        client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
        )

        image_input_dir = tmp_path / "image" / "input"
        assert image_input_dir.exists()
        assert len(list(image_input_dir.iterdir())) == 1
