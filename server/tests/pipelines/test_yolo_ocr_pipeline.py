"""Tests for yolo_ocr pipeline definition (Phase 15).

This test module validates:
- Pipeline structure (nodes, edges, entry/output)
- Plugin and tool references are real
- Input/output type compatibility
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def pipeline_path() -> Path:
    """Path to yolo_ocr pipeline definition."""
    return Path(__file__).resolve().parents[2] / "app" / "pipelines" / "yolo_ocr.json"


@pytest.fixture
def pipeline(pipeline_path: Path) -> dict:
    """Load yolo_ocr pipeline definition."""
    assert pipeline_path.exists(), f"Pipeline file not found: {pipeline_path}"
    with pipeline_path.open() as f:
        return json.load(f)


class TestYoloOcrPipelineStructure:
    """Validate pipeline structural requirements."""

    def test_pipeline_file_exists(self, pipeline_path: Path) -> None:
        """Pipeline file should exist at correct path."""
        assert pipeline_path.exists()
        assert pipeline_path.suffix == ".json"

    def test_pipeline_loads_as_valid_json(self, pipeline: dict) -> None:
        """Pipeline should be valid JSON."""
        assert isinstance(pipeline, dict)

    def test_pipeline_has_required_fields(self, pipeline: dict) -> None:
        """Pipeline must have id, name, description, nodes, edges."""
        assert "id" in pipeline
        assert "name" in pipeline
        assert "description" in pipeline
        assert "nodes" in pipeline
        assert "edges" in pipeline
        assert "entry_nodes" in pipeline
        assert "output_nodes" in pipeline

    def test_pipeline_id_is_correct(self, pipeline: dict) -> None:
        """Pipeline ID should be 'yolo_ocr'."""
        assert pipeline["id"] == "yolo_ocr"

    def test_pipeline_has_two_nodes(self, pipeline: dict) -> None:
        """Pipeline should have exactly 2 nodes: detect and read."""
        nodes = pipeline["nodes"]
        assert isinstance(nodes, list)
        assert len(nodes) == 2
        node_ids = {n["id"] for n in nodes}
        assert node_ids == {"detect", "read"}

    def test_pipeline_has_one_edge(self, pipeline: dict) -> None:
        """Pipeline should have exactly 1 edge: detect→read."""
        edges = pipeline["edges"]
        assert isinstance(edges, list)
        assert len(edges) == 1
        edge = edges[0]
        assert edge["from_node"] == "detect"
        assert edge["to_node"] == "read"

    def test_entry_nodes_is_detect(self, pipeline: dict) -> None:
        """Entry node should be 'detect'."""
        assert pipeline["entry_nodes"] == ["detect"]

    def test_output_nodes_is_read(self, pipeline: dict) -> None:
        """Output node should be 'read'."""
        assert pipeline["output_nodes"] == ["read"]


class TestYoloOcrPipelineNodes:
    """Validate individual node definitions."""

    def test_detect_node_has_required_fields(self, pipeline: dict) -> None:
        """Detect node must reference valid plugin and tool."""
        detect = next(n for n in pipeline["nodes"] if n["id"] == "detect")
        assert detect["plugin_id"] == "yolo-tracker"
        assert detect["tool_id"] == "player_detection"
        assert "input_schema" in detect

    def test_read_node_has_required_fields(self, pipeline: dict) -> None:
        """Read node must reference valid plugin and tool."""
        read = next(n for n in pipeline["nodes"] if n["id"] == "read")
        assert read["plugin_id"] == "ocr"
        assert read["tool_id"] == "analyze"
        assert "input_schema" in read

    def test_detect_input_schema_has_image_base64(self, pipeline: dict) -> None:
        """Detect node should require image_base64."""
        detect = next(n for n in pipeline["nodes"] if n["id"] == "detect")
        schema = detect["input_schema"]
        assert "properties" in schema
        assert "image_base64" in schema["properties"]
        assert "image_base64" in schema["required"]

    def test_read_input_schema_has_image_base64(self, pipeline: dict) -> None:
        """Read node should require image_base64."""
        read = next(n for n in pipeline["nodes"] if n["id"] == "read")
        schema = read["input_schema"]
        assert "properties" in schema
        assert "image_base64" in schema["properties"]
        assert "image_base64" in schema["required"]


class TestYoloOcrPipelinePluginReferences:
    """Validate that referenced plugins and tools exist (requires plugins installed)."""

    def test_yolo_tracker_plugin_exists(self) -> None:
        """yolo-tracker plugin should be available."""
        try:
            from app.plugins.loader.plugin_registry import get_registry

            registry = get_registry()
            available = registry.list_available()
            if not available:
                pytest.skip("Plugin registry empty in test environment")
            assert "yolo-tracker" in available, (
                f"yolo-tracker plugin not found. Available: {available}"
            )
        except RuntimeError:
            # Plugin registry may not be initialized in all test contexts
            pytest.skip("Plugin registry not initialized")

    def test_ocr_plugin_exists(self) -> None:
        """ocr plugin should be available."""
        try:
            from app.plugins.loader.plugin_registry import get_registry

            registry = get_registry()
            available = registry.list_available()
            if not available:
                pytest.skip("Plugin registry empty in test environment")
            assert "ocr" in available, f"ocr plugin not found. Available: {available}"
        except RuntimeError:
            # Plugin registry may not be initialized in all test contexts
            pytest.skip("Plugin registry not initialized")

    def test_player_detection_tool_exists(self) -> None:
        """player_detection tool should exist in yolo-tracker plugin."""
        try:
            from app.plugins.loader.plugin_registry import get_registry

            registry = get_registry()
            available = registry.list_available()
            if "yolo-tracker" not in available:
                pytest.skip("yolo-tracker plugin not installed")

            all_plugins = registry.list_all()
            yolo = next((p for p in all_plugins if p.name == "yolo-tracker"), None)
            assert yolo is not None, "yolo-tracker plugin metadata not found"

            tools = {t.id for t in yolo.tools}
            assert "player_detection" in tools, (
                f"player_detection tool not found. Available: {tools}"
            )
        except RuntimeError:
            pytest.skip("Plugin registry not initialized")

    def test_analyze_tool_exists(self) -> None:
        """analyze tool should exist in ocr plugin."""
        try:
            from app.plugins.loader.plugin_registry import get_registry

            registry = get_registry()
            available = registry.list_available()
            if "ocr" not in available:
                pytest.skip("ocr plugin not installed")

            all_plugins = registry.list_all()
            ocr = next((p for p in all_plugins if p.name == "ocr"), None)
            assert ocr is not None, "ocr plugin metadata not found"

            tools = {t.id for t in ocr.tools}
            assert "analyze" in tools, f"analyze tool not found. Available: {tools}"
        except RuntimeError:
            pytest.skip("Plugin registry not initialized")


class TestYoloOcrPipelineDAG:
    """Validate DAG properties (acyclic, all nodes reachable)."""

    def test_pipeline_is_acyclic(self, pipeline: dict) -> None:
        """Pipeline should have no cycles."""
        nodes = pipeline["nodes"]
        edges = pipeline["edges"]

        # Build adjacency list
        graph = {n["id"]: [] for n in nodes}
        for e in edges:
            graph[e["from_node"]].append(e["to_node"])

        # DFS to detect cycles
        visited = set()
        stack = set()

        def has_cycle(node_id: str) -> bool:
            if node_id in stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            stack.add(node_id)
            for next_id in graph.get(node_id, []):
                if has_cycle(next_id):
                    return True
            stack.remove(node_id)
            return False

        for node_id in graph:
            if node_id not in visited:
                assert not has_cycle(node_id), "Pipeline contains a cycle"

    def test_all_entry_nodes_reachable_from_themselves(self, pipeline: dict) -> None:
        """Entry nodes should be reachable (defined)."""
        node_ids = {n["id"] for n in pipeline["nodes"]}
        for entry in pipeline["entry_nodes"]:
            assert entry in node_ids

    def test_all_output_nodes_reachable(self, pipeline: dict) -> None:
        """All output nodes should be reachable from entry nodes."""
        nodes = pipeline["nodes"]
        edges = pipeline["edges"]
        node_ids = {n["id"] for n in nodes}

        # Build adjacency list
        graph = {n["id"]: [] for n in nodes}
        for e in edges:
            graph[e["from_node"]].append(e["to_node"])

        # BFS from entry nodes
        reachable = set()
        queue = list(pipeline["entry_nodes"])
        while queue:
            node = queue.pop(0)
            if node not in reachable:
                reachable.add(node)
                queue.extend(graph.get(node, []))

        for output in pipeline["output_nodes"]:
            assert output in reachable, (
                f"Output node '{output}' not reachable from entry nodes. "
                f"Reachable: {reachable}"
            )
