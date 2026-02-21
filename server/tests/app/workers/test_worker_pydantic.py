"""Tests for worker handling of Pydantic model results (Issue #210).

The worker's json.dumps() crashes when run_plugin_tool returns a Pydantic model
instead of a plain dict. This test verifies the fix handles both cases.
"""

import json
from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from app.models.job import Job, JobStatus
from app.workers.worker import JobWorker


class MockOCROutput(BaseModel):
    """Mock Pydantic model simulating OCROutput from forgesyte-ocr."""

    text: str
    confidence: float = 0.95


class TestWorkerPydanticSerialization:
    """Tests for Issue #210: Worker json.dumps crash on Pydantic model."""

    @pytest.mark.unit
    def test_worker_handles_pydantic_model_result(self, test_engine, session):
        """Test that worker can serialize Pydantic model results."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create pending job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="ocr",
            tool="extract_text",
            input_path="image/input/test.png",
            job_type="image",
        )
        session.add(job)
        session.commit()

        # Setup mock behaviors
        mock_storage.load_file.return_value = "/data/jobs/image/input/test.png"

        # Create a temp file for image loading
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            temp_path = f.name
        mock_storage.load_file.return_value = temp_path

        mock_storage.save_file.return_value = "image/output/test.json"

        # Return a Pydantic model (simulating OCROutput)
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [{"id": "extract_text", "inputs": ["image_base64"]}]
        }
        mock_plugin_service.run_plugin_tool.return_value = MockOCROutput(
            text="Hello, World!",
            confidence=0.98
        )

        # Create a real file for the worker to read
        with open(temp_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        # Execute - should NOT crash
        result = worker.run_once()

        assert result is True
        # Verify save_file was called with valid JSON
        mock_storage.save_file.assert_called_once()
        call_args = mock_storage.save_file.call_args
        saved_content = call_args[0][0]
        if hasattr(saved_content, "read"):
            saved_bytes = saved_content.read()
            if isinstance(saved_bytes, bytes):
                saved_json = json.loads(saved_bytes.decode())
            else:
                saved_json = json.loads(saved_bytes)
        else:
            saved_json = json.loads(saved_content)

        # Verify the Pydantic model was serialized correctly
        assert "results" in saved_json
        assert saved_json["results"]["text"] == "Hello, World!"
        assert saved_json["results"]["confidence"] == 0.98

        # Cleanup
        import os
        os.unlink(temp_path)

    @pytest.mark.unit
    def test_worker_handles_dict_result(self, test_engine, session):
        """Test that worker still handles dict results (no regression)."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create pending job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="ocr",
            tool="extract_text",
            input_path="image/input/test.png",
            job_type="image",
        )
        session.add(job)
        session.commit()

        # Setup mock behaviors
        mock_storage.load_file.return_value = "/data/jobs/image/input/test.png"

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            temp_path = f.name
        mock_storage.load_file.return_value = temp_path

        mock_storage.save_file.return_value = "image/output/test.json"

        # Return a plain dict (existing behavior)
        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [{"id": "extract_text", "inputs": ["image_base64"]}]
        }
        mock_plugin_service.run_plugin_tool.return_value = {
            "text": "Dict result",
            "confidence": 0.85
        }

        # Create a real file for the worker to read
        with open(temp_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        # Execute - should work as before
        result = worker.run_once()

        assert result is True
        mock_storage.save_file.assert_called_once()

        # Cleanup
        import os
        os.unlink(temp_path)

    @pytest.mark.unit
    def test_worker_handles_nested_pydantic_model(self, test_engine, session):
        """Test that worker handles nested Pydantic models."""
        Session = sessionmaker(bind=test_engine)

        mock_storage = MagicMock()
        mock_plugin_service = MagicMock()

        worker = JobWorker(
            session_factory=Session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Create pending job
        job_id = str(uuid4())
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="ocr",
            tool="extract_text",
            input_path="image/input/test.png",
            job_type="image",
        )
        session.add(job)
        session.commit()

        # Setup mock behaviors
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            temp_path = f.name
        mock_storage.load_file.return_value = temp_path
        mock_storage.save_file.return_value = "image/output/test.json"

        # Create a nested Pydantic model
        class BoundingBox(BaseModel):
            x: int
            y: int
            width: int
            height: int

        class Detection(BaseModel):
            label: str
            confidence: float
            bbox: BoundingBox

        detection_result = Detection(
            label="person",
            confidence=0.95,
            bbox=BoundingBox(x=10, y=20, width=100, height=200)
        )

        mock_plugin_service.get_plugin_manifest.return_value = {
            "tools": [{"id": "extract_text", "inputs": ["image_base64"]}]
        }
        mock_plugin_service.run_plugin_tool.return_value = detection_result

        # Create a real file for the worker to read
        with open(temp_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        # Execute - should NOT crash
        result = worker.run_once()

        assert result is True
        call_args = mock_storage.save_file.call_args
        saved_content = call_args[0][0]
        if hasattr(saved_content, "read"):
            saved_bytes = saved_content.read()
            if isinstance(saved_bytes, bytes):
                saved_json = json.loads(saved_bytes.decode())
            else:
                saved_json = json.loads(saved_bytes)
        else:
            saved_json = json.loads(saved_content)

        # Verify nested structure is preserved
        assert saved_json["results"]["label"] == "person"
        assert saved_json["results"]["bbox"]["x"] == 10

        # Cleanup
        import os
        os.unlink(temp_path)
