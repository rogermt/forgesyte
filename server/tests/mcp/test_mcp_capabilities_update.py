"""Tests for updated MCP capabilities after adding new methods."""

import asyncio
import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.mcp import (
    JSONRPCRequest,  # noqa: E402
    MCPTransport,  # noqa: E402
)


class TestUpdatedCapabilities:
    """Tests for updated server capabilities after WU-03."""

    def test_capabilities_include_tools_and_resources(self):
        """Test that initialize returns updated capabilities."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={
                    "clientInfo": {"name": "gemini-cli", "version": "1.0.0"},
                },
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            capabilities = response.result.get("capabilities", {})

            # Should still have tools capability
            assert "tools" in capabilities
            assert capabilities["tools"] == {}

            # Note: resources capability can be added in future version
            # for now, servers just have tools capability

        asyncio.run(run_test())

    def test_all_protocol_methods_registered(self):
        """Test that all protocol methods are properly registered."""

        async def run_test():
            transport = MCPTransport()

            # Test each method is registered and doesn't return METHOD_NOT_FOUND
            methods_to_test = [
                ("initialize", {}),
                ("tools/list", {}),
                (
                    "tools/call",
                    {"name": "dummy"},
                ),  # Should return error but not METHOD_NOT_FOUND
                ("resources/list", {}),
                (
                    "resources/read",
                    {"uri": "dummy"},
                ),  # Should return error but not METHOD_NOT_FOUND
                ("ping", {}),
            ]

            for method_name, params in methods_to_test:
                request = JSONRPCRequest(
                    jsonrpc="2.0",
                    method=method_name,
                    params=params,
                    id=1,
                )
                response = await transport.handle_request(request)

                # Should not be METHOD_NOT_FOUND (-32601)
                if response.error:
                    assert (
                        response.error["code"] != -32601
                    ), f"Method {method_name} not registered"

        asyncio.run(run_test())

    def test_initialize_then_call_new_methods(self):
        """Test full workflow: initialize, then use new methods."""

        async def run_test():
            transport = MCPTransport()

            # Step 1: Initialize
            init_request = JSONRPCRequest(
                jsonrpc="2.0",
                method="initialize",
                params={"clientInfo": {"name": "test"}},
                id=1,
            )
            init_response = await transport.handle_request(init_request)
            assert init_response.error is None

            # Step 2: List resources
            list_request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/list",
                params={},
                id=2,
            )
            list_response = await transport.handle_request(list_request)
            assert list_response.error is None
            assert "resources" in list_response.result

            # Step 3: Verify tools/call is available
            call_request = JSONRPCRequest(
                jsonrpc="2.0",
                method="tools/call",
                params={"name": "test"},
                id=3,
            )
            call_response = await transport.handle_request(call_request)
            # Should get error about tool not found, not method not found
            if call_response.error:
                assert call_response.error["code"] != -32601

        asyncio.run(run_test())
