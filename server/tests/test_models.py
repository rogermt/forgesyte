"""Comprehensive test suite for Pydantic models.

Tests cover:
- JobStatus enum values
- JobResponse validation (job_id, status, timestamps, results)
- AnalyzeRequest validation (plugin, options, image_url)
- PluginMetadata validation (name, description, version, inputs, outputs, permissions)
- MCPTool and MCPManifest structures
- WebSocketMessage validation
- Edge cases and constraint violations
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.models import (
    AnalyzeRequest,
    JobResponse,
    JobStatus,
    MCPManifest,
    MCPTool,
    PluginMetadata,
    WebSocketMessage,
)


class TestJobStatus:
    """Test JobStatus enum values."""

    def test_queued_status(self) -> None:
        """QUEUED status value."""
        assert JobStatus.QUEUED == "queued"

    def test_running_status(self) -> None:
        """RUNNING status value."""
        assert JobStatus.RUNNING == "running"

    def test_done_status(self) -> None:
        """DONE status value."""
        assert JobStatus.DONE == "done"

    def test_error_status(self) -> None:
        """ERROR status value."""
        assert JobStatus.ERROR == "error"

    def test_not_found_status(self) -> None:
        """NOT_FOUND status value."""
        assert JobStatus.NOT_FOUND == "not_found"

    def test_all_statuses_are_strings(self) -> None:
        """All status values are strings."""
        for status in JobStatus:
            assert isinstance(status.value, str)

    def test_status_from_string(self) -> None:
        """Can create JobStatus from string value."""
        status = JobStatus("running")
        assert status == JobStatus.RUNNING

    def test_invalid_status_value(self) -> None:
        """Invalid status string raises ValueError."""
        with pytest.raises(ValueError):
            JobStatus("invalid_status")


class TestJobResponse:
    """Test JobResponse model validation and structure."""

    def test_complete_job_response_done(self) -> None:
        """Complete JobResponse with status done."""
        response = JobResponse(
            job_id="job-001",
            status=JobStatus.DONE,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            completed_at=datetime(2026, 1, 14, 10, 5, 0),
            result={"text": "extracted text", "confidence": 0.95},
            progress=100,
            error=None,
        )
        assert response.job_id == "job-001"
        assert response.status == JobStatus.DONE
        assert response.result["confidence"] == 0.95
        assert response.error is None

    def test_job_response_running(self) -> None:
        """JobResponse with status running."""
        response = JobResponse(
            job_id="job-002",
            status=JobStatus.RUNNING,
            plugin="motion_detector",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            progress=45,
        )
        assert response.status == JobStatus.RUNNING
        assert response.progress == 45
        assert response.completed_at is None
        assert response.result is None

    def test_job_response_error(self) -> None:
        """JobResponse with status error."""
        response = JobResponse(
            job_id="job-003",
            status=JobStatus.ERROR,
            plugin="object_detection",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            completed_at=datetime(2026, 1, 14, 10, 1, 0),
            error="Failed to process image: invalid format",
        )
        assert response.status == JobStatus.ERROR
        assert response.error is not None
        assert "invalid format" in response.error

    def test_job_response_queued(self) -> None:
        """JobResponse with status queued."""
        response = JobResponse(
            job_id="job-004",
            status=JobStatus.QUEUED,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
        )
        assert response.status == JobStatus.QUEUED
        assert response.progress is None
        assert response.completed_at is None

    def test_job_response_not_found(self) -> None:
        """JobResponse with status not_found."""
        response = JobResponse(
            job_id="nonexistent",
            status=JobStatus.NOT_FOUND,
            plugin="unknown",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
        )
        assert response.status == JobStatus.NOT_FOUND

    def test_job_response_required_fields_only(self) -> None:
        """JobResponse with only required fields."""
        response = JobResponse(
            job_id="job-min",
            status=JobStatus.QUEUED,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
        )
        assert response.job_id == "job-min"
        assert response.completed_at is None
        assert response.result is None
        assert response.error is None
        assert response.progress is None

    def test_job_response_missing_job_id(self) -> None:
        """JobResponse without job_id fails validation."""
        with pytest.raises(ValidationError):
            JobResponse(
                status=JobStatus.DONE,
                plugin="ocr",
                created_at=datetime(2026, 1, 14, 10, 0, 0),
            )

    def test_job_response_missing_status(self) -> None:
        """JobResponse without status fails validation."""
        with pytest.raises(ValidationError):
            JobResponse(
                job_id="job-001",
                plugin="ocr",
                created_at=datetime(2026, 1, 14, 10, 0, 0),
            )

    def test_job_response_missing_plugin(self) -> None:
        """JobResponse without plugin fails validation."""
        with pytest.raises(ValidationError):
            JobResponse(
                job_id="job-001",
                status=JobStatus.DONE,
                created_at=datetime(2026, 1, 14, 10, 0, 0),
            )

    def test_job_response_missing_created_at(self) -> None:
        """JobResponse without created_at fails validation."""
        with pytest.raises(ValidationError):
            JobResponse(
                job_id="job-001",
                status=JobStatus.DONE,
                plugin="ocr",
            )

    def test_job_response_with_complex_result(self) -> None:
        """JobResponse result can be complex nested structure."""
        response = JobResponse(
            job_id="job-005",
            status=JobStatus.DONE,
            plugin="motion_detector",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            result={
                "motion_detected": True,
                "confidence": 0.87,
                "regions": [
                    {"x": 100, "y": 150, "width": 200, "height": 150},
                    {"x": 300, "y": 100, "width": 150, "height": 200},
                ],
                "metadata": {
                    "frames_analyzed": 30,
                    "fps": 30,
                    "duration_ms": 1000,
                },
            },
        )
        assert len(response.result["regions"]) == 2
        assert response.result["metadata"]["duration_ms"] == 1000

    def test_job_response_progress_boundaries(self) -> None:
        """Progress field can range from 0 to 100."""
        for progress in [0, 1, 50, 99, 100]:
            response = JobResponse(
                job_id=f"job-{progress}",
                status=JobStatus.RUNNING,
                plugin="ocr",
                created_at=datetime(2026, 1, 14, 10, 0, 0),
                progress=progress,
            )
            assert response.progress == progress

    def test_job_response_progress_over_100(self) -> None:
        """Progress over 100 is allowed (edge case)."""
        response = JobResponse(
            job_id="job-over",
            status=JobStatus.RUNNING,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            progress=150.5,
        )
        assert response.progress == 150.5

    def test_job_response_negative_progress(self) -> None:
        """Negative progress is allowed (edge case)."""
        response = JobResponse(
            job_id="job-neg",
            status=JobStatus.RUNNING,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            progress=-10,
        )
        assert response.progress == -10

    def test_job_response_timestamps_with_timezone(self) -> None:
        """Timestamps can have timezone info."""
        utc = ZoneInfo("UTC")
        response = JobResponse(
            job_id="job-tz",
            status=JobStatus.DONE,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0, tzinfo=utc),
            completed_at=datetime(2026, 1, 14, 10, 5, 0, tzinfo=utc),
        )
        assert response.created_at.tzinfo == utc

    def test_job_response_empty_result(self) -> None:
        """Result can be empty dict."""
        response = JobResponse(
            job_id="job-empty",
            status=JobStatus.DONE,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            result={},
        )
        assert response.result == {}

    def test_job_response_serialization(self) -> None:
        """JobResponse can be serialized to JSON-compatible dict."""
        response = JobResponse(
            job_id="job-json",
            status=JobStatus.DONE,
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
            result={"text": "extracted"},
        )
        data = response.model_dump()
        assert data["job_id"] == "job-json"
        assert isinstance(data["created_at"], datetime)

    def test_job_response_string_status(self) -> None:
        """JobResponse accepts status as string."""
        response = JobResponse(
            job_id="job-str",
            status="done",
            plugin="ocr",
            created_at=datetime(2026, 1, 14, 10, 0, 0),
        )
        assert response.status == JobStatus.DONE


class TestAnalyzeRequest:
    """Test AnalyzeRequest model validation."""

    def test_analyze_request_all_fields(self) -> None:
        """AnalyzeRequest with all fields."""
        request = AnalyzeRequest(
            plugin="ocr_plugin",
            image_url="https://example.com/image.jpg",
            options={"language": "en", "confidence": 0.8},
        )
        assert request.plugin == "ocr_plugin"
        assert request.image_url == "https://example.com/image.jpg"
        assert request.options["language"] == "en"

    def test_analyze_request_minimal(self) -> None:
        """AnalyzeRequest with defaults."""
        request = AnalyzeRequest()
        assert request.plugin == "default"
        assert request.image_url is None
        assert request.options is None

    def test_analyze_request_custom_plugin(self) -> None:
        """AnalyzeRequest with custom plugin."""
        request = AnalyzeRequest(plugin="motion_detector")
        assert request.plugin == "motion_detector"

    def test_analyze_request_with_url_only(self) -> None:
        """AnalyzeRequest with only image_url."""
        request = AnalyzeRequest(
            image_url="https://example.com/image.jpg",
        )
        assert request.image_url == "https://example.com/image.jpg"

    def test_analyze_request_with_options_only(self) -> None:
        """AnalyzeRequest with complex options."""
        request = AnalyzeRequest(
            options={
                "sensitivity": 0.5,
                "regions": [{"x": 0, "y": 0, "width": 100, "height": 100}],
                "metadata": {"source": "camera_1"},
            }
        )
        assert request.options["sensitivity"] == 0.5
        assert len(request.options["regions"]) == 1

    def test_analyze_request_serialization(self) -> None:
        """AnalyzeRequest serializes to dict."""
        request = AnalyzeRequest(
            plugin="ocr",
            image_url="https://example.com/img.jpg",
            options={"lang": "en"},
        )
        data = request.model_dump()
        assert data["plugin"] == "ocr"
        assert data["image_url"] == "https://example.com/img.jpg"


class TestPluginMetadata:
    """Test PluginMetadata model validation and constraints."""

    def test_plugin_metadata_all_fields(self) -> None:
        """PluginMetadata with all fields."""
        metadata = PluginMetadata(
            name="ocr_plugin",
            description="Extracts text from images",
            version="2.1.0",
            inputs=["image"],
            outputs=["json", "text"],
            permissions=["read:files", "write:results"],
            config_schema={
                "language": {"type": "string", "default": "en"},
                "confidence": {"type": "number", "default": 0.8},
            },
        )
        assert metadata.name == "ocr_plugin"
        assert metadata.version == "2.1.0"
        assert len(metadata.outputs) == 2
        assert len(metadata.permissions) == 2

    def test_plugin_metadata_minimal(self) -> None:
        """PluginMetadata with only required fields."""
        metadata = PluginMetadata(
            name="minimal_plugin",
            description="A minimal plugin",
        )
        assert metadata.name == "minimal_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.inputs == ["image"]
        assert metadata.outputs == ["json"]
        assert metadata.permissions == []

    def test_plugin_name_required(self) -> None:
        """PluginMetadata name is required."""
        with pytest.raises(ValidationError):
            PluginMetadata(description="Description only")

    def test_plugin_description_required(self) -> None:
        """PluginMetadata description is required."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="plugin_only")

    def test_plugin_name_empty_string_fails(self) -> None:
        """Empty string for name fails validation."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="", description="Description")

    def test_plugin_name_whitespace_only_fails(self) -> None:
        """Whitespace-only name fails validation."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="   ", description="Description")

    def test_plugin_description_empty_string_fails(self) -> None:
        """Empty string for description fails validation."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="plugin", description="")

    def test_plugin_description_whitespace_only_fails(self) -> None:
        """Whitespace-only description fails validation."""
        with pytest.raises(ValidationError):
            PluginMetadata(name="plugin", description="   ")

    def test_plugin_with_hyphenated_name(self) -> None:
        """Plugin names can use hyphens."""
        metadata = PluginMetadata(
            name="motion-detector",
            description="Detects motion",
        )
        assert metadata.name == "motion-detector"

    def test_plugin_with_underscored_name(self) -> None:
        """Plugin names can use underscores."""
        metadata = PluginMetadata(
            name="object_detection_v2",
            description="Detects objects",
        )
        assert metadata.name == "object_detection_v2"

    def test_plugin_with_special_version(self) -> None:
        """Plugin version supports semantic versioning variations."""
        for version in ["1.0.0", "2.1", "1.0.0-alpha", "1.0.0+build.123"]:
            metadata = PluginMetadata(
                name="test_plugin",
                description="Test",
                version=version,
            )
            assert metadata.version == version

    def test_plugin_with_empty_inputs_list(self) -> None:
        """Plugin inputs can be empty list."""
        metadata = PluginMetadata(
            name="plugin",
            description="No inputs",
            inputs=[],
        )
        assert metadata.inputs == []

    def test_plugin_with_empty_outputs_list(self) -> None:
        """Plugin outputs can be empty list."""
        metadata = PluginMetadata(
            name="plugin",
            description="No outputs",
            outputs=[],
        )
        assert metadata.outputs == []

    def test_plugin_with_multiple_inputs_outputs(self) -> None:
        """Plugin can have multiple inputs and outputs."""
        metadata = PluginMetadata(
            name="multi_plugin",
            description="Multi I/O plugin",
            inputs=["image", "config", "metadata"],
            outputs=["json", "text", "csv", "regions"],
        )
        assert len(metadata.inputs) == 3
        assert len(metadata.outputs) == 4

    def test_plugin_with_multiple_permissions(self) -> None:
        """Plugin can have multiple permissions."""
        metadata = PluginMetadata(
            name="secure_plugin",
            description="Secure plugin",
            permissions=[
                "read:files",
                "write:results",
                "gpu:access",
                "network:external",
            ],
        )
        assert len(metadata.permissions) == 4

    def test_plugin_with_complex_config_schema(self) -> None:
        """Plugin config schema can be complex."""
        metadata = PluginMetadata(
            name="configurable",
            description="Highly configurable",
            config_schema={
                "sensitivity": {
                    "type": "number",
                    "default": 0.5,
                    "description": "Detection sensitivity",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "regions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "ROI definitions",
                },
                "enabled_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["motion", "faces"],
                },
            },
        )
        assert "sensitivity" in metadata.config_schema
        assert metadata.config_schema["sensitivity"]["type"] == "number"

    def test_plugin_with_unicode_name(self) -> None:
        """Plugin names can contain unicode."""
        metadata = PluginMetadata(
            name="plugin_中文_test",
            description="Unicode plugin",
        )
        assert "中文" in metadata.name

    def test_plugin_serialization(self) -> None:
        """PluginMetadata serializes to dict."""
        metadata = PluginMetadata(
            name="test_plugin",
            description="Test",
            version="1.2.3",
        )
        data = metadata.model_dump()
        assert data["name"] == "test_plugin"
        assert data["version"] == "1.2.3"

    def test_plugin_exclude_none_serialization(self) -> None:
        """Serialization can exclude None fields."""
        metadata = PluginMetadata(
            name="test",
            description="Test",
            config_schema=None,
        )
        data = metadata.model_dump(exclude_none=True)
        assert "config_schema" not in data


class TestMCPTool:
    """Test MCPTool model validation."""

    def test_mcp_tool_all_fields(self) -> None:
        """MCPTool with all fields."""
        tool = MCPTool(
            id="ocr",
            title="OCR Tool",
            description="Extract text from images",
            inputs=["image"],
            outputs=["json"],
            invoke_endpoint="/api/analyze",
            permissions=["read:images"],
        )
        assert tool.id == "ocr"
        assert len(tool.permissions) == 1

    def test_mcp_tool_minimal(self) -> None:
        """MCPTool with required fields only."""
        tool = MCPTool(
            id="motion",
            title="Motion Detector",
            description="Detects motion",
            inputs=["video"],
            outputs=["regions"],
            invoke_endpoint="/v1/motion",
        )
        assert tool.id == "motion"
        assert tool.permissions == []

    def test_mcp_tool_missing_id(self) -> None:
        """MCPTool without id fails."""
        with pytest.raises(ValidationError):
            MCPTool(
                title="Tool",
                description="Description",
                inputs=["input"],
                outputs=["output"],
                invoke_endpoint="/api",
            )

    def test_mcp_tool_serialization(self) -> None:
        """MCPTool serializes to dict."""
        tool = MCPTool(
            id="test",
            title="Test Tool",
            description="Test description",
            inputs=["image"],
            outputs=["json"],
            invoke_endpoint="/test",
        )
        data = tool.model_dump()
        assert data["id"] == "test"
        assert data["title"] == "Test Tool"


class TestMCPManifest:
    """Test MCPManifest model validation."""

    def test_mcp_manifest_with_tools(self) -> None:
        """MCPManifest with tools and server info."""
        manifest = MCPManifest(
            tools=[
                MCPTool(
                    id="ocr",
                    title="OCR",
                    description="Extract text",
                    inputs=["image"],
                    outputs=["json"],
                    invoke_endpoint="/api/ocr",
                ),
                MCPTool(
                    id="motion",
                    title="Motion",
                    description="Detect motion",
                    inputs=["video"],
                    outputs=["regions"],
                    invoke_endpoint="/api/motion",
                ),
            ],
            server={"name": "ForgeServer", "version": "1.0"},
        )
        assert len(manifest.tools) == 2
        assert manifest.server["name"] == "ForgeServer"

    def test_mcp_manifest_empty_tools(self) -> None:
        """MCPManifest with empty tools list."""
        manifest = MCPManifest(
            tools=[],
            server={"name": "Empty"},
        )
        assert len(manifest.tools) == 0

    def test_mcp_manifest_default_version(self) -> None:
        """MCPManifest has default version."""
        manifest = MCPManifest(
            tools=[],
            server={},
        )
        assert manifest.version == "1.0"

    def test_mcp_manifest_custom_version(self) -> None:
        """MCPManifest can have custom version."""
        manifest = MCPManifest(
            tools=[],
            server={},
            version="2.0",
        )
        assert manifest.version == "2.0"


class TestWebSocketMessage:
    """Test WebSocketMessage model validation."""

    def test_websocket_message_all_fields(self) -> None:
        """WebSocketMessage with all fields."""
        message = WebSocketMessage(
            type="result",
            payload={"job_id": "job-001", "result": {"text": "extracted"}},
            timestamp=datetime(2026, 1, 14, 10, 0, 0),
        )
        assert message.type == "result"
        assert message.payload["job_id"] == "job-001"

    def test_websocket_message_default_timestamp(self) -> None:
        """WebSocketMessage has default timestamp."""
        message = WebSocketMessage(
            type="ping",
            payload={},
        )
        assert message.type == "ping"
        assert isinstance(message.timestamp, datetime)

    def test_websocket_message_frame_type(self) -> None:
        """WebSocketMessage with frame type."""
        message = WebSocketMessage(
            type="frame",
            payload={"frame_id": "frame-001", "data": "binary_data"},
        )
        assert message.type == "frame"

    def test_websocket_message_error_type(self) -> None:
        """WebSocketMessage with error type."""
        message = WebSocketMessage(
            type="error",
            payload={"code": "INVALID_INPUT", "message": "Invalid input"},
        )
        assert message.type == "error"
        assert message.payload["message"] == "Invalid input"

    def test_websocket_message_status_type(self) -> None:
        """WebSocketMessage with status type."""
        message = WebSocketMessage(
            type="status",
            payload={"status": "processing", "progress": 50},
        )
        assert message.payload["progress"] == 50

    def test_websocket_message_with_complex_payload(self) -> None:
        """WebSocketMessage can have complex payload."""
        message = WebSocketMessage(
            type="result",
            payload={
                "job_id": "job-002",
                "results": [
                    {"type": "text", "content": "Line 1"},
                    {"type": "text", "content": "Line 2"},
                ],
                "metadata": {
                    "processing_time_ms": 1234,
                    "confidence": 0.95,
                },
            },
        )
        assert len(message.payload["results"]) == 2
        assert message.payload["metadata"]["confidence"] == 0.95

    def test_websocket_message_serialization(self) -> None:
        """WebSocketMessage serializes to dict."""
        message = WebSocketMessage(
            type="ping",
            payload={"id": "ping-001"},
        )
        data = message.model_dump()
        assert data["type"] == "ping"
        assert isinstance(data["timestamp"], datetime)

    def test_websocket_message_required_fields(self) -> None:
        """WebSocketMessage requires type and payload."""
        with pytest.raises(ValidationError):
            WebSocketMessage(type="test")  # missing payload

        with pytest.raises(ValidationError):
            WebSocketMessage(payload={})  # missing type


class TestModelConstraints:
    """Test validation constraints across models."""

    def test_job_response_status_enum_constraint(self) -> None:
        """JobResponse status must be valid enum value."""
        with pytest.raises(ValidationError):
            JobResponse(
                job_id="job",
                status="unknown_status",
                plugin="ocr",
                created_at=datetime.now(),
            )

    def test_plugin_metadata_name_min_length(self) -> None:
        """PluginMetadata name has minimum length constraint."""
        # Single character should work
        metadata = PluginMetadata(
            name="a",
            description="Single char plugin",
        )
        assert metadata.name == "a"

    def test_plugin_metadata_description_min_length(self) -> None:
        """PluginMetadata description has minimum length constraint."""
        # Single character should work
        metadata = PluginMetadata(
            name="plugin",
            description="a",
        )
        assert metadata.description == "a"

    def test_analyze_request_empty_options(self) -> None:
        """AnalyzeRequest options can be empty dict."""
        request = AnalyzeRequest(options={})
        assert request.options == {}

    def test_model_immutability(self) -> None:
        """Models are not immutable by default (Pydantic v2)."""
        response = JobResponse(
            job_id="job-001",
            status=JobStatus.DONE,
            plugin="ocr",
            created_at=datetime.now(),
        )
        # Pydantic v2 allows mutation by default
        response.progress = 100
        assert response.progress == 100
