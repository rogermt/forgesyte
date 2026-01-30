"""Test /v1/plugins/yolo-tracker/tools/{tool}/run endpoint for JSON compliance.

Ensures YOLO player detection returns JSON-serializable output,
catching numpy/tensor/bytes leaks in API responses.
"""

import json
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRunYoloImageJSONCompliance:
    """Verify /v1/plugins/yolo-tracker/tools/*/run returns valid JSON."""

    async def test_yolo_player_detection_returns_valid_json_on_error(
        self, client: AsyncClient
    ) -> None:
        """Ensure YOLO player detection error responses are valid JSON."""
        payload = {"args": {"invalid_arg": "value"}}

        response = await client.post(
            "/v1/plugins/yolo-tracker/tools/player_detection/run", json=payload
        )

        # Even 400 errors should return valid JSON (catches numpy/tensor leaks)
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(
                f"YOLO error response must be valid JSON. Got: {response.text[:200]}"
            )

        assert isinstance(error_data, dict), "YOLO error response must be JSON object"

    async def test_yolo_ball_detection_returns_valid_json_on_error(
        self, client: AsyncClient
    ) -> None:
        """Ensure YOLO ball detection error responses are valid JSON."""
        payload = {"args": {"missing_frame": True}}

        response = await client.post(
            "/v1/plugins/yolo-tracker/tools/ball_detection/run", json=payload
        )

        # Even 400 errors should return valid JSON
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(
                f"YOLO ball detection error must be valid JSON. Got: {response.text[:200]}"
            )

        assert isinstance(error_data, dict), "YOLO error response must be JSON object"

    async def test_yolo_pitch_detection_returns_valid_json_on_error(
        self, client: AsyncClient
    ) -> None:
        """Ensure YOLO pitch detection error responses are valid JSON."""
        payload = {"args": {}}

        response = await client.post(
            "/v1/plugins/yolo-tracker/tools/pitch_detection/run", json=payload
        )

        # Even 400 errors should return valid JSON
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(
                f"YOLO pitch detection error must be valid JSON. Got: {response.text[:200]}"
            )

        assert isinstance(error_data, dict), "YOLO error response must be JSON object"
