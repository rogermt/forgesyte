"""Tests for AnalysisService image extraction and device resolution fixes.

TEST-CHANGE: Add 4 unit tests for Issue #164:
1. JSON base64 extraction from options["image"]
2. JSON base64 extraction from options["frame"]
3. Device resolution priority (param > options > default)
4. Error handling when no image source provided
"""

import base64
from typing import Any, Dict

import pytest

from app.protocols import TaskProcessor
from app.services.analysis_service import AnalysisService
from app.services.image_acquisition import ImageAcquisitionService


class MockProcessor(TaskProcessor):
    """Mock TaskProcessor that records calls."""

    def __init__(self) -> None:
        self.last_call: Dict[str, Any] = {}

    async def submit_job(
        self,
        image_bytes: bytes,
        plugin_name: str,
        options: Dict[str, Any],
    ) -> str:
        self.last_call = {
            "image_bytes": image_bytes,
            "plugin_name": plugin_name,
            "options": options,
        }
        return "job-123"


class MockAcquirer(ImageAcquisitionService):
    """Mock ImageAcquisitionService."""

    async def fetch_image_from_url(self, url: str) -> bytes:
        raise RuntimeError("Not used in tests")


class TestAnalysisServiceImageExtraction:
    """Test 1 & 2: JSON base64 extraction from options."""

    @pytest.mark.asyncio
    async def test_acquire_image_from_json_image_field(self) -> None:
        """Test 1: await svc._acquire_image(..., options={"image": b64}) returns decoded bytes."""
        svc = AnalysisService(MockProcessor(), MockAcquirer())
        raw_bytes = b"test_image_data"
        b64 = base64.b64encode(raw_bytes).decode("utf-8")

        result = await svc._acquire_image(
            file_bytes=None,
            image_url=None,
            body_bytes=None,
            options={"image": b64},
        )

        assert result == raw_bytes

    @pytest.mark.asyncio
    async def test_acquire_image_from_json_frame_field(self) -> None:
        """Test 2: await svc._acquire_image(..., options={"frame": b64}) returns decoded bytes."""
        svc = AnalysisService(MockProcessor(), MockAcquirer())
        raw_bytes = b"test_frame_data"
        b64 = base64.b64encode(raw_bytes).decode("utf-8")

        result = await svc._acquire_image(
            file_bytes=None,
            image_url=None,
            body_bytes=None,
            options={"frame": b64},
        )

        assert result == raw_bytes


class TestAnalysisServiceDeviceResolution:
    """Test 3: Device resolution priority (param > options > default)."""

    @pytest.mark.asyncio
    async def test_device_resolution_from_options(self) -> None:
        """Phase 12: Device comes from options['device'], not separate param."""
        proc = MockProcessor()
        svc = AnalysisService(proc, MockAcquirer())
        raw_bytes = b"image"
        b64 = base64.b64encode(raw_bytes).decode("utf-8")

        await svc.process_analysis_request(
            file_bytes=None,
            image_url=None,
            body_bytes=None,
            plugin="yolo-tracker",
            options={"image": b64, "device": "cuda"},
        )

        # Device is now in options dict, not separate submit_job call
        assert proc.last_call["options"]["device"] == "cuda"


class TestAnalysisServiceErrorHandling:
    """Test 4: Error when no image source provided."""

    @pytest.mark.asyncio
    async def test_error_when_no_image_source(self) -> None:
        """Test 4: await svc.process_analysis_request(..., options={}) raises ValueError."""
        svc = AnalysisService(MockProcessor(), MockAcquirer())

        with pytest.raises(ValueError, match="No valid image provided"):
            await svc.process_analysis_request(
                file_bytes=None,
                image_url=None,
                body_bytes=None,
                plugin="yolo-tracker",
                options={},
            )
