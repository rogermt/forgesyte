"""HTTP routes for MCP JSON-RPC 2.0 protocol."""

import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .jsonrpc import JSONRPCError, JSONRPCErrorCode, JSONRPCRequest
from .transport import MCPTransport

logger = logging.getLogger(__name__)
router = APIRouter()

# Global transport instance (lazy-loaded)
_transport: Optional[MCPTransport] = None


def get_transport(request: Request) -> MCPTransport:
    """Get or create the MCP transport instance.

    Uses the plugin manager from app.state if available.

    Args:
        request: FastAPI request object

    Returns:
        MCPTransport instance
    """
    global _transport
    if _transport is None:
        # Create transport with app's plugin manager
        plugin_manager = getattr(request.app.state, "plugins", None)
        _transport = MCPTransport(protocol_handlers=None)
        # If plugin manager is set, recreate transport with it
        if plugin_manager:
            from .handlers import MCPProtocolHandlers

            handlers = MCPProtocolHandlers(plugin_manager)
            _transport = MCPTransport(protocol_handlers=handlers)
    return _transport


@router.post("/mcp")
async def mcp_rpc(request: Request):
    """Handle MCP JSON-RPC 2.0 requests via HTTP POST.

    Accepts JSON-RPC 2.0 formatted requests and routes them to MCP protocol handlers.
    Responses follow JSON-RPC 2.0 specification.

    Args:
        request: FastAPI request with JSON body

    Returns:
        JSON-RPC 2.0 response (success or error format)

    Example:
        Request:
            {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {},
                "id": 1
            }

        Response:
            {
                "jsonrpc": "2.0",
                "result": {"status": "pong"},
                "id": 1
            }
    """
    try:
        # Parse request body as JSON-RPC request
        body = await request.json()
        jsonrpc_request = JSONRPCRequest(**body)

        # Get transport instance
        transport = get_transport(request)

        # Handle the request
        response = await transport.handle_request(jsonrpc_request)

        # For notifications (no id), return 204 No Content
        if jsonrpc_request.id is None:
            # Return empty response body for notifications
            return JSONResponse({"jsonrpc": "2.0"}, status_code=204)

        # Return JSON-RPC response
        return JSONResponse(response.model_dump(exclude_none=True), status_code=200)

    except ValidationError as e:
        # Validation error in JSON-RPC request
        logger.warning(f"Invalid JSON-RPC request: {e}")
        error = JSONRPCError(
            code=JSONRPCErrorCode.INVALID_REQUEST,
            message="Invalid Request",
            data={
                "errors": [
                    {"field": err["loc"], "message": err["msg"]} for err in e.errors()
                ]
            },
        )
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": error.model_dump(exclude_none=True),
                "id": None,
            },
            status_code=400,
        )
    except ValueError as e:
        # JSON parsing error
        logger.warning(f"JSON parse error: {e}")
        error = JSONRPCError(
            code=JSONRPCErrorCode.PARSE_ERROR,
            message="Parse error",
        )
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": error.model_dump(exclude_none=True),
                "id": None,
            },
            status_code=400,
        )
    except Exception:
        # Unexpected error
        logger.exception("Unexpected error in MCP endpoint")
        error = JSONRPCError(
            code=JSONRPCErrorCode.INTERNAL_ERROR,
            message="Internal server error",
        )
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": error.model_dump(exclude_none=True),
                "id": None,
            },
            status_code=500,
        )
