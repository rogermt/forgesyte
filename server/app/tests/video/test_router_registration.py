"""Test video router registration (Commit 5 - Registration Test).

Verifies:
- Router is properly registered in FastAPI app
- Endpoint schema is correct
- Request/response contracts match frozen spec
"""

import sys
from pathlib import Path

# Import path workaround for tests (per AGENTS.md)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class TestVideoRouterEndpointRegistration:
    """Test that video endpoint is registered in OpenAPI spec."""

    def test_video_endpoint_in_openapi(self):
        """Verify /v1/video/process endpoint is in OpenAPI schema."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        # Check endpoint registered
        assert "/v1/video/process" in paths, "Video process endpoint not registered"

    def test_video_endpoint_post_method(self):
        """Verify /v1/video/process accepts POST."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")
        openapi = response.json()

        paths = openapi.get("paths", {})
        video_path = paths.get("/v1/video/process", {})

        # Verify POST method defined
        assert "post" in video_path, "POST method not defined for /v1/video/process"

    def test_request_schema_structure(self):
        """Verify request schema matches frozen spec."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")
        openapi = response.json()

        paths = openapi.get("paths", {})
        post_op = paths.get("/v1/video/process", {}).get("post", {})

        # Verify request parameters
        params = post_op.get("parameters", [])
        param_names = {p.get("name") for p in params}

        # Required params per frozen spec
        assert "pipeline_id" in param_names or "requestBody" in post_op
        assert "frame_stride" in param_names or "requestBody" in post_op
        assert "max_frames" in param_names or "requestBody" in post_op

    def test_response_schema_structure(self):
        """Verify response schema matches frozen spec."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")
        openapi = response.json()

        paths = openapi.get("paths", {})
        post_op = paths.get("/v1/video/process", {}).get("post", {})

        # Verify response schema
        responses = post_op.get("responses", {})
        assert "200" in responses, "200 response not defined"

        success_response = responses["200"]
        schema = (
            success_response.get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )

        # Handle $ref schema references
        if "$ref" in schema:
            # Resolve the reference
            ref = schema["$ref"]
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.split("/")[-1]
                components = openapi.get("components", {})
                schemas = components.get("schemas", {})
                schema = schemas.get(schema_name, {})

        # Response must have 'results' array per frozen spec
        props = schema.get("properties", {})
        assert "results" in props, "Response missing 'results' field"

    def test_response_results_schema(self):
        """Verify results array contains frame_index and result."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")
        openapi = response.json()

        # Navigate to results array item schema
        # FastAPI uses components/schemas in OpenAPI 3.x
        components = openapi.get("components", {})
        schemas = components.get("schemas", {})

        # FrameResult should exist
        frame_result = schemas.get("FrameResult", {})
        frame_result_props = frame_result.get("properties", {})

        # Per frozen spec: frame_index (int) + result (dict)
        assert "frame_index" in frame_result_props
        assert "result" in frame_result_props

        # frame_index must be integer
        assert frame_result_props["frame_index"].get("type") == "integer"


class TestVideoRouterImports:
    """Test that router can be imported and instantiated."""

    def test_video_router_imports(self):
        """Verify video router module imports correctly."""
        from app.api_routes.routes.video_file_processing import router

        assert router is not None
        assert hasattr(router, "routes")

    def test_router_has_process_endpoint(self):
        """Verify router has the /process endpoint."""
        from app.api_routes.routes.video_file_processing import router

        # Find the POST /process route
        process_route = None
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/video/process":
                if "POST" in getattr(route, "methods", set()):
                    process_route = route
                    break

        assert (
            process_route is not None
        ), "POST /video/process route not found in router"

    def test_schemas_are_exported(self):
        """Verify request/response schemas are defined."""
        from app.api_routes.routes.video_file_processing import (
            FrameResult,
            VideoProcessingRequest,
            VideoProcessingResponse,
        )

        assert VideoProcessingRequest is not None
        assert VideoProcessingResponse is not None
        assert FrameResult is not None

    def test_schemas_match_frozen_spec(self):
        """Verify schema classes match frozen protocol."""
        from app.api_routes.routes.video_file_processing import (
            FrameResult,
            VideoProcessingRequest,
            VideoProcessingResponse,
        )

        # VideoProcessingRequest must have these fields
        req_fields = VideoProcessingRequest.model_fields
        assert "pipeline_id" in req_fields
        assert "frame_stride" in req_fields
        assert "max_frames" in req_fields

        # FrameResult must have frame_index and result
        frame_fields = FrameResult.model_fields
        assert "frame_index" in frame_fields
        assert "result" in frame_fields

        # VideoProcessingResponse must have results list
        resp_fields = VideoProcessingResponse.model_fields
        assert "results" in resp_fields
