"""Tests for JobWorker Ray integration.

These tests verify the JobWorker's ability to dispatch jobs to Ray
and poll for completion.
"""

from unittest.mock import MagicMock, patch

import pytest


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


class TestJobWorkerRayDispatch:
    """Tests for JobWorker Ray dispatch functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_job(self):
        """Create a mock Job model."""
        import uuid

        from app.models.job import Job, JobStatus

        job = MagicMock(spec=Job)
        job.job_id = uuid.uuid4()
        job.status = JobStatus.pending
        job.plugin_id = "test_plugin"
        job.tool = "test_tool"
        job.tool_list = None
        job.input_path = "image/test.jpg"
        job.job_type = "image"
        job.output_path = None
        job.error_message = None
        job.progress = None
        return job

    @pytest.fixture
    def mock_storage(self):
        """Create a mock StorageService."""
        storage = MagicMock()
        storage.save_file.return_value = "image/output/test-job-id.json"
        return storage

    def test_worker_has_ray_state_tracking(self):
        """Test that JobWorker has active_futures and job_metadata tracking."""
        from app.workers.worker import JobWorker

        worker = JobWorker(storage=MagicMock(), plugin_service=MagicMock())

        assert hasattr(worker, "active_futures")
        assert hasattr(worker, "job_metadata")
        assert isinstance(worker.active_futures, dict)
        assert isinstance(worker.job_metadata, dict)

    def test_dispatches_job_to_ray(self, mock_job, mock_storage):
        """Test that worker dispatches jobs to Ray when use_ray=True."""
        from app.workers.worker import JobWorker

        # Create worker with Ray enabled
        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,  # Enable Ray mode
        )

        # Mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_job
        )
        mock_db.query.return_value.filter.return_value.update.return_value = 1

        worker._session_factory = lambda: mock_db

        # Mock Ray
        mock_ref = MockRayObjectRef(str(mock_job.job_id))

        with patch("ray.wait", return_value=([], [])):
            with patch("ray.ObjectRef", MockRayObjectRef):
                # Patch execute_pipeline_remote at the module level
                with patch("app.ray_tasks.execute_pipeline_remote") as mock_execute:
                    mock_execute.remote.return_value = mock_ref

                    # Run once
                    worker.run_once()

        # Verify job was dispatched
        mock_execute.remote.assert_called_once()
        assert len(worker.active_futures) == 1
        assert str(mock_job.job_id) in worker.job_metadata

    def test_polls_ray_futures(self, mock_job, mock_storage):
        """Test that worker polls active Ray futures."""
        from app.workers.worker import JobWorker

        # Create worker with Ray enabled
        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,  # Enable Ray mode
        )

        # Setup TWO existing futures - this puts us at the concurrency limit
        # so no new jobs will be dispatched after polling one
        mock_ref1 = MockRayObjectRef(str(mock_job.job_id))
        mock_ref2 = MockRayObjectRef("another_job_id")
        worker.active_futures[mock_ref1] = str(mock_job.job_id)
        worker.active_futures[mock_ref2] = "another_job_id"
        worker.job_metadata[str(mock_job.job_id)] = {
            "plugin_id": "test_plugin",
            "job_type": "image",
            "tools_to_run": ["test_tool"],
            "is_multi": False,
        }
        worker.job_metadata["another_job_id"] = {
            "plugin_id": "test_plugin",
            "job_type": "image",
            "tools_to_run": ["test_tool"],
            "is_multi": False,
        }

        # Mock database for finalize
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        worker._session_factory = lambda: mock_db

        # Create mock ray module
        mock_ray = MagicMock()
        mock_ray.wait.return_value = ([mock_ref1], [mock_ref2])
        mock_ray.get.return_value = {"test_tool": {"result": "success"}}

        # Create mock execute_pipeline_remote
        mock_execute = MagicMock()

        # Patch the imports inside run_once
        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch("app.ray_tasks.execute_pipeline_remote", mock_execute):
                # Run once - should poll ref1 and finalize it
                worker.run_once()

        # Verify ref1 was cleaned up but ref2 is still there
        assert mock_ref1 not in worker.active_futures
        assert mock_ref2 in worker.active_futures
        assert str(mock_job.job_id) not in worker.job_metadata

    def test_finalize_job_saves_results(self, mock_job, mock_storage):
        """Test that _finalize_job saves results correctly."""
        from app.models.job import JobStatus
        from app.workers.worker import JobWorker

        worker = JobWorker(storage=mock_storage, plugin_service=MagicMock())

        # Mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        worker._session_factory = lambda: mock_db

        meta = {
            "plugin_id": "test_plugin",
            "job_type": "image",
            "tools_to_run": ["test_tool"],
            "is_multi": False,
        }
        results = {"test_tool": {"result": "success"}}

        # Call _finalize_job
        worker._finalize_job(str(mock_job.job_id), meta, results)

        # Verify storage was called
        mock_storage.save_file.assert_called_once()

        # Verify job was marked completed
        assert mock_job.status == JobStatus.completed
        assert mock_job.output_path is not None
        mock_db.commit.assert_called()

    def test_finalize_video_job_flattens_results(self, mock_storage):
        """Test that _finalize_job flattens video results correctly."""
        import uuid

        from app.models.job import Job, JobStatus
        from app.workers.worker import JobWorker

        worker = JobWorker(storage=mock_storage, plugin_service=MagicMock())

        # Create video job
        job = MagicMock(spec=Job)
        job.job_id = uuid.uuid4()
        job.job_type = "video"
        job.plugin_id = "yolo"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = job
        worker._session_factory = lambda: mock_db

        meta = {
            "plugin_id": "yolo",
            "job_type": "video",
            "tools_to_run": ["player_detector"],
            "is_multi": False,
        }
        results = {
            "player_detector": {
                "frames": [{"frame": 1, "detections": []}],
                "total_frames": 1,
            }
        }

        worker._finalize_job(str(job.job_id), meta, results)

        # Verify progress was set to 100
        assert job.progress == 100
        assert job.status == JobStatus.completed

    def test_fail_job_marks_failed(self, mock_job):
        """Test that _fail_job marks job as failed."""
        from app.models.job import JobStatus
        from app.workers.worker import JobWorker

        worker = JobWorker(storage=MagicMock(), plugin_service=MagicMock())

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        worker._session_factory = lambda: mock_db

        worker._fail_job(str(mock_job.job_id), "Test error message")

        assert mock_job.status == JobStatus.failed
        assert mock_job.error_message == "Test error message"
        mock_db.commit.assert_called()

    def test_limits_concurrent_jobs(self, mock_job, mock_storage):
        """Test that worker limits concurrent Ray jobs to avoid OOM."""
        from app.workers.worker import JobWorker

        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,  # Enable Ray mode to test concurrency limit
        )

        # Simulate 2 active futures (at limit)
        for i in range(2):
            ref = MockRayObjectRef(f"job_{i}")
            worker.active_futures[ref] = f"job_{i}"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_job
        )
        worker._session_factory = lambda: mock_db

        with patch("ray.wait", return_value=([], [])):
            with patch("app.ray_tasks.execute_pipeline_remote") as mock_execute:
                # Run once
                worker.run_once()

        # Should NOT dispatch new job since at limit
        mock_execute.remote.assert_not_called()

    def test_handles_ray_task_exception(self, mock_job, mock_storage):
        """Test that Ray task exceptions are handled properly."""
        from app.models.job import JobStatus
        from app.workers.worker import JobWorker

        # Create worker with Ray enabled
        worker = JobWorker(
            storage=mock_storage,
            plugin_service=MagicMock(),
            use_ray=True,  # Enable Ray mode
        )

        # Setup existing future
        mock_ref = MockRayObjectRef(str(mock_job.job_id))
        worker.active_futures[mock_ref] = str(mock_job.job_id)
        worker.job_metadata[str(mock_job.job_id)] = {
            "plugin_id": "test_plugin",
            "job_type": "image",
            "tools_to_run": ["test_tool"],
            "is_multi": False,
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        worker._session_factory = lambda: mock_db

        with patch("ray.wait", return_value=([mock_ref], [])):
            with patch("ray.get", side_effect=RuntimeError("Ray task failed")):
                with patch("app.ray_tasks.execute_pipeline_remote"):
                    # Run once - should handle exception
                    worker.run_once()

        # Verify job was marked failed
        assert mock_job.status == JobStatus.failed
        assert "Ray task failed" in mock_job.error_message


class TestJobWorkerBackwardCompatibility:
    """Tests for backward compatibility with non-Ray execution."""

    def test_worker_still_supports_synchronous_fallback(self):
        """Test that worker can still run synchronously if Ray not available."""
        from app.workers.worker import JobWorker

        # Worker should initialize even without Ray
        worker = JobWorker(storage=MagicMock(), plugin_service=MagicMock())

        # Should have Ray state tracking (empty initially)
        assert worker.active_futures == {}
        assert worker.job_metadata == {}

    def test_worker_uses_injected_storage(self):
        """Test that worker uses injected storage service."""
        from app.workers.worker import JobWorker

        mock_storage = MagicMock()
        worker = JobWorker(storage=mock_storage, plugin_service=MagicMock())

        # Check the private attribute
        assert worker._storage == mock_storage

    def test_worker_uses_injected_plugin_service(self):
        """Test that worker uses injected plugin service."""
        from app.workers.worker import JobWorker

        mock_plugin = MagicMock()
        worker = JobWorker(storage=MagicMock(), plugin_service=mock_plugin)

        # Check the private attribute
        assert worker._plugin_service == mock_plugin
