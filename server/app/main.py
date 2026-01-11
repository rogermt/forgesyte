"""Main FastAPI application entry point."""

import base64
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .auth import init_api_keys
from .mcp import router as mcp_router
from .plugin_loader import PluginManager
from .tasks import init_task_processor
from .websocket_manager import ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ForgeSyte...")

    # Initialize API keys
    init_api_keys()

    # Load plugins
    plugins_dir = os.getenv("FORGESYTE_PLUGINS_DIR", "../example_plugins")
    plugin_manager = PluginManager(plugins_dir)
    result = plugin_manager.load_plugins()
    logger.info(f"Loaded plugins: {list(result.get('loaded', {}).keys())}")
    if result.get("errors"):
        logger.warning(f"Plugin errors: {result['errors']}")

    app.state.plugins = plugin_manager

    # Initialize task processor
    init_task_processor(plugin_manager)
    logger.info("Task processor initialized")

    yield

    # Shutdown
    logger.info("Shutting down ForgeSyte...")
    for plugin in plugin_manager.plugins.values():
        try:
            plugin.on_unload()
        except Exception as e:
            logger.error(f"Error unloading plugin: {e}")


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

# Include API and MCP routers
app.include_router(api_router, prefix="/v1")
app.include_router(mcp_router, prefix="/v1")


# Also mount at root for MCP discovery
@app.get("/.well-known/mcp-manifest")
async def root_mcp_manifest():
    """Root-level MCP manifest redirect."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/v1/.well-known/mcp-manifest")


@app.websocket("/v1/stream")
async def websocket_stream(
    websocket: WebSocket,
    plugin: str = Query(default="motion_detector"),
    api_key: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time frame streaming and analysis.

    Send frames as base64-encoded JSON: {"type": "frame", "data": "<base64>"}
    Receive results as JSON: {"type": "result", "payload": {...}}
    """
    client_id = str(uuid.uuid4())

    if not await ws_manager.connect(websocket, client_id):
        return

    pm: PluginManager = app.state.plugins
    active_plugin = pm.get(plugin)

    if not active_plugin:
        await ws_manager.send_error(client_id, f"Plugin '{plugin}' not found")
        await ws_manager.disconnect(client_id)
        return

    try:
        await ws_manager.send_personal(
            client_id,
            {
                "type": "connected",
                "payload": {
                    "client_id": client_id,
                    "plugin": plugin,
                    "plugin_metadata": active_plugin.metadata(),
                },
            },
        )

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                frame_id = data.get("frame_id", str(uuid.uuid4()))

                try:
                    image_bytes = base64.b64decode(data["data"])
                    start_time = time.time()

                    result = active_plugin.analyze(image_bytes, data.get("options", {}))

                    processing_time = (time.time() - start_time) * 1000

                    await ws_manager.send_frame_result(
                        client_id, frame_id, plugin, result, processing_time
                    )

                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    await ws_manager.send_error(client_id, str(e), frame_id)

            elif data.get("type") == "subscribe":
                topic = data.get("topic")
                if topic:
                    await ws_manager.subscribe(client_id, topic)

            elif data.get("type") == "switch_plugin":
                new_plugin_name = data.get("plugin")
                new_plugin = pm.get(new_plugin_name)
                if new_plugin:
                    active_plugin = new_plugin
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "plugin_switched",
                            "payload": {"plugin": new_plugin_name},
                        },
                    )
                else:
                    await ws_manager.send_error(
                        client_id, f"Plugin '{new_plugin_name}' not found"
                    )

            elif data.get("type") == "ping":
                await ws_manager.send_personal(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(client_id)


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
