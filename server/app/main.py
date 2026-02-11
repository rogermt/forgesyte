"""
ForgeSyte Core: FastAPI Application Entry Point.

This module orchestrates the lifespan, dependency injection, routing,
logging, and server execution for the ForgeSyte modular vision server.
It provides:
- Structured JSON logging
- Plugin loading and health registry initialization
- REST + WebSocket routing
- Dependency injection for analysis, job, and plugin services
- A clean create_app() factory for import‑safe app creation
- A CLI entrypoint using run_server()
"""

import logging
import logging.handlers
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, NoReturn, Optional

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

# Routers
from .api import router as api_router
from .api_plugins import router as plugins_router
from .api_routes.routes.execution import router as execution_router
from .routes_pipeline import init_pipeline_routes

# Services
from .auth import init_auth_service
from .mcp import router as mcp_router
from .plugin_loader import PluginRegistry
from .plugins.health.health_router import router as health_router
from .realtime import websocket_router as realtime_router
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
# Configuration Layer
# ---------------------------------------------------------------------------


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

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
# Logging Setup
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Configure JSON structured logging for console + file output."""
    working_dir = os.environ.get("KAGGLE_WORKING", os.getcwd())
    log_file = Path(working_dir) / "forgesyte.log"

    try:
        from pythonjsonlogger import jsonlogger

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.handlers.clear()

        fmt = "%(timestamp)s %(level)s %(name)s %(message)s"
        formatter = jsonlogger.JsonFormatter(fmt=fmt, timestamp=True)

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_file), maxBytes=10_000_000, backupCount=5
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        print(f"📝 Logging to: {log_file}")

    except ImportError:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
# Lifespan Management
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage system-wide resources during startup and shutdown.

    Startup:
        - Initialize authentication
        - Load plugins
        - Register plugins in health registry
        - Initialize task processor
        - Initialize REST + WebSocket services

    Shutdown:
        - Gracefully unload plugins
    """
    logger.info("Initializing ForgeSyte Core...")

    # Authentication
    try:
        init_auth_service()
        logger.debug("Authentication service initialized")
    except Exception as e:
        logger.error("Failed to initialize authentication", extra={"error": str(e)})

    # Plugin Manager
    plugin_manager = PluginRegistry()
    try:
        load_result = plugin_manager.load_plugins()
        loaded = list(load_result.get("loaded", {}).keys())
        logger.info("Plugins loaded", extra={"count": len(loaded), "plugins": loaded})
    except Exception as e:
        logger.error("Plugin loading failed", extra={"error": str(e)})
        raise

    app.state.plugins = plugin_manager

    # Health Registry Registration
    try:
        from .plugins.loader.plugin_registry import get_registry

        registry = get_registry()
        for name in loaded:
            plugin = plugin_manager.get(name)
            if plugin and registry.get_status(name) is None:
                registry.register(
                    name,
                    getattr(plugin, "description", ""),
                    getattr(plugin, "version", ""),
                    instance=plugin,
                )
                registry.mark_initialized(name)
    except Exception as e:
        logger.error("Health registry registration failed", extra={"error": str(e)})

    # Startup Audit
    try:
        from .plugins.loader.startup_audit import run_startup_audit

        run_startup_audit(loaded)
    except Exception as e:
        logger.error("Startup audit failed", extra={"error": str(e)})

    # Task Processor + Services
    try:
        processor = init_task_processor(plugin_manager)
        app.state.analysis_service = VisionAnalysisService(plugin_manager, ws_manager)

        image_acquisition = ImageAcquisitionService()
        app.state.analysis_service_rest = AnalysisService(processor, image_acquisition)
        app.state.job_service = JobManagementService(job_store, processor)
        app.state.plugin_service = PluginManagementService(plugin_manager)

    except Exception as e:
        logger.error("Service initialization failed", extra={"error": str(e)})

    yield

    # Shutdown
    logger.info("Shutting down ForgeSyte...")
    for name in plugin_manager.list().keys():
        try:
            plugin = plugin_manager.get(name)
            if plugin and hasattr(plugin, "on_unload"):
                plugin.on_unload()
        except Exception as e:
            logger.error(
                "Error unloading plugin", extra={"plugin": name, "error": str(e)}
            )


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Construct and configure the ForgeSyte FastAPI application.

    Returns:
        FastAPI: Fully initialized application instance.
    """
    app = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routing
    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(mcp_router, prefix=settings.api_prefix)
    app.include_router(plugins_router, prefix="")
    app.include_router(realtime_router, prefix=settings.api_prefix)
    app.include_router(health_router)
    app.include_router(execution_router)
    app.include_router(init_pipeline_routes())

    return app


# ASGI app for uvicorn
app = create_app()


# ---------------------------------------------------------------------------
# Dependency Injection
# ---------------------------------------------------------------------------


def create_plugin_management_service() -> PluginManagementService:
    """Factory for PluginManagementService wired to a fresh PluginRegistry.

    Returns:
        PluginManagementService instance with loaded plugins
    """
    registry = PluginRegistry()
    registry.load_plugins()
    return PluginManagementService(registry)


def get_analysis_service() -> VisionAnalysisService:
    """Retrieve WebSocket analysis service from app state."""
    service = getattr(app.state, "analysis_service", None)
    if not service:
        raise HTTPException(status_code=503, detail="Analysis service unavailable")
    return service


# ---------------------------------------------------------------------------
# Root Endpoints
# ---------------------------------------------------------------------------


@app.get("/.well-known/mcp-manifest", include_in_schema=False)
async def root_mcp_manifest() -> RedirectResponse:
    """Redirect to versioned MCP manifest."""
    return RedirectResponse(url=f"{settings.api_prefix}/.well-known/mcp-manifest")


@app.get("/")
async def root() -> Dict[str, str]:
    """Return basic system metadata."""
    return {
        "name": settings.title,
        "version": settings.version,
        "docs": "/docs",
        "mcp_manifest": "/.well-known/mcp-manifest",
        "gemini_extension": f"{settings.api_prefix}/gemini-extension",
    }


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------


@app.websocket("/v1/stream")
async def websocket_stream(
    websocket: WebSocket,
    plugin: str = Query("default"),
    api_key: Optional[str] = Query(None),
    service: VisionAnalysisService = Depends(get_analysis_service),
) -> None:
    """High-frequency real-time frame analysis WebSocket endpoint."""
    client_id = str(uuid.uuid4())

    if not await ws_manager.connect(websocket, client_id):
        return

    try:
        await ws_manager.send_personal(
            client_id,
            {
                "type": "connected",
                "payload": {"client_id": client_id, "plugin": plugin},
            },
        )

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "frame":
                await service.handle_frame(client_id, plugin, data)

            elif msg_type == "switch_plugin":
                new_plugin = data.get("plugin")
                registry = getattr(service, "plugins", {})
                exists = False

                if new_plugin:
                    try:
                        exists = registry.get(new_plugin) is not None
                    except Exception:
                        exists = False

                if exists:
                    plugin = new_plugin
                    await ws_manager.send_personal(
                        client_id,
                        {"type": "plugin_switched", "payload": {"plugin": plugin}},
                    )
                else:
                    await ws_manager.send_personal(
                        client_id,
                        {
                            "type": "error",
                            "message": f"Plugin '{new_plugin}' not found",
                        },
                    )

            elif msg_type == "ping":
                await ws_manager.send_personal(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(client_id)


# ---------------------------------------------------------------------------
# Server Execution
# ---------------------------------------------------------------------------


def run_server(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = False
) -> NoReturn:
    """
    Launch the ForgeSyte server using uvicorn.

    Args:
        host: Host interface to bind to.
        port: TCP port to listen on.
        reload: Enable auto-reload for development.
    """
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
    raise SystemExit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ForgeSyte Core Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    run_server(args.host, args.port, args.reload)
