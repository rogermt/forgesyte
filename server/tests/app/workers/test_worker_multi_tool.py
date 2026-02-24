"""Tests for v0.9.4 multi-tool worker execution.

Tests verify:
1. Worker detects image_multi job type
2. Worker executes tools sequentially via plugin_service.run_plugin_tool()
3. Worker aggregates results into {"plugin_id": ..., "tools": {...}} format
4. Worker preserves tool execution order
5. Worker fail-fast: one tool failure fails entire job
6. Single-tool jobs still use old format {"results": ...}
"""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
from app.workers.worker import JobWorker


@pytest.fixture
def multi_tool_job_setup(test_engine, session):
    """Create a multi-tool job in the database."""
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="yolo-tracker",
        tool=None,
        tool_list=json.dumps(["player_detection", "ball_detection"]),
        input_path="image/input/test.png",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()
    return job_id


class TestMultiToolWorkerExecution:
    """Tests for multi-tool worker execution."""

    @pytest.mark.unit
    def test_worker_detects_image_multi_job_type(self, test_engine, session):
        """Test that worker detects job_type='image_multi' and processes tool_list."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create multi-tool job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="yolo-tracker",
            tool=None,
            tool_list=json.dumps(["t1", "t2"]),
            input_path="image/input/test.png",
            job_type="image_multi",
        )
        session.add(job)
        session.commit()

        # Setup mocks
        mock_storage.load_file.return_value = "/data/test.png"
        mock_storage.save_file.return_value = "image_multi/output/test.json"

        # Mock manifest with tools
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [
                {"id": "t1", "inputs": ["image_bytes"]},
                {"id": "t2", "inputs": ["image_bytes"]},
            ]
        }

        # Mock tool execution results
        mock_plugin_service.run_plugin_tool.side_effect = [
            {"detections": ["player1"]},
            {"detections": ["ball1"]},
        ]

        # Run worker
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            )
            result = worker.run_once()

        assert result is True

        # Verify job completed
        session.expire_all()
        updated_job = session.query(Job).filter(Job.job_id == job_id).first()
        assert updated_job.status == JobStatus.completed

    @pytest.mark.unit
    def test_worker_executes_tools_sequentially(self, test_engine, session):
        """Test that worker executes tools in order via run_plugin_tool()."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create multi-tool job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test-plugin",
            tool=None,
            tool_list=json.dumps(["tool_a", "tool_b", "tool_c"]),
            input_path="image/input/test.png",
            job_type="image_multi",
        )
        session.add(job)
        session.commit()

        # Setup mocks
        mock_storage.load_file.return_value = "/data/test.png"
        mock_storage.save_file.return_value = "image_multi/output/test.json"
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [
                {"id": "tool_a", "inputs": ["image_bytes"]},
                {"id": "tool_b", "inputs": ["image_bytes"]},
                {"id": "tool_c", "inputs": ["image_bytes"]},
            ]
        }

        # Track call order
        call_order = []

        def track_run_tool(plugin_id, tool_name, args, progress_callback=None):
            call_order.append(tool_name)
            return {"result": f"{tool_name}_output"}

        mock_plugin_service.run_plugin_tool.side_effect = track_run_tool

        # Run worker
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            )
            worker.run_once()

        # Verify tools executed in correct order
        assert call_order == ["tool_a", "tool_b", "tool_c"]

    @pytest.mark.unit
    def test_worker_aggregates_results_for_multi_tool(self, test_engine, session):
        """Test that worker aggregates results into tools dict."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create multi-tool job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test-plugin",
            tool=None,
            tool_list=json.dumps(["t1", "t2"]),
            input_path="image/input/test.png",
            job_type="image_multi",
        )
        session.add(job)
        session.commit()

        # Setup mocks
        mock_storage.load_file.return_value = "/data/test.png"
        mock_storage.save_file.return_value = "image_multi/output/test.json"
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [
                {"id": "t1", "inputs": ["image_bytes"]},
                {"id": "t2", "inputs": ["image_bytes"]},
            ]
        }

        mock_plugin_service.run_plugin_tool.side_effect = [
            {"detections": [1, 2, 3]},
            {"detections": [4, 5, 6]},
        ]

        saved_output = None

        def capture_save(src, dest_path):
            nonlocal saved_output
            saved_output = src.read()
            return dest_path

        mock_storage.save_file.side_effect = capture_save

        # Run worker
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            )
            worker.run_once()

        # Verify output format
        assert saved_output is not None
        output_data = json.loads(saved_output)

        # Multi-tool format: {"plugin_id": ..., "tools": {...}}
        assert "plugin_id" in output_data
        assert output_data["plugin_id"] == "test-plugin"
        assert "tools" in output_data
        assert "t1" in output_data["tools"]
        assert "t2" in output_data["tools"]
        assert output_data["tools"]["t1"]["detections"] == [1, 2, 3]
        assert output_data["tools"]["t2"]["detections"] == [4, 5, 6]

    @pytest.mark.unit
    def test_worker_single_tool_uses_old_format(self, test_engine, session):
        """Test that single-tool jobs still use old output format."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create single-tool job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test-plugin",
            tool="analyze",
            tool_list=None,
            input_path="image/input/test.png",
            job_type="image",
        )
        session.add(job)
        session.commit()

        # Setup mocks
        mock_storage.load_file.return_value = "/data/test.png"
        mock_storage.save_file.return_value = "image/output/test.json"
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [{"id": "analyze", "inputs": ["image_bytes"]}]
        }

        mock_plugin_service.run_plugin_tool.return_value = {"text": "extracted text"}

        saved_output = None

        def capture_save(src, dest_path):
            nonlocal saved_output
            saved_output = src.read()
            return dest_path

        mock_storage.save_file.side_effect = capture_save

        # Run worker
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            )
            worker.run_once()

        # Verify output format - single tool uses old format
        assert saved_output is not None
        output_data = json.loads(saved_output)
        assert "results" in output_data
        assert output_data["results"]["text"] == "extracted text"

    @pytest.mark.unit
    def test_worker_fail_fast_on_tool_error(self, test_engine, session):
        """Test that worker fails entire job if any tool fails (fail-fast)."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create multi-tool job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="test-plugin",
            tool=None,
            tool_list=json.dumps(["t1", "t2", "t3"]),
            input_path="image/input/test.png",
            job_type="image_multi",
        )
        session.add(job)
        session.commit()

        # Setup mocks
        mock_storage.load_file.return_value = "/data/test.png"
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [
                {"id": "t1", "inputs": ["image_bytes"]},
                {"id": "t2", "inputs": ["image_bytes"]},
                {"id": "t3", "inputs": ["image_bytes"]},
            ]
        }

        # t1 succeeds, t2 fails
        call_count = [0]

        def run_tool_with_failure(plugin_id, tool_name, args, progress_callback=None):
            call_count[0] += 1
            if tool_name == "t1":
                return {"result": "ok"}
            elif tool_name == "t2":
                raise ValueError("Tool t2 failed")
            # t3 should never be called
            return {"result": "t3"}

        mock_plugin_service.run_plugin_tool.side_effect = run_tool_with_failure

        # Run worker
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            )
            result = worker.run_once()

        assert result is False

        # Verify job failed
        session.expire_all()
        updated_job = session.query(Job).filter(Job.job_id == job_id).first()
        assert updated_job.status == JobStatus.failed
        assert "t2 failed" in updated_job.error_message

        # Verify t3 was never called (fail-fast)
        assert call_count[0] == 2  # Only t1 and t2 were called
