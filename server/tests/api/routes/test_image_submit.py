"""Tests for image_submit endpoint.

Tests verify:
1. Plugin validation works with properly loaded registry (Issue #209)
2. Tool validation uses Plugin.tools (canonical source, not manifest)
3. Error handling for invalid plugin/tool
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.image_submit import get_plugin_manager, get_plugin_service
from app.main import app
from app.models.job import Job


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with tools attribute."""
    plugin = MagicMock()
    plugin.name = "ocr"
    plugin.description = "OCR Plugin"
    plugin.version = "1.0.0"
    plugin.tools = {
        "extract_text": {
            "handler": "extract_text_handler",
            "description": "Extract text from images",
            "input_schema": {
                "properties": {
                    "image_bytes": {"type": "string"},
                    "image_base64": {"type": "string"},
                }
            },
            "output_schema": {"properties": {"text": {"type": "string"}}},
        }
    }
    return plugin


@pytest.fixture
def mock_plugin_service(mock_plugin):
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_available_tools.return_value = list(mock_plugin.tools.keys())
    return mock


@pytest.fixture
def mock_plugin_registry(mock_plugin):
    """Create a mock plugin registry with a loaded plugin."""
    mock = MagicMock()
    mock.get.return_value = mock_plugin
    return mock


@pytest.fixture
def client_with_mocks(mock_plugin_registry, mock_plugin_service):
    """Create a test client with mocked dependencies."""
    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestImageSubmitPluginValidation:
    """Tests for plugin validation in image submit endpoint."""

    def test_submit_image_with_valid_plugin_and_tool(
        self, session: Session, client_with_mocks
    ):
        """Test that image submission works with valid plugin and tool."""
        # Create a valid PNG image (1x1 pixel)
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG magic bytes + padding

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        # Should succeed
        assert response.status_code == 200, f"Unexpected status: {response.status_code}, body: {response.text}"

        # Verify job was created
        job_id = response.json()["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.plugin_id == "ocr"

    def test_submit_image_with_invalid_plugin(self):
        """Test that image submission fails with invalid plugin."""
        # Create a mock that returns None for invalid plugin
        mock_registry = MagicMock()
        mock_registry.get.return_value = None  # Plugin not found

        mock_service = MagicMock()

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=nonexistent&tool=extract_text",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_submit_image_with_invalid_tool(self, mock_plugin):
        """Test that image submission fails with invalid tool."""
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_plugin

        # Service returns different tools
        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["different_tool"]

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=nonexistent_tool",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


class TestImageSubmitValidation:
    """Tests for input validation in image submit endpoint."""

    def test_submit_image_invalid_format(
        self, session: Session, client_with_mocks
    ):
        """Test that non-PNG/JPEG files are rejected."""
        # Create a file with invalid magic bytes
        invalid_data = b"INVALID FILE CONTENT"

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.txt", BytesIO(invalid_data), "text/plain")},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_submit_image_valid_jpeg(
        self, session: Session, client_with_mocks
    ):
        """Test that JPEG files are accepted."""
        # Create a valid JPEG (minimal header)
        jpeg_data = b"\xFF\xD8\xFF" + b"\x00" * 100  # JPEG magic bytes + padding

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.jpg", BytesIO(jpeg_data), "image/jpeg")},
        )

        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

        # Verify job was created
        job_id = response.json()["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None


class TestImageSubmitToolInputValidation:
    """Tests for tool input type validation."""

    def test_submit_image_tool_supports_image_bytes(self, mock_plugin, session: Session):
        """Test that tools with image_bytes input are accepted."""
        # Create plugin with image_bytes support
        plugin = MagicMock()
        plugin.tools = {
            "extract_text": {
                "handler": "extract_text_handler",
                "description": "Extract text",
                "input_schema": {
                    "properties": {"image_bytes": {"type": "string"}}
                },
                "output_schema": {},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = list(plugin.tools.keys())

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_submit_image_tool_does_not_support_image(self, mock_plugin):
        """Test that tools without image input are rejected."""
        # Create plugin with video-only tool
        plugin = MagicMock()
        plugin.tools = {
            "video_only_tool": {
                "handler": "video_handler",
                "description": "Video only",
                "input_schema": {
                    "properties": {"video_path": {"type": "string"}}  # No image support
                },
                "output_schema": {},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = list(plugin.tools.keys())

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=video_only_tool",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "does not support image input" in response.json()["detail"].lower()


class TestImageSubmitDI:
    """Tests for dependency injection pattern in image submit endpoint (Issue #209)."""

    def test_get_plugin_manager_uses_app_state(self):
        """Test that get_plugin_manager uses app.state.plugins when available."""
        # Create a mock plugin manager
        mock_manager = MagicMock()

        # Set app.state.plugins
        original_plugins = getattr(app.state, "plugins", None)
        app.state.plugins = mock_manager

        try:
            result = get_plugin_manager()
            assert result is mock_manager
        finally:
            # Restore original state
            if original_plugins is not None:
                app.state.plugins = original_plugins
            else:
                delattr(app.state, "plugins")

    def test_get_plugin_manager_fallback_loads_plugins(self):
        """Test that get_plugin_manager falls back to loading plugins when app.state.plugins is None."""
        # Remove app.state.plugins
        original_plugins = getattr(app.state, "plugins", None)
        if hasattr(app.state, "plugins"):
            delattr(app.state, "plugins")

        try:
            result = get_plugin_manager()
            # Should return a PluginRegistry (not None)
            assert result is not None
            # Should have loaded plugins
            assert hasattr(result, "get")
        finally:
            # Restore original state
            if original_plugins is not None:
                app.state.plugins = original_plugins
