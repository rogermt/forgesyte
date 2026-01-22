"""ForgeSyte Core: FastAPI Application Entry Point.

This module orchestrates the lifespan, dependency injection, and core routing
for the ForgeSyte modular vision server. It ensures resilient service
initialization and graceful plugin unloading.
"""

import logging
import logging.handlers
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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

# ---------------------------------------------------------------------------
# Configuration Layer (Pydantic Settings)
# ---------------------------------------------------------------------------


class AppSettings(BaseSettings):
    """Externalized application configuration with validation.

    Uses environment variables and .env files for configuration management,
    following best practices for 12-factor apps.
    """

    title: str = "ForgeSyte"
    description: str = (
        "ForgeSyte: A modular AI-vision MCP server engineered for developers"
    )
    version: str = "0.1.0"
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"], validation_alias="CORS_ORIGINS"
    )
    api_prefix: str = "/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()

# ---------------------------------------------------------------------------
# Observability & Logging Setup
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Configure JSON structured logging with file output.

    Logs to both console and file. File location:
    - Kaggle: $KAGGLE_WORKING/forgesyte.log
    - Local: ./forgesyte.log
    """
    # Determine log file path (prefer KAGGLE_WORKING, fallback to server dir)
    working_dir = os.environ.get("KAGGLE_WORKING", os.getcwd())
    log_dir = Path(working_dir)
    log_file = log_dir / "forgesyte.log"

    try:
        from pythonjsonlogger import jsonlogger

        # Root logger config
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture DEBUG level

        # Remove any existing handlers
        root_logger.handlers.clear()

        # Format: timestamp, level, logger name, message, extra fields
        log_format = "%(timestamp)s %(level)s %(name)s %(message)s"
        json_formatter = jsonlogger.JsonFormatter(fmt=log_format, timestamp=True)

        # Console handler with JSON formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        root_logger.addHandler(console_handler)

        # File handler with JSON formatter (append mode)
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_file), maxBytes=10_000_000, backupCount=5
        )
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)

        print(f"📝 Logging to: {log_file}")
    except ImportError:
        # Fallback to basic config if pythonjsonlogger not installed
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.handlers.RotatingFileHandler(
                    str(log_file), maxBytes=10_000_000, backupCount=5
                ),
            ],
        )
        print(f"📝 Logging to: {log_file} (fallback mode)")


setup_logging()
logger = logging.getLogger(__name__)
logger.info("🚀 ForgeSyte server starting...")

# ---------------------------------------------------------------------------
# Lifespan Management (Orchestration)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage system-wide resources during app startup and shutdown.

    Startup phase:
        - Initialize authentication service
        - Dynamic plugin discovery and loading
        - Service layer instantiation (Analysis, Job, Plugin managers)
        - Task processor initialization

    Shutdown phase:
        - Graceful plugin unloading to prevent memory leaks
        - Resource cleanup
    """
    logger.info("Initializing ForgeSyte Core...")

    # Initialize authentication service
    try:
        init_auth_service()
        logger.debug("Authentication service initialized")
    except Exception as e:
        logger.error(
            "Failed to initialize authentication service", extra={"error": str(e)}
        )

    # Plugin Manager Initialization (entry-point plugins only)
    logger.info("Initializing plugin manager for entry-point plugins")
    plugin_manager = PluginManager()

    # Dynamic Plugin Loading
    try:
        load_result = plugin_manager.load_plugins()
        loaded_list = list(load_result.get("loaded", {}).keys())
        logger.info(
            "Plugins loaded successfully",
            extra={"count": len(loaded_list), "plugins": loaded_list},
        )
        if load_result.get("errors"):
            logger.warning(
                "Plugin loading errors detected",
                extra={
                    "error_count": len(load_result["errors"]),
                    "errors": load_result["errors"],
                },
            )
    except Exception as e:
        logger.error("Critical failure during plugin loading", extra={"error": str(e)})
        raise

    app.state.plugins = plugin_manager

    # Service & Task Processor Initialization
    local_task_processor = None
    try:
        local_task_processor = init_task_processor(plugin_manager)
        logger.debug("Task processor initialized")

        # WebSocket Analysis Service
        app.state.analysis_service = VisionAnalysisService(plugin_manager, ws_manager)

        # REST API Coordination Services
        image_acquisition = ImageAcquisitionService()
        app.state.analysis_service_rest = AnalysisService(
            local_task_processor, image_acquisition  # type: ignore[arg-type]
        )
        app.state.job_service = JobManagementService(
            job_store, local_task_processor  # type: ignore[arg-type]
        )
        app.state.plugin_service = PluginManagementService(plugin_manager)

        logger.debug("Core Service Layer initialized successfully")
    except Exception as e:
        logger.error(
            "Failed to initialize REST/Vision services", extra={"error": str(e)}
        )

    yield  # Application runs here

    # Shutdown: Graceful cleanup
    logger.info("Shutting down ForgeSyte...")
    for name, plugin in plugin_manager.plugins.items():
        try:
            if plugin and hasattr(plugin, "on_unload"):
                plugin.on_unload()
                logger.debug("Plugin unloaded", extra={"plugin": name})
        except Exception as e:
            logger.error(
                "Error unloading plugin",
                extra={"plugin": name, "error": str(e)},
            )


