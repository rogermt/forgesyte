"""Test /v1/plugins/{id}/tools/{tool}/run endpoint for JSON compliance.

Ensures the /run endpoint always returns valid JSON for any plugin/tool,
catching numpy/tensor/bytes leaks in API responses.
"""

import json
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRunEndpointJSONCompliance:
    """Verify /v1/plugins/{id}/tools/{tool}/run returns valid JSON."""

    async def test_run_endpoint_returns_valid_json_on_error(
        self, client: AsyncClient
    ) -> None:
        """Ensure error responses are valid JSON (catches serialization leaks)."""
        payload = {"args": {"nonexistent_arg": "value"}}

        response = await client.post(
            "/v1/plugins/ocr/tools/analyze/run", json=payload
        )

        # Even 400 errors should return valid JSON
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(
                f"Error response must be valid JSON. Got: {response.text[:200]}"
            )

        assert isinstance(error_data, dict), "Error response must be JSON object"
