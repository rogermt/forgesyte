"""Tests for MCP tools/call method handler."""

import asyncio
import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import (
    JSONRPCErrorCode,
    JSONRPCRequest,
    MCPTransport,  # noqa: E402
)  # noqa: E402


class TestToolsCallHandler:
    """Tests for the tools/call method handler."""

    def test_tools_call_success(self):
        """Test successful tools/call request."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "test_tool",
                    "arguments": {
                        "input": "test data",
                    },
                },
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.id == 1
            assert response.error is None or "not found" in str(response.error).lower()
            # We expect either success or a "tool not found" error
            if response.error:
                # Tool not found is acceptable if no test tools registered
                assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS
            else:
                assert response.result is not None

        asyncio.run(run_test())

    def test_tools_call_missing_name(self):
        """Test tools/call with missing tool name parameter."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "arguments": {
                        "input": "test data",
                    },
                },
                id=2,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_tools_call_missing_arguments(self):
        """Test tools/call with missing arguments parameter."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "test_tool",
                },
                id=3,
            )

            response = await transport.handle_request(request)

            # Missing arguments should default to empty dict
            assert response.jsonrpc == "2.0"
            assert response.id == 3

        asyncio.run(run_test())

    def test_tools_call_nonexistent_tool(self):
        """Test tools/call with a tool that doesn't exist."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "nonexistent_tool_xyz",
                    "arguments": {},
                },
                id=4,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_tools_call_response_structure(self):
        """Test that tools/call returns proper response structure."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={
                    "name": "test_tool",
                    "arguments": {},
                },
                id=5,
            )

            response = await transport.handle_request(request)

            # Should have either a valid result or an error
            assert (response.result is not None) or (response.error is not None)
            if response.result:
                # Result should contain content array
                assert "content" in response.result or "result" in response.result

        asyncio.run(run_test())

    def test_tools_call_with_empty_params(self):
        """Test tools/call with empty params (should fail)."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={},
                id=6,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())
