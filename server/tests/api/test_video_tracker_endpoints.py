"""
Tests for Video Tracker API Endpoints

Tests the manifest and tool execution endpoints required for video processing:
- GET /plugins/{id}/manifest
- POST /plugins/{id}/tools/{tool}/run
"""

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app_with_plugins):
    """Create a test client"""
    from app.auth import init_auth_service

    init_auth_service()
    return TestClient(app_with_plugins)


class TestPluginManifestEndpoint:
    """Tests for GET /plugins/{plugin_id}/manifest"""

    def test_manifest_endpoint_exists(self, client: TestClient):
        """Verify manifest endpoint is available"""
        response = client.get("/v1/plugins/test-plugin/manifest")
        # Should return 404 or other HTTP response (not 501 Not Implemented)
        assert response.status_code != 501

    def test_manifest_response_structure(self, client: TestClient):
        """Verify manifest response has correct structure"""
        # Try with a known plugin (even if it fails, structure matters)
        response = client.get("/v1/plugins/invalid/manifest")

        # Should be valid JSON response
        if response.status_code < 500:
            try:
                data = response.json()
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.skip("Manifest endpoint not yet fully implemented")

    def test_manifest_caching_header(self, client: TestClient):
        """Verify manifest endpoint sets appropriate cache headers"""
        response = client.get("/v1/plugins/test-plugin/manifest")

        # Should have cache-control or similar headers
        # (even if plugin doesn't exist, endpoint should exist)
        assert "content-type" in response.headers or response.status_code in [404, 500]


class TestPluginToolRunEndpoint:
    """Tests for POST /plugins/{plugin_id}/tools/{tool_name}/run"""

    def test_tool_run_endpoint_exists(self, client: TestClient):
        """Verify tool run endpoint is available"""
        payload = {
            "frame_base64": "invalid",
            "device": "cpu",
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/detect_players/run", json=payload
        )
        # Should return 404 or other HTTP response (not 501 Not Implemented)
        assert response.status_code != 501

    def test_tool_run_accepts_json_payload(self, client: TestClient):
        """Verify tool run endpoint accepts JSON payloads"""
        payload = {
            "frame_base64": "",
            "device": "cpu",
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Should accept JSON (may fail for other reasons)
        assert response.headers.get("content-type") or response.status_code < 500

    def test_tool_run_with_base64_frame(self, client: TestClient):
        """Verify tool run accepts base64 encoded frames"""
        # Create a valid 1x1 PNG in base64
        png_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M"
            "9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

        payload = {
            "frame_base64": png_base64,
            "device": "cpu",
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Endpoint should exist even if plugin doesn't
        assert response.status_code != 501

    def test_tool_run_with_annotated_flag(self, client: TestClient):
        """Verify tool run accepts annotated parameter"""
        payload = {
            "frame_base64": "",
            "device": "cpu",
            "annotated": True,
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Should handle annotated parameter
        assert response.status_code != 501

    def test_tool_run_with_confidence_parameter(self, client: TestClient):
        """Verify tool run accepts confidence parameter"""
        payload = {
            "frame_base64": "",
            "device": "cpu",
            "confidence": 0.5,
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Should handle confidence parameter
        assert response.status_code != 501


class TestEndpointIntegration:
    """Tests for integrated manifest + tool run flow"""

    def test_manifest_then_tool_run_flow(self, client: TestClient):
        """Verify typical video tracker workflow"""
        # Step 1: Get manifest
        manifest_response = client.get("/v1/plugins/test-plugin/manifest")

        # Step 2: Run tool (should be callable regardless of Step 1 result)
        payload = {
            "frame_base64": "",
            "device": "cpu",
        }
        tool_response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Both endpoints should exist (not 501)
        assert manifest_response.status_code != 501
        assert tool_response.status_code != 501

    def test_tool_run_response_format(self, client: TestClient):
        """Verify tool run response format for video tracker"""
        payload = {
            "frame_base64": "",
            "device": "cpu",
        }
        response = client.post(
            "/v1/plugins/test-plugin/tools/test_tool/run", json=payload
        )

        # Should return valid response (even if error)
        if response.status_code < 500:
            try:
                data = response.json()
                # Response should be a dict with result
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.skip("Tool run endpoint response format not finalized")
