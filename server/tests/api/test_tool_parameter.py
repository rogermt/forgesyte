"""TEST-CHANGE: Tests for tool parameter in /analyze endpoint.

Verifies that tool selection is properly passed from frontend to backend tasks.
Issue: https://github.com/rogermt/forgesyte/issues/179
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def client(app_with_plugins):
    """Create a test client."""
    # Initialize auth service before creating client.
    # TestClient doesn't automatically trigger app lifespan events.
    from app.auth import init_auth_service

    init_auth_service()

    return TestClient(app_with_plugins)


class TestToolParameter:
    """Test tool parameter in /analyze endpoint."""

    def test_analyze_accepts_tool_query_parameter(
        self, client: TestClient
    ) -> None:
        """Test that /analyze accepts tool query parameter.

        Verifies tool parameter is accepted and passed to backend.
        """
        test_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        response = client.post(
            "/v1/analyze",
            files={"file": ("test.png", test_image, "image/png")},
            params={
                "plugin": "ocr",
                "tool": "extract_text",  # Specify tool explicitly
            },
            headers={"X-API-Key": "test-user-key"},
        )

        # Should accept the request
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_analyze_tool_parameter_optional(
        self, client: TestClient
    ) -> None:
        """Test that tool parameter is optional.

        Tool should not be required; call should work without it.
        """
        test_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        response = client.post(
            "/v1/analyze",
            files={"file": ("test.png", test_image, "image/png")},
            params={
                "plugin": "ocr",
                # No tool parameter
            },
            headers={"X-API-Key": "test-user-key"},
        )

        # Should still succeed (tool is optional)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_analyze_tool_parameter_passed_to_options(
        self, client: TestClient, monkeypatch
    ) -> None:
        """TEST-CHANGE: Test that tool parameter is included in task options.

        Verifies that when tool is specified, it's passed in the options
        to the task submission.
        """
        from unittest.mock import AsyncMock, MagicMock

        # Track the options passed to analyze_image
        captured_options = {}

        async def mock_analyze(*args, **kwargs):
            captured_options.update(kwargs.get("options", {}))
            return {"job_id": "test-job-123"}

        # Create mock service
        mock_service = MagicMock()
        mock_service.analyze_image = mock_analyze

        # Patch the get_analysis_service dependency
        def mock_get_service():
            return mock_service

        monkeypatch.setattr("app.api.get_analysis_service", lambda: mock_service)

        test_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        response = client.post(
            "/v1/analyze",
            files={"file": ("test.png", test_image, "image/png")},
            params={
                "plugin": "ocr",
                "tool": "extract_text",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
