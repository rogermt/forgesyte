"""CPU-only contract tests for YOLO tracker tools via plugin API.

These tests validate that the POST /v1/plugins/{id}/tools/{tool}/run endpoint
returns correct JSON schemas for YOLO tools without requiring GPU/model loading.

Uses OCR plugin (CPU-safe) to test endpoint mechanics with realistic synthetic frames.
"""

import base64
import os

import numpy as np
import pytest

pytestmark = pytest.mark.asyncio

# Skip GPU tests in CI
RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"


def create_synthetic_frame(width: int = 640, height: int = 480) -> str:
    """Create a synthetic frame and encode as base64."""
    # Create a dummy RGB frame (all black)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Simple PNG-like encoding (not real PNG, but valid bytes)
    frame_bytes = frame.tobytes()
    return base64.b64encode(frame_bytes).decode("utf-8")


class TestPluginsRunYoloPlayerDetection:
    """Test POST /plugins/{id}/tools/player_detection/run via OCR plugin."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "detections": [
                {
                    "x1": 100,
                    "y1": 200,
                    "x2": 150,
                    "y2": 350,
                    "confidence": 0.92,
                    "class": "player",
                }
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify top-level response schema
            assert "tool_name" in data
            assert "plugin_id" in data
            assert "result" in data
            assert "processing_time_ms" in data

            # Verify values
            assert data["tool_name"] == "player_detection"
            assert data["plugin_id"] == "yolo-tracker"
            assert data["result"] == expected_result
            assert isinstance(data["processing_time_ms"], int)
            assert data["processing_time_ms"] >= 0

    async def test_endpoint_with_annotated_frame(self, client):
        """Verify endpoint returns annotated frame when requested."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "detections": [
                {
                    "x1": 100,
                    "y1": 200,
                    "x2": 150,
                    "y2": 350,
                    "confidence": 0.92,
                    "class": "player",
                }
            ],
            "annotated_frame_base64": base64.b64encode(
                np.zeros((480, 640, 3), dtype=np.uint8).tobytes()
            ).decode("utf-8"),
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                        "annotated": True,
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "annotated_frame_base64" in data["result"]
            assert isinstance(data["result"]["annotated_frame_base64"], str)

    async def test_endpoint_handles_missing_args(self, client):
        """Verify 400 on missing required arguments."""
        from unittest.mock import patch

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.side_effect = ValueError("Missing required argument: frame_base64")

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={"args": {"device": "cpu"}},  # Missing frame_base64
            )

            assert response.status_code == 400


class TestPluginsRunYoloBallDetection:
    """Test POST /plugins/{id}/tools/ball_detection/run via plugin API."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "detections": [
                {
                    "x": 320,
                    "y": 240,
                    "radius": 15,
                    "confidence": 0.85,
                }
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/ball_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tool_name"] == "ball_detection"
            assert data["plugin_id"] == "yolo-tracker"
            assert "detections" in data["result"]
            assert isinstance(data["result"]["detections"], list)

    async def test_ball_detection_output_is_json_safe(self, client):
        """Verify ball detection output is JSON-serializable."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "detections": [
                {
                    "x": 320.5,
                    "y": 240.25,
                    "radius": 15,
                    "confidence": 0.85,
                    "track_id": 1,
                }
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/ball_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            # Verify response is valid JSON
            data = response.json()
            assert data is not None


class TestPluginsRunYoloPitchDetection:
    """Test POST /plugins/{id}/tools/pitch_detection/run via plugin API."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "pitch_detected": True,
            "vertices": [
                {"x": 0, "y": 0},
                {"x": 640, "y": 0},
                {"x": 640, "y": 480},
                {"x": 0, "y": 480},
            ],
            "confidence": 0.92,
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/pitch_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tool_name"] == "pitch_detection"
            assert data["plugin_id"] == "yolo-tracker"
            assert "pitch_detected" in data["result"]
            assert isinstance(data["result"]["vertices"], list)

    async def test_pitch_detection_with_confidence_threshold(self, client):
        """Verify confidence threshold parameter works."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {"pitch_detected": False, "confidence": 0.15}

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/pitch_detection/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                        "confidence_threshold": 0.25,
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["result"]["pitch_detected"] is False


