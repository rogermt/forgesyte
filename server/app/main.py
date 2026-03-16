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
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, NoReturn, Optional

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

# Routers
from .api import router as api_router
from .api_plugins import router as plugins_router
from .api_routes.routes.execution import router as execution_router
from .api_routes.routes.image_submit import router as image_submit_router
from .api_routes.routes.job_results import router as job_results_router
from .api_routes.routes.job_status import router as job_status_router
from .api_routes.routes.jobs import router as jobs_router
from .api_routes.routes.video_file_processing import router as video_router
from .api_routes.routes.video_submit import router as video_submit_router
from .api_routes.routes.worker_health import router as worker_health_router

# Services
from .auth import init_auth_service
from .core.database import init_db
from .mcp import router as mcp_router
from .plugin_loader import PluginRegistry
from .plugins.health.health_router import router as health_router
from .realtime import websocket_router as realtime_router
from .realtime.job_progress_router import router as job_progress_router
from .routes.routes_pipelines import router as pipelines_router
from .routes_pipeline import init_pipeline_routes
from .services import (
    PluginManagementService,
    VisionAnalysisService,
)
from .settings import settings

# v0.9.2: TaskProcessor replaced by JobWorker
# v0.9.3: Legacy AnalysisService and JobManagementService removed
from .websocket_manager import ws_manager

# ---------------------------------------------------------------------------
# Configuration Layer
# ---------------------------------------------------------------------------

# Use settings for CORS and other configuration
cors_settings = settings


# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Configure JSON structured logging for console + file output."""
    working_dir = os.environ.get("KAGGLE_WORKING", os.getcwd())
    log_file = Path(working_dir) / "forgesyte.log"

    try:
        # python-json-logger v3.x+ import path
        from pythonjsonlogger.json import JsonFormatter

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.handlers.clear()

        # Use valid LogRecord attributes, rename for cleaner output
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
        formatter = JsonFormatter(
            fmt=fmt,
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )

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
        # Fallback for older pythonjsonlogger versions
        try:
            from pythonjsonlogger import jsonlogger

            root = logging.getLogger()
            root.setLevel(logging.DEBUG)
            root.handlers.clear()

            fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
            formatter = jsonlogger.JsonFormatter(fmt=fmt)

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
logger.info("ForgeSyte server starting...")


