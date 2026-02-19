"""Tests for worker health endpoint."""

import pytest
from fastapi.testclient import TestClient

from server.app.main import app
from server.app.workers.worker_state import worker_last_heartbeat


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_worker_health_endpoint_exists(client):
    """Verify /v1/worker/health endpoint exists."""
    response = client.get("/v1/worker/health")
    assert response.status_code == 200


def test_worker_health_returns_json(client):
    """Verify endpoint returns JSON with required fields."""
    response = client.get("/v1/worker/health")
    data = response.json()

    assert "alive" in data
    assert "last_heartbeat" in data
    assert isinstance(data["alive"], bool)
    assert isinstance(data["last_heartbeat"], (int, float))


def test_worker_health_not_alive_initially(client, monkeypatch):
    """Worker should not be alive initially (no heartbeat)."""
    # Reset heartbeat
    monkeypatch.setattr(worker_last_heartbeat, "timestamp", 0)

    response = client.get("/v1/worker/health")
    data = response.json()

    assert data["alive"] is False


def test_worker_health_alive_after_heartbeat(client):
    """Worker should be alive after heartbeat."""
    worker_last_heartbeat.beat()

    response = client.get("/v1/worker/health")
    data = response.json()

    assert data["alive"] is True
    assert data["last_heartbeat"] > 0