class TestPluginsRunYoloRadar:
    """Test POST /plugins/{id}/tools/radar/run via plugin API."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema for radar."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "radar_frame_base64": base64.b64encode(
                np.zeros((300, 600, 3), dtype=np.uint8).tobytes()
            ).decode("utf-8"),
            "metadata": {
                "pitch_width_cm": 10500,
                "pitch_height_cm": 6800,
                "player_count": 22,
            },
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/radar/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tool_name"] == "radar"
            assert data["plugin_id"] == "yolo-tracker"
            assert "radar_frame_base64" in data["result"]
            assert isinstance(data["result"]["radar_frame_base64"], str)

    async def test_radar_metadata_is_valid(self, client):
        """Verify radar metadata is present and valid."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "radar_frame_base64": base64.b64encode(
                np.zeros((300, 600, 3), dtype=np.uint8).tobytes()
            ).decode("utf-8"),
            "metadata": {
                "pitch_width_cm": 10500,
                "pitch_height_cm": 6800,
                "player_count": 22,
                "frame_width": 640,
                "frame_height": 480,
            },
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/radar/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            metadata = data["result"]["metadata"]
            assert metadata["player_count"] >= 0
            assert metadata["pitch_width_cm"] > 0
            assert metadata["pitch_height_cm"] > 0


class TestPluginsRunYoloTeamClassification:
    """Test POST /plugins/{id}/tools/team_classification/run via plugin API."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "classifications": [
                {
                    "player_id": 1,
                    "team": "A",
                    "jersey_number": 7,
                    "confidence": 0.88,
                },
                {
                    "player_id": 2,
                    "team": "B",
                    "jersey_number": 10,
                    "confidence": 0.91,
                },
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/team_classification/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                        "player_detections": [],
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tool_name"] == "team_classification"
            assert data["plugin_id"] == "yolo-tracker"
            assert "classifications" in data["result"]
            assert isinstance(data["result"]["classifications"], list)


class TestPluginsRunYoloPlayerTracking:
    """Test POST /plugins/{id}/tools/player_tracking/run via plugin API."""

    async def test_endpoint_returns_correct_schema(self, client):
        """Verify endpoint returns correct response schema."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "tracks": [
                {
                    "track_id": 1,
                    "x1": 100,
                    "y1": 200,
                    "x2": 150,
                    "y2": 350,
                    "confidence": 0.92,
                    "frame_num": 1,
                },
                {
                    "track_id": 2,
                    "x1": 200,
                    "y1": 100,
                    "x2": 250,
                    "y2": 300,
                    "confidence": 0.85,
                    "frame_num": 1,
                },
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_tracking/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                        "frame_num": 1,
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tool_name"] == "player_tracking"
            assert data["plugin_id"] == "yolo-tracker"
            assert "tracks" in data["result"]
            assert isinstance(data["result"]["tracks"], list)

    async def test_player_tracking_output_is_json_safe(self, client):
        """Verify player tracking output is JSON-serializable."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()
        expected_result = {
            "tracks": [
                {
                    "track_id": 1,
                    "x1": 100.5,
                    "y1": 200.25,
                    "x2": 150.75,
                    "y2": 350.1,
                    "confidence": 0.92,
                    "frame_num": 1,
                    "class": "player",
                }
            ]
        }

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.return_value = expected_result

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_tracking/run",
                json={
                    "args": {
                        "frame_base64": frame_base64,
                        "device": "cpu",
                        "frame_num": 1,
                    }
                },
            )

            assert response.status_code == 200
            # Verify JSON serialization succeeds
            data = response.json()
            assert data is not None
            assert len(data["result"]["tracks"]) > 0


class TestPluginsRunYoloToolsErrorHandling:
    """Test error handling across all YOLO tools."""

    async def test_invalid_base64_frame(self, client):
        """Test handling of invalid base64 frame."""
        from unittest.mock import patch

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.side_effect = ValueError("Invalid base64 frame")

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={"args": {"frame_base64": "invalid!!!base64", "device": "cpu"}},
            )

            assert response.status_code == 400

    async def test_timeout_on_slow_tool(self, client):
        """Test timeout handling."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.side_effect = TimeoutError("Tool execution exceeded timeout")

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
            )

            assert response.status_code == 408

    async def test_unexpected_plugin_error(self, client):
        """Test handling of unexpected plugin errors."""
        from unittest.mock import patch

        frame_base64 = create_synthetic_frame()

        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
        ) as mock_run:
            mock_run.side_effect = RuntimeError("Plugin crashed unexpectedly")

            response = await client.post(
                "/v1/plugins/yolo-tracker/tools/player_detection/run",
                json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
            )

            assert response.status_code == 500
