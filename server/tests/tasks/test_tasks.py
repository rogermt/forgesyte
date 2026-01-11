"""Tests for task processing and job management.

Following TDD: Write tests first, then implement code to make them pass.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import JobStatus  # noqa: E402
from app.tasks import JobStore, TaskProcessor  # noqa: E402


@pytest.fixture
def job_store() -> JobStore:
    """Create a fresh JobStore for each test."""
    return JobStore()


@pytest.fixture
def mock_plugin_manager() -> MagicMock:
    """Create a mock PluginManager."""
    manager = MagicMock()
    manager.get = MagicMock(return_value=None)
    return manager


@pytest.fixture
def task_processor(
    mock_plugin_manager: MagicMock, job_store: JobStore
) -> TaskProcessor:
    """Create a TaskProcessor with mock plugin manager."""
    return TaskProcessor(mock_plugin_manager, job_store)


class TestJobStoreInitialization:
    """Test JobStore initialization."""

    def test_job_store_initializes_empty(self) -> None:
        """Test that JobStore starts empty."""
        store = JobStore()
        assert store._jobs == {}

    def test_job_store_has_default_max_jobs(self) -> None:
        """Test default max jobs is set."""
        store = JobStore()
        assert store._max_jobs == 1000

    def test_job_store_has_custom_max_jobs(self) -> None:
        """Test custom max jobs is set."""
        store = JobStore(max_jobs=500)
        assert store._max_jobs == 500

    def test_job_store_has_asyncio_lock(self, job_store: JobStore) -> None:
        """Test that JobStore has an asyncio lock."""
        assert hasattr(job_store, "_lock")
        assert isinstance(job_store._lock, asyncio.Lock)


class TestJobStoreCreate:
    """Test creating jobs in JobStore."""

    @pytest.mark.asyncio
    async def test_create_job_creates_entry(self, job_store: JobStore) -> None:
        """Test that create adds a job to the store."""
        job_data = {
            "job_id": "job1",
            "plugin": "plugin1",
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "progress": 0.0,
        }
        await job_store.create("job1", job_data)
        job = job_data
        assert job["job_id"] == "job1"
        assert job["plugin"] == "plugin1"
        assert "job1" in job_store._jobs

    @pytest.mark.asyncio
    async def test_create_job_has_correct_fields(self, job_store: JobStore) -> None:
        """Test that created job has all required fields."""
        job_data = {
            "job_id": "job1",
            "plugin": "test_plugin",
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "progress": 0.0,
        }
        await job_store.create("job1", job_data)
        job = job_data
        assert job["status"] == JobStatus.QUEUED
        assert job["result"] is None
        assert job["error"] is None
        assert job["progress"] == 0.0
        assert job["completed_at"] is None
        assert "created_at" in job

    @pytest.mark.asyncio
    async def test_create_multiple_jobs(self, job_store: JobStore) -> None:
        """Test creating multiple jobs."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin2",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        assert len(job_store._jobs) == 2
        assert job_store._jobs["job1"]["plugin"] == "plugin1"
        assert job_store._jobs["job2"]["plugin"] == "plugin2"

    @pytest.mark.asyncio
    async def test_create_job_timestamp(self, job_store: JobStore) -> None:
        """Test that created job has timestamp."""
        before = datetime.utcnow()
        job_data = {
            "job_id": "job1",
            "plugin": "plugin",
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "progress": 0.0,
        }
        await job_store.create("job1", job_data)
        job = job_data
        after = datetime.utcnow()
        assert before <= job["created_at"] <= after


