"""Main FastAPI application entry point and lifespan management.

This module configures the FastAPI application with proper dependency injection,
structured logging, and graceful lifespan management. Business logic is delegated
to service layer classes, keeping endpoints thin and focused on HTTP concerns.

The lifespan manager handles:
1. Startup: Load plugins, initialize services, set up dependencies
2. Shutdown: Gracefully cleanup resources and unload plugins
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .auth import init_auth_service
from .mcp import router as mcp_router
from .plugin_loader import PluginManager
from .services import (
    AnalysisService,
    ImageAcquisitionService,
    JobManagementService,
    PluginManagementService,
    VisionAnalysisService,
)
from .tasks import init_task_processor, job_store
from .websocket_manager import ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Manages system-wide resources during app startup and shutdown:
    - Startup: Load plugins, initialize task processor, set up services
    - Shutdown: Gracefully unload plugins and cleanup resources
    """
    # Startup
    logger.info("Initializing ForgeSyte Core...")

    # Initialize authentication service
    try:
        init_auth_service()
        logger.debug("Authentication service initialized")
    except Exception as e:
        logger.error(
            "Failed to initialize authentication service", extra={"error": str(e)}
        )

    # Load plugins
    # Use absolute path to ensure it works from any working directory
    plugins_dir_env = os.getenv("FORGESYTE_PLUGINS_DIR", None)
    if plugins_dir_env:
        plugins_dir = Path(plugins_dir_env).resolve()
    else:
        # Default: ../example_plugins relative to this file's directory
        plugins_dir = Path(__file__).parent.parent.parent / "example_plugins"

    logger.info(
        "Loading plugins from directory",
        extra={"plugins_dir": str(plugins_dir), "exists": plugins_dir.exists()},
    )

    plugin_manager = PluginManager(str(plugins_dir))

    try:
        result = plugin_manager.load_plugins()
        loaded_plugins = list(result.get("loaded", {}).keys())
        logger.info(
            "Plugins loaded successfully",
            extra={"count": len(loaded_plugins), "plugins": loaded_plugins},
        )
        if result.get("errors"):
            logger.warning(
                "Plugin loading errors",
                extra={
                    "error_count": len(result["errors"]),
                    "errors": result["errors"],
                },
            )
    except Exception as e:
        logger.error("Failed to load plugins", extra={"error": str(e)})
        raise

    app.state.plugins = plugin_manager

    # Initialize task processor
    local_task_processor = None
    try:
        local_task_processor = init_task_processor(plugin_manager)
        logger.debug("Task processor initialized")
    except Exception as e:
        logger.error("Failed to initialize task processor", extra={"error": str(e)})

    # Initialize vision analysis service (for WebSocket streaming)
    try:
        app.state.analysis_service = VisionAnalysisService(plugin_manager, ws_manager)
        logger.debug("VisionAnalysisService initialized")
    except Exception as e:
        logger.error(
            "Failed to initialize VisionAnalysisService", extra={"error": str(e)}
        )

    # Initialize REST API services
    try:
        if local_task_processor is None:
            logger.error("Task processor not initialized, cannot create API services")
            raise RuntimeError("Task processor initialization failed")

        # Analysis service coordinates image requests
        image_acquisition = ImageAcquisitionService()
        app.state.analysis_service_rest = AnalysisService(
            local_task_processor, image_acquisition  # type: ignore[arg-type]
        )
        logger.debug("AnalysisService initialized")

        # Job management service handles job queries and control
        app.state.job_service = JobManagementService(
            job_store, local_task_processor  # type: ignore[arg-type]
        )
        logger.debug("JobManagementService initialized")

        # Plugin management service handles plugin operations
        app.state.plugin_service = PluginManagementService(plugin_manager)
        logger.debug("PluginManagementService initialized")
    except Exception as e:
        logger.error("Failed to initialize REST API services", extra={"error": str(e)})

    yield

    # Shutdown
    logger.info("Shutting down ForgeSyte...")
    for name, plugin in plugin_manager.plugins.items():
        try:
            if plugin:
                plugin.on_unload()
                logger.debug("Plugin unloaded", extra={"plugin": name})
        except Exception as e:
            logger.error(
                "Error unloading plugin",
                extra={"plugin": name, "error": str(e)},
            )


