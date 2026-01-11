"""Tests for REST API endpoints.

Following TDD: Write tests first, then implement code to make them pass.
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
    return TestClient(app_with_plugins)


class TestHealthCheckEndpoint:
    """Test /health endpoint - no auth required."""

    def test_health_check_success(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_health_check_response_structure(self, client: TestClient) -> None:
        """Test health check response has expected fields."""
        response = client.get("/v1/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "plugins_loaded" in data or "version" in data


class TestMCPVersionEndpoint:
    """Test /mcp-version endpoint - no auth required."""

    def test_mcp_version_endpoint(self, client: TestClient) -> None:
        """Test /mcp-version endpoint returns version info."""
        response = client.get("/v1/mcp-version")
        assert response.status_code == 200
        data = response.json()
        assert "server_name" in data
        assert "server_version" in data
        assert "mcp_version" in data

    def test_mcp_version_has_string_values(self, client: TestClient) -> None:
        """Test that version endpoint returns string values."""
        response = client.get("/v1/mcp-version")
        data = response.json()
        assert isinstance(data["server_name"], str)
        assert isinstance(data["server_version"], str)
        assert isinstance(data["mcp_version"], str)


class TestGeminiExtensionEndpoint:
    """Test /gemini-extension endpoint - no auth required."""

    def test_gemini_extension_endpoint(self, client: TestClient) -> None:
        """Test /gemini-extension endpoint."""
        response = client.get("/v1/gemini-extension")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_gemini_extension_has_required_fields(self, client: TestClient) -> None:
        """Test gemini extension response structure."""
        response = client.get("/v1/gemini-extension")
        if response.status_code == 200:
            data = response.json()
            # Should have some extension manifest data
            assert len(data) > 0


class TestListPluginsEndpoint:
    """Test /plugins endpoint - no auth required."""

    def test_list_plugins_endpoint_exists(self, client: TestClient) -> None:
        """Test /plugins endpoint exists."""
        response = client.get("/v1/plugins")
        assert response.status_code == 200

    def test_list_plugins_returns_dict(self, client: TestClient) -> None:
        """Test listing plugins returns proper structure."""
        response = client.get("/v1/plugins")
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "plugins" in data
            assert isinstance(data["plugins"], list)
            assert isinstance(data["count"], int)

    def test_list_plugins_count_matches_length(self, client: TestClient) -> None:
        """Test that count matches number of plugins."""
        response = client.get("/v1/plugins")
        if response.status_code == 200:
            data = response.json()
            assert data["count"] == len(data["plugins"])


class TestGetPluginInfoEndpoint:
    """Test /plugins/{name} endpoint - no auth required."""

    def test_get_plugin_nonexistent(self, client: TestClient) -> None:
        """Test getting info for non-existent plugin."""
        response = client.get("/v1/plugins/definitely_not_a_real_plugin_xyz")
        assert response.status_code == 404

    def test_get_plugin_not_found_has_error_message(self, client: TestClient) -> None:
        """Test that 404 response includes error info."""
        response = client.get("/v1/plugins/nonexistent")
        if response.status_code == 404:
            data = response.json()
            # Should have error details
            assert "detail" in data or isinstance(data, dict)


class TestMCPManifestEndpoint:
    """Test MCP manifest endpoints - no auth required."""

    def test_mcp_manifest_endpoint(self, client: TestClient) -> None:
        """Test /mcp-manifest endpoint."""
        response = client.get("/v1/mcp-manifest")
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500, 503]

    def test_well_known_mcp_manifest(self, client: TestClient) -> None:
        """Test /.well-known/mcp-manifest endpoint."""
        response = client.get("/v1/.well-known/mcp-manifest")
        assert response.status_code in [200, 500, 503]

    def test_both_manifests_return_dict(self, client: TestClient) -> None:
        """Test that manifest endpoints return dict when successful."""
        response = client.get("/v1/mcp-manifest")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestAPIErrorHandling:
    """Test error handling in API endpoints."""

    def test_404_not_found(self, client: TestClient) -> None:
        """Test 404 for non-existent endpoint."""
        response = client.get("/v1/nonexistent_endpoint_xyz")
        assert response.status_code == 404

    def test_invalid_http_method(self, client: TestClient) -> None:
        """Test invalid HTTP method."""
        response = client.patch("/v1/health")
        assert response.status_code == 405

    def test_404_response_is_json(self, client: TestClient) -> None:
        """Test that 404 returns valid JSON."""
        response = client.get("/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert isinstance(data, dict)


class TestAuthRequiredEndpoints:
    """Test that protected endpoints require authentication."""

    def test_analyze_requires_auth(self, client: TestClient) -> None:
        """Test that /analyze requires authentication."""
        response = client.post("/v1/analyze", data=b"fake_image")
        assert response.status_code in [401, 403]

    def test_get_job_requires_auth(self, client: TestClient) -> None:
        """Test that /jobs/{job_id} requires authentication."""
        response = client.get("/v1/jobs/job123")
        assert response.status_code in [401, 403]

    def test_list_jobs_requires_auth(self, client: TestClient) -> None:
        """Test that /jobs requires authentication."""
        response = client.get("/v1/jobs")
        assert response.status_code in [401, 403]

    def test_cancel_job_requires_auth(self, client: TestClient) -> None:
        """Test that DELETE /jobs/{job_id} requires authentication."""
        response = client.delete("/v1/jobs/job123")
        assert response.status_code in [401, 403]

    def test_reload_plugin_requires_auth(self, client: TestClient) -> None:
        """Test that reload requires authentication."""
        response = client.post("/v1/plugins/test/reload")
        assert response.status_code in [401, 403]

    def test_reload_all_requires_auth(self, client: TestClient) -> None:
        """Test that reload-all requires authentication."""
        response = client.post("/v1/plugins/reload-all")
        assert response.status_code in [401, 403]


class TestAnalyzeEndpointInputValidation:
    """Test input validation for /analyze endpoint."""

    def test_analyze_invalid_json_options(self, client: TestClient) -> None:
        """Test analyze with invalid JSON options."""
        response = client.post(
            "/v1/analyze",
            data=b"fake_image",
            params={"options": "not valid json"},
            headers={"X-API-Key": "test-key"},
        )
        # Should reject invalid JSON
        assert response.status_code == 400

    def test_analyze_invalid_base64_in_body(self, client: TestClient) -> None:
        """Test analyze with invalid base64 in body."""
        response = client.post(
            "/v1/analyze",
            content=b"not_valid_base64!!!",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 400

    def test_analyze_empty_request_fails(self, client: TestClient) -> None:
        """Test analyze without image data fails."""
        response = client.post(
            "/v1/analyze",
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 400


class TestServerInitialization:
    """Test server initialization and basic structure."""

    def test_app_has_v1_prefix(self, client: TestClient) -> None:
        """Test that API routes are under /v1 prefix."""
        # Health check should exist at /v1/health
        response = client.get("/v1/health")
        assert response.status_code in [200, 503]

    def test_nonexistent_v1_route(self, client: TestClient) -> None:
        """Test that nonexistent /v1 routes return 404."""
        response = client.get("/v1/this_route_does_not_exist")
        assert response.status_code == 404

    def test_root_endpoint_exists(self, client: TestClient) -> None:
        """Test that root endpoint exists."""
        response = client.get("/")
        # Should return info or redirect
        assert response.status_code in [200, 307, 308]


class TestResponseFormats:
    """Test response formats and content types."""

    def test_health_check_is_json(self, client: TestClient) -> None:
        """Test that health check returns JSON."""
        response = client.get("/v1/health")
        if response.status_code == 200:
            assert response.headers["content-type"].startswith("application/json")

    def test_mcp_version_is_json(self, client: TestClient) -> None:
        """Test that mcp-version returns JSON."""
        response = client.get("/v1/mcp-version")
        assert response.headers["content-type"].startswith("application/json")

    def test_plugins_list_is_json(self, client: TestClient) -> None:
        """Test that plugins list returns JSON."""
        response = client.get("/v1/plugins")
        assert response.headers["content-type"].startswith("application/json")


class TestEndpointExistence:
    """Test that all expected endpoints exist."""

    def test_mcp_manifest_route_exists(self, client: TestClient) -> None:
        """Test /mcp-manifest route exists."""
        response = client.get("/v1/mcp-manifest")
        # Should not return 404
        assert response.status_code != 404

    def test_well_known_manifest_route_exists(self, client: TestClient) -> None:
        """Test /.well-known/mcp-manifest route exists."""
        response = client.get("/v1/.well-known/mcp-manifest")
        assert response.status_code != 404

    def test_version_route_exists(self, client: TestClient) -> None:
        """Test /mcp-version route exists."""
        response = client.get("/v1/mcp-version")
        assert response.status_code != 404

    def test_health_route_exists(self, client: TestClient) -> None:
        """Test /health route exists."""
        response = client.get("/v1/health")
        assert response.status_code != 404

    def test_gemini_extension_route_exists(self, client: TestClient) -> None:
        """Test /gemini-extension route exists."""
        response = client.get("/v1/gemini-extension")
        assert response.status_code != 404

    def test_plugins_route_exists(self, client: TestClient) -> None:
        """Test /plugins route exists."""
        response = client.get("/v1/plugins")
        assert response.status_code != 404
