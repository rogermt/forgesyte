"""Tests for MCP resources/* method handlers."""

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


class TestResourcesListHandler:
    """Tests for the resources/list method handler."""

    def test_resources_list_success(self):
        """Test successful resources/list request."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/list",
                params={},
                id=1,
            )

            response = await transport.handle_request(request)

            assert response.jsonrpc == "2.0"
            assert response.id == 1
            assert response.error is None
            assert response.result is not None
            assert "resources" in response.result
            assert isinstance(response.result["resources"], list)

        asyncio.run(run_test())

    def test_resources_list_returns_list_of_resources(self):
        """Test that resources/list returns properly formatted resources."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/list",
                params={},
                id=2,
            )

            response = await transport.handle_request(request)

            resources = response.result.get("resources", [])
            assert isinstance(resources, list)

            # Each resource should have required fields
            for resource in resources:
                assert "uri" in resource
                assert "name" in resource
                assert "mimeType" in resource

        asyncio.run(run_test())

    def test_resources_list_pagination(self):
        """Test that resources/list supports pagination."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/list",
                params={
                    "cursor": None,
                },
                id=3,
            )

            response = await transport.handle_request(request)

            assert response.error is None
            result = response.result
            # May include nextCursor if more resources available
            if "nextCursor" in result:
                assert result["nextCursor"] is None or isinstance(
                    result["nextCursor"], str
                )

        asyncio.run(run_test())


class TestResourcesReadHandler:
    """Tests for the resources/read method handler."""

    def test_resources_read_missing_uri(self):
        """Test resources/read with missing URI parameter."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/read",
                params={},
                id=4,
            )

            response = await transport.handle_request(request)

            assert response.error is not None
            assert response.error["code"] == JSONRPCErrorCode.INVALID_PARAMS

        asyncio.run(run_test())

    def test_resources_read_nonexistent_resource(self):
        """Test resources/read with nonexistent resource URI."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/read",
                params={
                    "uri": "forgesyte://nonexistent/resource",
                },
                id=5,
            )

            response = await transport.handle_request(request)

            # Should return error for missing resource
            assert response.error is not None

        asyncio.run(run_test())

    def test_resources_read_response_structure(self):
        """Test that resources/read returns proper response structure."""

        async def run_test():
            transport = MCPTransport()
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/read",
                params={
                    "uri": "forgesyte://test/dummy",
                },
                id=6,
            )

            response = await transport.handle_request(request)

            # Response should have either valid result or error
            if response.result:
                assert "contents" in response.result
                assert isinstance(response.result["contents"], list)

        asyncio.run(run_test())


class TestJobResourceHandler:
    """Tests for job-related resource methods."""

    def test_get_job_resource(self):
        """Test getting a job resource."""

        async def run_test():
            transport = MCPTransport()

            # First get job list to find a job URI
            list_request = JSONRPCRequest(
                jsonrpc="2.0",
                method="resources/list",
                params={},
                id=1,
            )

            response = await transport.handle_request(list_request)

            # Resources might include job resources
            resources = response.result.get("resources", [])

            if resources:
                # Try to read first resource
                resource_uri = resources[0].get("uri")
                read_request = JSONRPCRequest(
                    jsonrpc="2.0",
                    method="resources/read",
                    params={
                        "uri": resource_uri,
                    },
                    id=2,
                )

                read_response = await transport.handle_request(read_request)
                # Should either succeed or return error
                assert read_response.id == 2

        asyncio.run(run_test())