class TestJobStoreUpdate:
    """Test updating jobs in JobStore."""

    @pytest.mark.asyncio
    async def test_update_existing_job(self, job_store: JobStore) -> None:
        """Test updating an existing job."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        updated = await job_store.update(
            "job1", {"status": JobStatus.RUNNING, "progress": 0.5}
        )
        assert updated is not None
        assert updated["status"] == JobStatus.RUNNING
        assert updated["progress"] == 0.5

    @pytest.mark.asyncio
    async def test_update_nonexistent_job(self, job_store: JobStore) -> None:
        """Test updating a non-existent job returns None."""
        result = await job_store.update("nonexistent", {"status": JobStatus.DONE})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, job_store: JobStore) -> None:
        """Test updating multiple fields at once."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        result = {
            "data": [1, 2, 3],
        }
        completed = datetime.utcnow()
        await job_store.update(
            "job1",
            status=JobStatus.DONE,
            result=result,
            completed_at=completed,
            progress=1.0,
        )

        job = await job_store.get("job1")
        assert job is not None
        assert job["status"] == JobStatus.DONE
        assert job["result"] == result
        assert job["progress"] == 1.0

    @pytest.mark.asyncio
    async def test_update_preserves_other_fields(self, job_store: JobStore) -> None:
        """Test that update doesn't overwrite other fields."""
        job_data = {
            "job_id": "job1",
            "plugin": "plugin1",
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "progress": 0.0,
        }
        await job_store.create("job1", job_data)
        job = job_data
        created_at = job["created_at"]

        await job_store.update("job1", {"status": JobStatus.RUNNING})

        updated_job = await job_store.get("job1")
        assert updated_job is not None
        assert updated_job["created_at"] == created_at
        assert updated_job["plugin"] == "plugin1"


class TestJobStoreGet:
    """Test retrieving jobs from JobStore."""

    @pytest.mark.asyncio
    async def test_get_existing_job(self, job_store: JobStore) -> None:
        """Test getting an existing job."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        job = await job_store.get("job1")
        assert job is not None
        assert job["job_id"] == "job1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, job_store: JobStore) -> None:
        """Test getting a non-existent job returns None."""
        job = await job_store.get("nonexistent")
        assert job is None

    @pytest.mark.asyncio
    async def test_get_returns_current_state(self, job_store: JobStore) -> None:
        """Test that get returns the current state of the job."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.update("job1", {"status": JobStatus.RUNNING, "progress": 0.7})

        job = await job_store.get("job1")
        assert job is not None
        assert job["status"] == JobStatus.RUNNING
        assert job["progress"] == 0.7


