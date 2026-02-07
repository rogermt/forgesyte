"""Pytest configuration for execution tests."""

import os

# Configure authentication BEFORE importing app or pytest
os.environ.setdefault("FORGESYTE_ADMIN_KEY", "test-admin-key")
os.environ.setdefault("FORGESYTE_USER_KEY", "test-user-key")

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_routes.routes.execution import clear_service_resolver, set_service_resolver
from app.auth import init_auth_service


@pytest.fixture(scope="module")
def setup_auth():
    """Initialize auth service for execution tests."""
    init_auth_service()


@pytest.fixture
def mock_analysis_service():
    """Create a mock AnalysisExecutionService with proper async support."""
    service = MagicMock()

    # Set up async methods using AsyncMock (without spec to preserve async behavior)
    service.submit_analysis_async = AsyncMock(return_value="mock-job-id")
    service.get_job_result = AsyncMock(return_value=None)
    service.list_jobs = AsyncMock(return_value=[])
    service.cancel_job = AsyncMock(return_value=True)

    # Sync method
    service.analyze = MagicMock(return_value=({"result": {}}, None))

    return service


@pytest.fixture
def client(setup_auth, mock_analysis_service):
    """Create a test client with mocked service."""
    from app.main import app

    # Set up the resolver to return our mock service
    set_service_resolver(lambda: mock_analysis_service)

    yield TestClient(app)

    # Clean up
    clear_service_resolver()
