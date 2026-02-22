"""Tests for GET /video/status/{job_id} endpoint."""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
@pytest.mark.asyncio
class TestJobStatusEndpoint:
    """Tests for job status endpoint."""

    async def test_status_pending(self, client, session) -> None:
        """Assert pending job returns progress=0.0."""
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            status=JobStatus.pending,
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = await client.get(f"/v1/video/status/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == str(job.job_id)
        assert data["status"] == "pending"
        assert data["progress"] == 0.0
        assert "created_at" in data
        assert "updated_at" in data

    async def test_status_running(self, client, session) -> None:
        """Assert running job returns progress=0.5."""
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            status=JobStatus.running,
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = await client.get(f"/v1/video/status/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert data["progress"] == 0.5

    async def test_status_completed(self, client, session) -> None:
        """Assert completed job returns progress=1.0."""
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            output_path="video/output/test_results.json",
            status=JobStatus.completed,
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = await client.get(f"/v1/video/status/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0

    async def test_status_failed(self, client, session) -> None:
        """Assert failed job returns progress=1.0."""
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            status=JobStatus.failed,
            error_message="Test error",
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = await client.get(f"/v1/video/status/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "failed"
        assert data["progress"] == 1.0

    async def test_status_response_schema(self, client, session) -> None:
        """Assert response has all required fields."""
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            status=JobStatus.running,
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = await client.get(f"/v1/video/status/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert len(data) == 5  # exactly these fields

    async def test_status_not_found(self, client) -> None:
        """Assert 404 for missing job."""
        response = await client.get(
            "/v1/video/status/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
