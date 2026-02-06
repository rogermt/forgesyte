"""TEST-CHANGE (Phase 11): /v1/plugins/{name}/health is the canonical endpoint.

Regression test to ensure canonical endpoint stability.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app_with_plugins):
    """Create a test client."""
    from app.auth import init_auth_service

    init_auth_service()
    return TestClient(app_with_plugins)


def test_health_endpoint_is_canonical(client: TestClient) -> None:
    """Verify /v1/plugins/{name}/health is the only valid detail endpoint."""
    resp = client.get("/v1/plugins/ocr/health")
    assert resp.status_code == 200, (
        "Phase 11 violation: canonical health endpoint must return 200"
    )

    data = resp.json()
    assert "name" in data and "state" in data, (
        "Phase 11 violation: health endpoint returned invalid schema"
    )


def test_health_endpoint_returns_valid_schema(client: TestClient) -> None:
    """Verify health endpoint returns complete PluginHealthResponse."""
    resp = client.get("/v1/plugins/ocr/health")
    assert resp.status_code == 200

    data = resp.json()
    required_fields = {
        "name",
        "state",
        "description",
        "reason",
        "success_count",
        "error_count",
        "last_used",
        "uptime_seconds",
        "last_execution_time_ms",
        "avg_execution_time_ms",
    }
    assert required_fields.issubset(set(data.keys())), (
        f"Health response missing fields. Got: {set(data.keys())}, "
        f"Expected: {required_fields}"
    )


def test_nonexistent_plugin_returns_404(client: TestClient) -> None:
    """Verify health endpoint returns 404 for nonexistent plugins."""
    resp = client.get("/v1/plugins/nonexistent-plugin/health")
    assert resp.status_code == 404
