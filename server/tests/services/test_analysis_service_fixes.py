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
        device: str,
    ) -> str:
        self.last_call = {
            "image_bytes": image_bytes,
            "plugin_name": plugin_name,
            "options": options,
            "device": device,
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
    async def test_device_resolution_param_over_options(self) -> None:
        """Test 3: If device=None and options={"device": "cuda"}, submit job with device="cuda"."""
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
            device=None,
        )

        assert proc.last_call["device"] == "cuda"


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
                device="cpu",
            )
