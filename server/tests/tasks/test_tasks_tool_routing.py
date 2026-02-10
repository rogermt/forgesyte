"""TDD tests for tool routing fix in TaskProcessor.

Verifies that tasks.py warns when tool is missing from options.
"""

import base64
import logging
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.models import JobStatus
from app.tasks import JobStore, TaskProcessor


class TestTaskToolRoutingWarning:
    """Test that TaskProcessor warns when tool missing from options."""

    @pytest.fixture
    def job_store(self):
        return JobStore()

    @pytest.fixture
    def mock_plugin_manager(self):
        manager = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.tools = {
            "player_detection": {"description": "Detect players"},
            "ball_detection": {"description": "Detect ball"},
        }
        mock_plugin.run_tool.return_value = {"detections": []}
        manager.get.return_value = mock_plugin
        return manager

    @pytest.fixture
    def processor(self, mock_plugin_manager, job_store):
        return TaskProcessor(mock_plugin_manager, job_store)

    @pytest.mark.asyncio
    async def test_warns_when_tool_missing_from_options(
        self, processor, job_store, caplog
    ):
        """When options omit tool, should log warning and default to first tool."""
        job_id = "job-no-tool"
        await job_store.create(
            job_id,
            {
                "job_id": job_id,
                "plugin": "yolo",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        image_bytes = base64.b64decode(
            base64.b64encode(b"fake-image")
        )
        options_without_tool = {"device": "cpu"}

        with caplog.at_level(logging.WARNING):
            await processor._process_job(
                job_id, "yolo", image_bytes, options_without_tool
            )

        assert any(
            "missing" in r.message.lower() and "tool" in r.message.lower()
            for r in caplog.records
        ), f"Expected warning about missing tool, got: {[r.message for r in caplog.records]}"

    @pytest.mark.asyncio
    async def test_no_warning_when_tool_provided(
        self, processor, job_store, caplog
    ):
        """When options include tool, should NOT log missing-tool warning."""
        job_id = "job-with-tool"
        await job_store.create(
            job_id,
            {
                "job_id": job_id,
                "plugin": "yolo",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        image_bytes = b"fake-image"
        options_with_tool = {"tool": "ball_detection", "device": "cpu"}

        with caplog.at_level(logging.WARNING):
            await processor._process_job(
                job_id, "yolo", image_bytes, options_with_tool
            )

        missing_tool_warnings = [
            r for r in caplog.records
            if "missing" in r.message.lower() and "tool" in r.message.lower()
        ]
        assert len(missing_tool_warnings) == 0
