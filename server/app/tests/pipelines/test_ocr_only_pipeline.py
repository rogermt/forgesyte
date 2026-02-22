"""Tests for ocr_only pipeline definition."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def test_ocr_only_pipeline_exists():
    """Test: ocr_only.json file exists."""
    pipeline_path = Path(__file__).resolve().parents[2] / "pipelines" / "ocr_only.json"
    assert pipeline_path.exists(), f"ocr_only.json not found at {pipeline_path}"


def test_ocr_only_pipeline_valid_json():
    """Test: ocr_only.json is valid JSON."""
    import json

    pipeline_path = Path(__file__).resolve().parents[2] / "pipelines" / "ocr_only.json"

    with open(pipeline_path, "r") as f:
        data = json.load(f)

    assert data["id"] == "ocr_only"
    assert data["name"] == "OCR Only Pipeline"
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["plugin_id"] == "ocr"
    assert data["nodes"][0]["tool_id"] == "analyze"
    assert data["entry_nodes"] == ["read"]
    assert data["output_nodes"] == ["read"]
    assert len(data["edges"]) == 0  # No edges for single node pipeline


def test_ocr_only_pipeline_loads_via_registry():
    """Test: ocr_only pipeline can be loaded by DagPipelineService."""
    from pathlib import Path

    from app.services.pipeline_registry_service import PipelineRegistryService

    # Get pipelines directory
    pipelines_dir = Path(__file__).resolve().parents[2] / "pipelines"

    # Create registry
    registry = PipelineRegistryService(pipelines_dir)

    # Load ocr_only pipeline
    pipeline = registry.get_pipeline("ocr_only")

    assert pipeline is not None, "ocr_only pipeline not found in registry"
    assert pipeline.id == "ocr_only"
    assert len(pipeline.nodes) == 1
    assert len(pipeline.edges) == 0


if __name__ == "__main__":
    test_ocr_only_pipeline_exists()
    test_ocr_only_pipeline_valid_json()
    test_ocr_only_pipeline_loads_via_registry()
    print("✅ All ocr_only pipeline tests passed!")
