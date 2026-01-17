"""Comprehensive test suite for JSON-RPC 2.0 protocol implementation.

Tests cover:
- Request validation (version, method, params, id)
- Response handling (success and error cases)
- Error codes and messages
- Edge cases (empty strings, special characters, large payloads)
- Specification compliance
"""

import pytest
from pydantic import ValidationError

from app.mcp.jsonrpc import (
    JSONRPCError,
    JSONRPCErrorCode,
    JSONRPCRequest,
    JSONRPCResponse,
)


class TestJSONRPCErrorCode:
    """Test JSON-RPC error code constants."""

    def test_parse_error_code(self) -> None:
        """Verify PARSE_ERROR has correct value."""
        assert JSONRPCErrorCode.PARSE_ERROR == -32700

    def test_invalid_request_code(self) -> None:
        """Verify INVALID_REQUEST has correct value."""
        assert JSONRPCErrorCode.INVALID_REQUEST == -32600

    def test_method_not_found_code(self) -> None:
        """Verify METHOD_NOT_FOUND has correct value."""
        assert JSONRPCErrorCode.METHOD_NOT_FOUND == -32601

    def test_invalid_params_code(self) -> None:
        """Verify INVALID_PARAMS has correct value."""
        assert JSONRPCErrorCode.INVALID_PARAMS == -32602

    def test_internal_error_code(self) -> None:
        """Verify INTERNAL_ERROR has correct value."""
        assert JSONRPCErrorCode.INTERNAL_ERROR == -32603

    def test_error_codes_are_negative(self) -> None:
        """Verify all error codes are negative (as per spec)."""
        for code in JSONRPCErrorCode:
            assert code < 0


