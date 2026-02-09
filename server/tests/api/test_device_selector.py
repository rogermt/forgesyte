"""
Tests for device selection in /v1/analyze endpoint (Step 6).

These are RED tests — they verify the device parameter works correctly
from the API layer perspective.
"""

import pytest


class TestDeviceSelector:
    """Tests for device parameter in /analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_accepts_device_cpu_param(self, client) -> None:
        """Verify /v1/analyze accepts device=cpu query parameter."""
        response = await client.post(
            "/v1/analyze?plugin=ocr&device=cpu",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data.get("device_requested") == "cpu"

    @pytest.mark.asyncio
    async def test_analyze_accepts_device_gpu_param(self, client) -> None:
        """Verify /v1/analyze accepts device=gpu query parameter."""
        response = await client.post(
            "/v1/analyze?plugin=ocr&device=gpu",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data.get("device_requested") == "gpu"

    @pytest.mark.asyncio
    async def test_analyze_rejects_invalid_device_param(self, client) -> None:
        """Verify /v1/analyze rejects device=invalid (invalid value)."""
        response = await client.post(
            "/v1/analyze?plugin=ocr&device=invalid",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "device" in data["detail"].lower() or "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_analyze_no_device_param_allows_plugin_resolution(self, client) -> None:
        """Phase 12: Device is optional. If not provided, plugin resolves from models.yaml."""
        response = await client.post(
            "/v1/analyze?plugin=ocr",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )
        assert response.status_code == 200
        data = response.json()
        # Device should be "default" (plugin will resolve via models.yaml)
        assert data.get("device_requested") == "default"

    @pytest.mark.asyncio
    async def test_analyze_device_case_insensitive(self, client) -> None:
        """Verify device parameter is case-insensitive (GPU/Gpu should work)."""
        response = await client.post(
            "/v1/analyze?plugin=ocr&device=GPU",
            files={"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("device_requested") in ["gpu", "GPU"]
