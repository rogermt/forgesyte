"""Phase 14 Player Tracking Pipeline Test.

This is the "first failing test" for Phase 14 DAG execution.
It locks in the whole contract: registry + plugin manager + merge + type flow.

The test will:
- fail if the registry lookup is wrong
- fail if plugin resolution is wrong
- fail if payload merging is wrong
- fail if type flow is broken
- pass only when the Phase 14 DAG engine is wired correctly end-to-end.
"""

from typing import Any, Dict

import pytest

from app.pipeline_models.pipeline_graph_models import (
    Pipeline,
    PipelineEdge,
    PipelineNode,
)
from app.services.dag_pipeline_service import DagPipelineService


class DummyPlugin:
    """Dummy plugin for testing."""

    def __init__(self, behavior):
        self.behavior = behavior

    def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.behavior(tool_id, payload)


class DummyPluginManager:
    """Dummy plugin manager for testing."""

    def __init__(self):
        self._plugins = {}

    def register(self, plugin_id: str, plugin: DummyPlugin):
        self._plugins[plugin_id] = plugin

    def get_plugin(self, plugin_id: str) -> DummyPlugin:
        return self._plugins[plugin_id]


class DummyRegistry:
    """Dummy pipeline registry for testing."""

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        assert pipeline_id == self._pipeline.id
        return self._pipeline


def make_player_tracking_pipeline() -> Pipeline:
    """Create a test player tracking pipeline.

    Returns:
        Pipeline: Player tracking pipeline definition
    """
    return Pipeline(
        id="player_tracking_v1",
        name="Player tracking pipeline",
        nodes=[
            PipelineNode(id="detect", plugin_id="yolo", tool_id="detect_players"),
            PipelineNode(id="track", plugin_id="reid", tool_id="track_ids"),
            PipelineNode(id="render", plugin_id="viz", tool_id="render_overlay"),
        ],
        edges=[
            PipelineEdge(from_node="detect", to_node="track"),
            PipelineEdge(from_node="track", to_node="render"),
        ],
        entry_nodes=["detect"],
        output_nodes=["render"],
    )


def test_phase14_player_tracking_pipeline_end_to_end():
    """Test end-to-end execution of player tracking pipeline.

    This test validates:
    - Registry lookup
    - Plugin resolution
    - Payload merging
    - Type flow
    - DAG execution
    """
    pipeline = make_player_tracking_pipeline()
    registry = DummyRegistry(pipeline)
    pm = DummyPluginManager()

    def yolo_behavior(tool_id, payload):
        assert tool_id == "detect_players"
        assert "frame" in payload
        return {"detections": [{"id": 1}]}

    def reid_behavior(tool_id, payload):
        assert tool_id == "track_ids"
        assert "detections" in payload
        return {"tracks": [{"id": 1, "track_id": "p1"}]}

    def viz_behavior(tool_id, payload):
        assert tool_id == "render_overlay"
        assert "tracks" in payload
        # simulate overlay frame
        return {"overlay_frame": b"fake-bytes"}

    pm.register("yolo", DummyPlugin(yolo_behavior))
    pm.register("reid", DummyPlugin(reid_behavior))
    pm.register("viz", DummyPlugin(viz_behavior))

    dag = DagPipelineService(registry, pm)

    initial_payload = {"frame": b"raw-frame"}
    result = dag.run_pipeline("player_tracking_v1", initial_payload)

    # Final result should include overlay_frame from last node
    assert "overlay_frame" in result
    # And original frame should still be present (depending on your merge rules)
    assert "frame" in result