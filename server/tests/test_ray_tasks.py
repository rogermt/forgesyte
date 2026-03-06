"""Tests for Ray remote tasks module.

These tests verify the execute_pipeline_remote function that runs
plugin tools in a Ray distributed environment.
"""

import base64
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Shared fixtures at module level
@pytest.fixture
def mock_plugin_service():
    """Create a mock PluginManagementService."""
    service = MagicMock()
    service.get_plugin_manifest.return_value = {
        "id": "test_plugin",
        "tools": [
            {
                "id": "test_tool",
                "inputs": ["image_bytes"],
                "description": "Test tool",
            }
        ],
    }
    service.run_plugin_tool.return_value = {"result": "success"}
    return service


@pytest.fixture
def mock_storage():
    """Create a mock StorageService with a temp file."""
    storage = MagicMock()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"fake_image_bytes")
        temp_path = Path(f.name)
    storage.load_file.return_value = temp_path
    yield storage
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestExecutePipelineRemote:
    """Tests for the execute_pipeline_remote Ray task."""

    def test_execute_image_job_single_tool(self, mock_plugin_service, mock_storage):
        """Test executing a single-tool image job via Ray task."""
        from app.ray_tasks import _execute_pipeline_impl

        result = _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["test_tool"],
            input_path="image/test.jpg",
            job_type="image",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        assert "test_tool" in result
        assert result["test_tool"] == {"result": "success"}
        mock_plugin_service.run_plugin_tool.assert_called_once()

    def test_execute_video_job(self, mock_plugin_service, mock_storage):
        """Test executing a video job via Ray task."""
        from app.ray_tasks import _execute_pipeline_impl

        mock_plugin_service.get_plugin_manifest.return_value = {
            "id": "test_plugin",
            "tools": [
                {
                    "id": "video_tool",
                    "inputs": ["video_path"],
                    "description": "Video tool",
                }
            ],
        }
        mock_plugin_service.run_plugin_tool.return_value = {
            "frames": [{"frame": 1}, {"frame": 2}],
            "total_frames": 2,
        }

        result = _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["video_tool"],
            input_path="video/test.mp4",
            job_type="video",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        assert "video_tool" in result
        assert result["video_tool"]["total_frames"] == 2

    def test_execute_multi_tool_job(self, mock_plugin_service, mock_storage):
        """Test executing a multi-tool job via Ray task."""
        from app.ray_tasks import _execute_pipeline_impl

        mock_plugin_service.get_plugin_manifest.return_value = {
            "id": "test_plugin",
            "tools": [
                {"id": "tool1", "inputs": ["image_bytes"], "description": "Tool 1"},
                {"id": "tool2", "inputs": ["image_bytes"], "description": "Tool 2"},
            ],
        }

        call_count = [0]

        def mock_run_tool(plugin_id, tool_name, args, progress_callback=None):
            call_count[0] += 1
            return {"tool": tool_name, "result": f"output_{call_count[0]}"}

        mock_plugin_service.run_plugin_tool.side_effect = mock_run_tool

        result = _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["tool1", "tool2"],
            input_path="image/test.jpg",
            job_type="image_multi",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        assert "tool1" in result
        assert "tool2" in result
        assert mock_plugin_service.run_plugin_tool.call_count == 2

    def test_cleanup_temp_file(self, mock_plugin_service):
        """Test that temp files are cleaned up after execution."""
        from app.ray_tasks import _execute_pipeline_impl

        # Create a real temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"fake_image_bytes")
            temp_path = Path(f.name)

        mock_storage = MagicMock()
        mock_storage.load_file.return_value = temp_path

        _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["test_tool"],
            input_path="image/test.jpg",
            job_type="image",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        # Temp file should be cleaned up
        assert not temp_path.exists()

    def test_handles_image_base64_input(self, mock_plugin_service):
        """Test handling of image_base64 input type."""
        from app.ray_tasks import _execute_pipeline_impl

        mock_plugin_service.get_plugin_manifest.return_value = {
            "id": "test_plugin",
            "tools": [
                {
                    "id": "base64_tool",
                    "inputs": ["image_base64"],
                    "description": "Base64 tool",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"test_image_data")
            temp_path = Path(f.name)

        mock_storage = MagicMock()
        mock_storage.load_file.return_value = temp_path

        captured_args = {}

        def capture_args(plugin_id, tool_name, args, progress_callback=None):
            captured_args.update(args)
            return {"result": "ok"}

        mock_plugin_service.run_plugin_tool.side_effect = capture_args

        _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["base64_tool"],
            input_path="image/test.jpg",
            job_type="image",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        # Should have base64 encoded the image
        assert "image_base64" in captured_args
        expected_b64 = base64.b64encode(b"test_image_data").decode("utf-8")
        assert captured_args["image_base64"] == expected_b64

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_handles_tool_error(self, mock_plugin_service, mock_storage):
        """Test that tool errors are propagated properly."""
        from app.ray_tasks import _execute_pipeline_impl

        mock_plugin_service.run_plugin_tool.side_effect = RuntimeError(
            "Tool failed to execute"
        )

        with pytest.raises(RuntimeError, match="Tool failed to execute"):
            _execute_pipeline_impl(
                plugin_id="test_plugin",
                tools_to_run=["test_tool"],
                input_path="image/test.jpg",
                job_type="image",
                get_plugin_service_fn=lambda: mock_plugin_service,
                get_storage_service_fn=lambda: mock_storage,
            )

    def test_handles_plugin_not_found(self, mock_storage):
        """Test that missing plugin raises an error."""
        from app.ray_tasks import _execute_pipeline_impl

        mock_service = MagicMock()
        mock_service.get_plugin_manifest.return_value = None

        with pytest.raises(RuntimeError, match="Plugin .* not found"):
            _execute_pipeline_impl(
                plugin_id="missing_plugin",
                tools_to_run=["test_tool"],
                input_path="image/test.jpg",
                job_type="image",
                get_plugin_service_fn=lambda: mock_service,
                get_storage_service_fn=lambda: mock_storage,
            )


class TestRayTaskDecorator:
    """Tests for the Ray remote decorator configuration."""

    def test_execute_pipeline_remote_is_decorated(self):
        """Test that execute_pipeline_remote has @ray.remote decorator."""
        from app.ray_tasks import execute_pipeline_remote

        # Check that it's a Ray remote function
        # Ray remote functions have a 'remote' attribute
        assert hasattr(execute_pipeline_remote, "remote")
        assert callable(execute_pipeline_remote.remote)


class TestStorageIntegration:
    """Tests for storage integration in Ray tasks."""

    def test_loads_file_from_storage(self, mock_plugin_service):
        """Test that files are loaded from storage correctly."""
        from app.ray_tasks import _execute_pipeline_impl

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(b"stored_file_content")
            temp_path = Path(f.name)

        mock_storage = MagicMock()
        mock_storage.load_file.return_value = temp_path

        _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["test_tool"],
            input_path="s3://bucket/image.jpg",
            job_type="image",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        # Should have called load_file with the input path
        mock_storage.load_file.assert_called_once_with("s3://bucket/image.jpg")

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()


class TestPydanticModelHandling:
    """Tests for handling Pydantic model results."""

    def test_converts_pydantic_model_to_dict(self, mock_plugin_service, mock_storage):
        """Test that Pydantic models are converted to dicts."""
        from pydantic import BaseModel

        from app.ray_tasks import _execute_pipeline_impl

        class ToolResult(BaseModel):
            status: str
            count: int

        mock_plugin_service.run_plugin_tool.return_value = ToolResult(
            status="completed", count=42
        )

        result = _execute_pipeline_impl(
            plugin_id="test_plugin",
            tools_to_run=["test_tool"],
            input_path="image/test.jpg",
            job_type="image",
            get_plugin_service_fn=lambda: mock_plugin_service,
            get_storage_service_fn=lambda: mock_storage,
        )

        # Result should be a dict, not a Pydantic model
        assert isinstance(result["test_tool"], dict)
        assert result["test_tool"]["status"] == "completed"
        assert result["test_tool"]["count"] == 42
