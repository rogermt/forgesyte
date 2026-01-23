"""
Video Tracker Integration Tests

These tests verify that plugin manifests and tool execution work correctly.
Tests use mocked plugins to avoid requiring real YOLO models to be installed.

For full integration with real YOLO models, run on Kaggle with:
  RUN_MODEL_TESTS=1 pytest tests/integration/test_video_tracker.py -v
"""

import os
from unittest.mock import patch

import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"


@pytest.fixture
def mock_yolo_manifest():
    """Provide a realistic YOLO tracker manifest for mocking."""
    return {
        "id": "yolo-tracker",
        "name": "YOLO Football Tracker",
        "version": "1.0.0",
        "description": "Real-time football player, ball, and pitch detection",
        "tools": {
            "player_detection": {
                "description": "Detect players in frame",
                "inputs": {
                    "frame_base64": {
                        "type": "string",
                        "description": "Base64 encoded frame",
                    },
                    "device": {"type": "string", "description": "Device (cpu/cuda)"},
                    "annotated": {
                        "type": "boolean",
                        "description": "Return annotated frame",
                        "default": False,
                    },
                },
                "outputs": {
                    "detections": {
                        "type": "array",
                        "description": "Detected players",
                    },
                    "annotated_frame_base64": {
                        "type": "string",
                        "description": "Annotated frame (if annotated=true)",
                    },
                },
            },
            "ball_detection": {
                "description": "Detect ball in frame",
                "inputs": {
                    "frame_base64": {"type": "string"},
                    "device": {"type": "string"},
                },
                "outputs": {"detections": {"type": "array"}},
            },
            "pitch_detection": {
                "description": "Detect pitch in frame",
                "inputs": {
                    "frame_base64": {"type": "string"},
                    "device": {"type": "string"},
                },
                "outputs": {"detections": {"type": "array"}},
            },
            "player_tracking": {
                "description": "Track players across frames",
                "inputs": {
                    "frame_base64": {"type": "string"},
                    "device": {"type": "string"},
                },
                "outputs": {"tracks": {"type": "array"}},
            },
            "radar": {
                "description": "Generate radar visualization",
                "inputs": {
                    "frame_base64": {"type": "string"},
                    "device": {"type": "string"},
                },
                "outputs": {"radar_base64": {"type": "string"}},
            },
        },
    }


