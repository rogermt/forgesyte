"""Unit test: Verify video router is registered in FastAPI app (Commit 5).

This is a UNIT test - no real endpoint calls, no real files, no OpenCV.
Just verify: router exists, can be imported, is wired into main.py
"""

import sys
from pathlib import Path

# Import path workaround for tests (per AGENTS.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class TestVideoRouterRegistration:
    """Verify video router is registered."""

    def test_router_imports(self):
        """Router module can be imported."""
        from app.api_routes.routes.video_file_processing import router

        assert router is not None
        assert hasattr(router, "routes")

    def test_router_in_main(self):
        """Router is imported in main.py."""
        from app import main

        # Check that main module has video_router
        assert hasattr(main, "video_router"), "video_router not imported in main"

    def test_router_registered_in_app(self):
        """Router is registered with app.include_router."""
        from app.main import app

        # Check router is in app routes
        found = False
        for route in app.routes:
            if hasattr(route, "path") and "/video" in route.path:
                found = True
                break

        assert found, "Video router not found in app routes"

    def test_schemas_exist(self):
        """Request/response schemas are defined."""
        from app.api_routes.routes.video_file_processing import (
            FrameResult,
            VideoProcessingRequest,
            VideoProcessingResponse,
        )

        assert VideoProcessingRequest is not None
        assert VideoProcessingResponse is not None
        assert FrameResult is not None

    def test_request_schema_has_required_fields(self):
        """VideoProcessingRequest has frozen fields."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingRequest,
        )

        fields = VideoProcessingRequest.model_fields
        assert "pipeline_id" in fields
        assert "frame_stride" in fields
        assert "max_frames" in fields

    def test_response_schema_has_results(self):
        """VideoProcessingResponse has results field."""
        from app.api_routes.routes.video_file_processing import (
            VideoProcessingResponse,
        )

        fields = VideoProcessingResponse.model_fields
        assert "results" in fields

    def test_frame_result_has_frame_index_and_result(self):
        """FrameResult has frame_index and result."""
        from app.api_routes.routes.video_file_processing import FrameResult

        fields = FrameResult.model_fields
        assert "frame_index" in fields
        assert "result" in fields