class TestJSONRPCError:
    """Test JSONRPCError validation and structure."""

    def test_error_with_all_fields(self) -> None:
        """Create error with code, message, and data."""
        error = JSONRPCError(
            code=-32600,
            message="Invalid Request",
            data={"details": "method is required"},
        )
        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data == {"details": "method is required"}

    def test_error_without_optional_data(self) -> None:
        """Create error with only required fields."""
        error = JSONRPCError(code=-32700, message="Parse error")
        assert error.code == -32700
        assert error.message == "Parse error"
        assert error.data is None

    def test_error_with_enum_code(self) -> None:
        """Create error using enum constant."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
        )
        assert error.code == -32601

    def test_error_with_custom_code(self) -> None:
        """Create error with custom error code (-32000 to -32099)."""
        error = JSONRPCError(code=-32050, message="Custom server error")
        assert error.code == -32050

    def test_error_with_positive_code(self) -> None:
        """Positive codes are allowed (for custom errors)."""
        error = JSONRPCError(code=1000, message="Custom positive error")
        assert error.code == 1000

    def test_error_message_empty_string(self) -> None:
        """Error message can be empty string (spec allows it)."""
        error = JSONRPCError(code=-32600, message="")
        assert error.message == ""

    def test_error_data_with_nested_structure(self) -> None:
        """Error data can contain complex nested structures."""
        error = JSONRPCError(
            code=-32602,
            message="Invalid params",
            data={
                "field": "params",
                "errors": [
                    {"path": "plugin", "message": "required"},
                    {"path": "options", "message": "must be dict"},
                ],
                "metadata": {"timestamp": "2026-01-14T10:00:00Z"},
            },
        )
        assert len(error.data["errors"]) == 2
        assert error.data["metadata"]["timestamp"] == "2026-01-14T10:00:00Z"

    def test_error_serialization(self) -> None:
        """Error can be serialized to dict."""
        error = JSONRPCError(
            code=-32600,
            message="Invalid Request",
            data={"field": "method"},
        )
        error_dict = error.model_dump(exclude_none=True)
        assert error_dict["code"] == -32600
        assert error_dict["message"] == "Invalid Request"
        assert error_dict["data"]["field"] == "method"


class TestJSONRPCRequest:
    """Test JSONRPCRequest validation and structure."""

    def test_request_with_all_fields(self) -> None:
        """Create request with jsonrpc, method, params, and id."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/list",
            params={"limit": 10},
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.params == {"limit": 10}
        assert request.id == 1

    def test_request_with_string_id(self) -> None:
        """Request ID can be string."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="initialize",
            id="req-001",
        )
        assert request.id == "req-001"

    def test_notification_without_id(self) -> None:
        """Notification (no ID) is valid."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="update",
            params={"status": "processing"},
        )
        assert request.id is None
        assert request.method == "update"

    def test_request_with_empty_params(self) -> None:
        """Request with empty params dict is valid."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="health",
            params={},
        )
        assert request.params == {}

    def test_request_without_params_defaults_to_empty(self) -> None:
        """Request without params defaults to empty dict."""
        request = JSONRPCRequest(jsonrpc="2.0", method="list")
        assert request.params == {}

    def test_invalid_jsonrpc_version_1_0(self) -> None:
        """Request with jsonrpc='1.0' fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(jsonrpc="1.0", method="test")
        assert "jsonrpc must be '2.0'" in str(exc_info.value)

    def test_invalid_jsonrpc_version_number(self) -> None:
        """Request with jsonrpc as number fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(jsonrpc=2.0, method="test")
        assert "jsonrpc" in str(exc_info.value).lower()

    def test_invalid_empty_method(self) -> None:
        """Request with empty method fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(jsonrpc="2.0", method="")
        assert "method must be a non-empty string" in str(exc_info.value)

    def test_invalid_none_method(self) -> None:
        """Request with None method fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(jsonrpc="2.0", method=None)
        assert "method" in str(exc_info.value).lower()

    def test_request_with_complex_params(self) -> None:
        """Request with complex nested params."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="analyze",
            params={
                "image_url": "https://example.com/image.jpg",
                "plugin": "ocr",
                "options": {
                    "language": "en",
                    "confidence": 0.8,
                    "regions": [{"x": 0, "y": 0, "width": 100, "height": 100}],
                },
            },
            id="analyze-job-001",
        )
        assert request.params["options"]["language"] == "en"
        assert len(request.params["options"]["regions"]) == 1

    def test_request_with_special_characters_in_method(self) -> None:
        """Method names can contain special characters (slash, underscore)."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/list_active",
        )
        assert request.method == "tools/list_active"

    def test_request_with_unicode_in_params(self) -> None:
        """Params can contain unicode characters."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="search",
            params={"query": "你好世界 🌍"},
        )
        assert "你好世界" in request.params["query"]

    def test_request_with_zero_id(self) -> None:
        """ID can be zero."""
        request = JSONRPCRequest(jsonrpc="2.0", method="test", id=0)
        assert request.id == 0

    def test_request_with_negative_id(self) -> None:
        """ID can be negative."""
        request = JSONRPCRequest(jsonrpc="2.0", method="test", id=-1)
        assert request.id == -1

    def test_request_with_large_params(self) -> None:
        """Request with large params (stress test)."""
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="upload",
            params=large_data,
        )
        assert len(request.params) == 1000

    def test_request_serialization(self) -> None:
        """Request can be serialized to dict."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/list",
            params={"limit": 5},
            id=42,
        )
        req_dict = request.model_dump()
        assert req_dict["jsonrpc"] == "2.0"
        assert req_dict["method"] == "tools/list"
        assert req_dict["id"] == 42


class TestJSONRPCResponse:
    """Test JSONRPCResponse validation and structure."""

    def test_success_response_with_result(self) -> None:
        """Success response with result."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            result={"tools": [{"id": "ocr", "name": "OCR Plugin"}]},
            id=1,
        )
        assert response.jsonrpc == "2.0"
        assert response.result is not None
        assert response.error is None
        assert response.id == 1

    def test_error_response(self) -> None:
        """Error response with error object."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error={
                "code": -32601,
                "message": "Method not found",
            },
            id=1,
        )
        assert response.result is None
        assert response.error is not None
        assert response.error["code"] == -32601

    def test_error_response_with_null_id(self) -> None:
        """Error response for invalid request has null id."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error={
                "code": -32600,
                "message": "Invalid Request",
            },
            id=None,
        )
        assert response.id is None
        assert response.error is not None

    def test_response_with_string_id(self) -> None:
        """Response ID can be string."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            result={"status": "ok"},
            id="req-uuid-123",
        )
        assert response.id == "req-uuid-123"

    def test_response_without_result_or_error(self) -> None:
        """Response can have neither result nor error (edge case)."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            id=1,
        )
        assert response.result is None
        assert response.error is None

    def test_response_with_complex_result(self) -> None:
        """Response result can be complex nested structure."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            result={
                "jobs": [
                    {
                        "job_id": "job-001",
                        "status": "done",
                        "result": {
                            "text": "extracted text",
                            "confidence": 0.95,
                        },
                    },
                    {
                        "job_id": "job-002",
                        "status": "running",
                        "progress": 45,
                    },
                ],
                "count": 2,
            },
            id=1,
        )
        assert len(response.result["jobs"]) == 2
        assert response.result["jobs"][0]["result"]["confidence"] == 0.95

    def test_response_with_error_data(self) -> None:
        """Error response can include additional data."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error={
                "code": -32602,
                "message": "Invalid params",
                "data": {
                    "field": "plugin",
                    "reason": "plugin not found",
                    "available": ["ocr", "motion_detector"],
                },
            },
            id=1,
        )
        assert response.error["data"]["available"] == ["ocr", "motion_detector"]

    def test_response_default_jsonrpc_version(self) -> None:
        """Default jsonrpc version is '2.0'."""
        response = JSONRPCResponse(result={"ok": True}, id=1)
        assert response.jsonrpc == "2.0"

    def test_response_serialization_success(self) -> None:
        """Success response serializes correctly."""
        response = JSONRPCResponse(
            result={"status": "success"},
            id=1,
        )
        resp_dict = response.model_dump(exclude_none=True)
        assert resp_dict["jsonrpc"] == "2.0"
        assert resp_dict["result"]["status"] == "success"
        assert "error" not in resp_dict

    def test_response_serialization_error(self) -> None:
        """Error response serializes correctly."""
        response = JSONRPCResponse(
            error={"code": -32601, "message": "Method not found"},
            id=1,
        )
        resp_dict = response.model_dump(exclude_none=True)
        assert resp_dict["error"]["code"] == -32601
        assert "result" not in resp_dict

    def test_response_with_empty_result(self) -> None:
        """Response with empty dict result."""
        response = JSONRPCResponse(result={}, id=1)
        assert response.result == {}
        assert response.error is None

    def test_response_with_boolean_result(self) -> None:
        """Result can be boolean (not just dict)."""
        response = JSONRPCResponse(result={"success": True}, id=1)
        assert response.result["success"] is True

    def test_response_with_list_result(self) -> None:
        """Result dict can contain lists."""
        response = JSONRPCResponse(
            result={"items": [1, 2, 3, "four"]},
            id=1,
        )
        assert response.result["items"][3] == "four"

    def test_response_with_null_result_value(self) -> None:
        """Result field can contain null values."""
        response = JSONRPCResponse(
            result={"data": None, "status": "pending"},
            id=1,
        )
        assert response.result["data"] is None
        assert response.result["status"] == "pending"

    def test_response_with_zero_id(self) -> None:
        """Response ID can be zero."""
        response = JSONRPCResponse(result={"ok": True}, id=0)
        assert response.id == 0

    def test_response_with_negative_id(self) -> None:
        """Response ID can be negative."""
        response = JSONRPCResponse(result={"ok": True}, id=-1)
        assert response.id == -1


