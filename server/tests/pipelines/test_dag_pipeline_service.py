"""
Tests for pipeline DAG Pipeline Service.
TDD: Write failing tests first, then implement service.
"""

import logging
from typing import Any, Dict

import pytest

# Import models for mocking even if service doesn't exist
from app.pipeline_models.pipeline_graph_models import (
    Pipeline,
    PipelineEdge,
    PipelineNode,
    PipelineValidationResult,
)

try:
    from app.services.dag_pipeline_service import DagPipelineService

    SERVICE_EXISTS = True
except ImportError:
    SERVICE_EXISTS = False


# Mock plugin and plugin manager for testing
class MockPlugin:
    """Mock plugin for testing."""

    def __init__(self, plugin_id: str, outputs: Dict[str, Any] | None = None):
        self.id = plugin_id
        self._outputs = outputs or {}

    def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool and return mock output."""
        return {
            **self._outputs,
            "plugin_id": self.id,
            "tool_id": tool_id,
        }


class MockPluginManager:
    """Mock plugin manager for testing."""

    def __init__(self):
        self._plugins = {}

    def add_plugin(self, plugin: MockPlugin):
        """Add a plugin to the manager."""
        self._plugins[plugin.id] = plugin

    def get_plugin(self, plugin_id: str) -> MockPlugin:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)


class MockRegistry:
    """Mock pipeline registry for testing."""

    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        """Get a pipeline by ID."""
        return self._pipeline


@pytest.mark.skipif(not SERVICE_EXISTS, reason="DagPipelineService not implemented yet")
class TestDagPipelineService:
    """Test DagPipelineService functionality."""

    def test_execute_linear_pipeline(self, caplog):
        """Test executing a simple linear pipeline."""
        # Create linear pipeline: n1 -> n2
        pipeline = Pipeline(
            id="linear",
            name="Linear Pipeline",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )

        # Setup mock plugins
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"output_a": "value_a"}))
        plugin_manager.add_plugin(MockPlugin("plugin_b", {"output_b": "value_b"}))

        registry = MockRegistry(pipeline)
        dag_service = DagPipelineService(registry, plugin_manager)

        # Execute pipeline
        result = dag_service.run_pipeline("linear", {"input": "test"})

        # Verify result contains outputs from both nodes
        assert "output_a" in result
        assert "output_b" in result
        assert result["output_a"] == "value_a"
        assert result["output_b"] == "value_b"

    def test_execute_with_multiple_predecessors(self, caplog):
        """Test executing a node with multiple predecessors (merge)."""
        # Create pipeline: n1 -> n3, n2 -> n3
        pipeline = Pipeline(
            id="merge",
            name="Merge Pipeline",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
                PipelineNode(id="n3", plugin_id="plugin_c", tool_id="tool3"),
            ],
            edges=[
                PipelineEdge(from_node="n1", to_node="n3"),
                PipelineEdge(from_node="n2", to_node="n3"),
            ],
            entry_nodes=["n1", "n2"],
            output_nodes=["n3"],
        )

        # Setup mock plugins
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"key1": "value1"}))
        plugin_manager.add_plugin(MockPlugin("plugin_b", {"key2": "value2"}))
        plugin_manager.add_plugin(MockPlugin("plugin_c", {"final": "result"}))

        registry = MockRegistry(pipeline)
        dag_service = DagPipelineService(registry, plugin_manager)

        # Execute pipeline
        result = dag_service.run_pipeline("merge", {"input": "test"})

        # Verify result contains merged outputs
        assert "key1" in result
        assert "key2" in result
        assert "final" in result

    def test_execute_logs_observability_events(self, caplog):
        """Test that execution logs observability events."""
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1")],
            edges=[],
            entry_nodes=["n1"],
            output_nodes=["n1"],
        )

        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"output": "value"}))

        registry = MockRegistry(pipeline)
        dag_service = DagPipelineService(registry, plugin_manager)

        caplog.set_level(logging.INFO, logger="pipelines.dag")

        # Execute pipeline
        dag_service.run_pipeline("test", {"input": "test"})

        # Verify observability events were logged
        event_types = [getattr(record, "event_type", None) for record in caplog.records]
        assert "pipeline_started" in event_types
        assert "pipeline_node_started" in event_types
        assert "pipeline_node_completed" in event_types
        assert "pipeline_completed" in event_types

    def test_execute_handles_node_failure(self, caplog):
        """Test that execution handles node failure gracefully."""

        class FailingPlugin(MockPlugin):
            def run_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                raise RuntimeError("Tool execution failed")

        pipeline = Pipeline(
            id="failing",
            name="Failing Pipeline",
            nodes=[PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1")],
            edges=[],
            entry_nodes=["n1"],
            output_nodes=["n1"],
        )

        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(FailingPlugin("plugin_a"))

        registry = MockRegistry(pipeline)
        dag_service = DagPipelineService(registry, plugin_manager)

        caplog.set_level(logging.INFO, logger="pipelines.dag")

        # Execute pipeline should raise exception
        with pytest.raises(RuntimeError, match="Tool execution failed"):
            dag_service.run_pipeline("failing", {"input": "test"})

        # Verify failure events were logged
        event_types = [getattr(record, "event_type", None) for record in caplog.records]
        assert "pipeline_started" in event_types
        assert "pipeline_node_failed" in event_types
        assert "pipeline_failed" in event_types

    def test_validate_returns_result(self):
        """Test that validate() returns PipelineValidationResult."""
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1")],
            edges=[],
            entry_nodes=["n1"],
            output_nodes=["n1"],
        )

        plugin_manager = MockPluginManager()
        registry = MockRegistry(pipeline)
        dag_service = DagPipelineService(registry, plugin_manager)

        result = dag_service.validate(pipeline)

        assert isinstance(result, PipelineValidationResult)
        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
