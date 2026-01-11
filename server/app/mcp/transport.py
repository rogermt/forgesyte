"""HTTP transport layer for JSON-RPC 2.0 MCP protocol."""

import logging
from typing import Any, Dict, Optional

from .jsonrpc import (
    JSONRPCError,
    JSONRPCErrorCode,
    JSONRPCRequest,
    JSONRPCResponse,
)

logger = logging.getLogger(__name__)


class MCPTransportError(Exception):
    """Transport-level error that can be converted to JSON-RPC error response.

    Holds error information that can be serialized to JSON-RPC error format.
    """

    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize transport error.

        Args:
            code: JSON-RPC error code
            message: Error message
            data: Optional error data dictionary
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_jsonrpc_error(self) -> JSONRPCError:
        """Convert to JSONRPCError for serialization.

        Returns:
            JSONRPCError object
        """
        return JSONRPCError(
            code=self.code,
            message=self.message,
            data=self.data,
        )


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

    def __init__(self, protocol_handlers: Optional[Any] = None) -> None:
        """Initialize the transport layer.

        Args:
            protocol_handlers: Optional MCPProtocolHandlers instance.
                If None, creates default handlers with default PluginManager.
        """
        self._method_handlers: Dict[str, Any] = {}
        self._protocol_handlers = protocol_handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register standard JSON-RPC method handlers."""
        # Import here to avoid circular imports
        if self._protocol_handlers is None:
            # Create default handlers with lazy-loaded PluginManager
            from ..plugin_loader import PluginManager
            from .handlers import MCPProtocolHandlers

            plugin_manager = PluginManager()
            self._protocol_handlers = MCPProtocolHandlers(plugin_manager)

        # Register core protocol handlers
        self.register_handler("initialize", self._protocol_handlers.initialize)
        self.register_handler("tools/list", self._protocol_handlers.tools_list)
        self.register_handler("tools/call", self._protocol_handlers.tools_call)
        self.register_handler("resources/list", self._protocol_handlers.resources_list)
        self.register_handler("resources/read", self._protocol_handlers.resources_read)
        self.register_handler("ping", self._protocol_handlers.ping)

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
            logger.warning(
                "Transport error",
                extra={
                    "method": request.method,
                    "code": e.code,
                    "error": e.message,
                    "request_id": request.id,
                },
            )
            error = e.to_jsonrpc_error()
            return JSONRPCResponse(
                jsonrpc="2.0",
                error=error.model_dump(exclude_none=True),
                id=request.id,
            )
        except Exception as e:
            # Unexpected error
            logger.exception(
                "Unexpected error in transport handler",
                extra={"method": request.method, "error": str(e)},
            )
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
            logger.debug(
                "Method not found",
                extra={"method": method, "request_id": request.id},
            )
            raise MCPTransportError(
                code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                message=f'The method "{method}" does not exist / is not available',
            )

        # Get handler
        handler = self._method_handlers[method]

        try:
            # Call handler with params
            result = await handler(request.params)

            # Log successful handler execution
            logger.debug(
                "Handler executed successfully",
                extra={"method": method, "request_id": request.id},
            )

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
            logger.warning(
                "Invalid method parameters",
                extra={"method": method, "error": str(e)},
            )
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
        logger.debug(
            "Registered handler for method",
            extra={"method": method},
        )

    async def handle_batch_request(
        self,
        requests: list,
    ) -> list:
        """Handle a batch of JSON-RPC requests.

        Per JSON-RPC 2.0 spec, a batch is an array of request objects.
        Responses are returned in the same order as requests.
        Notifications (requests without id) don't generate responses.

        Args:
            requests: List of request dicts

        Returns:
            List of response dicts (excluding responses to notifications)
        """
        if not requests:
            return []

        logger.debug(
            "Processing batch request",
            extra={"request_count": len(requests)},
        )

        responses = []
        for request_dict in requests:
            try:
                # Parse request
                request = JSONRPCRequest(**request_dict)

                # Handle request
                response = await self.handle_request(request)

                # Only include response if request had an id (not a notification)
                if request.id is not None:
                    responses.append(response.model_dump(exclude_none=True))
            except Exception as e:
                # If we can't even parse the request, create error response
                logger.exception(
                    "Error processing batch request",
                    extra={"error": str(e)},
                )
                error = JSONRPCError(
                    code=JSONRPCErrorCode.PARSE_ERROR,
                    message="Error parsing batch request",
                )
                response = JSONRPCResponse(
                    jsonrpc="2.0",
                    error=error.model_dump(exclude_none=True),
                    id=None,
                )
                responses.append(response.model_dump(exclude_none=True))

        return responses

    def convert_v1_request(self, request_dict: dict) -> dict:
        """Convert JSON-RPC v1.0 request to v2.0 format.

        Args:
            request_dict: Request in v1.0 format

        Returns:
            Request converted to v2.0 format
        """
        import uuid

        # Make a copy to avoid mutating original
        converted = dict(request_dict)

        # Convert version field
        if converted.get("jsonrpc") == "1.0":
            converted["jsonrpc"] = "2.0"
            logger.warning(
                "Received deprecated JSON-RPC v1.0 request",
                extra={"method": converted.get("method", "unknown")},
            )

        # Generate id if missing (v1.0 allowed omitting id)
        if "id" not in converted:
            converted["id"] = str(uuid.uuid4())

        return converted

    async def handle_request_with_v1_fallback(self, request_dict: dict) -> dict:
        """Handle request with v1.0 backwards compatibility fallback.

        Args:
            request_dict: Request dict that might be v1.0

        Returns:
            Response dict
        """
        # Try v2.0 format first
        if request_dict.get("jsonrpc") == "2.0":
            request = JSONRPCRequest(**request_dict)
            response = await self.handle_request(request)
        else:
            # Try v1.0 conversion
            converted = self.convert_v1_request(request_dict)
            request = JSONRPCRequest(**converted)
            response = await self.handle_request(request)

        return response.model_dump(exclude_none=True)
