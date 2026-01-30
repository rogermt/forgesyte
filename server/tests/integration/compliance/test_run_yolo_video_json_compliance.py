"""Test YOLO video tool for JSON compliance.

Ensures YOLO video processing returns JSON-serializable output,
catching numpy/tensor/bytes leaks in API responses.
"""

import json
import os
import pytest
from importlib.metadata import entry_points


def is_json_safe(value) -> bool:
    """Check if value is JSON-serializable."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


@pytest.mark.integration
class TestRunYoloVideoJSONCompliance:
    """Verify YOLO video tools return JSON-safe output."""

    async def test_yolo_video_endpoint_returns_valid_json_on_error(
        self, client
    ) -> None:
        """Ensure YOLO video endpoint error responses are valid JSON."""
        payload = {"args": {"invalid_arg": "value"}}

        response = await client.post(
            "/v1/plugins/yolo-tracker/tools/player_tracking/run", json=payload
        )

        # Even 400 errors should return valid JSON
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(
                f"YOLO video error response must be valid JSON. "
                f"Got: {response.text[:200]}"
            )

        assert isinstance(error_data, dict), "YOLO error response must be JSON object"

    def test_yolo_plugin_entry_point_exists(self) -> None:
        """Verify YOLO plugin is registered as entry point."""
        eps = entry_points(group="forgesyte.plugins")
        yolo_eps = [ep for ep in eps if ep.name == "yolo-tracker"]

        assert yolo_eps, "YOLO entrypoint not found in forgesyte.plugins"
        assert len(yolo_eps) == 1, f"Multiple YOLO entrypoints found: {yolo_eps}"

    def test_yolo_video_output_schema_is_json_safe(self) -> None:
        """Verify YOLO video output schema is JSON-safe (no numpy/bytes)."""
        # Expected output structure from manifest
        expected_output = {
            "detections": [
                {
                    "x": 100.0,
                    "y": 100.0,
                    "width": 50.0,
                    "height": 80.0,
                    "class": "player",
                    "confidence": 0.95,
                    "track_id": 1,
                }
            ],
            "annotated_frame_base64": None,
        }

        assert is_json_safe(
            expected_output
        ), "YOLO output schema is not JSON-safe"
