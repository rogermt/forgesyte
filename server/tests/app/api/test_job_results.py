"""Tests for GET /video/results/{job_id} endpoint."""

import json

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
@pytest.mark.asyncio
class TestJobResultsEndpoint:
    """Tests for job results endpoint."""

    async def test_results_completed(self, client, session) -> None:
        """Assert completed job returns results."""
        from pathlib import Path

        # Create results file first
        results_data = {"results": [{"frame_index": 0, "result": {"text": "test"}}]}
        results_file = "video/output/test_results.json"
        results_path = Path("./data/jobs") / results_file
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, "w") as f:
            json.dump(results_data, f)

        # Create completed job with output_path
        job = Job(
            plugin_id="yolo-tracker",
            tool="video_track",
            input_path="video/test.mp4",
            output_path=results_file,
            status=JobStatus.completed,
            job_type="video",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # GET /video/results/{job_id}
        response = await client.get(f"/v1/video/results/{job.job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == str(job.job_id)
        assert "results" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_results_pending(self, client, session) -> None:
        """Assert pending job returns 404."""
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

        response = await client.get(f"/v1/video/results/{job.job_id}")
        assert response.status_code == 404

    async def test_results_running(self, client, session) -> None:
        """Assert running job returns 404."""
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

        response = await client.get(f"/v1/video/results/{job.job_id}")
        assert response.status_code == 404

    async def test_results_failed(self, client, session) -> None:
        """Assert failed job returns 404."""
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

        response = await client.get(f"/v1/video/results/{job.job_id}")
        assert response.status_code == 404

    async def test_results_not_found(self, client) -> None:
        """Assert 404 for missing job."""
        response = await client.get(
            "/v1/video/results/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
