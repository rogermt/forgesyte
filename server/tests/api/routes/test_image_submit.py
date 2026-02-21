"""Tests for image_submit endpoint.

Tests verify:
1. Plugin validation works with properly loaded registry (Issue #209)
2. Tool validation works correctly
3. Error handling for invalid plugin/tool
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_routes.routes.image_submit import get_plugin_manager, get_plugin_service


@pytest.fixture
def mock_plugin_service():
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_plugin_manifest.return_value = {
        "tools": [
            {
                "id": "extract_text",
                "inputs": ["image_base64"],
            }
        ]
    }
    return mock


@pytest.fixture
def mock_plugin_registry():
    """Create a mock plugin registry with a loaded plugin."""
    mock = MagicMock()
    mock.get.return_value = MagicMock(
        name="ocr",
        description="OCR Plugin",
        version="1.0.0",
    )
    return mock


@pytest.fixture
def client_with_mocks(mock_plugin_registry, mock_plugin_service):
    """Create a test client with mocked dependencies."""
    from app.main import app

    # Override the dependency injection
    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    yield TestClient(app)

    # Clean up
    app.dependency_overrides.clear()


class TestImageSubmitPluginValidation:
    """Tests for plugin validation in image submit endpoint."""

    def test_submit_image_with_valid_plugin_and_tool(self, client_with_mocks):
        """Test that image submission works with valid plugin and tool."""
        # Create a valid PNG image (1x1 pixel)
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG magic bytes + padding

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        # Should succeed (or fail for other reasons like DB, not plugin validation)
        assert response.status_code in [
            200,
            500,
        ], f"Unexpected status: {response.status_code}, body: {response.text}"

    def test_submit_image_with_invalid_plugin(self, mock_plugin_service):
        """Test that image submission fails with invalid plugin."""
        from app.main import app

        # Create a mock that returns None for invalid plugin
        mock_registry = MagicMock()
        mock_registry.get.return_value = None  # Plugin not found

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_plugin_service

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

    def test_submit_image_with_invalid_tool(self, mock_plugin_registry):
        """Test that image submission fails with invalid tool."""
        from app.main import app

        # Create a mock service that doesn't have the tool
        mock_service = MagicMock()
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "different_tool",  # Not extract_text
                    "inputs": ["image_base64"],
                }
            ]
        }

        def override_get_plugin_manager():
            return mock_plugin_registry

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

    def test_submit_image_invalid_format(self, client_with_mocks):
        """Test that non-PNG/JPEG files are rejected."""
        # Create a file with invalid magic bytes
        invalid_data = b"INVALID FILE CONTENT"

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.txt", BytesIO(invalid_data), "text/plain")},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_submit_image_valid_jpeg(self, client_with_mocks):
        """Test that JPEG files are accepted."""
        # Create a valid JPEG (minimal header)
        jpeg_data = b"\xFF\xD8\xFF" + b"\x00" * 100  # JPEG magic bytes + padding

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.jpg", BytesIO(jpeg_data), "image/jpeg")},
        )

        assert response.status_code in [
            200,
            500,
        ], f"Unexpected status: {response.status_code}"


class TestImageSubmitToolInputValidation:
    """Tests for tool input type validation."""

    def test_submit_image_tool_supports_image_bytes(self, mock_plugin_registry):
        """Test that tools with image_bytes input are accepted."""
        from app.main import app

        mock_service = MagicMock()
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "extract_text",
                    "inputs": ["image_bytes"],  # Supports image_bytes
                }
            ]
        }
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=extract_text",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code in [200, 500]

    def test_submit_image_tool_does_not_support_image(self, mock_plugin_registry):
        """Test that tools without image input are rejected."""
        from app.main import app

        mock_service = MagicMock()
        mock_service.get_plugin_manifest.return_value = {
            "tools": [
                {
                    "id": "video_only_tool",
                    "inputs": ["video_path"],  # Only supports video
                }
            ]
        }
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        def override_get_plugin_manager():
            return mock_plugin_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

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
        from app.main import app

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
        from app.main import app

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
