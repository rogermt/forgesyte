"""Tests for JSON-RPC 2.0 protocol implementation."""

import json
import os
import sys

import pytest
from pydantic import ValidationError

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp_jsonrpc import (  # noqa: E402
    JSONRPCError,
    JSONRPCErrorCode,
    JSONRPCRequest,
    JSONRPCResponse,
)


class TestJSONRPCRequest:
    """Test JSON-RPC 2.0 request validation."""

    def test_valid_request_with_params_and_id(self) -> None:
        """Test valid request with params and id."""
        data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"clientInfo": {"name": "test"}},
            "id": 1,
        }
        req = JSONRPCRequest(**data)
        assert req.jsonrpc == "2.0"
        assert req.method == "initialize"
        assert req.params == {"clientInfo": {"name": "test"}}
        assert req.id == 1

    def test_valid_request_with_string_id(self) -> None:
        """Test valid request with string id."""
        data = {
            "jsonrpc": "2.0",
            "method": "ping",
            "id": "request-1",
        }
        req = JSONRPCRequest(**data)
        assert req.jsonrpc == "2.0"
        assert req.method == "ping"
        assert req.id == "request-1"
        assert req.params == {}

    def test_valid_notification_without_id(self) -> None:
        """Test valid notification (no id field)."""
        data = {
            "jsonrpc": "2.0",
            "method": "ping",
        }
        req = JSONRPCRequest(**data)
        assert req.jsonrpc == "2.0"
        assert req.method == "ping"
        assert req.id is None
        assert req.params == {}

    def test_valid_request_empty_params(self) -> None:
        """Test request with explicitly empty params."""
        data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1,
        }
        req = JSONRPCRequest(**data)
        assert req.params == {}

    def test_missing_jsonrpc_field(self) -> None:
        """Test that missing jsonrpc field raises validation error."""
        data = {
            "method": "initialize",
            "id": 1,
        }
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(**data)
        assert "jsonrpc" in str(exc_info.value)

    def test_missing_method_field(self) -> None:
        """Test that missing method field raises validation error."""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
        }
        with pytest.raises(ValidationError) as exc_info:
            JSONRPCRequest(**data)
        assert "method" in str(exc_info.value)

    def test_invalid_jsonrpc_version(self) -> None:
        """Test that invalid jsonrpc version raises validation error."""
        data = {
            "jsonrpc": "1.0",
            "method": "test",
            "id": 1,
        }
        with pytest.raises(ValidationError):
            JSONRPCRequest(**data)

    def test_empty_method(self) -> None:
        """Test that empty method raises validation error."""
        data = {
            "jsonrpc": "2.0",
            "method": "",
            "id": 1,
        }
        with pytest.raises(ValidationError):
            JSONRPCRequest(**data)

    def test_id_can_be_none_explicitly(self) -> None:
        """Test that id can be explicitly None."""
        data = {
            "jsonrpc": "2.0",
            "method": "test",
            "id": None,
        }
        req = JSONRPCRequest(**data)
        assert req.id is None

    def test_params_with_nested_object(self) -> None:
        """Test params with nested object structure."""
        data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "ocr",
                "arguments": {"image": "/path/to/image.png", "options": {"lang": "en"}},
            },
            "id": 1,
        }
        req = JSONRPCRequest(**data)
        assert req.params["arguments"]["options"]["lang"] == "en"

    def test_model_dump_excludes_none(self) -> None:
        """Test that model can be dumped with exclude_none."""
        data = {
            "jsonrpc": "2.0",
            "method": "ping",
        }
        req = JSONRPCRequest(**data)
        dumped = req.model_dump(exclude_none=True)
        assert "id" not in dumped
        assert dumped["jsonrpc"] == "2.0"
        assert dumped["method"] == "ping"


