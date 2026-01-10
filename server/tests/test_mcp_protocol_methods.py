"""Tests for MCP protocol methods (initialize, tools/list, ping)."""

import asyncio
import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp_jsonrpc import (
    JSONRPCErrorCode,
    JSONRPCRequest,
)  # noqa: E402
from app.mcp_transport import MCPTransport  # noqa: E402


class TestInitializeHandler:
    """Tests for the initialize method handler."""

    def test_initialize_success(self):
        """Test successful initialize request."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={
                    "clientInfo": {"name": "gemini-cli", "version": "1.0.0"},
                    "protocolVersion": "1.0.0",
                },
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.id == 1
            assert response.error is None
            assert response.result is not None
            assert "serverInfo" in response.result
            assert "capabilities" in response.result
            assert response.result["serverInfo"]["name"] == "forgesyte"
            assert response.result["serverInfo"]["version"] == "0.1.0"

        asyncio.run(run_test())

    def test_initialize_with_empty_params(self):
        """Test initialize with empty params (should still work)."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="initialize", params={}, id=2
            )

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.error is None
            assert response.result is not None
            assert "serverInfo" in response.result

        asyncio.run(run_test())

    def test_initialize_capabilities(self):
        """Test that initialize returns correct capabilities."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={"clientInfo": {"name": "test"}},
                id=3,
            )

            response = await transport.handle_request(request)

            # Verify capability structure
            caps = response.result.get("capabilities", {})
            assert "tools" in caps
            assert caps["tools"] is True

        asyncio.run(run_test())


class TestToolsListHandler:
    """Tests for the tools/list method handler."""

    def test_tools_list_success(self):
        """Test successful tools/list request."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="tools/list", params={}, id=4
            )

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.id == 4
            assert response.error is None
            assert response.result is not None
            assert "tools" in response.result
            assert isinstance(response.result["tools"], list)

        asyncio.run(run_test())

    def test_tools_list_returns_tools_from_adapter(self):
        """Test that tools/list returns tools from MCPAdapter."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="tools/list", params={}, id=5
            )

            response = await transport.handle_request(request)

            # Should have tools in response
            tools = response.result.get("tools", [])
            assert isinstance(tools, list)

            # Each tool should have required fields
            for tool in tools:
                assert "id" in tool
                assert "title" in tool
                assert "description" in tool

        asyncio.run(run_test())

    def test_tools_list_with_params_ignored(self):
        """Test that tools/list works even with params (should ignore them)."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/list",
                params={"filter": "somefilter"},
                id=6,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            assert response.result is not None
            assert "tools" in response.result

        asyncio.run(run_test())


class TestPingHandler:
    """Tests for the ping method handler."""

    def test_ping_success(self):
        """Test successful ping request."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(jsonrpc="2.0", method="ping", params={}, id=7)

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.id == 7
            assert response.error is None
            assert response.result is not None

        asyncio.run(run_test())

    def test_ping_response_structure(self):
        """Test that ping returns proper response structure."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(jsonrpc="2.0", method="ping", params={}, id=8)

            response = await transport.handle_request(request)

            result = response.result
            assert "status" in result
            assert result["status"] == "pong"

        asyncio.run(run_test())

    def test_ping_as_notification(self):
        """Test ping as a notification (no id)."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(jsonrpc="2.0", method="ping", params={})

            response = await transport.handle_request(request)

            # Even as notification, should return response with id=None
            assert response.id is None
            assert response.error is None

        asyncio.run(run_test())


class TestProtocolMethodIntegration:
    """Integration tests for protocol methods."""

    def test_initialize_then_tools_list(self):
        """Test initialize followed by tools/list."""

        async def run_test():
            transport = MCPTransport()

            # First initialize
            init_request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={"clientInfo": {"name": "test"}},
                id=1,
            )
            init_response = await transport.handle_request(init_request)
            assert init_response.error is None

            # Then list tools
            tools_request = JSONRPCRequest(
                jsonrpc="2.0", method="tools/list", params={}, id=2
            )
            tools_response = await transport.handle_request(tools_request)
            assert tools_response.error is None
            assert "tools" in tools_response.result

        asyncio.run(run_test())

    def test_unknown_method_returns_error(self):
        """Test that unknown method returns METHOD_NOT_FOUND error."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="unknown/method", params={}, id=9
            )

            response = await transport.handle_request(request)

            assert response.result is None
            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND

        asyncio.run(run_test())


class TestCapabilityNegotiation:
    """Tests for protocol capability negotiation in initialize."""

    def test_initialize_server_capabilities(self):
        """Test that initialize returns server capabilities."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="initialize", params={}, id=10
            )

            response = await transport.handle_request(request)

            capabilities = response.result.get("capabilities", {})

            # Should support tools capability
            assert "tools" in capabilities
            assert capabilities["tools"] is True

        asyncio.run(run_test())

    def test_initialize_server_info(self):
        """Test that initialize returns server info."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0", method="initialize", params={}, id=11
            )

            response = await transport.handle_request(request)

            server_info = response.result.get("serverInfo", {})

            # Should have name, version, protocolVersion
            assert "name" in server_info
            assert "version" in server_info
            assert "protocolVersion" in server_info
            assert server_info["name"] == "forgesyte"

        asyncio.run(run_test())
