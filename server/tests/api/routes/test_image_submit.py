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
        "analyze": {
            "handler": "analyze_handler",
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
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        # Should succeed
        assert (
            response.status_code == 200
        ), f"Unexpected status: {response.status_code}, body: {response.text}"

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
            "/v1/image/submit?plugin_id=nonexistent&tool=analyze",
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

    def test_submit_image_invalid_format(self, session: Session, client_with_mocks):
        """Test that non-PNG/JPEG files are rejected."""
        # Create a file with invalid magic bytes
        invalid_data = b"INVALID FILE CONTENT"

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.txt", BytesIO(invalid_data), "text/plain")},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_submit_image_valid_jpeg(self, session: Session, client_with_mocks):
        """Test that JPEG files are accepted."""
        # Create a valid JPEG (minimal header)
        jpeg_data = b"\xFF\xD8\xFF" + b"\x00" * 100  # JPEG magic bytes + padding

        response = client_with_mocks.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.jpg", BytesIO(jpeg_data), "image/jpeg")},
        )

        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

        # Verify job was created
        job_id = response.json()["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None


class TestImageSubmitToolInputValidation:
    """Tests for tool input type validation."""

    def test_submit_image_tool_supports_image_bytes(
        self, mock_plugin, session: Session
    ):
        """Test that tools with image_bytes input are accepted."""
        # Create plugin with image_bytes support
        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "description": "Extract text",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
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
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
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


class TestImageSubmitMutualExclusivity:
    """Tests for tool/logical_tool_id mutual exclusivity (v0.9.8)."""

    def test_mutual_exclusivity_tool_and_logical_tool_id(self, mock_plugin):
        """400 if both tool and logical_tool_id provided."""
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = list(mock_plugin.tools.keys())

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze&logical_tool_id=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "mutually exclusive" in response.json()["detail"].lower()


class TestImageSubmitRepeatableLogicalToolId:
    """Tests for repeatable logical_tool_id parameter (v0.9.8)."""

    def test_repeatable_logical_tool_id_single(self, mock_plugin, session: Session):
        """Single logical_tool_id resolves correctly."""
        # Create plugin with capabilities in manifest
        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "description": "Extract text",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
                "output_schema": {},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]
        mock_service.get_plugin_manifest.return_value = {
            "name": "ocr",
            "tools": [
                {
                    "id": "analyze",
                    "input_types": ["image_bytes"],
                    "capabilities": ["analyze"],
                }
            ],
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&logical_tool_id=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "submitted_at" in data
        assert "tool" in data  # Single tool response

    def test_repeatable_logical_tool_id_multiple(self, mock_plugin, session: Session):
        """Multiple logical_tool_id params resolve correctly."""
        plugin = MagicMock()
        plugin.tools = {
            "ocr_text": {
                "handler": "ocr_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            },
            "ocr_tables": {
                "handler": "tables_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["ocr_text", "ocr_tables"]
        mock_service.get_plugin_manifest.return_value = {
            "name": "ocr",
            "tools": [
                {
                    "id": "ocr_text",
                    "input_types": ["image_bytes"],
                    "capabilities": ["text_extraction"],
                },
                {
                    "id": "ocr_tables",
                    "input_types": ["image_bytes"],
                    "capabilities": ["table_extraction"],
                },
            ],
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&logical_tool_id=text_extraction&logical_tool_id=table_extraction",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "submitted_at" in data
        assert "tools" in data  # Multi-tool response
        assert len(data["tools"]) == 2
        # Verify structure: [{"logical": "...", "resolved": "..."}]
        assert "logical" in data["tools"][0]
        assert "resolved" in data["tools"][0]

        # Verify job_type in database
        job = session.query(Job).filter(Job.job_id == data["job_id"]).first()
        assert job is not None
        assert job.job_type == "image_multi"


class TestImageSubmitCanonicalJson:
    """Tests for canonical JSON response format (v0.9.8)."""

    def test_canonical_json_single_tool(self, mock_plugin, session: Session):
        """Single tool response includes submitted_at and tool field."""
        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]
        mock_service.get_plugin_manifest.return_value = {
            "name": "ocr",
            "tools": [
                {
                    "id": "analyze",
                    "input_types": ["image_bytes"],
                    "capabilities": ["analyze"],
                }
            ],
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&logical_tool_id=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Canonical JSON fields
        assert "job_id" in data
        assert "plugin" in data
        assert data["plugin"] == "ocr"
        assert "tool" in data
        assert "status" in data
        assert data["status"] == "queued"
        assert "submitted_at" in data
        # ISO 8601 format check
        assert "T" in data["submitted_at"]
        assert data["submitted_at"].endswith("Z")

    def test_canonical_json_multi_tool(self, mock_plugin, session: Session):
        """Multi-tool response includes tools array with logical/resolved."""
        plugin = MagicMock()
        plugin.tools = {
            "ocr_text": {
                "handler": "ocr_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            },
            "ocr_tables": {
                "handler": "tables_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            },
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["ocr_text", "ocr_tables"]
        mock_service.get_plugin_manifest.return_value = {
            "name": "ocr",
            "tools": [
                {
                    "id": "ocr_text",
                    "input_types": ["image_bytes"],
                    "capabilities": ["text_extraction"],
                },
                {
                    "id": "ocr_tables",
                    "input_types": ["image_bytes"],
                    "capabilities": ["table_extraction"],
                },
            ],
        }

        def override_get_plugin_manager():
            return mock_registry

        def override_get_plugin_service():
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&logical_tool_id=text_extraction&logical_tool_id=table_extraction",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Canonical JSON fields for multi-tool
        assert "job_id" in data
        assert "plugin" in data
        assert data["plugin"] == "ocr"
        assert "tools" in data
        assert "status" in data
        assert data["status"] == "queued"
        assert "submitted_at" in data

        # Tools array structure
        assert len(data["tools"]) == 2
        for tool_entry in data["tools"]:
            assert "logical" in tool_entry
            assert "resolved" in tool_entry

    def test_canonical_json_legacy_tool_path(self, mock_plugin, session: Session):
        """
        Verify that the legacy tool= submission path returns the canonical JSON response including job_id, plugin, tool, status and submitted_at.

        Submits a PNG file using the legacy query parameters (plugin_id and tool) and asserts a 200 response, presence of the canonical fields, and that `submitted_at` is an ISO 8601 UTC timestamp ending with 'Z'.
        """
        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]

        def override_get_plugin_manager():
            """
            Provide the mocked plugin registry to use as the application's plugin manager override.

            Returns:
                mock_registry: The mocked plugin registry instance to be injected as the plugin manager.
            """
            return mock_registry

        def override_get_plugin_service():
            """
            Provide the mocked plugin service used for dependency injection in tests.

            Returns:
                The mocked plugin service instance (`mock_service`) supplied by the test fixture.
            """
            return mock_service

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        # Canonical JSON fields - ALL paths should return these
        assert "job_id" in data
        assert "plugin" in data
        assert data["plugin"] == "ocr"
        assert "tool" in data
        assert data["tool"] == "analyze"
        assert "status" in data
        assert data["status"] == "queued"
        assert "submitted_at" in data
        # ISO 8601 format check
        assert "T" in data["submitted_at"]
        assert data["submitted_at"].endswith("Z")


class TestImageSubmitStorageRetry:
    """Tests for storage retry logic (Issue #332)."""

    def test_storage_save_retries_on_transient_failure(
        self, mock_plugin, session: Session
    ):
        """Storage save retries on transient errors (Issue #332).

        If storage.save_file fails with a transient error, it should be
        retried with exponential backoff before raising.
        """
        from app.api_routes.routes.image_submit import get_storage

        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]

        # Mock storage to fail once, then succeed
        call_count = [0]

        def mock_save_file(*args, **kwargs):
            """
            Simulate a storage save operation that fails once with a transient network error and then succeeds.

            Returns:
                str: The saved file path ("image/input/test.png") on successful save.

            Raises:
                ConnectionError: On the first invocation to simulate a transient network error.
            """
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: simulate transient S3 error
                raise ConnectionError("Transient network error")
            # Second call: succeed
            return "image/input/test.png"

        mock_storage = MagicMock()
        mock_storage.save_file.side_effect = mock_save_file

        def override_get_plugin_manager():
            """
            Provide the mocked plugin registry to use as the application's plugin manager override.

            Returns:
                mock_registry: The mocked plugin registry instance to be injected as the plugin manager.
            """
            return mock_registry

        def override_get_plugin_service():
            """
            Provide the mocked plugin service used for dependency injection in tests.

            Returns:
                The mocked plugin service instance (`mock_service`) supplied by the test fixture.
            """
            return mock_service

        def override_get_storage():
            """
            Provide the mock storage instance for dependency overrides in tests.

            Returns:
                mock_storage: The mock storage object used by tests, exposing the same public methods as the production storage implementation (e.g. `save_file`).
            """
            return mock_storage

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service
        app.dependency_overrides[get_storage] = override_get_storage

        client = TestClient(app)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        # Should succeed after retry
        assert response.status_code == 200, f"Got: {response.text}"
        data = response.json()
        assert "job_id" in data
        # Verify retry happened
        assert call_count[0] >= 2, "Expected at least 2 calls (1 fail + 1 success)"

    def test_non_transient_error_propagates_without_retry(
        self, mock_plugin, session: Session
    ):
        """Non-transient errors like FileNotFoundError should NOT retry (Issue #337).

        Only transient errors (ConnectionError, TimeoutError) should be retried.
        Non-transient errors should propagate immediately.
        """
        from app.api_routes.routes.image_submit import get_storage

        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]

        # Mock storage to raise non-transient error
        call_count = [0]

        def mock_save_file(*args, **kwargs):
            """
            Simulate a storage save that always fails with a non-transient error.

            Increments the external `call_count[0]` counter on each invocation and raises
            FileNotFoundError to emulate a non-transient storage failure (no return).
            """
            call_count[0] += 1
            raise FileNotFoundError("Path not found")

        mock_storage = MagicMock()
        mock_storage.save_file.side_effect = mock_save_file

        def override_get_plugin_manager():
            """
            Provide the mocked plugin registry to use as the application's plugin manager override.

            Returns:
                mock_registry: The mocked plugin registry instance to be injected as the plugin manager.
            """
            return mock_registry

        def override_get_plugin_service():
            """
            Provide the mocked plugin service used for dependency injection in tests.

            Returns:
                The mocked plugin service instance (`mock_service`) supplied by the test fixture.
            """
            return mock_service

        def override_get_storage():
            """
            Provide the mock storage instance for dependency overrides in tests.

            Returns:
                mock_storage: The mock storage object used by tests, exposing the same public methods as the production storage implementation (e.g. `save_file`).
            """
            return mock_storage

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service
        app.dependency_overrides[get_storage] = override_get_storage

        # Use raise_server_exceptions=False to catch exceptions as 500 responses
        client = TestClient(app, raise_server_exceptions=False)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        # Should fail with 500 (internal error) after exception is caught
        assert (
            response.status_code == 500
        ), f"Got status {response.status_code}: {response.text[:200] if response.text else 'empty'}"
        # CRITICAL (Issue #337): Should NOT retry non-transient errors
        assert (
            call_count[0] == 1
        ), f"Expected exactly 1 call (no retry), got {call_count[0]} calls"

    def test_transient_error_retries_three_times_then_raises(
        self, mock_plugin, session: Session
    ):
        """Transient errors should retry exactly 3 times before raising (Issue #337)."""
        from app.api_routes.routes.image_submit import get_storage

        plugin = MagicMock()
        plugin.tools = {
            "analyze": {
                "handler": "analyze_handler",
                "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            }
        }

        mock_registry = MagicMock()
        mock_registry.get.return_value = plugin

        mock_service = MagicMock()
        mock_service.get_available_tools.return_value = ["analyze"]

        # Mock storage to always fail with transient error
        call_count = [0]

        def mock_save_file(*args, **kwargs):
            """
            Mock replacement for a storage `save_file` function that records invocation and simulates a transient network failure.

            Increments `call_count[0]` to indicate an attempted save, then raises a `ConnectionError`.

            Raises:
                ConnectionError: Always raised to simulate a transient network error.
            """
            call_count[0] += 1
            raise ConnectionError("Network error")

        mock_storage = MagicMock()
        mock_storage.save_file.side_effect = mock_save_file

        def override_get_plugin_manager():
            """
            Provide the mocked plugin registry to use as the application's plugin manager override.

            Returns:
                mock_registry: The mocked plugin registry instance to be injected as the plugin manager.
            """
            return mock_registry

        def override_get_plugin_service():
            """
            Provide the mocked plugin service used for dependency injection in tests.

            Returns:
                The mocked plugin service instance (`mock_service`) supplied by the test fixture.
            """
            return mock_service

        def override_get_storage():
            """
            Provide the mock storage instance for dependency overrides in tests.

            Returns:
                mock_storage: The mock storage object used by tests, exposing the same public methods as the production storage implementation (e.g. `save_file`).
            """
            return mock_storage

        app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
        app.dependency_overrides[get_plugin_service] = override_get_plugin_service
        app.dependency_overrides[get_storage] = override_get_storage

        # Use raise_server_exceptions=False to catch exceptions as 500 responses
        client = TestClient(app, raise_server_exceptions=False)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        response = client.post(
            "/v1/image/submit?plugin_id=ocr&tool=analyze",
            files={"file": ("test.png", BytesIO(png_data), "image/png")},
        )

        app.dependency_overrides.clear()

        # Should fail with 500 after retries exhausted
        assert response.status_code == 500, f"Got: {response.text}"
        # CRITICAL (Issue #337): Should retry exactly 3 times
        assert (
            call_count[0] == 3
        ), f"Expected exactly 3 retries, got {call_count[0]} calls"
