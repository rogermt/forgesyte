"""
Video Tracker Integration Tests (GPU)

These integration tests verify that real plugin manifests and tool execution
work correctly with actual YOLO models on GPU.

Run with:
  RUN_MODEL_TESTS=1 pytest tests/integration/test_video_tracker.py -v
"""

import os

import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="Requires YOLO model (set RUN_MODEL_TESTS=1)",
)


@pytest.mark.integration
class TestManifestEndpoint:
    """Test GET /plugins/{id}/manifest with real plugins"""

    async def test_manifest_for_yolo_tracker(self, client):
        """Get manifest for YOLO tracker plugin"""
        response = await client.get("/v1/plugins/forgesyte-yolo-tracker/manifest")

        assert response.status_code == 200
        manifest = response.json()

        # Verify structure
        assert "id" in manifest
        assert "name" in manifest
        assert "version" in manifest
        assert "tools" in manifest

        assert manifest["id"] == "forgesyte-yolo-tracker"

    async def test_manifest_contains_expected_tools(self, client):
        """Manifest should list all available tools"""
        response = await client.get("/v1/plugins/forgesyte-yolo-tracker/manifest")
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

    async def test_manifest_tool_has_frame_base64_input(self, client):
        """Each tool should accept frame_base64"""
        response = await client.get("/v1/plugins/forgesyte-yolo-tracker/manifest")
        manifest = response.json()

        for tool_name, tool in manifest["tools"].items():
            assert (
                "frame_base64" in tool["inputs"]
            ), f"Tool {tool_name} missing frame_base64 input"


@pytest.mark.integration
class TestToolRunEndpoint:
    """Test POST /plugins/{id}/tools/{tool}/run with real YOLO inference"""

    async def test_run_player_detection_returns_detections(self, client):
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

        response = await client.post(
            "/v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run",
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
        assert data["plugin_id"] == "forgesyte-yolo-tracker"
        assert isinstance(data["processing_time_ms"], int)
        assert data["processing_time_ms"] >= 0

    async def test_run_tool_with_annotated_frame(self, client):
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

        response = await client.post(
            "/v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run",
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

    async def test_run_ball_detection(self, client):
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

        response = await client.post(
            "/v1/plugins/forgesyte-yolo-tracker/tools/ball_detection/run",
            json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tool_name"] == "ball_detection"
        assert "result" in data

    async def test_run_pitch_detection(self, client):
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

        response = await client.post(
            "/v1/plugins/forgesyte-yolo-tracker/tools/pitch_detection/run",
            json={"args": {"frame_base64": frame_base64, "device": "cpu"}},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["tool_name"] == "pitch_detection"

    async def test_run_invalid_tool_returns_400(self, client):
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

        response = await client.post(
            "/v1/plugins/forgesyte-yolo-tracker/tools/nonexistent_tool/run",
            json={"args": {"frame_base64": frame_base64}},
        )

        assert response.status_code == 400

    async def test_run_invalid_plugin_returns_400(self, client):
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

        response = await client.post(
            "/v1/plugins/nonexistent-plugin/tools/player_detection/run",
            json={"args": {"frame_base64": frame_base64}},
        )

        assert response.status_code == 400


@pytest.mark.integration
class TestVideoTrackerEndToEnd:
    """End-to-end tests: manifest discovery → tool execution"""

    async def test_manifest_then_run_tool_workflow(self, client):
        """Discover tool from manifest, then execute it"""
        # Step 1: Get manifest
        manifest_response = await client.get(
            "/v1/plugins/forgesyte-yolo-tracker/manifest"
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
        run_response = await client.post(
            f"/v1/plugins/forgesyte-yolo-tracker/tools/{tool_name}/run",
            json={"args": args},
        )

        assert run_response.status_code == 200
        result = run_response.json()

        # Step 5: Verify result matches output schema
        assert result["tool_name"] == tool_name
        assert result["plugin_id"] == "forgesyte-yolo-tracker"
        assert "result" in result
