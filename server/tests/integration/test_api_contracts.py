"""
API Contract Verification Tests

These integration tests verify that real API responses match documented schemas.
This ensures that client mocks (based on fixtures) always match server reality.

Each test calls a real endpoint and validates the response shape against
the Pydantic models defined in server/app/models.py

Related: Issue #22 - Mock Data Standardization
Reference: fixtures/api-responses.json (golden fixtures)
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.models import JobResponse, JobStatus, JobStatusResponse


@pytest.mark.integration
class TestJobsEndpointContract:
    """Verify /v1/jobs endpoint returns documented JobResponse schema"""

    async def test_jobs_list_endpoint_returns_valid_job_responses(
        self, client: AsyncClient
    ) -> None:
        """GET /v1/jobs should return list matching JobResponse schema"""
        response = await client.get("/v1/jobs?limit=10")
        assert response.status_code == 200

        data = response.json()

        # Verify top-level structure
        assert "jobs" in data, "Response must contain 'jobs' key"
        assert "count" in data, "Response must contain 'count' key"
        assert isinstance(data["jobs"], list), "jobs must be a list"
        assert isinstance(data["count"], int), "count must be an integer"

        # Verify each job matches JobResponse schema
        for job_data in data["jobs"]:
            try:
                job = JobResponse(**job_data)
                # If validation passes, schema is correct
                assert job.job_id is not None
                assert job.status in [s.value for s in JobStatus]
                assert job.created_at is not None
            except ValidationError as e:
                pytest.fail(f"Job response doesn't match schema: {e}")

    async def test_jobs_endpoint_field_names_match_schema(
        self, client: AsyncClient
    ) -> None:
        """Verify job response uses correct field names (job_id not id)"""
        response = await client.get("/v1/jobs?limit=1")
        data = response.json()

        if data["jobs"]:
            job = data["jobs"][0]
            # These must be present with exact names
            assert "job_id" in job, "Must use 'job_id' not 'id'"
            assert "status" in job, "Must contain 'status'"
            assert "created_at" in job, "Must contain 'created_at'"
            assert "plugin" in job, "Must contain 'plugin'"

            # These should NOT be present
            assert "id" not in job, "Should not use 'id' field"
            assert "updated_at" not in job, "Should not use 'updated_at'"

    async def test_jobs_endpoint_status_values_valid(self, client: AsyncClient) -> None:
        """Verify job status values match JobStatus enum"""
        response = await client.get("/v1/jobs?limit=100")
        data = response.json()

        valid_statuses = {s.value for s in JobStatus}

        for job in data["jobs"]:
            assert (
                job["status"] in valid_statuses
            ), f"Status '{job['status']}' not in valid values: {valid_statuses}"

    async def test_jobs_endpoint_required_fields_present(
        self, client: AsyncClient
    ) -> None:
        """Verify all required fields are present in job responses"""
        response = await client.get("/v1/jobs?limit=5")
        data = response.json()

        required_fields = {"job_id", "status", "plugin", "created_at"}

        for job in data["jobs"]:
            for field in required_fields:
                assert field in job, f"Required field '{field}' missing from job"
                assert job[field] is not None, f"Required field '{field}' is null"

    async def test_jobs_endpoint_optional_fields_correct_when_present(
        self, client: AsyncClient
    ) -> None:
        """Verify optional fields have correct types when present"""
        response = await client.get("/v1/jobs?limit=10")
        data = response.json()

        for job in data["jobs"]:
            # completed_at should be datetime string or null
            if "completed_at" in job and job["completed_at"] is not None:
                assert isinstance(job["completed_at"], str)

            # result should be dict or null
            if "result" in job and job["result"] is not None:
                assert isinstance(job["result"], dict)

            # error should be string or null
            if "error" in job and job["error"] is not None:
                assert isinstance(job["error"], str)

            # progress should be number or null
            if "progress" in job and job["progress"] is not None:
                assert isinstance(job["progress"], (int, float))
                assert 0 <= job["progress"] <= 100


@pytest.mark.integration
class TestSingleJobEndpointContract:
    """Verify /v1/jobs/{id} endpoint returns documented JobResponse schema"""

    async def test_single_job_endpoint_returns_valid_job_response(
        self, client: AsyncClient
    ) -> None:
        """GET /v1/jobs/{id} returns single job matching JobStatusResponse."""
        # First get a job ID
        list_response = await client.get("/v1/jobs?limit=1")
        jobs = list_response.json()["jobs"]

        if not jobs:
            pytest.skip("No jobs available to test")

        job_id = jobs[0]["job_id"]

        # Now get single job
        response = await client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()

        # Verify it's a JobStatusResponse (GET /jobs/{id} endpoint)
        try:
            job = JobStatusResponse(**data)
            assert job.job_id == job_id
        except ValidationError as e:
            pytest.fail(f"Job response doesn't match schema: {e}")

    async def test_single_job_field_names_correct(self, client: AsyncClient) -> None:
        """Verify single job endpoint also uses correct field names"""
        list_response = await client.get("/v1/jobs?limit=1")
        jobs = list_response.json()["jobs"]

        if not jobs:
            pytest.skip("No jobs available to test")

        job_id = jobs[0]["job_id"]
        response = await client.get(f"/v1/jobs/{job_id}")
        data = response.json()

        assert "job_id" in data
        assert "id" not in data


@pytest.mark.integration
class TestPluginsEndpointContract:
    """Verify /v1/plugins endpoint returns documented PluginHealthResponse list (Phase 11)"""

    async def test_plugins_endpoint_returns_valid_plugins(
        self, client: AsyncClient
    ) -> None:
        """GET /v1/plugins should return flat list of PluginHealthResponse dicts

        TEST-CHANGE (Phase 11): Endpoint now returns flat list (not wrapped in {plugins: [...], count: ...})
        """
        response = await client.get("/v1/plugins")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list), "Phase 11: response must be a flat list"

        # Verify each item is a dict with Phase 11 health fields
        for plugin_data in data:
            assert isinstance(plugin_data, dict)
            assert "name" in plugin_data
            assert "state" in plugin_data
            assert "description" in plugin_data

    async def test_plugins_endpoint_required_fields(self, client: AsyncClient) -> None:
        """Verify all 10 required Phase 11 plugin fields are present

        TEST-CHANGE (Phase 11): Updated to check flat list with Phase 11 health schema fields
        """
        response = await client.get("/v1/plugins")
        data = response.json()

        assert isinstance(data, list), "Phase 11: response must be a flat list"

        # All 10 Phase 11 required fields
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

        for plugin in data:
            for field in required_fields:
                assert field in plugin, f"Required field '{field}' missing from plugin"

            # Validate state is one of allowed Phase 11 values
            assert plugin["state"] in [
                "LOADED",
                "INITIALIZED",
                "RUNNING",
                "FAILED",
                "UNAVAILABLE",
            ], f"Invalid state: {plugin['state']}"

    async def test_plugins_endpoint_inputs_outputs_are_lists(
        self, client: AsyncClient
    ) -> None:
        """Verify Phase 11 endpoint returns flat list (inputs/outputs in detailed schema)

        TEST-CHANGE (Phase 11): Updated for flat list health schema.
        Phase 11 list endpoint uses health response, not detailed tool schema.
        """
        response = await client.get("/v1/plugins")
        data = response.json()

        assert isinstance(data, list), "Phase 11: response must be a flat list"
        # Phase 11 health schema doesn't include inputs/outputs - those are in /plugins/{name}


@pytest.mark.integration
class TestFixtureConsistency:
    """Verify that real API responses match golden fixtures"""

    @staticmethod
    def load_fixtures() -> Dict[str, Any]:
        """Load golden fixtures from fixtures/api-responses.json"""
        fixture_path = (
            Path(__file__).parent.parent.parent.parent
            / "fixtures"
            / "api-responses.json"
        )
        with open(fixture_path) as f:
            return json.load(f)

    async def test_jobs_endpoint_matches_fixture_schema(
        self, client: AsyncClient
    ) -> None:
        """Real /v1/jobs response should have same field structure as fixture"""
        fixtures = self.load_fixtures()
        fixture_jobs = fixtures["jobs_list"]["jobs"]

        if not fixture_jobs:
            pytest.skip("No fixture jobs to compare")

        # Get real response
        response = await client.get("/v1/jobs?limit=10")
        real_jobs = response.json()["jobs"]

        if not real_jobs:
            pytest.skip("No real jobs to compare")

        # Compare field names (not values, just structure)
        fixture_fields = set(fixture_jobs[0].keys())
        real_fields = set(real_jobs[0].keys())

        assert (
            fixture_fields == real_fields
        ), f"Field mismatch. Fixture: {fixture_fields}, Real: {real_fields}"

    async def test_plugins_endpoint_matches_fixture_schema(
        self, client: AsyncClient
    ) -> None:
        """Real /v1/plugins response should match fixture structure (Phase 11)

        TEST-CHANGE (Phase 11): Updated for flat list health schema.
        Endpoint returns list directly (not wrapped in {plugins: [...], count: ...})
        
        TEST-CHANGE (Phase 14): Runs in local dev and CI if forgesyte-plugins is available
        - Fixture attempts to install OCR plugin from multiple search paths
        - CI workflows should clone forgesyte-plugins as sibling to forgesyte
        - Skips only if plugin repo completely unavailable
        """
        fixtures = self.load_fixtures()
        fixture_plugins = fixtures["plugins_list"]

        # Get real response - Phase 11 returns flat list
        response = await client.get("/v1/plugins")
        real_plugins = response.json()

        # If no fixture plugins, skip (test env doesn't have plugins defined)
        if not fixture_plugins:
            pytest.skip("No fixture plugins to compare")
        
        # If real response has no plugins, skip (forgesyte-plugins repo not available)
        if not real_plugins:
            pytest.skip("forgesyte-plugins not available in this environment")

        # Compare field names (both are flat lists)
        fixture_fields = set(fixture_plugins[0].keys())
        real_fields = set(real_plugins[0].keys())

        assert (
            fixture_fields == real_fields
        ), f"Plugin field mismatch. Fixture: {fixture_fields}, Real: {real_fields}"

    async def test_health_endpoint_matches_fixture(self, client: AsyncClient) -> None:
        """Real /v1/health response should match fixture structure"""
        fixtures = self.load_fixtures()
        fixture_health = fixtures["health"]

        response = await client.get("/v1/health")
        real_health = response.json()

        fixture_fields = set(fixture_health.keys())
        real_fields = set(real_health.keys())

        assert (
            fixture_fields == real_fields
        ), f"Health field mismatch. Fixture: {fixture_fields}, Real: {real_fields}"
