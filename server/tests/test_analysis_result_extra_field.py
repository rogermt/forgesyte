"""Test that AnalysisResult includes extra field for plugin-specific data."""

from app.models import AnalysisResult


class TestAnalysisResultExtraField:
    """Tests for AnalysisResult.extra field support."""

    def test_extra_field_exists(self) -> None:
        """Verify AnalysisResult has extra field."""
        result = AnalysisResult(
            text="",
            blocks=[],
            confidence=1.0,
            language=None,
            error=None,
            extra={"detections": []},
        )
        assert result.extra == {"detections": []}

    def test_extra_field_optional(self) -> None:
        """Verify extra field is optional (defaults to None)."""
        result = AnalysisResult(
            text="",
            blocks=[],
            confidence=1.0,
        )
        assert result.extra is None

    def test_extra_field_serializes(self) -> None:
        """Verify extra field is included in model_dump()."""
        result = AnalysisResult(
            text="sample",
            blocks=[],
            confidence=0.95,
            extra={"players": 11, "ball": {"x": 100, "y": 200}},
        )
        dumped = result.model_dump()
        assert "extra" in dumped
        assert dumped["extra"]["players"] == 11