# ---------------------------------------------------------------------------
# Lifespan Management
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage system-wide resources during startup and shutdown.

    Startup:
        - Initialize database migrations
        - Initialize authentication
        - Load plugins
        - Register plugins in health registry
        - Initialize task processor
        - Initialize REST + WebSocket services

    Shutdown:
        - Gracefully unload plugins
    """
    logger.info("Initializing ForgeSyte Core...")

    # Database Initialization
    try:
        init_db()
        logger.info("Database schema initialized")
    except Exception as e:
        logger.error("Failed to initialize database", extra={"error": str(e)})

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

    # Services (v0.9.2: TaskProcessor removed, using JobWorker instead)
    # v0.9.3: Legacy AnalysisService and JobManagementService removed
    try:
        app.state.plugin_service = PluginManagementService(plugin_manager)
        app.state.analysis_service = VisionAnalysisService(
            app.state.plugin_service, ws_manager
        )

        # Phase 14: Pipeline Services
        from .services.pipeline_registry_service import PipelineRegistryService

        pipelines_dir = Path(__file__).parent.parent / "app" / "pipelines"
        app.state.pipeline_registry = PipelineRegistryService(str(pipelines_dir))
        app.state.plugin_manager_for_pipelines = plugin_manager

        # Phase 12: Initialize execution service chain for /v1/analyze-execution endpoint
        # Issue #303: This chain is required for the sync analyze-execution endpoint
        import base64
        import inspect

        from .services.execution import (
            AnalysisExecutionService,
            JobExecutionService,
            PluginExecutionService,
        )

        async def tool_runner(tool_name: str, args: dict) -> dict:
            """Production tool_runner that delegates to loaded plugins.

            The tool_runner receives plugin_name via args (passed by
            AnalysisExecutionService.analyze()) to route to the correct plugin.

            Args:
                tool_name: Name of the tool to execute
                args: Tool arguments including 'plugin_name', 'image', etc.

            Returns:
                Tool execution result as dict
            """
            # Default to 'analyze' if tool_name is empty
            effective_tool = tool_name or "analyze"

            # Get plugin name from args (passed by AnalysisExecutionService)
            plugin_name = args.get("plugin_name")
            if not plugin_name:
                raise ValueError("plugin_name required in args for tool execution")

            plugin = plugin_manager.get(plugin_name)
            if not plugin:
                raise ValueError(f"Plugin '{plugin_name}' not found")

            # Convert base64 image string to bytes for plugins
            processed_args = dict(args)
            if "image" in processed_args and isinstance(processed_args["image"], str):
                try:
                    processed_args["image_bytes"] = base64.b64decode(
                        processed_args["image"]
                    )
                except Exception:
                    pass  # Keep original if decode fails

            if hasattr(plugin, "run_tool"):
                # run_tool may be sync or async
                result = plugin.run_tool(effective_tool, processed_args)
                if inspect.iscoroutine(result):
                    result = await result
                # Handle Pydantic models
                if hasattr(result, "model_dump"):
                    return result.model_dump()
                return result if isinstance(result, dict) else {"result": result}

            # Fallback: try analyze method directly
            if hasattr(plugin, "analyze"):
                image_data = processed_args.get(
                    "image_bytes", processed_args.get("image", b"")
                )
                result = plugin.analyze(image_data)
                if hasattr(result, "model_dump"):
                    return result.model_dump()
                return result if isinstance(result, dict) else {"result": result}

            raise RuntimeError(
                f"Plugin '{plugin_name}' has no run_tool or analyze method"
            )

        plugin_exec_service = PluginExecutionService(tool_runner)
        job_exec_service = JobExecutionService(plugin_exec_service)
        # Issue #302: Pass plugin_service for tool_name resolution from manifest
        analysis_exec_service = AnalysisExecutionService(
            job_exec_service, app.state.plugin_service
        )
        app.state.analysis_execution_service = analysis_exec_service
        logger.info("Execution service chain initialized for /v1/analyze-execution")

    except Exception as e:
        logger.error("Service initialization failed", extra={"error": str(e)})

    # Start JobWorker thread (DuckDB requires same process)
    # Disabled in pytest via FORGESYTE_ENABLE_WORKERS=0 to prevent DB lock errors
    if os.getenv("FORGESYTE_ENABLE_WORKERS", "1") == "1":
        try:
            # v0.15.0: Ray initialization removed - JobWorker runs without Ray
            from .workers.run_job_worker import run_worker_forever

            worker_thread = threading.Thread(
                target=run_worker_forever,
                args=(plugin_manager,),
                name="job-worker-thread",
                daemon=True,
            )
            worker_thread.start()
            logger.info("JobWorker thread started (Ray disabled)")
        except Exception as e:
            logger.error("Failed to start JobWorker thread", extra={"error": str(e)})
    else:
        logger.debug("JobWorker thread disabled (FORGESYTE_ENABLE_WORKERS=0)")

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

    # Global exception handler to catch unhandled errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        import traceback

        logger.error(f"[UNHANDLED EXCEPTION] {type(exc).__name__}: {exc}")
        logger.error(f"[UNHANDLED EXCEPTION] Traceback:\n{traceback.format_exc()}")
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Internal server error: {type(exc).__name__}: {str(exc)}"
            },
        )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.cors_origins,
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
    app.include_router(worker_health_router)
    app.include_router(execution_router)
    app.include_router(init_pipeline_routes())
    app.include_router(pipelines_router, prefix=settings.api_prefix)
    app.include_router(video_router, prefix=settings.api_prefix)
    app.include_router(video_submit_router, prefix="")
    app.include_router(image_submit_router, prefix="")
    app.include_router(jobs_router, prefix="")
    app.include_router(job_status_router, prefix="")
    app.include_router(job_results_router, prefix="")
    app.include_router(job_progress_router)

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


@app.get("/v1/debug/cors")
async def debug_cors() -> Dict[str, Any]:
    """Return CORS configuration for debugging.

    This endpoint provides runtime introspection of the CORS configuration,
    which is invaluable for debugging tunnels and cross-origin issues.
    """
    return {
        "allowed_origins": cors_settings.cors_origins,
        "raw_env": cors_settings.cors_origins_raw,
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
        # v0.13.0: Clean up GPU actors when WebSocket disconnects
        await service.cleanup_client(client_id)
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
