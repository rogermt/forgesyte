"""Integration tests for Ray job execution.

These tests verify the full Ray job flow with mocked Ray components.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.job import JobStatus


class MockRayObjectRef:
    """Mock Ray ObjectRef for testing."""

    def __init__(self, job_id: str):
        self.job_id = job_id

    def __hash__(self):
        return hash(self.job_id)

    def __eq__(self, other):
        if isinstance(other, MockRayObjectRef):
            return self.job_id == other.job_id
        return False


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    import tempfile
    from pathlib import Path

    storage = MagicMock()

    # Create a temp file for input
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"test_image_data")
        temp_path = Path(f.name)

    storage.load_file.return_value = temp_path
    storage.save_file.return_value = "image/output/test.json"

    yield storage

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_plugin_service():
    """Create a mock plugin service."""
    service = MagicMock()
    service.get_plugin_manifest.return_value = {
        "id": "test_plugin",
        "tools": [
            {"id": "test_tool", "inputs": ["image_bytes"], "description": "Test tool"}
        ],
    }
    service.run_plugin_tool.return_value = {"result": "success"}
    return service


class TestRayJobDispatch:
    """Tests for Ray job dispatch functionality."""

    def test_dispatches_to_ray_when_enabled(self, mock_storage, mock_plugin_service):
        """Test that jobs are dispatched to Ray when use_ray=True."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=mock_storage,
            plugin_service=mock_plugin_service,
            use_ray=True,
        )

        mock_ray = MagicMock()
        mock_ref = MockRayObjectRef("test-job-id")
        mock_ray.wait.return_value = ([], [])

        mock_execute = MagicMock()
        mock_execute.remote.return_value = mock_ref

        mock_job = MagicMock()
        mock_job.job_id = "test-job-id"
        mock_job.plugin_id = "test_plugin"
        mock_job.tool = "test_tool"
        mock_job.tool_list = None
        mock_job.job_type = "image"
        mock_job.input_path = "image/input/test.jpg"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_job
        )

        worker._session_factory = lambda: mock_db

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch("app.ray_tasks.execute_pipeline_remote", mock_execute):
                worker.run_once()

        # Verify dispatch happened
        mock_execute.remote.assert_called_once()
        assert len(worker.active_futures) == 1
        assert "test-job-id" in worker.job_metadata

    def test_no_dispatch_when_at_limit(self, mock_storage, mock_plugin_service):
        """Test that no new jobs dispatch when at concurrency limit."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=mock_storage,
            plugin_service=mock_plugin_service,
            use_ray=True,
        )

        # Pre-populate at limit
        ref1 = MockRayObjectRef("job-1")
        ref2 = MockRayObjectRef("job-2")
        worker.active_futures[ref1] = "job-1"
        worker.active_futures[ref2] = "job-2"

        mock_ray = MagicMock()
        mock_ray.wait.return_value = ([], [])

        mock_execute = MagicMock()

        mock_db = MagicMock()

        worker._session_factory = lambda: mock_db

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch("app.ray_tasks.execute_pipeline_remote", mock_execute):
                worker.run_once()

        mock_execute.remote.assert_not_called()


class TestRayJobFinalization:
    """Tests for Ray job finalization."""

    def test_finalize_job_saves_results(self, mock_storage):
        """Test that _finalize_job saves results correctly."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,
        )

        mock_job = MagicMock()
        mock_job.job_id = "test-job-id"
        mock_job.job_type = "image"
        mock_job.plugin_id = "test_plugin"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        meta = {
            "tools_to_run": ["test_tool"],
            "is_multi": False,
        }
        results = {"test_tool": {"result": "success"}}

        worker._session_factory = lambda: mock_db
        worker._finalize_job("test-job-id", meta, results)

        mock_storage.save_file.assert_called_once()
        assert mock_job.status == JobStatus.completed

    def test_finalize_video_job_flattens(self, mock_storage):
        """Test that video jobs are flattened for UI."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,
        )

        mock_job = MagicMock()
        mock_job.job_id = "video-job-id"
        mock_job.job_type = "video"
        mock_job.plugin_id = "test_plugin"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        meta = {
            "tools_to_run": ["video_tool"],
            "is_multi": False,
        }
        results = {
            "video_tool": {
                "frames": [{"frame": 1}, {"frame": 2}],
                "total_frames": 2,
            }
        }

        worker._session_factory = lambda: mock_db
        worker._finalize_job("video-job-id", meta, results)

        # Verify save_file was called
        assert mock_storage.save_file.called
        assert mock_job.progress == 100


class TestRayJobFailure:
    """Tests for Ray job failure handling."""

    def test_fail_job_marks_failed(self):
        """Test that _fail_job marks job as failed."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=MagicMock(),
            plugin_service=MagicMock(),
            use_ray=True,
        )

        mock_job = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        worker._session_factory = lambda: mock_db
        worker._fail_job("failing-job-id", "GPU out of memory")

        assert mock_job.status == JobStatus.failed
        assert mock_job.error_message == "GPU out of memory"
        mock_db.commit.assert_called()


class TestSynchronousFallback:
    """Tests for synchronous fallback when Ray is disabled."""

    def test_synchronous_mode_uses_run_once_sync(self):
        """Test that synchronous mode uses _run_once_sync method."""
        from unittest.mock import patch

        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=MagicMock(),
            plugin_service=MagicMock(),
            use_ray=False,
        )

        # Verify use_ray is False
        assert worker._use_ray is False

        # Exercise run_once() and verify it delegates to _run_once_sync()
        with patch.object(worker, "_run_once_sync", return_value=True) as mock_run_once_sync:
            assert worker.run_once() is True
            mock_run_once_sync.assert_called_once()