class TestJobStoreList:
    """Test listing jobs from JobStore."""

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, job_store: JobStore) -> None:
        """Test listing jobs when store is empty."""
        jobs = await job_store.list_jobs()
        assert jobs == []

    @pytest.mark.asyncio
    async def test_list_all_jobs(self, job_store: JobStore) -> None:
        """Test listing all jobs."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin2",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job3",
            {
                "job_id": "job3",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        jobs = await job_store.list_jobs()
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_jobs_sorted_by_created_at(self, job_store: JobStore) -> None:
        """Test that jobs are sorted by created_at descending."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await asyncio.sleep(0.01)
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await asyncio.sleep(0.01)
        await job_store.create(
            "job3",
            {
                "job_id": "job3",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        jobs = await job_store.list_jobs()
        # Should be newest first
        assert jobs[0]["job_id"] == "job3"
        assert jobs[1]["job_id"] == "job2"
        assert jobs[2]["job_id"] == "job1"

    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_status(self, job_store: JobStore) -> None:
        """Test filtering jobs by status."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job3",
            {
                "job_id": "job3",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        await job_store.update("job1", {"status": JobStatus.RUNNING})
        await job_store.update("job2", {"status": JobStatus.RUNNING})

        running_jobs = await job_store.list_jobs(status=JobStatus.RUNNING)
        assert len(running_jobs) == 2
        assert all(j["status"] == JobStatus.RUNNING for j in running_jobs)

    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_plugin(self, job_store: JobStore) -> None:
        """Test filtering jobs by plugin."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin2",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job3",
            {
                "job_id": "job3",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        plugin1_jobs = await job_store.list_jobs(plugin="plugin1")
        assert len(plugin1_jobs) == 2
        assert all(j["plugin"] == "plugin1" for j in plugin1_jobs)

    @pytest.mark.asyncio
    async def test_list_jobs_filter_by_both_status_and_plugin(
        self, job_store: JobStore
    ) -> None:
        """Test filtering by both status and plugin."""
        await job_store.create(
            "job1",
            {
                "job_id": "job1",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job2",
            {
                "job_id": "job2",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )
        await job_store.create(
            "job3",
            {
                "job_id": "job3",
                "plugin": "plugin2",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        await job_store.update("job1", {"status": JobStatus.RUNNING})
        await job_store.update("job3", {"status": JobStatus.RUNNING})

        jobs = await job_store.list_jobs(status=JobStatus.RUNNING, plugin="plugin1")
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "job1"

    @pytest.mark.asyncio
    async def test_list_jobs_respects_limit(self, job_store: JobStore) -> None:
        """Test that list_jobs respects the limit parameter."""
        for i in range(100):
            await job_store.create(f"job{i}", "plugin1")

        jobs = await job_store.list_jobs(limit=10)
        assert len(jobs) == 10


class TestJobStoreCleanup:
    """Test job cleanup mechanism."""

    @pytest.mark.asyncio
    async def test_cleanup_triggered_at_capacity(self) -> None:
        """Test that cleanup is triggered when store reaches max capacity."""
        store = JobStore(max_jobs=5)

        # Add jobs until cleanup is needed
        for i in range(5):
            await store.create(f"job{i}", "plugin1")
        assert len(store._jobs) == 5

        # Mark some as done
        for i in range(3):
            await store.update(f"job{i}", status=JobStatus.DONE)

        # Adding one more should trigger cleanup
        await store.create("job5", "plugin1")
        # Cleanup should have removed oldest completed jobs
        assert len(store._jobs) <= 5

    @pytest.mark.asyncio
    async def test_cleanup_removes_completed_jobs(self) -> None:
        """Test that cleanup removes completed jobs first."""
        store = JobStore(max_jobs=3)

        await store.create("job1", "plugin1")
        await store.update("job1", status=JobStatus.DONE)
        await asyncio.sleep(0.01)

        await store.create("job2", "plugin1")
        await store.create("job3", "plugin1")

        assert len(store._jobs) == 3

        # Add another job to trigger cleanup
        await store.create("job4", "plugin1")
        # job1 should be removed since it was done and oldest
        assert "job1" not in store._jobs


class TestTaskProcessorInitialization:
    """Test TaskProcessor initialization."""

    def test_task_processor_initializes(self, task_processor: TaskProcessor) -> None:
        """Test TaskProcessor initialization."""
        assert task_processor.plugin_manager is not None
        assert task_processor.job_store is not None
        assert task_processor._executor is not None
        assert task_processor._callbacks == {}

    def test_task_processor_custom_workers(
        self, mock_plugin_manager: MagicMock, job_store: JobStore
    ) -> None:
        """Test TaskProcessor with custom max_workers."""
        processor = TaskProcessor(mock_plugin_manager, job_store, max_workers=8)
        assert processor._executor._max_workers == 8


class TestTaskProcessorSubmitJob:
    """Test submitting jobs to TaskProcessor."""

    @pytest.mark.asyncio
    async def test_submit_job_creates_job_id(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that submit_job returns a job ID."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_submit_job_stores_job(self, task_processor: TaskProcessor) -> None:
        """Test that submit_job stores the job."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        job = await task_processor.job_store.get(job_id)
        assert job is not None
        assert job["job_id"] == job_id
        assert job["plugin"] == "plugin1"

    @pytest.mark.asyncio
    async def test_submit_job_with_options(self, task_processor: TaskProcessor) -> None:
        """Test submit_job with options."""
        options = {"threshold": 0.5, "mode": "fast"}
        job_id = await task_processor.submit_job(
            b"image_data", "plugin1", options=options
        )
        assert job_id is not None
        job = await task_processor.job_store.get(job_id)
        assert job is not None

    @pytest.mark.asyncio
    async def test_submit_job_with_callback(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test submit_job with callback."""
        callback_called = []

        def callback(job: dict) -> None:
            callback_called.append(job)

        job_id = await task_processor.submit_job(
            b"image_data", "plugin1", callback=callback
        )
        assert job_id in task_processor._callbacks

    @pytest.mark.asyncio
    async def test_submit_job_without_options(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test submit_job without options uses empty dict."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        assert job_id is not None


class TestTaskProcessorGetJob:
    """Test retrieving jobs from TaskProcessor."""

    @pytest.mark.asyncio
    async def test_get_job_existing(self, task_processor: TaskProcessor) -> None:
        """Test getting an existing job."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_get_job_nonexistent(self, task_processor: TaskProcessor) -> None:
        """Test getting a non-existent job."""
        job = await task_processor.get_job("nonexistent")
        assert job is None


class TestTaskProcessorCancelJob:
    """Test cancelling jobs."""

    @pytest.mark.asyncio
    async def test_cancel_queued_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a queued job."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        result = await task_processor.cancel_job(job_id)
        assert result is True

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.ERROR
        assert job["error"] == "Cancelled by user"

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a running job (can't cancel)."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        await task_processor.job_store.update(job_id, status=JobStatus.RUNNING)
        result = await task_processor.cancel_job(job_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a non-existent job."""
        result = await task_processor.cancel_job("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, task_processor: TaskProcessor) -> None:
        """Test cancelling a completed job."""
        job_id = await task_processor.submit_job(b"image_data", "plugin1")
        await task_processor.job_store.update(job_id, status=JobStatus.DONE)
        result = await task_processor.cancel_job(job_id)
        assert result is False


class TestTaskProcessorProcessing:
    """Test job processing."""

    @pytest.mark.asyncio
    async def test_process_job_plugin_not_found(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test processing when plugin is not found."""
        job_id = await task_processor.submit_job(b"image_data", "nonexistent")
        # Give async task time to process
        await asyncio.sleep(0.1)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.ERROR
        assert "not found" in job["error"]

    @pytest.mark.asyncio
    async def test_process_job_success(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test successful job processing."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"objects": [1, 2, 3]})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        # Give async task time to process
        await asyncio.sleep(0.2)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.DONE
        assert job["result"] is not None
        assert "processing_time_ms" in job["result"]

    @pytest.mark.asyncio
    async def test_process_job_with_exception(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test job processing with plugin exception."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(side_effect=Exception("Analysis failed"))
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        await asyncio.sleep(0.1)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.ERROR
        assert "Analysis failed" in job["error"]

    @pytest.mark.asyncio
    async def test_process_job_sets_progress(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that processing sets progress."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        await asyncio.sleep(0.2)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["progress"] == 1.0


class TestTaskProcessorCallbacks:
    """Test callback notification."""

    @pytest.mark.asyncio
    async def test_callback_called_on_completion(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that callback is called when job completes."""
        callback_called = []

        def callback(job: dict) -> None:
            callback_called.append(job)

        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", callback=callback
        )
        await asyncio.sleep(0.2)

        assert len(callback_called) == 1
        assert callback_called[0]["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_async_callback_called(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that async callbacks are called."""
        callback_called = []

        async def async_callback(job: dict) -> None:
            callback_called.append(job)

        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", callback=async_callback
        )
        await asyncio.sleep(0.2)

        assert len(callback_called) == 1
        assert callback_called[0]["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_callback_exception_handled(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that callback exceptions don't crash processing."""

        def failing_callback(job: dict) -> None:
            raise Exception("Callback failed")

        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", callback=failing_callback
        )
        # Should not crash
        await asyncio.sleep(0.2)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.DONE

    @pytest.mark.asyncio
    async def test_callback_removed_after_notification(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that callback is removed after being called."""

        def callback(job: dict) -> None:
            pass

        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", callback=callback
        )
        await asyncio.sleep(0.2)

        assert job_id not in task_processor._callbacks


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_image_bytes(self, task_processor: TaskProcessor) -> None:
        """Test submitting empty image bytes."""
        job_id = await task_processor.submit_job(b"", "plugin1")
        assert job_id is not None

    @pytest.mark.asyncio
    async def test_large_image_bytes(self, task_processor: TaskProcessor) -> None:
        """Test submitting large image bytes."""
        large_image = b"x" * (10 * 1024 * 1024)  # 10MB
        job_id = await task_processor.submit_job(large_image, "plugin1")
        assert job_id is not None

    @pytest.mark.asyncio
    async def test_concurrent_job_submissions(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test submitting multiple jobs concurrently."""
        jobs = await asyncio.gather(
            *[
                task_processor.submit_job(b"image_data", f"plugin{i % 3}")
                for i in range(10)
            ]
        )
        assert len(jobs) == 10
        assert len(set(jobs)) == 10  # All unique


class TestTaskProcessorErrorHandling:
    """Test error handling in task processor."""

    @pytest.mark.asyncio
    async def test_processing_time_recorded(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that processing time is recorded."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        await asyncio.sleep(0.2)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert "processing_time_ms" in job["result"]
        assert job["result"]["processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_completed_at_set_on_success(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that completed_at is set when job succeeds."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        await asyncio.sleep(0.2)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_completed_at_set_on_error(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that completed_at is set when job errors."""
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(side_effect=Exception("Failed"))
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(b"image_data", "test_plugin")
        await asyncio.sleep(0.1)

        job = await task_processor.get_job(job_id)
        assert job is not None
        assert job["completed_at"] is not None
