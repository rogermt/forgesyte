"""Tests for analysis execution API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_routes.routes.execution import clear_service_resolver, set_service_resolver
from app.auth import init_auth_service

# Initialize auth once at module load
init_auth_service()


@pytest.fixture
def mock_service():
    """Create a fresh mock service for each test."""
    service = MagicMock()

    # Async methods - use AsyncMock for await support
    service.submit_analysis_async = AsyncMock(return_value="mock-job-id")
    service.get_job_result = AsyncMock(return_value=None)
    service.list_jobs = AsyncMock(return_value=[])
    service.cancel_job = AsyncMock(return_value=True)
    service.analyze = AsyncMock(return_value=({"result": {}, "value": 42}, None))

    return service


@pytest.fixture
def client(mock_service):
    """Create a test client with mocked service."""
    from app.main import app

    # Clear any previous resolver and set new one
    clear_service_resolver()
    set_service_resolver(lambda: mock_service)

    with TestClient(app) as client:
        yield client

    # Cleanup
    clear_service_resolver()


class TestSyncExecution:
    """Tests for synchronous analysis execution."""

    def test_sync_execution_success(self, mock_service, client):
        """Test synchronous analysis execution - success case."""
        # Set up the mock return value
        mock_service.analyze.return_value = (
            {"result": {}, "value": 42, "detections": []},
            None,  # no error
        )

        response = client.post(
            "/v1/analyze-execution",
            json={
                "tools": ["analyze"],
                "plugin": "good",
                "image": "test_image_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["plugin"] == "good"
        assert body["result"]["value"] == 42

    def test_sync_execution_failure(self, mock_service, client):
        """Test synchronous analysis execution - error case."""
        # Set up the mock to return an error
        mock_service.analyze.return_value = (
            None,
            {"type": "execution_error", "message": "Plugin failed"},
        )

        response = client.post(
            "/v1/analyze-execution",
            json={
                "tools": ["analyze"],
                "plugin": "bad",
                "image": "test_image_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert body["detail"]["type"] == "execution_error"

    def test_sync_execution_default_plugin(self, mock_service, client):
        """Test that default plugin 'default' is used when not specified."""
        mock_service.analyze.return_value = ({"result": {}}, None)

        response = client.post(
            "/v1/analyze-execution",
            json={
                "tools": ["analyze"],
                "image": "test_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200


class TestAsyncExecution:
    """Tests for asynchronous job creation."""

    def test_async_job_creation(self, mock_service, client):
        """Test async job creation returns job_id."""
        response = client.post(
            "/v1/analyze-execution/async",
            json={
                "tools": ["analyze"],
                "plugin": "good",
                "image": "test_image_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
        assert body["job_id"] == "mock-job-id"
        mock_service.submit_analysis_async.assert_called_once()

    def test_async_job_creation_calls_service(self, mock_service, client):
        """Test that async job creation calls the service method."""
        response = client.post(
            "/v1/analyze-execution/async",
            json={
                "tools": ["analyze"],
                "plugin": "test_plugin",
                "image": "test_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        mock_service.submit_analysis_async.assert_called_once()
        call_kwargs = mock_service.submit_analysis_async.call_args.kwargs
        assert call_kwargs["plugin_name"] == "test_plugin"
        assert call_kwargs["mime_type"] == "image/png"


class TestJobStatus:
    """Tests for job status retrieval."""

    def test_get_job_status_success(self, mock_service, client):
        """Test getting status of an existing job."""
        # Set up the mock to return a job
        mock_service.get_job_result.return_value = {
            "id": "test-job-123",
            "plugin": "yolo_football",
            "status": "running",
        }

        response = client.get(
            "/v1/analyze-execution/jobs/test-job-123",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["job"]["id"] == "test-job-123"
        assert body["job"]["status"] == "running"

    def test_get_job_status_not_found(self, mock_service, client):
        """Test getting status of non-existent job returns 404."""
        # Keep mock returning None for not found
        mock_service.get_job_result.return_value = None

        response = client.get(
            "/v1/analyze-execution/jobs/non-existent-id",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 404


class TestJobResult:
    """Tests for job result retrieval."""

    def test_get_job_result_success(self, mock_service, client):
        """Test getting result of a completed job."""
        mock_service.get_job_result.return_value = {
            "id": "completed-job",
            "plugin": "yolo_football",
            "status": "success",
            "result": {"value": 100},
        }

        response = client.get(
            "/v1/analyze-execution/jobs/completed-job/result",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["job_id"] == "completed-job"
        assert body["status"] == "success"
        assert body["result"]["value"] == 100

    def test_get_job_result_still_running(self, mock_service, client):
        """Test getting result of still-running job returns 409."""
        mock_service.get_job_result.return_value = {
            "id": "running-job",
            "plugin": "yolo_football",
            "status": "running",
        }

        response = client.get(
            "/v1/analyze-execution/jobs/running-job/result",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 409
        assert "still running" in response.json()["detail"].lower()

    def test_get_job_result_not_found(self, mock_service, client):
        """Test getting result of non-existent job returns 404."""
        mock_service.get_job_result.return_value = None

        response = client.get(
            "/v1/analyze-execution/jobs/missing-job/result",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 404


class TestJobList:
    """Tests for job listing."""

    def test_list_jobs_empty(self, mock_service, client):
        """Test listing jobs when none exist."""
        mock_service.list_jobs.return_value = []

        response = client.get(
            "/v1/analyze-execution/jobs",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["jobs"] == []
        assert body["count"] == 0

    def test_list_jobs_with_results(self, mock_service, client):
        """Test listing jobs returns all jobs."""
        mock_service.list_jobs.return_value = [
            {"id": "job-1", "plugin": "yolo", "status": "success"},
            {"id": "job-2", "plugin": "ocr", "status": "running"},
        ]

        response = client.get(
            "/v1/analyze-execution/jobs",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["jobs"]) == 2
        assert body["count"] == 2

    def test_list_jobs_filter_by_plugin(self, mock_service, client):
        """Test listing jobs with plugin filter."""
        mock_service.list_jobs.return_value = [
            {"id": "job-1", "plugin": "yolo_football", "status": "success"},
        ]

        response = client.get(
            "/v1/analyze-execution/jobs?plugin=yolo_football",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["jobs"]) == 1
        assert body["jobs"][0]["plugin"] == "yolo_football"

    def test_list_jobs_filter_by_status(self, mock_service, client):
        """Test listing jobs with status filter."""
        mock_service.list_jobs.return_value = [
            {"id": "job-1", "plugin": "yolo", "status": "success"},
        ]

        response = client.get(
            "/v1/analyze-execution/jobs?status=success",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["jobs"]) == 1
        assert body["jobs"][0]["status"] == "success"


class TestJobCancel:
    """Tests for job cancellation."""

    def test_cancel_job_success(self, mock_service, client):
        """Test cancelling a pending job."""
        # get_job returns a running job (not cancelled yet)
        mock_service.get_job_result.return_value = {
            "id": "pending-job",
            "plugin": "yolo_football",
            "status": "running",
        }

        response = client.delete(
            "/v1/analyze-execution/jobs/pending-job",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["job_id"] == "pending-job"
        assert body["status"] == "cancelled"

    def test_cancel_job_not_found(self, mock_service, client):
        """Test cancelling non-existent job returns 404."""
        mock_service.get_job_result.return_value = None

        response = client.delete(
            "/v1/analyze-execution/jobs/non-existent",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 404

    def test_cancel_job_already_completed(self, mock_service, client):
        """Test cancelling already completed job returns 409."""
        mock_service.get_job_result.return_value = {
            "id": "completed-job",
            "plugin": "yolo_football",
            "status": "success",
        }

        response = client.delete(
            "/v1/analyze-execution/jobs/completed-job",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 409
        assert "already completed" in response.json()["detail"].lower()

    def test_cancel_job_already_failed(self, mock_service, client):
        """Test cancelling already failed job returns 409."""
        mock_service.get_job_result.return_value = {
            "id": "failed-job",
            "plugin": "yolo_football",
            "status": "failed",
        }

        response = client.delete(
            "/v1/analyze-execution/jobs/failed-job",
            headers={"X-API-Key": "test-user-key"},
        )

        assert response.status_code == 409


class TestAsyncWorkflow:
    """Integration tests for async workflow."""

    def test_async_workflow_full_flow(self, mock_service, client):
        """Test complete async workflow: create -> poll -> result."""
        # Step 1: Create async job
        create_response = client.post(
            "/v1/analyze-execution/async",
            json={
                "tools": ["analyze"],
                "plugin": "yolo_football",
                "image": "frame_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Step 2: Set up mock for status check
        mock_service.get_job_result.return_value = {
            "id": job_id,
            "plugin": "yolo_football",
            "status": "success",
            "result": {"detections": []},
        }

        # Poll for status until complete
        status_response = client.get(
            f"/v1/analyze-execution/jobs/{job_id}",
            headers={"X-API-Key": "test-user-key"},
        )

        assert status_response.status_code == 200

        # Step 3: Get result
        result_response = client.get(
            f"/v1/analyze-execution/jobs/{job_id}/result",
            headers={"X-API-Key": "test-user-key"},
        )

        assert result_response.status_code == 200
        body = result_response.json()
        assert body["job_id"] == job_id

    def test_async_workflow_cancel_flow(self, mock_service, client):
        """Test async workflow with cancellation."""
        # Step 1: Create async job
        create_response = client.post(
            "/v1/analyze-execution/async",
            json={
                "tools": ["analyze"],
                "plugin": "yolo_football",
                "image": "frame_data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "test-user-key"},
        )

        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Step 2: Set up mock for pending job
        mock_service.get_job_result.return_value = {
            "id": job_id,
            "plugin": "yolo_football",
            "status": "running",
        }

        # Cancel the job
        cancel_response = client.delete(
            f"/v1/analyze-execution/jobs/{job_id}",
            headers={"X-API-Key": "test-user-key"},
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"


class TestAuthentication:
    """Tests for authentication enforcement."""

    def test_requires_authentication(self, client):
        """Test that endpoints require authentication."""
        response = client.post(
            "/v1/analyze-execution",
            json={
                "tools": ["analyze"],
                "plugin": "test",
                "image": "data",
                "mime_type": "image/png",
            },
        )

        # Should fail without auth header
        assert response.status_code in (401, 403)

    def test_wrong_api_key_rejected(self, client):
        """Test that wrong API key is rejected."""
        response = client.post(
            "/v1/analyze-execution",
            json={
                "tools": ["analyze"],
                "plugin": "test",
                "image": "data",
                "mime_type": "image/png",
            },
            headers={"X-API-Key": "wrong-key"},
        )

        assert response.status_code in (401, 403)
