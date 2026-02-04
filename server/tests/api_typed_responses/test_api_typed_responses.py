"""RED Tests for Typed API Responses.

These tests define the expected behavior for Phase 9 typed API responses:
- AnalyzeResponse
- JobStatusResponse
- JobResultResponse

Tests will FAIL until the models are implemented.
"""


class TestAnalyzeResponse:
    """Tests for AnalyzeResponse model."""

    def test_analyze_response_has_required_fields(self):
        """AnalyzeResponse must have job_id, device_requested, device_used, fallback, frames."""
        from app.models import AnalyzeResponse

        response = AnalyzeResponse(
            job_id="test-job-123",
            device_requested="gpu",
            device_used="gpu",
            fallback=False,
            frames=[{"data": "test"}],
        )
        assert response.job_id == "test-job-123"
        assert response.device_requested == "gpu"
        assert response.device_used == "gpu"
        assert response.fallback is False
        assert response.frames == [{"data": "test"}]

    def test_analyze_response_frames_is_list(self):
        """frames field must be a list of Any."""
        from app.models import AnalyzeResponse

        response = AnalyzeResponse(
            job_id="test-job-456",
            device_requested="cpu",
            device_used="cpu",
            fallback=False,
            frames=[],  # Empty list should be valid
        )
        assert isinstance(response.frames, list)

    def test_analyze_response_optional_fields(self):
        """AnalyzeResponse should accept optional result field."""
        from app.models import AnalyzeResponse

        response = AnalyzeResponse(
            job_id="test-job-789",
            device_requested="gpu",
            device_used="gpu",
            fallback=True,  # Fallback occurred
            frames=[{"frame": 1}],
            result={"detections": ["person"]},
        )
        assert response.result == {"detections": ["person"]}


class TestJobStatusResponse:
    """Tests for JobStatusResponse model."""

    def test_job_status_response_has_required_fields(self):
        """JobStatusResponse must have required fields."""
        from app.models import JobStatusResponse

        response = JobStatusResponse(
            job_id="job-123",
            status="running",
            device_requested="gpu",
            device_used="gpu",
        )
        assert response.job_id == "job-123"
        assert response.status == "running"
        assert response.device_requested == "gpu"
        assert response.device_used == "gpu"

    def test_job_status_response_all_statuses(self):
        """JobStatusResponse must accept all valid statuses."""
        from app.models import JobStatusResponse

        statuses = ["queued", "running", "done", "error", "not_found"]
        for status in statuses:
            response = JobStatusResponse(
                job_id=f"job-{status}",
                status=status,
                device_requested="cpu",
                device_used="cpu",
            )
            assert response.status == status


class TestJobResultResponse:
    """Tests for JobResultResponse model."""

    def test_job_result_response_has_required_fields(self):
        """JobResultResponse must have required fields."""
        from app.models import JobResultResponse

        response = JobResultResponse(
            job_id="result-job-123",
            device_requested="gpu",
            device_used="gpu",
            fallback=False,
            frames=[{"annotated": True}],
        )
        assert response.job_id == "result-job-123"
        assert response.device_requested == "gpu"
        assert response.device_used == "gpu"
        assert response.fallback is False
        assert response.frames == [{"annotated": True}]

    def test_job_result_response_with_result(self):
        """JobResultResponse should include result field."""
        from app.models import JobResultResponse

        response = JobResultResponse(
            job_id="result-job-456",
            device_requested="cpu",
            device_used="cpu",
            fallback=False,
            frames=[{"data": "test"}],
            result={"text": "Hello World", "confidence": 0.95},
        )
        assert response.result == {"text": "Hello World", "confidence": 0.95}


class TestDeviceFields:
    """Tests for device field consistency across models."""

    def test_analyze_response_device_fields(self):
        """AnalyzeResponse must have device_requested and device_used."""
        from app.models import AnalyzeResponse

        # Test with gpu requested, cpu used (fallback case)
        response = AnalyzeResponse(
            job_id="device-test-1",
            device_requested="gpu",
            device_used="cpu",
            fallback=True,
            frames=[],
        )
        assert response.device_requested == "gpu"
        assert response.device_used == "cpu"
        assert response.fallback is True

    def test_job_status_response_device_fields(self):
        """JobStatusResponse must have device_requested and device_used."""
        from app.models import JobStatusResponse

        response = JobStatusResponse(
            job_id="device-test-2",
            status="running",
            device_requested="gpu",
            device_used="gpu",
        )
        assert response.device_requested == "gpu"
        assert response.device_used == "gpu"

    def test_job_result_response_device_fields(self):
        """JobResultResponse must have device_requested and device_used."""
        from app.models import JobResultResponse

        response = JobResultResponse(
            job_id="device-test-3",
            device_requested="gpu",
            device_used="nvidia",
            fallback=False,
            frames=[],
        )
        assert response.device_requested == "gpu"
        assert response.device_used == "nvidia"
