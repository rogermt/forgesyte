"""Fully mocked image submit tests — no disk, no plugins, no DB."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROUTE = "app.api_routes.routes.image_submit"

FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
FAKE_JPEG = b"\xFF\xD8\xFF" + b"\x00" * 10
FAKE_MANIFEST = {
    "tools": {
        "analyze": {
            "inputs": ["image_bytes"],
        }
    }
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_deps():
    """Patch dependency injections: get_plugin_manager, get_plugin_service, storage."""
    mock_plugin = MagicMock()
    mock_plugin_service = MagicMock()
    mock_db = MagicMock()

    with (
        patch(f"{ROUTE}.get_plugin_manager") as get_pm,
        patch(f"{ROUTE}.get_plugin_service") as get_ps,
        patch(f"{ROUTE}.storage") as st,
        patch(f"{ROUTE}.SessionLocal", return_value=mock_db),
    ):
        get_pm.return_value = mock_plugin
        get_ps.return_value = mock_plugin_service
        mock_plugin_service.get_plugin_manifest.return_value = FAKE_MANIFEST
        yield {"plugin_manager": mock_plugin, "plugin_service": mock_plugin_service, "storage": st, "db": mock_db}


class TestImageSubmitSuccess:
    """Happy-path tests for image submission."""

    def test_png_returns_200_with_job_id(self, client, mock_deps):
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)

    def test_jpeg_returns_200_with_job_id(self, client, mock_deps):
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.jpg", BytesIO(FAKE_JPEG), "image/jpeg")},
        )
        assert response.status_code == 200
        assert "job_id" in response.json()

    def test_saves_file_to_storage(self, client, mock_deps):
        client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
        )
        mock_deps["storage"].save_file.assert_called_once()

    def test_creates_db_record(self, client, mock_deps):
        client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
        )
        mock_deps["db"].add.assert_called_once()
        mock_deps["db"].commit.assert_called_once()


class TestImageSubmitValidation:
    """Validation / rejection tests."""

    def test_invalid_file_returns_400(self, client, mock_deps):
        fake_file = b"this is not an image"
        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.txt", BytesIO(fake_file), "text/plain")},
        )
        assert response.status_code == 400
        assert "Invalid image file" in response.json()["detail"]

    def test_unknown_plugin_returns_400(self, client):
        with patch(f"{ROUTE}.plugin_manager") as pm:
            pm.get.return_value = None
            response = client.post(
                "/v1/image/submit?plugin_id=nonexistent&tool=analyze",
                files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
            )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_unknown_tool_returns_400(self, client):
        with (
            patch(f"{ROUTE}.plugin_manager") as pm,
            patch(f"{ROUTE}.plugin_service") as ps,
        ):
            pm.get.return_value = MagicMock()
            ps.get_plugin_manifest.return_value = {"tools": {}}
            response = client.post(
                "/v1/image/submit?plugin_id=ocr&tool=nonexistent",
                files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
            )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_tool_without_image_input_returns_400(self, client):
        manifest_no_image = {
            "tools": {
                "some_tool": {
                    "inputs": ["video_bytes"],
                }
            }
        }
        with (
            patch(f"{ROUTE}.plugin_manager") as pm,
            patch(f"{ROUTE}.plugin_service") as ps,
        ):
            pm.get.return_value = MagicMock()
            ps.get_plugin_manifest.return_value = manifest_no_image
            response = client.post(
                "/v1/image/submit?plugin_id=ocr&tool=some_tool",
                files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
            )
        assert response.status_code == 400
        assert "does not support image input" in response.json()["detail"]

    def test_null_manifest_returns_400(self, client):
        with (
            patch(f"{ROUTE}.plugin_manager") as pm,
            patch(f"{ROUTE}.plugin_service") as ps,
        ):
            pm.get.return_value = MagicMock()
            ps.get_plugin_manifest.return_value = None
            response = client.post(
                "/v1/image/submit?plugin_id=ocr&tool=analyze",
                files={"file": ("test.png", BytesIO(FAKE_PNG), "image/png")},
            )
        assert response.status_code == 400
        assert "manifest" in response.json()["detail"].lower()
