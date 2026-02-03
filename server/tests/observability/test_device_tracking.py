"""Tests for device usage tracking and observability logging."""

from unittest.mock import MagicMock

import pytest


class TestDeviceTracking:
    """Tests for DeviceTracker observability."""

    @pytest.mark.asyncio
    async def test_log_device_usage_cpu(self) -> None:
        """Verify CPU device usage is logged correctly."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_db.execute = MagicMock()
        tracker = DeviceTracker(mock_db)

        await tracker.log_device_usage(
            job_id="job-123",
            device_requested="cpu",
            device_used="cpu",
        )

        # Verify execute was called
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_log_device_usage_gpu_fallback(self) -> None:
        """Verify GPU→CPU fallback is detected and logged."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_db.execute = MagicMock()
        tracker = DeviceTracker(mock_db)

        await tracker.log_device_usage(
            job_id="job-456",
            device_requested="gpu",
            device_used="cpu",
        )

        # Verify fallback=True was passed
        call_args = mock_db.execute.call_args
        assert call_args is not None
        # Third positional arg should be the values list with fallback=True
        values = call_args[0][1]
        assert values[4] is True  # fallback flag

    @pytest.mark.asyncio
    async def test_log_device_usage_gpu_success(self) -> None:
        """Verify GPU usage without fallback is logged correctly."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_db.execute = MagicMock()
        tracker = DeviceTracker(mock_db)

        await tracker.log_device_usage(
            job_id="job-789",
            device_requested="gpu",
            device_used="gpu",
        )

        # Verify fallback=False was passed
        call_args = mock_db.execute.call_args
        assert call_args is not None
        values = call_args[0][1]
        assert values[4] is False  # no fallback

    @pytest.mark.asyncio
    async def test_log_device_usage_case_insensitive(self) -> None:
        """Verify device names are normalized to lowercase."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_db.execute = MagicMock()
        tracker = DeviceTracker(mock_db)

        await tracker.log_device_usage(
            job_id="job-999",
            device_requested="GPU",
            device_used="CPU",
        )

        # Verify values are normalized
        call_args = mock_db.execute.call_args
        assert call_args is not None
        values = call_args[0][1]
        assert values[2] == "gpu"  # device_requested
        assert values[3] == "cpu"  # device_used

    @pytest.mark.asyncio
    async def test_get_device_stats(self) -> None:
        """Verify device statistics are calculated correctly."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[(10, 7, 3, 1)])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 10
        assert stats["cpu_jobs"] == 7
        assert stats["gpu_jobs"] == 3
        assert stats["fallback_count"] == 1
        assert stats["gpu_success_rate"] == pytest.approx(66.67, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_device_stats_no_gpu(self) -> None:
        """Verify stats when no GPU jobs exist."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[(5, 5, 0, 0)])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 5
        assert stats["cpu_jobs"] == 5
        assert stats["gpu_jobs"] == 0
        assert stats["fallback_count"] == 0
        assert stats["gpu_success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_device_stats_empty(self) -> None:
        """Verify stats return defaults when table is empty."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 0
        assert stats["cpu_jobs"] == 0
        assert stats["gpu_jobs"] == 0
        assert stats["fallback_count"] == 0
        assert stats["gpu_success_rate"] == 0.0
