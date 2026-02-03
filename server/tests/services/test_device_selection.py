"""
Tests for device selection in service layer (Step 6).

These are RED tests — they verify device selection works correctly
in AnalysisService and through the job pipeline.
"""




class TestDeviceAvailability:
    """Tests for GPU availability detection and fallback."""

    def test_cpu_device_always_available(self) -> None:
        """Verify CPU device is always available (never falls back)."""
        from app.services.device_selector import resolve_device

        actual = resolve_device("cpu", gpu_available=False)
        assert actual == "cpu"

    def test_gpu_fallback_when_unavailable(self) -> None:
        """Verify GPU falls back to CPU when unavailable."""
        from app.services.device_selector import resolve_device

        actual = resolve_device("gpu", gpu_available=False)
        assert actual == "cpu"

    def test_gpu_used_when_available(self) -> None:
        """Verify GPU is used when available."""
        from app.services.device_selector import resolve_device

        actual = resolve_device("gpu", gpu_available=True)
        assert actual == "gpu"

    def test_validate_device_accepts_cpu(self) -> None:
        """Verify validate_device accepts 'cpu'."""
        from app.services.device_selector import validate_device

        assert validate_device("cpu") is True

    def test_validate_device_accepts_gpu(self) -> None:
        """Verify validate_device accepts 'gpu'."""
        from app.services.device_selector import validate_device

        assert validate_device("gpu") is True

    def test_validate_device_accepts_case_insensitive(self) -> None:
        """Verify validate_device is case-insensitive."""
        from app.services.device_selector import validate_device

        assert validate_device("CPU") is True
        assert validate_device("GPU") is True
        assert validate_device("Gpu") is True

    def test_validate_device_rejects_invalid(self) -> None:
        """Verify validate_device rejects invalid values."""
        from app.services.device_selector import validate_device

        assert validate_device("invalid") is False
        assert validate_device("cuda") is False
        assert validate_device("") is False
