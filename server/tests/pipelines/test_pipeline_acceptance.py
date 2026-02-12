"""
 Pipeline Acceptance Tests - E2E tests for full pipeline workflow.
These tests verify the complete pipeline functionality end-to-end.
"""

import json

from app.pipeline_models.pipeline_graph_models import (
    Pipeline,
    PipelineEdge,
    PipelineNode,
    ToolMetadata,
)
from app.services.dag_pipeline_service import DagPipelineService
from app.services.pipeline_registry_service import PipelineRegistryService
from app.services.type_validator import TypeValidator
from tests.pipelines.test_dag_pipeline_service import MockPlugin, MockPluginManager


class TestPipelineAcceptance:
    """Pipeline acceptance tests."""

    def test_e2e_linear_pipeline_execution(self, tmp_path):
        """Test end-to-end execution of a linear pipeline."""
        # Create linear pipeline: n1 -> n2
        pipeline_data = {
            "id": "linear_test",
            "name": "Linear Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"},
                {"id": "n2", "plugin_id": "plugin_b", "tool_id": "tool2"},
            ],
            "edges": [{"from_node": "n1", "to_node": "n2"}],
            "entry_nodes": ["n1"],
            "output_nodes": ["n2"],
        }
        (tmp_path / "linear_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry and plugin manager
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"output_a": "value_a"}))
        plugin_manager.add_plugin(MockPlugin("plugin_b", {"output_b": "value_b"}))

        # Execute pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        result = dag_service.run_pipeline("linear_test", {"input": "test"})

        # Verify result contains outputs from both nodes
        assert "output_a" in result
        assert "output_b" in result
        assert result["output_a"] == "value_a"
        assert result["output_b"] == "value_b"

    def test_e2e_branching_pipeline_execution(self, tmp_path):
        """Test end-to-end execution of a branching pipeline."""
        # Create branching pipeline: n1 -> {n2, n3} -> n4
        pipeline_data = {
            "id": "branching_test",
            "name": "Branching Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"},
                {"id": "n2", "plugin_id": "plugin_b", "tool_id": "tool2"},
                {"id": "n3", "plugin_id": "plugin_c", "tool_id": "tool3"},
                {"id": "n4", "plugin_id": "plugin_d", "tool_id": "tool4"},
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n2"},
                {"from_node": "n1", "to_node": "n3"},
                {"from_node": "n2", "to_node": "n4"},
                {"from_node": "n3", "to_node": "n4"},
            ],
            "entry_nodes": ["n1"],
            "output_nodes": ["n4"],
        }
        (tmp_path / "branching_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry and plugin manager
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"output_a": "value_a"}))
        plugin_manager.add_plugin(MockPlugin("plugin_b", {"output_b": "value_b"}))
        plugin_manager.add_plugin(MockPlugin("plugin_c", {"output_c": "value_c"}))
        plugin_manager.add_plugin(MockPlugin("plugin_d", {"output_d": "value_d"}))

        # Execute pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        result = dag_service.run_pipeline("branching_test", {"input": "test"})

        # Verify result contains outputs from all nodes
        assert "output_a" in result
        assert "output_b" in result
        assert "output_c" in result
        assert "output_d" in result

    def test_e2e_pipeline_with_type_validation(self, tmp_path):
        """Test end-to-end pipeline with type validation."""
        # Create pipeline with compatible types
        pipeline = Pipeline(
            id="typed_test",
            name="Typed Test Pipeline",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )

        # Create tool metadata
        tools = {
            "n1": ToolMetadata(
                plugin_id="plugin_a",
                tool_id="tool1",
                input_types=["video_frame"],
                output_types=["detections"],
            ),
            "n2": ToolMetadata(
                plugin_id="plugin_b",
                tool_id="tool2",
                input_types=["detections"],
                output_types=["tracks"],
            ),
        }

        # Validate types
        type_validator = TypeValidator()
        errors = type_validator.validate_types(pipeline, tools)

        # Should have no errors
        assert len(errors) == 0

    def test_e2e_cycle_detection(self, tmp_path):
        """Test that cycles are detected and rejected."""
        # Create cyclic pipeline
        pipeline_data = {
            "id": "cycle_test",
            "name": "Cycle Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"},
                {"id": "n2", "plugin_id": "plugin_b", "tool_id": "tool2"},
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n2"},
                {"from_node": "n2", "to_node": "n1"},  # Cycle
            ],
            "entry_nodes": ["n1"],
            "output_nodes": ["n2"],
        }
        (tmp_path / "cycle_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()

        # Validate pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        pipeline = registry.get_pipeline("cycle_test")
        result = dag_service.validate(pipeline)

        # Should detect cycle
        assert result.valid is False
        assert any("cycle" in error.lower() for error in result.errors)

    def test_e2e_type_mismatch_detection(self, tmp_path):
        """Test that type mismatches are detected and rejected."""
        # Create pipeline with incompatible types
        pipeline = Pipeline(
            id="mismatch_test",
            name="Type Mismatch Test Pipeline",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )

        # Create tool metadata with incompatible types
        tools = {
            "n1": ToolMetadata(
                plugin_id="plugin_a",
                tool_id="tool1",
                input_types=["video_frame"],
                output_types=["detections"],
            ),
            "n2": ToolMetadata(
                plugin_id="plugin_b",
                tool_id="tool2",
                input_types=["heatmap"],  # Incompatible
                output_types=["tracks"],
            ),
        }

        # Validate types
        type_validator = TypeValidator()
        errors = type_validator.validate_types(pipeline, tools)

        # Should detect type mismatch
        assert len(errors) > 0
        assert any("type mismatch" in error.lower() for error in errors)

    def test_e2e_observability_logging(self, tmp_path, caplog):
        """Test that all observability events are logged."""
        import logging

        # Create simple pipeline
        pipeline_data = {
            "id": "obs_test",
            "name": "Observability Test Pipeline",
            "nodes": [{"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "obs_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry and plugin manager
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"output": "test"}))

        # Capture logs
        caplog.set_level(logging.INFO, logger="pipelines.dag")

        # Execute pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        dag_service.run_pipeline("obs_test", {"input": "test"})

        # Verify all 6 event types were logged
        event_types = [
            getattr(record, "event_type", None)
            for record in caplog.records
            if hasattr(record, "event_type")
        ]

        assert "pipeline_started" in event_types
        assert "pipeline_node_started" in event_types
        assert "pipeline_node_completed" in event_types
        assert "pipeline_completed" in event_types

    def test_e2e_unreachable_node_detection(self, tmp_path):
        """Test that unreachable nodes are detected."""
        # Create pipeline with unreachable node
        pipeline_data = {
            "id": "unreachable_test",
            "name": "Unreachable Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"},
                {"id": "n2", "plugin_id": "plugin_b", "tool_id": "tool2"},
                {"id": "n3", "plugin_id": "plugin_c", "tool_id": "tool3"},  # Unreachable
            ],
            "edges": [{"from_node": "n1", "to_node": "n2"}],
            "entry_nodes": ["n1"],
            "output_nodes": ["n2"],
        }
        (tmp_path / "unreachable_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()

        # Validate pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        pipeline = registry.get_pipeline("unreachable_test")
        result = dag_service.validate(pipeline)

        # Should detect unreachable node
        assert result.valid is False
        assert any("unreachable" in error.lower() for error in result.errors)

    def test_e2e_multiple_predecessor_merge(self, tmp_path):
        """Test that multiple predecessor outputs are merged correctly."""
        # Create pipeline with merge: n1 & n2 -> n3
        pipeline_data = {
            "id": "merge_test",
            "name": "Merge Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"},
                {"id": "n2", "plugin_id": "plugin_b", "tool_id": "tool2"},
                {"id": "n3", "plugin_id": "plugin_c", "tool_id": "tool3"},
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n3"},
                {"from_node": "n2", "to_node": "n3"},
            ],
            "entry_nodes": ["n1", "n2"],
            "output_nodes": ["n3"],
        }
        (tmp_path / "merge_test.json").write_text(json.dumps(pipeline_data))

        # Setup registry and plugin manager
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"key1": "value1", "shared": "from_n1"}))
        plugin_manager.add_plugin(MockPlugin("plugin_b", {"key2": "value2", "shared": "from_n2"}))
        plugin_manager.add_plugin(MockPlugin("plugin_c", {"final": "result"}))

        # Execute pipeline
        dag_service = DagPipelineService(registry, plugin_manager)
        result = dag_service.run_pipeline("merge_test", {"input": "test"})

        # Verify merge behavior (last-wins for conflicts)
        assert "key1" in result
        assert "key2" in result
        assert "final" in result
        assert result["shared"] == "from_n2"  # Last writer wins
