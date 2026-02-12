"""
Pipeline E2E Test - Cross-plugin DAG execution via REST

This test verifies complete E2E pipeline execution via REST API
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.pipeline_registry_service import PipelineRegistryService
from app.services.dag_pipeline_service import DagPipelineService
from tests.pipelines.test_dag_pipeline_service import MockPluginManager, MockPlugin


@pytest.fixture
def app_with_pipeline(tmp_path: Path):
    """Create app with test pipeline loaded."""
    # Create a simple 2-node cross-plugin pipeline
    pipeline_data = {
        "id": "player_tracking_v1",
        "name": "Player tracking v1",
        "nodes": [
            {"id": "n1", "plugin_id": "yolo", "tool_id": "detect_players"},
            {"id": "n2", "plugin_id": "reid", "tool_id": "track_ids"},
        ],
        "edges": [{"from_node": "n1", "to_node": "n2"}],
        "entry_nodes": ["n1"],
        "output_nodes": ["n2"],
    }
    (tmp_path / "player_tracking_v1.json").write_text(json.dumps(pipeline_data))

    # Create app and initialize pipeline services
    app = create_app()
    registry = PipelineRegistryService(str(tmp_path))
    plugin_manager = MockPluginManager()
    plugin_manager.add_plugin(MockPlugin("yolo", {"detections": ["player1", "player2"]}))
    plugin_manager.add_plugin(MockPlugin("reid", {"tracks": ["track1", "track2"]}))

    app.state.pipeline_registry = registry
    app.state.plugin_manager_for_pipelines = plugin_manager

    return app


def test_pipeline_e2e_runs_via_rest(app_with_pipeline):
    """Test that a cross-plugin DAG pipeline runs end-to-end via REST."""
    client = TestClient(app_with_pipeline)

    # When: we call the new DAG run endpoint
    resp = client.post(
        "/v1/pipelines/player_tracking_v1/run",
        json={"payload": {"frame_id": 1, "image_bytes": "base64_image_data"}},
    )

    # Then: it should succeed and return a result
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "success"
    assert "output" in data

    # And the result should contain outputs from both nodes
    output = data["output"]
    assert "detections" in output
    assert "tracks" in output
    assert output["detections"] == ["player1", "player2"]
    assert output["tracks"] == ["track1", "track2"]
    # Note: initial payload keys (frame_id, image_bytes) are not included in final output
    # Only node outputs are returned, which is the correct behavior for pipeline results