# ---------------------------------------------------------------------------
# FastAPI Application Construction
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Dependency Injection
# ---------------------------------------------------------------------------


def get_analysis_service() -> VisionAnalysisService:
    """Retrieve analysis service from app state with safety checks.

    Returns:
        VisionAnalysisService: WebSocket analysis service instance

    Raises:
        HTTPException: If service not initialized (503 Service Unavailable)
    """
    service = getattr(app.state, "analysis_service", None)
    if not service:
        logger.error("VisionAnalysisService retrieval failed - not initialized")
        raise HTTPException(status_code=503, detail="Analysis service unavailable")
    return service


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(mcp_router, prefix=settings.api_prefix)


@app.get("/.well-known/mcp-manifest", include_in_schema=False)
async def root_mcp_manifest() -> RedirectResponse:
    """Redirect to versioned MCP discovery endpoint."""
    return RedirectResponse(url=f"{settings.api_prefix}/.well-known/mcp-manifest")


@app.get("/")
async def root() -> Dict[str, str]:
    """System information root endpoint.

    Returns:
        Dictionary containing API metadata and endpoint information
    """
    return {
        "name": settings.title,
        "version": settings.version,
        "docs": "/docs",
        "mcp_manifest": "/.well-known/mcp-manifest",
        "gemini_extension": f"{settings.api_prefix}/gemini-extension",
    }


# ---------------------------------------------------------------------------
# WebSocket Streaming Implementation
# ---------------------------------------------------------------------------


@app.websocket("/v1/stream")
async def websocket_stream(
    websocket: WebSocket,
    plugin: str = Query(default="motion_detector", description="Plugin to use"),
    api_key: Optional[str] = Query(None, description="API key for authentication"),
    service: VisionAnalysisService = Depends(get_analysis_service),
) -> None:
    """WebSocket endpoint for high-frequency frame analysis.

    Handles real-time image frame analysis with plugin switching and error handling.
    Delegates business logic to VisionAnalysisService.

    WebSocket Message Protocol:
        Incoming:
            - {"type": "frame", "data": "<base64>", "options": {...}}
            - {"type": "ping"}
            - {"type": "switch_plugin", "plugin": "plugin_name"}
            - {"type": "subscribe", "topic": "topic_name"}

        Outgoing:
            - {"type": "connected", "payload": {"client_id": str, "plugin": str}}
            - {"type": "pong"}
            - {"type": "plugin_switched", "payload": {"plugin": str}}
            - {"type": "error", "message": str}

    Args:
        websocket: FastAPI WebSocket connection
        plugin: Initial plugin to use for analysis
        api_key: Optional API key for authentication
        service: VisionAnalysisService injected dependency
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
        # Connection Acknowledgment
        await ws_manager.send_personal(
            client_id,
            {
                "type": "connected",
                "payload": {"client_id": client_id, "plugin": plugin},
            },
        )
        logger.info(
            "websocket_connection_confirmed",
            extra={"client_id": client_id, "plugin": plugin},
        )

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "frame":
                # Delegate frame processing to service layer
                await service.handle_frame(client_id, plugin, data)

            elif msg_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await ws_manager.subscribe(client_id, topic)
                    logger.debug(
                        "Client subscribed to topic",
                        extra={"client_id": client_id, "topic": topic},
                    )

            elif msg_type == "switch_plugin":
                new_plugin_name: str | None = data.get("plugin")
                registry = getattr(service, "plugins", {})

                # Check for plugin existence robustly (Protocol or Dict)
                exists = False
                if new_plugin_name and registry is not None:
                    if hasattr(registry, "get"):
                        # Use .get() if available (Protocol recommendation)
                        try:
                            exists = registry.get(new_plugin_name) is not None
                        except (TypeError, AttributeError):
                            exists = False
                    else:
                        # Fallback to 'in' operator for dicts or other objects
                        try:
                            exists = new_plugin_name in registry
                        except TypeError:
                            exists = False

                if exists:
                    # new_plugin_name is not None here because exists is True
                    plugin = str(new_plugin_name)
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "plugin_switched",
                            "payload": {"plugin": plugin},
                        },
                    )
                    logger.debug(
                        "Plugin switched",
                        extra={"client_id": client_id, "plugin": plugin},
                    )
                else:
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "error",
                            "message": f"Plugin '{new_plugin_name}' not found",
                        },
                    )

            elif msg_type == "ping":
                await ws_manager.send_personal(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        logger.debug("Client disconnected", extra={"client_id": client_id})
    except Exception as e:
        logger.exception(
            "WebSocket error", extra={"client_id": client_id, "error": str(e)}
        )
    finally:
        await ws_manager.disconnect(client_id)
        logger.debug("Client connection closed", extra={"client_id": client_id})


# ---------------------------------------------------------------------------
# Server Execution Logic
# ---------------------------------------------------------------------------


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Launch uvicorn server with project-specific logging configuration.

    Args:
        host: Binding host address
        port: Binding port number
        reload: Enable auto-reload on code changes (dev only)
    """
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ForgeSyte Core Server")
    parser.add_argument("--host", default="0.0.0.0", help="Binding host")
    parser.add_argument("--port", type=int, default=8000, help="Binding port")
    parser.add_argument("--reload", action="store_true", help="Enable dev reload")
    args = parser.parse_args()

    run_server(args.host, args.port, args.reload)
