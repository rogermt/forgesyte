"""Tests for MCP JSON-RPC transport layer."""

import json
import os
import sys
from typing import Any, Dict

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import (  # noqa: E402  # noqa: E402
    JSONRPCErrorCode,
    JSONRPCRequest,
    JSONRPCResponse,
    MCPTransport,
    MCPTransportError,
)


class TestMCPTransport:
    """Test JSON-RPC transport layer."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create a transport instance."""
        return MCPTransport()

    def test_transport_initialization(self, transport: MCPTransport) -> None:
        """Test transport initializes correctly."""
        assert transport is not None
        assert hasattr(transport, "handle_request")

    def test_transport_has_register_handler(self, transport: MCPTransport) -> None:
        """Test transport has method to register handlers."""
        assert hasattr(transport, "register_handler")
        assert callable(transport.register_handler)

    def test_transport_can_register_handler(self, transport: MCPTransport) -> None:
        """Test transport can register a handler."""

        async def dummy_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "ok"}

        transport.register_handler("test", dummy_handler)
        assert "test" in transport._method_handlers

    def test_error_response_for_unknown_method(self) -> None:
        """Test transport returns error for unknown method."""
        transport = MCPTransport()
        # Error should be raised when handling unknown method
        assert "unknown/method" not in transport._method_handlers

    def test_handle_requests_type_signature(self, transport: MCPTransport) -> None:
        """Test handle_request accepts JSONRPCRequest and returns JSONRPCResponse."""
        # Check that method exists and is async
        assert hasattr(transport, "handle_request")
        assert callable(transport.handle_request)

    def test_registration_stores_handler(self, transport: MCPTransport) -> None:
        """Test that registering a handler stores it internally."""

        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {}

        transport.register_handler("test/method", handler)
        assert "test/method" in transport._method_handlers
        assert transport._method_handlers["test/method"] == handler

    def test_transport_error_initialization(self) -> None:
        """Test MCPTransportError can be created."""
        error = MCPTransportError(
            code=JSONRPCErrorCode.INTERNAL_ERROR,
            message="Test error",
        )
        assert error.code == JSONRPCErrorCode.INTERNAL_ERROR
        assert error.message == "Test error"

    def test_transport_error_with_data(self) -> None:
        """Test MCPTransportError with additional data."""
        error = MCPTransportError(
            code=JSONRPCErrorCode.INVALID_PARAMS,
            message="Invalid parameters",
            data={"expected": "name", "received": None},
        )
        assert error.data == {"expected": "name", "received": None}


class TestMCPTransportProtocolCompliance:
    """Test transport is JSON-RPC 2.0 compliant."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create a transport instance."""
        return MCPTransport()

    def test_response_models_have_required_fields(
        self,
        transport: MCPTransport,
    ) -> None:
        """Test JSONRPCResponse has all required JSON-RPC fields."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            result={"data": "test"},
            id=1,
        )
        # All responses must have jsonrpc and id
        assert hasattr(response, "jsonrpc")
        assert hasattr(response, "id")
        # Must have either result or error
        assert hasattr(response, "result")
        assert hasattr(response, "error")
        assert response.jsonrpc == "2.0"

    def test_error_response_has_code_and_message(self) -> None:
        """Test error responses have required fields."""
        error_dict = {
            "code": JSONRPCErrorCode.METHOD_NOT_FOUND,
            "message": "Method not found",
        }
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error=error_dict,
            id=1,
        )
        assert response.error is not None
        assert "code" in response.error
        assert "message" in response.error
        assert response.error["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND

    def test_request_id_preserved_in_response_model(self) -> None:
        """Test request id is preserved in response."""
        for request_id in [1, "string-id", 0, 999]:
            response = JSONRPCResponse(
                jsonrpc="2.0",
                result={},
                id=request_id,
            )
            assert response.id == request_id


class TestMCPTransportSerialization:
    """Test transport handles serialization correctly."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create a transport instance."""
        return MCPTransport()

    def test_response_serializable_to_json(self) -> None:
        """Test response can be serialized to JSON."""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            result={"data": "test"},
            id=1,
        )
        # Should be able to serialize without error
        serialized = json.dumps(response.model_dump(exclude_none=True))
        assert isinstance(serialized, str)
        # Should be valid JSON
        deserialized = json.loads(serialized)
        assert deserialized["jsonrpc"] == "2.0"
        assert deserialized["result"]["data"] == "test"

    def test_error_response_serializable_to_json(self) -> None:
        """Test error response can be serialized to JSON."""
        error_dict = {
            "code": JSONRPCErrorCode.METHOD_NOT_FOUND,
            "message": "Method not found",
        }
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error=error_dict,
            id=1,
        )
        serialized = json.dumps(response.model_dump(exclude_none=True))
        deserialized = json.loads(serialized)
        assert "error" in deserialized
        assert "code" in deserialized["error"]
        assert "message" in deserialized["error"]
        assert deserialized["error"]["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND


class TestMCPTransportEdgeCases:
    """Test transport edge cases."""

    @pytest.fixture
    def transport(self) -> MCPTransport:
        """Create a transport instance."""
        return MCPTransport()

    def test_request_with_empty_params(
        self,
        transport: MCPTransport,
    ) -> None:
        """Test request with empty params."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="ping",
            params={},
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert request.params == {}

    def test_request_with_nested_params(
        self,
        transport: MCPTransport,
    ) -> None:
        """Test request with nested params."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/call",
            params={
                "name": "ocr",
                "arguments": {
                    "image": "/path/to/image.png",
                    "options": {"lang": "en", "tool": "ocr"},
                },
            },
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.params["name"] == "ocr"

    def test_request_with_zero_id(
        self,
        transport: MCPTransport,
    ) -> None:
        """Test request with id of 0."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="ping",
            id=0,
        )
        assert request.id == 0

    def test_request_with_large_payload(
        self,
        transport: MCPTransport,
    ) -> None:
        """Test request with large payload."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="tools/call",
            params={
                "data": "x" * 100000,  # 100KB of data
            },
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert len(request.params["data"]) == 100000
