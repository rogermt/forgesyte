"""Test that AnalysisResult is the shared contract between core and plugins.

Ensures plugins return AnalysisResult (Pydantic model) that can be
serialized to dict for storage and API responses.
"""

import pytest
from pydantic import ValidationError

from app.models import AnalysisResult


def test_analysis_result_model_exists():
    """Test that AnalysisResult model is defined and importable."""
    assert AnalysisResult is not None
    assert hasattr(AnalysisResult, "model_dump")  # Pydantic v2


def test_analysis_result_with_minimal_fields():
    """Test creating AnalysisResult with minimal required fields."""
    result = AnalysisResult(
        text="extracted text",
        blocks=[],
        confidence=0.95,
    )
    assert result.text == "extracted text"
    assert result.blocks == []
    assert result.confidence == 0.95


def test_analysis_result_can_convert_to_dict():
    """Test that AnalysisResult can be converted to dict for storage."""
    result = AnalysisResult(
        text="test text",
        blocks=[{"text": "block1"}],
        confidence=0.9,
        language="eng",
    )

    # Must be convertible to dict (for {**result, ...} unpacking)
    result_dict = result.model_dump()

    assert isinstance(result_dict, dict)
    assert result_dict["text"] == "test text"
    assert result_dict["blocks"] == [{"text": "block1"}]
    assert result_dict["confidence"] == 0.9
    assert result_dict["language"] == "eng"


def test_analysis_result_unpacking():
    """Test that AnalysisResult dict can be unpacked with ** operator.

    This is the key requirement from tasks.py:
        {**result, "processing_time_ms": processing_time_ms}
    """
    result = AnalysisResult(text="test", blocks=[], confidence=0.8)
    result_dict = result.model_dump()

    # Simulate what tasks.py does
    job_data = {**result_dict, "processing_time_ms": 123.45}

    assert job_data["text"] == "test"
    assert job_data["blocks"] == []
    assert job_data["confidence"] == 0.8
    assert job_data["processing_time_ms"] == 123.45


def test_analysis_result_with_error():
    """Test AnalysisResult can represent an error state."""
    result = AnalysisResult(
        text="",
        blocks=[],
        confidence=0.0,
        error="Tesseract not installed",
    )

    assert result.error == "Tesseract not installed"
    assert result.confidence == 0.0


def test_analysis_result_validation():
    """Test that AnalysisResult enforces required fields."""
    # Missing required 'text' field
    with pytest.raises(ValidationError):
        AnalysisResult(confidence=0.9)

    # Missing required 'confidence' field
    with pytest.raises(ValidationError):
        AnalysisResult(text="test")

    # Invalid confidence value (must be 0.0-1.0)
    with pytest.raises(ValidationError):
        AnalysisResult(text="test", confidence=1.5)
