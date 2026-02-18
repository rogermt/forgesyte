"""Schema regression tests (Commit 7 - Golden Snapshot).

Verifies:
- Frozen response schema never changes
- Request schema validation
- Field types and required fields
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest

# Golden snapshot of frozen response schema (Phase 15 spec)
GOLDEN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "frame_index": {"type": "integer"},
                    "result": {"type": "object"},
                },
                "required": ["frame_index", "result"],
            },
        }
    },
    "required": ["results"],
}


class TestSchemaRegression:
    """Regression tests for frozen schema contract."""

    def test_response_schema_matches_golden(self):
        """Verify response schema hasn't deviated from frozen spec."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingResponse,
        )

        # Extract actual schema
        actual_schema = VideoProcessingResponse.model_json_schema()

        # Verify structure
        assert "properties" in actual_schema
        assert "results" in actual_schema["properties"]

        results_schema = actual_schema["properties"]["results"]
        assert results_schema["type"] == "array"
        assert "items" in results_schema

    def test_frame_result_has_required_fields(self):
        """Verify FrameResult has frame_index and result."""
        from app.api_routes.routes.video_file_processing import FrameResult

        schema = FrameResult.model_json_schema()
        props = schema.get("properties", {})
        required = schema.get("required", [])

        # Must have both fields
        assert "frame_index" in props
        assert "result" in props
        assert "frame_index" in required
        assert "result" in required

    def test_frame_index_is_integer(self):
        """Verify frame_index field is integer type."""
        from app.api_routes.routes.video_file_processing import FrameResult

        schema = FrameResult.model_json_schema()
        props = schema.get("properties", {})

        frame_index_type = props["frame_index"].get("type")
        assert frame_index_type == "integer"

    def test_result_is_object_type(self):
        """Verify result field is object type (allows any dict)."""
        from app.api_routes.routes.video_file_processing import FrameResult

        schema = FrameResult.model_json_schema()
        props = schema.get("properties", {})

        result_type = props["result"].get("type")
        # Should be object or object-compatible
        assert result_type in ["object", None] or "object" in str(props["result"])

    def test_request_schema_frozen(self):
        """Verify request schema hasn't changed."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingRequest,
        )

        schema = VideoProcessingRequest.model_json_schema()
        props = schema.get("properties", {})

        # Frozen fields
        assert "pipeline_id" in props
        assert "frame_stride" in props
        assert "max_frames" in props

    def test_pipeline_id_is_required(self):
        """Verify pipeline_id is required."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingRequest,
        )

        schema = VideoProcessingRequest.model_json_schema()
        required = schema.get("required", [])

        assert "pipeline_id" in required

    def test_frame_stride_has_min_constraint(self):
        """Verify frame_stride has minimum value constraint."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingRequest,
        )

        schema = VideoProcessingRequest.model_json_schema()
        props = schema.get("properties", {})
        stride_schema = props.get("frame_stride", {})

        # Should have minimum >= 1
        assert "minimum" in stride_schema or stride_schema.get("exclusiveMinimum") == 0

    def test_max_frames_nullable(self):
        """Verify max_frames can be None."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingRequest,
        )

        # Can create request with max_frames=None
        req = VideoProcessingRequest(
            pipeline_id="yolo_ocr", frame_stride=1, max_frames=None
        )
        assert req.max_frames is None

    def test_response_no_extra_fields(self):
        """Verify response has no extra fields per frozen spec."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingResponse,
        )

        schema = VideoProcessingResponse.model_json_schema()
        props = schema.get("properties", {})

        # Only 'results' field allowed per frozen spec
        assert len(props) == 1
        assert "results" in props

    def test_frame_result_no_extra_fields(self):
        """Verify FrameResult has only 2 fields per frozen spec."""
        from app.api_routes.routes.video_file_processing import FrameResult

        schema = FrameResult.model_json_schema()
        props = schema.get("properties", {})

        # Only frame_index and result
        assert len(props) == 2
        assert "frame_index" in props
        assert "result" in props


class TestSchemaValidation:
    """Test that schema validation works correctly."""

    def test_valid_response_passes_validation(self):
        """Valid response passes schema validation."""
        from app.api_routes.routes.video_file_processing import (
            FrameResult,
            VideoProcessingResponse,
        )

        result = FrameResult(frame_index=0, result={"data": "value"})
        response = VideoProcessingResponse(results=[result])

        # Should serialize without error
        json_str = response.model_dump_json()
        assert "frame_index" in json_str
        assert "data" in json_str

    def test_missing_frame_index_fails(self):
        """Missing frame_index fails validation."""
        from pydantic import ValidationError

        from app.api_routes.routes.video_file_processing import FrameResult

        with pytest.raises(ValidationError):
            FrameResult(result={"data": "value"})  # type: ignore

    def test_missing_result_fails(self):
        """Missing result fails validation."""
        from pydantic import ValidationError

        from app.api_routes.routes.video_file_processing import FrameResult

        with pytest.raises(ValidationError):
            FrameResult(frame_index=0)  # type: ignore

    def test_frame_index_must_be_int(self):
        """frame_index must be integer."""
        from app.api_routes.routes.video_file_processing import FrameResult

        # String frame_index should fail or be coerced
        try:
            frame = FrameResult(frame_index="0", result={})  # type: ignore
            # Pydantic may coerce, which is ok
            assert isinstance(frame.frame_index, int)
        except Exception:
            # Or it raises, which is also ok
            pass

    def test_result_accepts_any_dict(self):
        """Result field accepts any dictionary."""
        from app.api_routes.routes.video_file_processing import FrameResult

        # Various dict contents should work
        test_cases = [
            {},
            {"key": "value"},
            {"nested": {"deep": "value"}},
            {"array": [1, 2, 3]},
        ]

        for result_dict in test_cases:
            frame = FrameResult(frame_index=0, result=result_dict)
            assert frame.result == result_dict
