"""
Tests for Phase 14 Pipeline Registry Service.
TDD: Write failing tests first, then implement service.
"""
import pytest
import json
from pathlib import Path

try:
    from app.services.pipeline_registry_service import PipelineRegistryService
    from app.pipeline_models.pipeline_graph_models import Pipeline, PipelineNode, PipelineEdge
    SERVICE_EXISTS = True
except ImportError:
    SERVICE_EXISTS = False


@pytest.mark.skipif(not SERVICE_EXISTS, reason="PipelineRegistryService not implemented yet")
class TestPipelineRegistryService:
    """Test PipelineRegistryService functionality."""

    @pytest.fixture
    def temp_pipeline_dir(self, tmp_path):
        """Create a temporary directory with test pipelines."""
        # Create example pipeline
        pipeline_data = {
            "id": "test_pipeline",
            "name": "Test Pipeline",
            "nodes": [
                {"id": "n1", "plugin_id": "ocr", "tool_id": "analyze"},
                {"id": "n2", "plugin_id": "yolo", "tool_id": "detect"},
            ],
            "edges": [{"from_node": "n1", "to_node": "n2"}],
            "entry_nodes": ["n1"],
            "output_nodes": ["n2"],
        }
        
        pipeline_file = tmp_path / "test_pipeline.json"
        pipeline_file.write_text(json.dumps(pipeline_data))
        
        return tmp_path

    def test_list_returns_all_pipelines(self, temp_pipeline_dir):
        """Test that list() returns all registered pipelines."""
        registry = PipelineRegistryService(str(temp_pipeline_dir))
        pipelines = registry.list()
        
        assert len(pipelines) == 1
        assert pipelines[0]["id"] == "test_pipeline"

    def test_get_returns_pipeline_by_id(self, temp_pipeline_dir):
        """Test that get() returns a specific pipeline."""
        registry = PipelineRegistryService(str(temp_pipeline_dir))
        pipeline = registry.get("test_pipeline")
        
        assert pipeline is not None
        assert pipeline.id == "test_pipeline"
        assert len(pipeline.nodes) == 2

    def test_get_returns_none_for_unknown_pipeline(self, temp_pipeline_dir):
        """Test that get() returns None for unknown pipeline ID."""
        registry = PipelineRegistryService(str(temp_pipeline_dir))
        pipeline = registry.get("nonexistent")
        
        assert pipeline is None

    def test_get_info_returns_pipeline_metadata(self, temp_pipeline_dir):
        """Test that get_info() returns pipeline metadata."""
        registry = PipelineRegistryService(str(temp_pipeline_dir))
        info = registry.get_info("test_pipeline")
        
        assert info is not None
        assert info["id"] == "test_pipeline"
        assert info["name"] == "Test Pipeline"
        assert "node_count" in info
        assert info["node_count"] == 2

    def test_get_info_returns_none_for_unknown_pipeline(self, temp_pipeline_dir):
        """Test that get_info() returns None for unknown pipeline ID."""
        registry = PipelineRegistryService(str(temp_pipeline_dir))
        info = registry.get_info("nonexistent")
        
        assert info is None

    def test_loads_multiple_pipelines(self, tmp_path):
        """Test that registry loads multiple pipeline files."""
        # Create first pipeline
        pipeline1_data = {
            "id": "pipeline1",
            "name": "Pipeline 1",
            "nodes": [{"id": "n1", "plugin_id": "ocr", "tool_id": "analyze"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "pipeline1.json").write_text(json.dumps(pipeline1_data))
        
        # Create second pipeline
        pipeline2_data = {
            "id": "pipeline2",
            "name": "Pipeline 2",
            "nodes": [{"id": "n1", "plugin_id": "yolo", "tool_id": "detect"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "pipeline2.json").write_text(json.dumps(pipeline2_data))
        
        registry = PipelineRegistryService(str(tmp_path))
        pipelines = registry.list()
        
        assert len(pipelines) == 2
        pipeline_ids = {p["id"] for p in pipelines}
        assert pipeline_ids == {"pipeline1", "pipeline2"}

    def test_ignores_non_json_files(self, tmp_path):
        """Test that registry ignores non-JSON files."""
        # Create valid pipeline
        pipeline_data = {
            "id": "test_pipeline",
            "name": "Test",
            "nodes": [{"id": "n1", "plugin_id": "ocr", "tool_id": "analyze"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "test_pipeline.json").write_text(json.dumps(pipeline_data))
        
        # Create non-JSON file
        (tmp_path / "README.md").write_text("# Pipeline documentation")
        
        registry = PipelineRegistryService(str(tmp_path))
        pipelines = registry.list()
        
        assert len(pipelines) == 1

    def test_handles_invalid_json_gracefully(self, tmp_path):
        """Test that registry handles invalid JSON files gracefully."""
        # Create valid pipeline
        pipeline_data = {
            "id": "valid_pipeline",
            "name": "Valid",
            "nodes": [{"id": "n1", "plugin_id": "ocr", "tool_id": "analyze"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "valid_pipeline.json").write_text(json.dumps(pipeline_data))
        
        # Create invalid JSON file
        (tmp_path / "invalid.json").write_text("{ invalid json }")
        
        registry = PipelineRegistryService(str(tmp_path))
        pipelines = registry.list()
        
        assert len(pipelines) == 1
        assert pipelines[0]["id"] == "valid_pipeline"