"""Tests for VideoPipelineService.

Phase 13 - Multi-Tool Linear Pipelines
"""

import pytest

from app.services.video_pipeline_service import VideoPipelineService
from tests.helpers import FakePlugin, FakeRegistry


def test_import():
    """Test service can be imported."""
    assert VideoPipelineService is not None


def test_instantiation():
    """Test service can be instantiated."""
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert service is not None


def test_run_pipeline_method_exists():
    """Test run_pipeline method exists."""
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, "run_pipeline")
    assert callable(service.run_pipeline)


def test_validate_method_exists():
    """Test _validate method exists."""
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, "_validate")
    assert callable(service._validate)


class TestRunPipelineValidation:
    """Test validation in run_pipeline."""

    def test_raises_error_when_plugin_not_found(self):
        """Test run_pipeline raises ValueError when plugin not found."""
        registry = FakeRegistry(plugin=None)
        service = VideoPipelineService(plugins=registry)

        with pytest.raises(ValueError, match="Plugin 'unknown-plugin' not found"):
            service.run_pipeline(
                plugin_id="unknown-plugin",
                tools=["detect_players"],
                payload={"image_bytes": b"test"},
            )

    def test_raises_error_when_tools_is_empty(self):
        """Test run_pipeline raises ValueError when tools is empty."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        with pytest.raises(ValueError, match="Pipeline requires a non-empty tools"):
            service.run_pipeline(
                plugin_id="test-plugin",
                tools=[],
                payload={"image_bytes": b"test"},
            )

    def test_raises_error_when_tools_is_none(self):
        """Test run_pipeline raises ValueError when tools is None."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        with pytest.raises(ValueError, match="Pipeline requires a non-empty tools"):
            service.run_pipeline(
                plugin_id="test-plugin",
                tools=None,
                payload={"image_bytes": b"test"},
            )

    def test_raises_error_when_tool_not_in_plugin(self):
        """Test run_pipeline raises ValueError when tool not found in plugin."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        with pytest.raises(ValueError, match="Tool 'unknown_tool' not found in plugin"):
            service.run_pipeline(
                plugin_id="test-plugin",
                tools=["unknown_tool"],
                payload={"image_bytes": b"test"},
            )


class TestRunPipelineSequentialExecution:
    """Test sequential execution in run_pipeline."""

    def test_executes_single_tool(self):
        """Test run_pipeline executes a single tool and returns structured output."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        result = service.run_pipeline(
            plugin_id="test-plugin",
            tools=["detect_players"],
            payload={"image_bytes": b"test"},
        )

        # Should return structured output
        assert "result" in result
        assert "steps" in result
        assert len(result["steps"]) == 1
        assert result["steps"][0]["tool"] == "detect_players"
        assert "output" in result["steps"][0]

    def test_executes_multiple_tools_sequentially(self):
        """Test run_pipeline executes multiple tools in order."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        result = service.run_pipeline(
            plugin_id="test-plugin",
            tools=["detect_players", "track_players"],
            payload={"image_bytes": b"test"},
        )

        # Should return structured output with 2 steps
        assert "result" in result
        assert "steps" in result
        assert len(result["steps"]) == 2
        assert result["steps"][0]["tool"] == "detect_players"
        assert result["steps"][1]["tool"] == "track_players"

    def test_passes_previous_tool_output_as_input(self):
        """Test run_pipeline passes previous tool output as 'input' to next tool."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        result = service.run_pipeline(
            plugin_id="test-plugin",
            tools=["detect_players", "track_players"],
            payload={"image_bytes": b"test"},
        )

        # First tool should receive original payload
        first_step_args = result["steps"][0]["output"]
        assert "image_bytes" in first_step_args

        # Second tool should receive original payload + input from first tool
        second_step_args = result["steps"][1]["output"]
        assert "image_bytes" in second_step_args
        assert "input" in second_step_args

    def test_returns_last_tool_output_as_result(self):
        """Test run_pipeline returns last tool's output as result."""
        plugin = FakePlugin()
        registry = FakeRegistry(plugin=plugin)
        service = VideoPipelineService(plugins=registry)

        result = service.run_pipeline(
            plugin_id="test-plugin",
            tools=["detect_players", "track_players", "annotate_frame"],
            payload={"image_bytes": b"test"},
        )

        # Result should be the last tool's output
        assert result["result"] == result["steps"][-1]["output"]