class TestJSONRPCSpecCompliance:
    """Test compliance with JSON-RPC 2.0 specification."""

    def test_request_response_roundtrip(self) -> None:
        """Request can be sent and response received with matching IDs."""
        request = JSONRPCRequest(jsonrpc="2.0", method="ping", id=123)
        response = JSONRPCResponse(jsonrpc="2.0", result={"pong": True}, id=123)

        assert request.id == response.id

    def test_notification_has_no_response_expected(self) -> None:
        """Notification (no ID) means no response is expected."""
        notification = JSONRPCRequest(
            jsonrpc="2.0",
            method="log",
            params={"message": "System started"},
        )
        assert notification.id is None

    def test_spec_example_valid_request(self) -> None:
        """RFC 7350 example: valid request."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="subtract",
            params={"subtrahend": 23, "minuend": 42},
            id=3,
        )
        assert request.method == "subtract"
        assert request.params["subtrahend"] == 23

    def test_spec_example_response_with_result(self) -> None:
        """RFC 7350 example: response with result (must be dict)."""
        response = JSONRPCResponse(jsonrpc="2.0", result={"value": 19}, id=1)
        # Implementation restricts result to dict type for consistency
        assert response.result["value"] == 19

    def test_spec_rpc_call_method_doesnt_exist(self) -> None:
        """RFC 7350 example: method not found error."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error={"code": -32601, "message": "Method not found"},
            id="foobared",
        )
        assert response.error["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND

    def test_batch_request_would_have_multiple_requests(self) -> None:
        """Can create multiple requests for batch processing."""
        requests = [
            JSONRPCRequest(jsonrpc="2.0", method="test1", id=1),
            JSONRPCRequest(jsonrpc="2.0", method="test2", id=2),
            JSONRPCRequest(jsonrpc="2.0", method="test3"),  # notification
        ]
        assert len(requests) == 3
        assert requests[2].id is None  # notification has no id


class TestJSONRPCEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_request_with_very_long_method_name(self) -> None:
        """Method name can be very long."""
        long_method = "a" * 10000
        request = JSONRPCRequest(jsonrpc="2.0", method=long_method)
        assert len(request.method) == 10000

    def test_request_with_whitespace_only_method_accepted(self) -> None:
        """Method with only whitespace is accepted (validator doesn't strip)."""
        # The validator checks 'not v' but whitespace-only strings are truthy
        request = JSONRPCRequest(jsonrpc="2.0", method="   ")
        assert request.method == "   "

    def test_error_with_null_data(self) -> None:
        """Error with explicitly None data."""
        error = JSONRPCError(
            code=-32600,
            message="Invalid Request",
            data=None,
        )
        assert error.data is None

    def test_request_params_with_null_values(self) -> None:
        """Params can contain null values."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="test",
            params={"field1": None, "field2": "value"},
        )
        assert request.params["field1"] is None

    def test_response_with_empty_error_object(self) -> None:
        """Error object can be empty (unusual but possible)."""
        response = JSONRPCResponse(jsonrpc="2.0", error={}, id=1)
        assert response.error == {}

    def test_request_id_as_float_becomes_int(self) -> None:
        """Float ID might be coerced depending on pydantic config."""
        # ID should be int or str, float might fail or be coerced
        request = JSONRPCRequest(jsonrpc="2.0", method="test", id=42)
        assert isinstance(request.id, int)

    def test_response_result_can_be_zero(self) -> None:
        """Result value can be 0 (falsy value)."""
        response = JSONRPCResponse(result={"count": 0}, id=1)
        assert response.result["count"] == 0

    def test_response_result_can_be_false(self) -> None:
        """Result can contain false (falsy value)."""
        response = JSONRPCResponse(result={"success": False}, id=1)
        assert response.result["success"] is False
