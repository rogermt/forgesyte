"""
Tests for pipeline pipeline graph models.
TDD: Write failing tests first, then implement models.
"""

import pytest
from pydantic import ValidationError

# These imports will fail initially - models don't exist yet
try:
    from app.pipeline_models.pipeline_graph_models import (
        Pipeline,
        PipelineEdge,
        PipelineNode,
        PipelineValidationResult,
        ToolMetadata,
    )

    MODELS_EXIST = True
except ImportError:
    MODELS_EXIST = False


@pytest.mark.skipif(not MODELS_EXIST, reason="Models not implemented yet")
class TestPipelineNode:
    """Test PipelineNode model."""

    def test_create_valid_node(self):
        """Test creating a valid pipeline node."""
        node = PipelineNode(id="n1", plugin_id="ocr", tool_id="analyze")
        assert node.id == "n1"
        assert node.plugin_id == "ocr"
        assert node.tool_id == "analyze"

    def test_node_requires_id(self):
        """Test that node id is required."""
        with pytest.raises(ValidationError):
            PipelineNode(plugin_id="ocr", tool_id="analyze")

    def test_node_requires_plugin_id(self):
        """Test that plugin_id is required."""
        with pytest.raises(ValidationError):
            PipelineNode(id="n1", tool_id="analyze")

    def test_node_requires_tool_id(self):
        """Test that tool_id is required."""
        with pytest.raises(ValidationError):
            PipelineNode(id="n1", plugin_id="ocr")

    def test_node_serialization(self):
        """Test that node can be serialized to dict."""
        node = PipelineNode(id="n1", plugin_id="ocr", tool_id="analyze")
        data = node.model_dump()
        assert data["id"] == "n1"
        assert data["plugin_id"] == "ocr"
        assert data["tool_id"] == "analyze"


@pytest.mark.skipif(not MODELS_EXIST, reason="Models not implemented yet")
class TestPipelineEdge:
    """Test PipelineEdge model."""

    def test_create_valid_edge(self):
        """Test creating a valid pipeline edge."""
        edge = PipelineEdge(from_node="n1", to_node="n2")
        assert edge.from_node == "n1"
        assert edge.to_node == "n2"

    def test_edge_requires_from_node(self):
        """Test that from_node is required."""
        with pytest.raises(ValidationError):
            PipelineEdge(to_node="n2")

    def test_edge_requires_to_node(self):
        """Test that to_node is required."""
        with pytest.raises(ValidationError):
            PipelineEdge(from_node="n1")


@pytest.mark.skipif(not MODELS_EXIST, reason="Models not implemented yet")
class TestPipeline:
    """Test Pipeline model."""

    def test_create_valid_pipeline(self):
        """Test creating a valid pipeline."""
        nodes = [
            PipelineNode(id="n1", plugin_id="ocr", tool_id="analyze"),
            PipelineNode(id="n2", plugin_id="yolo", tool_id="detect"),
        ]
        edges = [PipelineEdge(from_node="n1", to_node="n2")]

        pipeline = Pipeline(
            id="test_pipeline",
            name="Test Pipeline",
            nodes=nodes,
            edges=edges,
            entry_nodes=["n1"],
            output_nodes=["n2"],
        )

        assert pipeline.id == "test_pipeline"
        assert pipeline.name == "Test Pipeline"
        assert len(pipeline.nodes) == 2
        assert len(pipeline.edges) == 1
        assert pipeline.entry_nodes == ["n1"]
        assert pipeline.output_nodes == ["n2"]

    def test_pipeline_requires_id(self):
        """Test that pipeline id is required."""
        with pytest.raises(ValidationError):
            Pipeline(
                name="Test",
                nodes=[],
                edges=[],
                entry_nodes=[],
                output_nodes=[],
            )

    def test_pipeline_requires_nodes(self):
        """Test that nodes is required."""
        with pytest.raises(ValidationError):
            Pipeline(
                id="test",
                name="Test",
                edges=[],
                entry_nodes=[],
                output_nodes=[],
            )

    def test_pipeline_requires_edges(self):
        """Test that edges is required."""
        with pytest.raises(ValidationError):
            Pipeline(
                id="test",
                name="Test",
                nodes=[],
                entry_nodes=[],
                output_nodes=[],
            )

    def test_pipeline_requires_entry_nodes(self):
        """Test that entry_nodes is required."""
        with pytest.raises(ValidationError):
            Pipeline(
                id="test",
                name="Test",
                nodes=[],
                edges=[],
                output_nodes=[],
            )

    def test_pipeline_requires_output_nodes(self):
        """Test that output_nodes is required."""
        with pytest.raises(ValidationError):
            Pipeline(
                id="test",
                name="Test",
                nodes=[],
                edges=[],
                entry_nodes=[],
            )

    def test_pipeline_serialization(self):
        """Test that pipeline can be serialized to dict."""
        nodes = [PipelineNode(id="n1", plugin_id="ocr", tool_id="analyze")]
        edges = [PipelineEdge(from_node="n1", to_node="n1")]

        pipeline = Pipeline(
            id="test",
            name="Test",
            nodes=nodes,
            edges=edges,
            entry_nodes=["n1"],
            output_nodes=["n1"],
        )

        data = pipeline.model_dump()
        assert data["id"] == "test"
        assert len(data["nodes"]) == 1
        assert len(data["edges"]) == 1


@pytest.mark.skipif(not MODELS_EXIST, reason="Models not implemented yet")
class TestToolMetadata:
    """Test ToolMetadata model."""

    def test_create_valid_tool_metadata(self):
        """Test creating valid tool metadata."""
        metadata = ToolMetadata(
            plugin_id="ocr",
            tool_id="analyze",
            input_types=["image_bytes"],
            output_types=["text"],
            capabilities=["text_extraction"],
        )

        assert metadata.plugin_id == "ocr"
        assert metadata.tool_id == "analyze"
        assert metadata.input_types == ["image_bytes"]
        assert metadata.output_types == ["text"]
        assert metadata.capabilities == ["text_extraction"]

    def test_tool_metadata_allows_empty_lists(self):
        """Test that empty lists are allowed for types and capabilities."""
        metadata = ToolMetadata(
            plugin_id="test", tool_id="test", input_types=[], output_types=[]
        )

        assert metadata.input_types == []
        assert metadata.output_types == []


@pytest.mark.skipif(not MODELS_EXIST, reason="Models not implemented yet")
class TestPipelineValidationResult:
    """Test PipelineValidationResult model."""

    def test_valid_result(self):
        """Test creating a valid validation result."""
        result = PipelineValidationResult(valid=True, errors=[])

        assert result.valid is True
        assert result.errors == []

    def test_invalid_result(self):
        """Test creating an invalid validation result."""
        result = PipelineValidationResult(
            valid=False, errors=["Cycle detected", "Unknown plugin"]
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert "Cycle detected" in result.errors