class TestJSONRPCError:
    """Test JSON-RPC 2.0 error responses."""

    def test_error_parse_error(self) -> None:
        """Test parse error with standard code and message."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.PARSE_ERROR,
            message="Invalid JSON was received",
        )
        assert error.code == -32700
        assert error.message == "Invalid JSON was received"

    def test_error_invalid_request(self) -> None:
        """Test invalid request error."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.INVALID_REQUEST,
            message="The JSON sent is not a valid Request object",
        )
        assert error.code == -32600

    def test_error_method_not_found(self) -> None:
        """Test method not found error."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            message="The method does not exist / is not available",
        )
        assert error.code == -32601

    def test_error_invalid_params(self) -> None:
        """Test invalid params error."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.INVALID_PARAMS,
            message="Invalid method parameter(s)",
        )
        assert error.code == -32602

    def test_error_internal_error(self) -> None:
        """Test internal error."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.INTERNAL_ERROR,
            message="Internal JSON-RPC error",
        )
        assert error.code == -32603

    def test_error_server_error(self) -> None:
        """Test server error (custom error code)."""
        error = JSONRPCError(code=-32000, message="Server error")
        assert error.code == -32000
        assert error.message == "Server error"

    def test_error_with_data(self) -> None:
        """Test error with additional data."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.INVALID_PARAMS,
            message="Invalid parameters",
            data={"expected": "array", "received": "string"},
        )
        assert error.data == {"expected": "array", "received": "string"}

    def test_error_model_dump(self) -> None:
        """Test error can be dumped to dict."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
        )
        dumped = error.model_dump()
        assert dumped["code"] == -32601
        assert dumped["message"] == "Method not found"


class TestJSONRPCResponse:
    """Test JSON-RPC 2.0 response validation."""

    def test_successful_response_with_result(self) -> None:
        """Test successful response with result."""
        data = {
            "jsonrpc": "2.0",
            "result": {"tools": []},
            "id": 1,
        }
        resp = JSONRPCResponse(**data)
        assert resp.jsonrpc == "2.0"
        assert resp.result == {"tools": []}
        assert resp.error is None
        assert resp.id == 1

    def test_error_response(self) -> None:
        """Test error response."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
        )
        data = {
            "jsonrpc": "2.0",
            "error": error.model_dump(),
            "id": 1,
        }
        resp = JSONRPCResponse(**data)
        assert resp.jsonrpc == "2.0"
        assert resp.result is None
        assert resp.error is not None
        assert isinstance(resp.error, dict)
        assert resp.error.get("code") == -32601

    def test_response_with_null_result(self) -> None:
        """Test response with null result."""
        data = {
            "jsonrpc": "2.0",
            "result": None,
            "id": 1,
        }
        resp = JSONRPCResponse(**data)
        assert resp.result is None

    def test_response_result_and_error_mutually_exclusive_result(self) -> None:
        """Test response with both result and error (both accepted by Pydantic)."""
        error_dict = {
            "code": -32601,
            "message": "Method not found",
        }
        # When result is set and error is set, both are accepted by Pydantic
        # but in practice only one should be used
        data = {
            "jsonrpc": "2.0",
            "result": {"data": "test"},
            "error": error_dict,
            "id": 1,
        }
        resp = JSONRPCResponse(**data)
        # Both are accepted, but semantically only one should be used
        assert resp.result is not None
        assert resp.error is not None

    def test_response_with_string_id(self) -> None:
        """Test response with string id."""
        data = {
            "jsonrpc": "2.0",
            "result": {},
            "id": "req-1",
        }
        resp = JSONRPCResponse(**data)
        assert resp.id == "req-1"

    def test_response_without_id(self) -> None:
        """Test response without id (edge case)."""
        data = {
            "jsonrpc": "2.0",
            "result": {},
            "id": None,
        }
        resp = JSONRPCResponse(**data)
        assert resp.id is None

    def test_response_exclude_none(self) -> None:
        """Test response excludes None fields when dumped."""
        resp = JSONRPCResponse(
            jsonrpc="2.0",
            result={"data": "test"},
            id=1,
        )
        dumped = resp.model_dump(exclude_none=True)
        assert "error" not in dumped
        assert dumped["result"] == {"data": "test"}

    def test_response_error_exclude_none(self) -> None:
        """Test error response excludes None fields when dumped."""
        error = JSONRPCError(
            code=JSONRPCErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
        )
        resp = JSONRPCResponse(
            jsonrpc="2.0",
            error=error.model_dump(exclude_none=True),
            id=1,
        )
        dumped = resp.model_dump(exclude_none=True)
        assert "result" not in dumped
        assert dumped["error"]["code"] == -32601

    def test_response_with_complex_result(self) -> None:
        """Test response with complex nested result."""
        result = {
            "tools": [
                {
                    "id": "ocr",
                    "title": "OCR Tool",
                    "description": "Optical character recognition",
                    "inputs": ["image"],
                    "outputs": ["text"],
                }
            ]
        }
        resp = JSONRPCResponse(jsonrpc="2.0", result=result, id=1)
        assert resp.result is not None
        assert isinstance(resp.result, dict)
        assert len(resp.result["tools"]) == 1
        assert resp.result["tools"][0]["id"] == "ocr"


