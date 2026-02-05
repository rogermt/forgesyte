"""TEST-CHANGE: Integration test — normalisation wired into job pipeline.

Verify that plugin results are normalised before storage.
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.models import JobStatus
from app.tasks import JobStore, TaskProcessor


@pytest.fixture
def job_store():
    """In-memory job store for testing."""
    return JobStore(max_jobs=100)


@pytest.fixture
def plugin_manager():
    """Mock plugin manager."""
    manager = MagicMock()
    # Mock plugin with OCR-like output
    plugin = MagicMock()
    plugin.run_tool.return_value = {
        "boxes": [[10, 20, 30, 40]],
        "scores": [0.95],
        "labels": ["text"],
    }
    manager.get.return_value = plugin
    return manager


@pytest.mark.asyncio
async def test_job_pipeline_normalises_plugin_output(job_store, plugin_manager):
    """Verify plugin output is normalised before storage."""
    processor = TaskProcessor(job_store=job_store, plugin_manager=plugin_manager)

    # Submit job
    job_id = await processor.submit_job(
        image_bytes=b"fake_image_data",
        plugin_name="ocr",
        options={},
    )

    # Wait for processing to complete
    await asyncio.sleep(1.0)

    # Retrieve job
    job = await job_store.get(job_id)

    # Verify job completed
    assert job["status"] == JobStatus.DONE

    # Verify result is normalised (has frames[] structure)
    result = job["result"]
    assert "frames" in result, "Result must be normalised with frames[] structure"
    assert isinstance(result["frames"], list)
    assert len(result["frames"]) > 0

    # Verify frame contains canonical schema
    frame = result["frames"][0]
    assert "boxes" in frame
    assert "scores" in frame
    assert "labels" in frame

    # Verify boxes are in canonical form {x1, y1, x2, y2}
    if frame["boxes"]:
        box = frame["boxes"][0]
        assert set(box.keys()) == {"x1", "y1", "x2", "y2"}

    # Verify processing_time_ms still present
    assert "processing_time_ms" in result
