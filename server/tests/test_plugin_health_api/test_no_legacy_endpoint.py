"""TEST-CHANGE (Phase 11): /v1/plugins/{name} must not exist.

Regression test to prevent re-introduction of shadowed routes.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app_with_plugins):
    """Create a test client."""
    from app.auth import init_auth_service

    init_auth_service()
    return TestClient(app_with_plugins)


def test_legacy_plugin_endpoint_removed(client: TestClient) -> None:
    """Verify /v1/plugins/{name} no longer exists (Phase 11).

    This endpoint was removed because it shadowed the health endpoint.
    The canonical endpoint is now /v1/plugins/{name}/health only.
    """
    resp = client.get("/v1/plugins/ocr")
    assert resp.status_code in (404, 405), (
        "Phase 11 violation: /v1/plugins/{name} still exists. "
        "This endpoint must be removed. Use /v1/plugins/{name}/health instead."
    )
