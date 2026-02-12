"""
Tests for pipeline Type Compatibility Validation.
TDD: Write failing tests first, then implement validator.
"""
import pytest

try:
    from app.services.type_validator import TypeValidator
    from app.pipeline_models.pipeline_graph_models import (
        Pipeline,
        PipelineNode,
        PipelineEdge,
        ToolMetadata,
    )
    VALIDATOR_EXISTS = True
except ImportError:
    VALIDATOR_EXISTS = False


@pytest.mark.skipif(not VALIDATOR_EXISTS, reason="TypeValidator not implemented yet")
class TestTypeValidator:
    """Test TypeValidator functionality."""

    def test_valid_type_compatibility(self):
        """Test that compatible types pass validation."""
        validator = TypeValidator()
        
        # Create tool metadata with compatible types
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
        
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )
        
        errors = validator.validate_types(pipeline, tools)
        
        assert len(errors) == 0

    def test_type_mismatch_rejected(self):
        """Test that incompatible types are rejected."""
        validator = TypeValidator()
        
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
                input_types=["heatmap"],  # Incompatible with detections
                output_types=["tracks"],
            ),
        }
        
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )
        
        errors = validator.validate_types(pipeline, tools)
        
        assert len(errors) > 0
        assert any("type mismatch" in error.lower() for error in errors)

    def test_multiple_compatible_types(self):
        """Test that multiple compatible types are accepted."""
        validator = TypeValidator()
        
        # Create tool metadata with multiple compatible types
        tools = {
            "n1": ToolMetadata(
                plugin_id="plugin_a",
                tool_id="tool1",
                input_types=["video_frame"],
                output_types=["detections", "tracks"],  # Multiple outputs
            ),
            "n2": ToolMetadata(
                plugin_id="plugin_b",
                tool_id="tool2",
                input_types=["detections", "tracks"],  # Accepts either
                output_types=["overlay"],
            ),
        }
        
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )
        
        errors = validator.validate_types(pipeline, tools)
        
        assert len(errors) == 0

    def test_partial_type_overlap_accepted(self):
        """Test that partial type overlap is accepted."""
        validator = TypeValidator()
        
        # Create tool metadata with partial type overlap
        tools = {
            "n1": ToolMetadata(
                plugin_id="plugin_a",
                tool_id="tool1",
                input_types=["video_frame"],
                output_types=["detections", "heatmap"],  # Two outputs
            ),
            "n2": ToolMetadata(
                plugin_id="plugin_b",
                tool_id="tool2",
                input_types=["detections", "overlay"],  # One overlap (detections)
                output_types=["tracks"],
            ),
        }
        
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )
        
        errors = validator.validate_types(pipeline, tools)
        
        assert len(errors) == 0

    def test_empty_types_allowed(self):
        """Test that empty type lists are allowed (no validation)."""
        validator = TypeValidator()
        
        # Create tool metadata with empty types
        tools = {
            "n1": ToolMetadata(
                plugin_id="plugin_a",
                tool_id="tool1",
                input_types=[],
                output_types=[],
            ),
            "n2": ToolMetadata(
                plugin_id="plugin_b",
                tool_id="tool2",
                input_types=[],
                output_types=[],
            ),
        }
        
        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=[
                PipelineNode(id="n1", plugin_id="plugin_a", tool_id="tool1"),
                PipelineNode(id="n2", plugin_id="plugin_b", tool_id="tool2"),
            ],
            edges=[PipelineEdge(from_node="n1", to_node="n2")],
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )
        
        errors = validator.validate_types(pipeline, tools)
        
        # Empty types should not cause errors
        assert len(errors) == 0