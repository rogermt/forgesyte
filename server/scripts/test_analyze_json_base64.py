"""Integration test for /analyze/json endpoint with JSON base64 image."""

import base64
import os
import sys
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.api import get_analysis_service
from app.auth import get_auth_service
from app.main import app

# ---------------------------------------------------------------------------
# Override AUTH
# ---------------------------------------------------------------------------


def fake_auth_service():
    svc = MagicMock()
    svc.validate_token.return_value = {"user": "test", "permissions": ["analyze"]}
    return svc


app.dependency_overrides[get_auth_service] = fake_auth_service


# ---------------------------------------------------------------------------
# Override ANALYSIS SERVICE
# ---------------------------------------------------------------------------


def fake_analysis_service():
    svc = MagicMock()
    svc.process_analysis_request = AsyncMock(
        return_value={
            "job_id": "job-123",
            "plugin": "ocr",
        }
    )
    return svc


app.dependency_overrides[get_analysis_service] = fake_analysis_service


client = TestClient(app)


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------


def test_analyze_json_base64_uses_cuda() -> None:
    raw = b"fakeimg"
    b64 = base64.b64encode(raw).decode()

    resp = client.post(
        "/v1/analyze/json?plugin=ocr",
        json={"image": b64, "device": "cuda", "options": {}},
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    data = resp.json()

    assert data["job_id"] == "job-123"
    assert data["device_requested"] == "cuda"
