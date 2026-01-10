"""HTTP transport layer for JSON-RPC 2.0 MCP protocol."""

import logging
from typing import Any, Dict

from .mcp_jsonrpc import (
    JSONRPCError,
    JSONRPCErrorCode,
    JSONRPCRequest,
    JSONRPCResponse,
)

logger = logging.getLogger(__name__)


class MCPTransportError(JSONRPCError):
    """Transport-level error that can be converted to JSON-RPC error response."""

    pass


class MCPTransport:
    """JSON-RPC 2.0 HTTP transport handler for MCP protocol.

    Handles incoming JSON-RPC requests and routes them to appropriate
    protocol handlers. Returns properly formatted JSON-RPC responses.

    Example:
        transport = MCPTransport()
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="initialize",
            params={"clientInfo": {...}},
            id=1
        )
        response = await transport.handle_request(request)
    """

    def __init__(self) -> None:
        """Initialize the transport layer."""
        self._method_handlers: Dict[str, Any] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register standard JSON-RPC method handlers."""
        # Handlers will be registered by subclasses or via decorator
        # For now, keep empty - handlers added in WU-02
        pass

    async def handle_request(
        self,
        request: JSONRPCRequest,
    ) -> JSONRPCResponse:
        """Handle a JSON-RPC request and return response.

        Args:
            request: JSONRPCRequest with method and params

        Returns:
            JSONRPCResponse with result or error

        Note:
            For notifications (request.id is None), response.id will also be None.
            Error responses use standard JSON-RPC error codes.
        """
        try:
            # Route to appropriate handler
            response = await self._route_request(request)
            return response
        except MCPTransportError as e:
            # Transport-level error (invalid method, params, etc.)
            logger.warning(f"Transport error: {e.message}", extra={"code": e.code})
            return JSONRPCResponse(
                jsonrpc="2.0",
                error=e.model_dump(exclude_none=True),
                id=request.id,
            )
        except Exception:
            # Unexpected error
            logger.exception("Unexpected error in transport handler")
            error = JSONRPCError(
                code=JSONRPCErrorCode.INTERNAL_ERROR,
                message="Internal server error",
            )
            return JSONRPCResponse(
                jsonrpc="2.0",
                error=error.model_dump(exclude_none=True),
                id=request.id,
            )

    async def _route_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Route request to appropriate handler.

        Args:
            request: JSONRPCRequest to route

        Returns:
            JSONRPCResponse from handler

        Raises:
            MCPTransportError: If method not found or invalid params
        """
        method = request.method

        # Check if handler exists
        if method not in self._method_handlers:
            raise MCPTransportError(
                code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                message=f'The method "{method}" does not exist / is not available',
            )

        # Get handler
        handler = self._method_handlers[method]

        try:
            # Call handler with params
            result = await handler(request.params)

            # Return success response
            return JSONRPCResponse(
                jsonrpc="2.0",
                result=result,
                id=request.id,
            )
        except MCPTransportError:
            # Re-raise transport errors
            raise
        except TypeError as e:
            # Invalid params (e.g., missing required fields)
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message="Invalid method parameter(s)",
                data={"error": str(e)},
            ) from e

    def register_handler(
        self,
        method: str,
        handler: Any,
    ) -> None:
        """Register a handler for a method.

        Args:
            method: Method name (e.g., "initialize", "tools/list")
            handler: Async callable that takes params dict and returns result dict
        """
        self._method_handlers[method] = handler
        logger.debug(f"Registered handler for method: {method}")
