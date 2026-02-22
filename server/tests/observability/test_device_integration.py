"""Integration tests for device tracking in job pipeline.

Tests full flow: job submission → execution → device usage logging.
"""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest


def _plugins_available():
    """Check if plugins are available in the environment."""
    from app.plugin_loader import PluginRegistry

    plugin_manager = PluginRegistry()
    load_result = plugin_manager.load_plugins()
    loaded_list = list(load_result.get("loaded", {}).keys())
    return len(loaded_list) > 0


class TestDeviceIntegration:
    """Integration tests for device selector with observability."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _plugins_available(),
        reason="No plugins available (forgesyte-plugins not installed)",
    )
    async def test_job_submission_with_device_param(self, client) -> None:
        """Verify job submission with plugin parameter works end-to-end."""
        # Encode test PNG bytes as base64
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        image_base64 = base64.b64encode(png_bytes).decode("utf-8")

        response = await client.post(
            "/v1/analyze-execution",
            json={
                "plugin": "ocr",
                "image": image_base64,
                "mime_type": "image/png",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"]
        assert data["plugin"] == "ocr"

    @pytest.mark.asyncio
    async def test_device_tracking_called_on_job_completion(self) -> None:
        """Verify device tracker is called when job completes."""
        from app.tasks import TaskProcessor

        # Create mocks
        mock_plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(
            return_value={
                "boxes": [],
                "scores": [],
                "labels": [],
            }
        )
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        mock_job_store = MagicMock()
        mock_job_store.get = AsyncMock(
            return_value={
                "job_id": "test-job",
                "device_requested": "cpu",
                "status": "running",
            }
        )
        mock_job_store.update = AsyncMock()

        mock_device_tracker = MagicMock()
        mock_device_tracker.log_device_usage = AsyncMock()

        # Create processor with mocks
        processor = TaskProcessor(
            plugin_manager=mock_plugin_manager,
            job_store=mock_job_store,
            device_tracker=mock_device_tracker,
        )

        # Process job
        await processor._process_job(
            job_id="test-job",
            image_bytes=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            plugin_name="ocr",
            options={"tool": "ocr"},
            device_requested="cpu",
        )

        # Verify device tracker was called
        assert mock_device_tracker.log_device_usage.called
        call_args = mock_device_tracker.log_device_usage.call_args
        assert call_args[1]["job_id"] == "test-job"
        assert call_args[1]["device_requested"] == "cpu"
        assert call_args[1]["device_used"] == "cpu"

    @pytest.mark.asyncio
    async def test_device_used_stored_in_job_result(self) -> None:
        """Verify device_used is stored in job after completion."""
        from app.models_pydantic import JobStatus
        from app.tasks import TaskProcessor

        # Create mocks
        mock_plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(
            return_value={
                "boxes": [],
                "scores": [],
                "labels": [],
            }
        )
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        updates = {}

        async def mock_update(job_id, updates_dict):
            updates.update(updates_dict)

        mock_job_store = MagicMock()
        mock_job_store.get = AsyncMock(
            return_value={
                "job_id": "test-job",
                "device_requested": "cpu",
            }
        )
        mock_job_store.update = mock_update

        mock_device_tracker = MagicMock()
        mock_device_tracker.log_device_usage = AsyncMock()

        processor = TaskProcessor(
            plugin_manager=mock_plugin_manager,
            job_store=mock_job_store,
            device_tracker=mock_device_tracker,
        )

        # Process job
        await processor._process_job(
            job_id="test-job",
            image_bytes=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            plugin_name="ocr",
            options={"tool": "ocr"},
            device_requested="cpu",
        )

        # Verify device_used was stored
        assert updates["device_used"] == "cpu"
        assert updates["status"] == JobStatus.DONE

    @pytest.mark.asyncio
    async def test_device_tracker_failure_doesnt_block_job(self) -> None:
        """Verify job completes even if device tracker fails."""
        from app.models_pydantic import JobStatus
        from app.tasks import TaskProcessor

        # Create mocks
        mock_plugin_manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.analyze = MagicMock(
            return_value={
                "boxes": [],
                "scores": [],
                "labels": [],
            }
        )
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_updated = False

        async def mock_update(job_id, updates_dict):
            nonlocal job_updated
            if updates_dict.get("status") == JobStatus.DONE:
                job_updated = True

        mock_job_store = MagicMock()
        mock_job_store.get = AsyncMock(
            return_value={
                "job_id": "test-job",
                "device_requested": "cpu",
            }
        )
        mock_job_store.update = mock_update

        # Device tracker that raises exception
        mock_device_tracker = MagicMock()
        mock_device_tracker.log_device_usage = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        processor = TaskProcessor(
            plugin_manager=mock_plugin_manager,
            job_store=mock_job_store,
            device_tracker=mock_device_tracker,
        )

        # Process job — should not raise exception
        await processor._process_job(
            job_id="test-job",
            image_bytes=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            plugin_name="ocr",
            options={"tool": "ocr"},
            device_requested="cpu",
        )

        # Job should still be marked as DONE
        assert job_updated


class TestDeviceStatistics:
    """Tests for device statistics queries."""

    @pytest.mark.asyncio
    async def test_device_stats_all_cpu(self) -> None:
        """Verify statistics when all jobs use CPU."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[(10, 10, 0, 0)])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 10
        assert stats["cpu_jobs"] == 10
        assert stats["gpu_jobs"] == 0
        assert stats["fallback_count"] == 0
        assert stats["gpu_success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_device_stats_mixed(self) -> None:
        """Verify statistics with mixed CPU/GPU usage."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        # total=20, cpu=12, gpu=8, fallback=3
        mock_result.fetchall = MagicMock(return_value=[(20, 12, 8, 3)])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 20
        assert stats["cpu_jobs"] == 12
        assert stats["gpu_jobs"] == 8
        assert stats["fallback_count"] == 3
        # GPU success rate = (8-3) / 8 * 100 = 62.5%
        assert stats["gpu_success_rate"] == pytest.approx(62.5, abs=0.1)

    @pytest.mark.asyncio
    async def test_device_stats_all_gpu_no_fallback(self) -> None:
        """Verify statistics when all GPU jobs succeed (no fallback)."""
        from app.observability.device_tracking import DeviceTracker

        mock_db = MagicMock()
        mock_result = MagicMock()
        # total=10, cpu=0, gpu=10, fallback=0
        mock_result.fetchall = MagicMock(return_value=[(10, 0, 10, 0)])
        mock_db.execute = MagicMock(return_value=mock_result)

        tracker = DeviceTracker(mock_db)
        stats = await tracker.get_device_stats()

        assert stats["total_jobs"] == 10
        assert stats["cpu_jobs"] == 0
        assert stats["gpu_jobs"] == 10
        assert stats["fallback_count"] == 0
        assert stats["gpu_success_rate"] == 100.0
