"""Tests for Pipeline Validation.

Phase 13 - Multi-Tool Linear Pipelines

These tests validate VideoPipelineService validation rules.
"""

import pytest

from tests.helpers import FakePlugin, FakeRegistry


def test_pipeline_rejects_missing_plugin():
    """Test pipeline rejects when plugin doesn't exist."""
    registry = FakeRegistry(plugin=None)
    from app.services.video_pipeline_service import VideoPipelineService

    service = VideoPipelineService(plugins=registry)

    with pytest.raises(ValueError, match="Plugin 'nope' not found"):
        service.run_pipeline("nope", ["detect"], {})


def test_pipeline_rejects_missing_tools():
    """Test pipeline rejects when tools[] is missing."""
    plugin = FakePlugin()
    registry = FakeRegistry(plugin=plugin)
    from app.services.video_pipeline_service import VideoPipelineService

    service = VideoPipelineService(plugins=registry)

    with pytest.raises(ValueError, match="Pipeline requires a non-empty tools"):
        service.run_pipeline("test-plugin", [], {})


def test_pipeline_rejects_unknown_tool():
    """Test pipeline rejects when tool doesn't exist in plugin."""
    plugin = FakePlugin()
    registry = FakeRegistry(plugin=plugin)
    from app.services.video_pipeline_service import VideoPipelineService

    service = VideoPipelineService(plugins=registry)

    with pytest.raises(ValueError, match="Tool 'does_not_exist' not found in plugin"):
        service.run_pipeline("test-plugin", ["does_not_exist"], {})


def test_pipeline_executes_in_order():
    """Test pipeline executes tools in correct order."""
    plugin = FakePlugin()
    registry = FakeRegistry(plugin=plugin)
    from app.services.video_pipeline_service import VideoPipelineService

    service = VideoPipelineService(plugins=registry)

    result = service.run_pipeline(
        "test-plugin",
        ["detect_players", "track_players"],
        {"image_bytes": "AAA"},
    )

    assert len(result["steps"]) == 2
    assert result["steps"][0]["tool"] == "detect_players"
    assert result["steps"][1]["tool"] == "track_players"
