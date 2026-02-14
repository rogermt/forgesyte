"""Tests for JobManagementService."""

import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.models_pydantic import JobStatus
from app.protocols import JobStore, TaskProcessor
from app.services.job_management_service import JobManagementService


class TestJobManagementService:
    """Test JobManagementService functionality."""

    @pytest.fixture
    def mock_store(self):
        store = Mock(spec=JobStore)
        return store

    @pytest.fixture
    def mock_processor(self):
        processor = Mock(spec=TaskProcessor)
        return processor

    @pytest.fixture
    def service(self, mock_store, mock_processor):
        return JobManagementService(store=mock_store, processor=mock_processor)

    @pytest.mark.asyncio
    async def test_get_job_status_found(self, service, mock_store):
        """Test getting job status when job exists."""
        job_data = {"job_id": "job1", "status": JobStatus.DONE}
        mock_store.get = AsyncMock(return_value=job_data)

        result = await service.get_job_status("job1")

        assert result == job_data
        mock_store.get.assert_called_once_with("job1")

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, service, mock_store):
        """Test getting job status when job does not exist."""
        mock_store.get = AsyncMock(return_value=None)

        result = await service.get_job_status("job1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_job_status_exception(self, service, mock_store):
        """Test exception handling in get_job_status."""
        mock_store.get = AsyncMock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception, match="DB Error"):
            await service.get_job_status("job1")

    @pytest.mark.asyncio
    async def test_list_jobs_success(self, service, mock_store):
        """Test listing jobs successfully."""
        jobs = [{"job_id": "job1"}, {"job_id": "job2"}]
        mock_store.list_jobs = AsyncMock(return_value=jobs)

        result = await service.list_jobs(status=JobStatus.DONE, limit=10)

        assert result == jobs
        mock_store.list_jobs.assert_called_once_with(
            status=JobStatus.DONE, plugin=None, limit=10
        )

    @pytest.mark.asyncio
    async def test_list_jobs_invalid_limit(self, service):
        """Test listing jobs with invalid limit."""
        with pytest.raises(ValueError):
            await service.list_jobs(limit=0)
        with pytest.raises(ValueError):
            await service.list_jobs(limit=201)

    @pytest.mark.asyncio
    async def test_list_jobs_exception(self, service, mock_store):
        """Test exception handling in list_jobs."""
        mock_store.list_jobs = AsyncMock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception, match="DB Error"):
            await service.list_jobs()

    @pytest.mark.asyncio
    async def test_cancel_job_success(self, service, mock_processor):
        """Test cancelling a job successfully."""
        mock_processor.cancel_job = AsyncMock(return_value=True)

        result = await service.cancel_job("job1")

        assert result is True
        mock_processor.cancel_job.assert_called_once_with("job1")

    @pytest.mark.asyncio
    async def test_cancel_job_failure(self, service, mock_processor):
        """Test cancelling a job failure."""
        mock_processor.cancel_job = AsyncMock(return_value=False)

        result = await service.cancel_job("job1")

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_job_exception(self, service, mock_processor):
        """Test exception handling in cancel_job."""
        mock_processor.cancel_job = AsyncMock(side_effect=Exception("Error"))

        with pytest.raises(Exception, match="Error"):
            await service.cancel_job("job1")