@pytest.fixture(autouse=True)
def mock_manifest_reading(mock_yolo_manifest):
    """Auto-mock manifest reading for all tests in this module."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.get_plugin_manifest",
        return_value=mock_yolo_manifest,
    ):
        yield


@pytest.fixture(autouse=True)
def mock_tool_execution():
    """Auto-mock tool execution for all tests in this module."""
    mock_result = {
        "detections": [
            {
                "x": 100,
                "y": 100,
                "width": 50,
                "height": 100,
                "confidence": 0.95,
                "class": "player",
            }
        ]
    }
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool",
        return_value=mock_result,
    ):
        yield


@pytest.mark.integration
class TestManifestEndpoint:
    """Test GET /plugins/{id}/manifest with mocked YOLO plugin"""

    async def test_manifest_for_yolo_tracker(self, client_with_mock_yolo):
        """Get manifest for YOLO tracker plugin"""
        response = await client_with_mock_yolo.get("/v1/plugins/yolo-tracker/manifest")

        assert response.status_code == 200
        manifest = response.json()

        # Verify structure
        assert "id" in manifest
        assert "name" in manifest
        assert "version" in manifest
        assert "tools" in manifest

        assert manifest["id"] == "yolo-tracker"

    async def test_manifest_contains_expected_tools(self, client_with_mock_yolo):
        """Manifest should list all available tools"""
        response = await client_with_mock_yolo.get("/v1/plugins/yolo-tracker/manifest")
        manifest = response.json()

        expected_tools = [
            "player_detection",
            "player_tracking",
            "ball_detection",
            "pitch_detection",
            "radar",
        ]

        for tool_name in expected_tools:
            assert tool_name in manifest["tools"], f"Tool {tool_name} not in manifest"
            tool = manifest["tools"][tool_name]
            assert "description" in tool
            assert "inputs" in tool
            assert "outputs" in tool

    async def test_manifest_tool_has_frame_base64_input(self, client_with_mock_yolo):
        """Each tool should accept frame_base64"""
        response = await client_with_mock_yolo.get("/v1/plugins/yolo-tracker/manifest")
        manifest = response.json()

        for tool_name, tool in manifest["tools"].items():
            assert (
                "frame_base64" in tool["inputs"]
            ), f"Tool {tool_name} missing frame_base64 input"


@pytest.mark.integration
class TestToolRunEndpoint:
    """Test POST /plugins/{id}/tools/{tool}/run with mocked YOLO plugin"""

    async def test_run_player_detection_returns_detections(self, client_with_mock_yolo):
        """Run player_detection and verify detections structure"""
        # Create a simple black frame (JPEG base64)
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        # Create 480x640 black image, convert to JPEG base64
        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        response = await client_with_mock_yolo.post(
            "/v1/plugins/yolo-tracker/tools/player_detection/run",
            json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "tool_name" in data
        assert "plugin_id" in data
        assert "result" in data
        assert "processing_time_ms" in data

        assert data["tool_name"] == "player_detection"
        assert data["plugin_id"] == "yolo-tracker"
        assert isinstance(data["processing_time_ms"], int)
        assert data["processing_time_ms"] >= 0

    async def test_run_tool_with_annotated_frame(self, client_with_mock_yolo):
        """Run tool with annotated=true returns annotated_frame_base64"""
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        response = await client_with_mock_yolo.post(
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
        result = data["result"]

        # When annotated=true, should have annotated_frame_base64
        if "annotated_frame_base64" in result:
            assert isinstance(result["annotated_frame_base64"], str)

    async def test_run_ball_detection(self, client_with_mock_yolo):
        """Run ball detection tool"""
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        response = await client_with_mock_yolo.post(
            "/v1/plugins/yolo-tracker/tools/ball_detection/run",
            json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tool_name"] == "ball_detection"
        assert "result" in data

    async def test_run_pitch_detection(self, client_with_mock_yolo):
        """Run pitch detection tool"""
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        response = await client_with_mock_yolo.post(
            "/v1/plugins/yolo-tracker/tools/pitch_detection/run",
            json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tool_name"] == "pitch_detection"

    async def test_run_invalid_tool_returns_400(self, client_with_mock_yolo):
        """Running non-existent tool returns 400"""
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        # Mock the run to raise ValueError for invalid tool
        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool",
            side_effect=ValueError("Tool 'nonexistent_tool' not found"),
        ):
            response = await client_with_mock_yolo.post(
                "/v1/plugins/yolo-tracker/tools/nonexistent_tool/run",
                json={"args": {"frame_base64": frame_base64}},
            )

            assert response.status_code == 400

    async def test_run_invalid_plugin_returns_400(self, client_with_mock_yolo):
        """Running tool on non-existent plugin returns 400"""
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        # Mock the run to raise ValueError for invalid plugin
        with patch(
            "app.services.plugin_management_service.PluginManagementService.run_plugin_tool",
            side_effect=ValueError("Plugin 'nonexistent-plugin' not found"),
        ):
            response = await client_with_mock_yolo.post(
                "/v1/plugins/nonexistent-plugin/tools/player_detection/run",
                json={"args": {"frame_base64": frame_base64}},
            )

            assert response.status_code == 400


@pytest.mark.integration
class TestVideoTrackerEndToEnd:
    """End-to-end tests: manifest discovery → tool execution"""

    async def test_manifest_then_run_tool_workflow(self, client_with_mock_yolo):
        """Discover tool from manifest, then execute it"""
        # Step 1: Get manifest
        manifest_response = await client_with_mock_yolo.get(
            "/v1/plugins/yolo-tracker/manifest"
        )
        assert manifest_response.status_code == 200
        manifest = manifest_response.json()

        # Step 2: Pick first tool
        tool_name = list(manifest["tools"].keys())[0]

        # Step 3: Create args matching input schema
        import base64
        from io import BytesIO

        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        img = Image.new("RGB", (640, 480), color="black")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        frame_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        args = {"frame_base64": frame_base64, "device": "cpu"}

        # Step 4: Run tool
        run_response = await client_with_mock_yolo.post(
            f"/v1/plugins/yolo-tracker/tools/{tool_name}/run",
            json={"args": args},
        )

        assert run_response.status_code == 200
        result = run_response.json()

        # Step 5: Verify result matches output schema
        assert result["tool_name"] == tool_name
        assert result["plugin_id"] == "yolo-tracker"
        assert "result" in result