class TestJSONRPCProtocol:
    """Test JSON-RPC 2.0 protocol compliance."""

    def test_request_serialization_roundtrip(self) -> None:
        """Test request can be serialized and deserialized."""
        original = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/list",
            params={},
            id=1,
        )
        serialized = json.dumps(original.model_dump(exclude_none=True))
        deserialized = JSONRPCRequest(**json.loads(serialized))
        assert deserialized.method == original.method
        assert deserialized.id == original.id

    def test_response_serialization_roundtrip(self) -> None:
        """Test response can be serialized and deserialized."""
        original = JSONRPCResponse(
            jsonrpc="2.0",
            result={"tools": []},
            id=1,
        )
        serialized = json.dumps(original.model_dump(exclude_none=True))
        deserialized = JSONRPCResponse(**json.loads(serialized))
        assert deserialized.result == original.result
        assert deserialized.id == original.id

    def test_error_code_constants(self) -> None:
        """Test all JSON-RPC 2.0 error codes are correctly defined."""
        assert JSONRPCErrorCode.PARSE_ERROR == -32700
        assert JSONRPCErrorCode.INVALID_REQUEST == -32600
        assert JSONRPCErrorCode.METHOD_NOT_FOUND == -32601
        assert JSONRPCErrorCode.INVALID_PARAMS == -32602
        assert JSONRPCErrorCode.INTERNAL_ERROR == -32603

    def test_protocol_version_always_2_0(self) -> None:
        """Test that jsonrpc field must be '2.0'."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="1.0", method="test", id=1)

    def test_empty_notification(self) -> None:
        """Test valid notification (request without id)."""
        req = JSONRPCRequest(jsonrpc="2.0", method="ping")
        assert req.id is None
        dumped = req.model_dump(exclude_none=True)
        assert "id" not in dumped


class TestJSONRPCEdgeCases:
    """Test edge cases and error conditions."""

    def test_request_with_zero_id(self) -> None:
        """Test request with id of 0 (valid in JSON-RPC)."""
        req = JSONRPCRequest(jsonrpc="2.0", method="test", id=0)
        assert req.id == 0

    def test_request_with_false_params(self) -> None:
        """Test request with params field as empty dict."""
        req = JSONRPCRequest(jsonrpc="2.0", method="test", params={}, id=1)
        assert req.params == {}

    def test_error_with_integer_code_outside_range(self) -> None:
        """Test custom error code (not reserved range)."""
        error = JSONRPCError(code=-32000, message="Custom error")
        assert error.code == -32000

    def test_large_request_payload(self) -> None:
        """Test request with large params payload."""
        large_params = {
            "data": "x" * 10000,
            "nested": {"level1": {"level2": {"level3": "value"}}},
        }
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="test",
            params=large_params,
            id=1,
        )
        assert len(req.params["data"]) == 10000

    def test_request_with_array_id(self) -> None:
        """Test that array cannot be used as id."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="2.0", method="test", id=[1, 2, 3])

    def test_request_with_object_id(self) -> None:
        """Test that object cannot be used as id."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="2.0", method="test", id={"x": 1})

    def test_special_characters_in_method_name(self) -> None:
        """Test method names with slashes and special characters."""
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=1,
        )
        assert req.method == "tools/call"

    def test_unicode_in_params(self) -> None:
        """Test unicode characters in params."""
        req = JSONRPCRequest(
            jsonrpc="2.0",
            method="test",
            params={"text": "こんにちは世界 🌍"},
            id=1,
        )
        assert req.params["text"] == "こんにちは世界 🌍"