# Create FastAPI app
app = FastAPI(
    title="ForgeSyte",
    description="ForgeSyte: A modular AI-vision MCP server engineered for developers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection for service layer
def get_analysis_service(request) -> VisionAnalysisService:
    """Get the analysis service from app state.

    Args:
        request: FastAPI request object

    Returns:
        VisionAnalysisService instance

    Raises:
        RuntimeError: If service not initialized
    """
    service = getattr(request.app.state, "analysis_service", None)
    if not service:
        logger.error("VisionAnalysisService not initialized")
        raise RuntimeError("Analysis service not available")
    return service


# Include API and MCP routers
app.include_router(api_router, prefix="/v1")
app.include_router(mcp_router, prefix="/v1")


# MCP Discovery Endpoints


@app.get("/.well-known/mcp-manifest")
async def root_mcp_manifest():
    """Root-level MCP manifest redirect to well-known location."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/v1/.well-known/mcp-manifest")


# WebSocket Streaming


@app.websocket("/v1/stream")
async def websocket_stream(
    websocket: WebSocket,
    plugin: str = Query(default="motion_detector", description="Plugin to use"),
    api_key: Optional[str] = Query(None, description="API key for authentication"),
    service: VisionAnalysisService = Depends(get_analysis_service),
):
    """WebSocket endpoint for real-time frame streaming and analysis.

    Handles real-time image frame analysis with plugin switching and error handling.
    Delegates business logic to VisionAnalysisService.

    WebSocket Message Protocol:
        Incoming:
            - {"type": "frame", "data": "<base64>", "options": {...}}
            - {"type": "ping"}
            - {"type": "switch_plugin", "plugin": "plugin_name"}

        Outgoing:
            - {"type": "result", "frame_id": str, "result": {...}, "time_ms": float}
            - {"type": "error", "message": str}
            - {"type": "pong"}
            - {"type": "connected", "client_id": str, "plugin": str}
    """
    client_id = str(uuid.uuid4())
    logger.debug(
        "WebSocket connection attempt",
        extra={"client_id": client_id, "plugin": plugin},
    )

    if not await ws_manager.connect(websocket, client_id):
        logger.warning("Failed to connect WebSocket", extra={"client_id": client_id})
        return

    try:
        # Send initial connection confirmation
        await ws_manager.send_personal(
            client_id,
            {
                "type": "connected",
                "payload": {
                    "client_id": client_id,
                    "plugin": plugin,
                },
            },
        )

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                # Delegate frame processing to service layer
                await service.handle_frame(client_id, plugin, data)

            elif data.get("type") == "subscribe":
                topic = data.get("topic")
                if topic:
                    await ws_manager.subscribe(client_id, topic)
                    logger.debug(
                        "Client subscribed to topic",
                        extra={"client_id": client_id, "topic": topic},
                    )

            elif data.get("type") == "switch_plugin":
                new_plugin_name = data.get("plugin")
                new_plugin = service.plugins.get(new_plugin_name)
                if new_plugin:
                    plugin = new_plugin_name
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "plugin_switched",
                            "payload": {"plugin": new_plugin_name},
                        },
                    )
                    logger.debug(
                        "Plugin switched",
                        extra={"client_id": client_id, "plugin": new_plugin_name},
                    )
                else:
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "error",
                            "message": f"Plugin '{new_plugin_name}' not found",
                        },
                    )

            elif data.get("type") == "ping":
                await ws_manager.send_personal(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        logger.debug("Client disconnected", extra={"client_id": client_id})
    except Exception as e:
        logger.exception(
            "WebSocket error",
            extra={"client_id": client_id, "error": str(e)},
        )
    finally:
        await ws_manager.disconnect(client_id)
        logger.debug("Client connection closed", extra={"client_id": client_id})


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ForgeSyte",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp_manifest": "/.well-known/mcp-manifest",
        "gemini_extension": "/v1/gemini-extension",
    }


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the server with uvicorn."""
    uvicorn.run(
        "server.app.main:app", host=host, port=port, reload=reload, log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ForgeSyte")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()
    run_server(args.host, args.port, args.reload)
