"""
Tests for pipeline REST Pipeline Endpoints.
TDD: Write failing tests first, then implement endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# Import models for mocking even if service doesn't exist
from app.services.pipeline_registry_service import PipelineRegistryService
from tests.pipelines.test_dag_pipeline_service import MockPlugin, MockPluginManager

ENDPOINTS_EXIST = True


@pytest.mark.skipif(
    not ENDPOINTS_EXIST, reason="Pipeline endpoints not implemented yet"
)
class TestPipelineEndpoints:
    """Test pipeline REST endpoints."""

    @pytest.fixture
    def app_with_state(self, tmp_path):
        """Create app with initialized state for testing."""
        app = create_app()

        # Create test pipeline
        pipeline_data = {
            "id": "test_pipeline",
            "name": "Test Pipeline",
            "nodes": [{"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }
        (tmp_path / "test_pipeline.json").write_text(
            __import__("json").dumps(pipeline_data)
        )

        # Initialize pipeline services
        registry = PipelineRegistryService(str(tmp_path))
        plugin_manager = MockPluginManager()
        plugin_manager.add_plugin(MockPlugin("plugin_a", {"result": "test"}))

        app.state.pipeline_registry = registry
        app.state.plugin_manager_for_pipelines = plugin_manager

        return app

    @pytest.fixture
    def client(self, app_with_state):
        """Create test client with initialized app."""
        return TestClient(app_with_state)

    def test_list_pipelines(self, client):
        """Test GET /pipelines/list returns all pipelines."""
        response = client.get("/v1/pipelines/list")

        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert len(data["pipelines"]) == 1
        assert data["pipelines"][0]["id"] == "test_pipeline"

    def test_get_pipeline_info(self, client):
        """Test GET /pipelines/{id}/info returns pipeline metadata."""
        response = client.get("/v1/pipelines/test_pipeline/info")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_pipeline"
        assert data["name"] == "Test Pipeline"
        assert "node_count" in data

    def test_get_pipeline_info_not_found(self, client):
        """Test GET /pipelines/{id}/info returns 404 for unknown pipeline."""
        response = client.get("/v1/pipelines/nonexistent/info")

        assert response.status_code == 404

    def test_validate_pipeline_success(self, client):
        """Test POST /pipelines/validate with valid pipeline."""
        pipeline_data = {
            "id": "test",
            "name": "Test",
            "nodes": [{"id": "n1", "plugin_id": "plugin_a", "tool_id": "tool1"}],
            "edges": [],
            "entry_nodes": ["n1"],
            "output_nodes": ["n1"],
        }

        response = client.post("/v1/pipelines/validate", json=pipeline_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_pipeline_invalid_cycle(self, client):
        """Test POST /pipelines/validate detects cycles."""
        pipeline_data = {
            "id": "test",
            "name": "Test",
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

        response = client.post("/v1/pipelines/validate", json=pipeline_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("cycle" in error.lower() for error in data["errors"])

    def test_run_pipeline(self, client):
        """Test POST /pipelines/{id}/run executes pipeline."""
        response = client.post(
            "/v1/pipelines/test_pipeline/run", json={"input": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "output" in data

    def test_run_pipeline_not_found(self, client):
        """Test POST /pipelines/{id}/run returns 404 for unknown pipeline."""
        response = client.post("/v1/pipelines/nonexistent/run", json={"input": "test"})

        assert response.status_code == 404
