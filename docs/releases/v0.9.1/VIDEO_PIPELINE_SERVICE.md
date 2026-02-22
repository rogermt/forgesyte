%%writefile /kaggle/working/forgesyte/server/app/main.py
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
from pydantic_settings import BaseSettings, SettingsConfigDict

# Routers
from .api import router as api_router
from .api_plugins import router as plugins_router
from .api_routes.routes.execution import router as execution_router
from .api_routes.routes.job_results import router as job_results_router
from .api_routes.routes.job_status import router as job_status_router
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
from .routes.routes_pipelines import router as pipelines_router
from .routes_pipeline import init_pipeline_routes
from .services import (
    AnalysisService,
    ImageAcquisitionService,
    JobManagementService,
    PluginManagementService,
    VisionAnalysisService,
)

# Phase 14 Settings
from .settings import get_settings
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
    api_prefix: str = "/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Phase 14 Settings
phase14_settings = get_settings()
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

    # Start JobWorker thread (after plugin_manager exists)
    try:
        from .workers.run_job_worker import run_worker_forever

        def _safe_worker():
            try:
                run_worker_forever(plugin_manager)
            except Exception:
                logger.error("Worker thread crashed", exc_info=True)

        worker_thread = threading.Thread(
            target=_safe_worker,
            name="job-worker-thread",
            daemon=True,
        )
        worker_thread.start()
        logger.info("JobWorker thread started")
    except Exception as e:
        logger.error("Failed to start JobWorker thread", extra={"error": str(e)})

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

        from .services.pipeline_registry_service import PipelineRegistryService
        pipelines_dir = Path(__file__).parent.parent / "app" / "pipelines"
        app.state.pipeline_registry = PipelineRegistryService(str(pipelines_dir))
        app.state.plugin_manager_for_pipelines = plugin_manager

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
        allow_origins=phase14_settings.cors_origins,
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
    app.include_router(job_status_router, prefix="")
    app.include_router(job_results_router, prefix="")

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
        "allowed_origins": phase14_settings.cors_origins,
        "raw_env": phase14_settings.cors_origins_raw,
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


%%writefile  /kaggle/working/forgesyte/server/app/workers/worker.py
"""Job worker for Phase 16 asynchronous processing.

This worker:
1. Dequeues job_ids from the queue
2. Updates job status to RUNNING
3. Executes pipeline on input file (Commit 6)
4. Saves results to storage as JSON
5. Handles errors with graceful failure
6. Handles signals (SIGINT/SIGTERM) for graceful shutdown
"""

import json
import logging
import signal
import time
from io import BytesIO
from typing import Optional, Protocol
import threading

from ..core.database import SessionLocal
from ..models.job import Job, JobStatus
from ..services.queue.memory_queue import InMemoryQueueService
from .worker_state import worker_last_heartbeat

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    """Protocol for storage service (allows dependency injection)."""

    def load_file(self, path: str):
        """Load file from storage."""
        ...

    def save_file(self, src, dest_path: str) -> str:
        """Save file to storage."""
        ...


class PipelineService(Protocol):
    """Protocol for pipeline service (allows dependency injection)."""

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ):
        """Execute pipeline on video file."""
        ...


class JobWorker:
    """Processes jobs from the queue."""

    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
        storage: Optional[StorageService] = None,
        pipeline_service: Optional[PipelineService] = None,
    ) -> None:
        """Initialize worker.

        Args:
            queue: Ignored (kept for backward compatibility with tests)
            session_factory: Session factory (defaults to SessionLocal from database.py)
            storage: StorageService instance for file I/O
            pipeline_service: PipelineService instance for pipeline execution
        """
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._pipeline_service = pipeline_service
        self._running = True

        # Register signal handlers only if running in main thread
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)


    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number (SIGINT, SIGTERM)
            frame: Signal frame
        """
        logger.info("Received signal %s, shutting down gracefully", signum)
        self._running = False

    def run_once(self) -> bool:
        """Process one job from the database.

        Returns:
            True if a job was processed, False if no pending jobs
        """
        db = self._session_factory()
        try:
            job = (
                db.query(Job)
                .filter(Job.status == JobStatus.pending)
                .order_by(Job.created_at.asc())
                .first()
            )

            if job is None:
                return False

            rows_updated = (
                db.query(Job)
                .filter(Job.job_id == job.job_id)
                .filter(Job.status == JobStatus.pending)
                .update({"status": JobStatus.running})
            )
            db.commit()

            if rows_updated == 0:
                return False

            db.refresh(job)

            logger.info("Job %s marked RUNNING", job.job_id)

            # COMMIT 6: Execute pipeline on input file
            return self._execute_pipeline(job, db)
        finally:
            db.close()

    def _execute_pipeline(self, job: Job, db) -> bool:
        """Execute pipeline on job input file.

        Args:
            job: Job model instance
            db: Database session

        Returns:
            True if pipeline executed successfully, False on error
        """
        try:
            # Verify storage and pipeline services are available
            if not self._storage or not self._pipeline_service:
                logger.warning(
                    "Job %s: storage or pipeline service not available", job.job_id
                )
                job.status = JobStatus.failed
                job.error_message = "Pipeline execution services not configured"
                db.commit()
                return False

            # Load input file from storage
            input_file_path = self._storage.load_file(job.input_path)
            logger.info("Job %s: loaded input file %s", job.job_id, input_file_path)

            # Execute pipeline on video file
            results = self._pipeline_service.run_on_file(
                str(input_file_path),
                job.pipeline_id,
            )
            logger.info(
                "Job %s: pipeline executed, %d results", job.job_id, len(results)
            )

            # Prepare JSON output
            output_data = {"results": results}
            output_json = json.dumps(output_data)
            output_bytes = BytesIO(output_json.encode())

            # Save results to storage
            output_path = self._storage.save_file(
                output_bytes,
                f"output/{job.job_id}.json",
            )
            logger.info("Job %s: saved results to %s", job.job_id, output_path)

            # Mark job as completed
            job.status = JobStatus.completed
            job.output_path = output_path
            job.error_message = None
            db.commit()

            logger.info("Job %s marked COMPLETED", job.job_id)
            return True

        except Exception as e:
            # Mark job as failed with error message
            logger.error("Job %s: pipeline execution failed: %s", job.job_id, str(e))
            job.status = JobStatus.failed
            job.error_message = str(e)
            db.commit()
            return False

    def run_forever(self) -> None:
        """Run the worker loop until shutdown signal is received."""
        logger.info("Worker started")
        while self._running:
            # Send heartbeat to indicate worker is alive
            worker_last_heartbeat.beat()

            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
        logger.info("Worker stopped")


%%writefile  /kaggle/working/forgesyte/server/app/services/video_pipeline_service.py
"""VideoPipelineService for Phase 13 - Multi-Tool Linear Pipelines.

This service executes linear, single-plugin tool pipelines for the VideoTracker.
"""

import logging
from typing import Any, Dict, List

from ..protocols import PluginRegistry

logger = logging.getLogger(__name__)


class VideoPipelineService:
    """Executes linear multi-tool pipelines for VideoTracker."""

    def __init__(self, plugins: PluginRegistry) -> None:
        """Initialize the pipeline service with a plugin registry.

        Args:
            plugins: Plugin registry implementing PluginRegistry protocol
        """
        self.plugins = plugins

    def run_pipeline(
        self, plugin_id: str, tools: List[str], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools sequentially, chaining outputs.

        Args:
            plugin_id: The plugin to execute tools from
            tools: List of tool names to execute in order
            payload: Initial payload dictionary

        Returns:
            Dictionary with:
                - result: Output from the last tool execution
                - steps: List of step outputs for debugging

        Raises:
            ValueError: If plugin not found, tools is empty, or tool not in plugin
        """
        # Validate plugin
        plugin = self.plugins.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        # Validate tools[]
        if not tools or not isinstance(tools, list):
            raise ValueError("Pipeline requires a non-empty tools[] array")

        steps: List[Dict[str, Any]] = []
        current_payload = payload

        for idx, tool_name in enumerate(tools):
            # Validate tool exists
            if tool_name not in plugin.tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in plugin '{plugin_id}'"
                )

            # Execute tool
            output = plugin.run_tool(tool_name, current_payload)

            # -----------------------------------------
            # PHASE‑13 COMMIT 8: Logging for observability
            # -----------------------------------------
            logger.info(
                "Video pipeline step",
                extra={
                    "plugin_id": plugin_id,
                    "tool_name": tool_name,
                    "step": idx,
                },
            )

            # Record step
            steps.append({"tool": tool_name, "output": output})

            # Prepare payload for next tool
            # Pass original payload + previous tool output as "input"
            current_payload = {**payload, "input": output}

        # Final output is the last tool's output
        return {"result": steps[-1]["output"], "steps": steps}

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist.

        Args:
            plugin_id: Plugin identifier to validate
            tools: List of tool names to validate

        Raises:
            ValueError: If validation fails
        """
        pass

    def run_on_file(self, file_path: str, plugin_id: str, tools: List[str]):
        """
        Phase‑16 compatibility: run a pipeline using a file path.
        The worker always calls this with (file_path, plugin_id, tools).
        """
        payload = {"file_path": file_path}
        return self.run_pipeline(plugin_id, tools, payload)

    def run(self, file_path: str, plugin_id: str, tools: List[str]):
        """
        Alias used by some worker implementations.
        """
        return self.run_on_file(file_path, plugin_id, tools)

    def run_on_payload(self, payload: Dict[str, Any], plugin_id: str, tools: List[str]):
        """
        Optional compatibility wrapper for payload‑based execution.
        """
        return self.run_pipeline(plugin_id, tools, payload)


%%writefile /kaggle/working/forgesyte/server/app/workers/run_job_worker.py
"""Startup script for JobWorker - processes video jobs.

Run as:
  python -m server.app.workers.run_job_worker
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_db  # noqa: E402
from server.app.workers.worker import JobWorker  # noqa: E402
from server.app.services.storage.local_storage import LocalStorageService
from server.app.services.video_pipeline_service import VideoPipelineService  


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_worker_forever(plugin_manager):
    logger.info("🚀 Starting JobWorker thread...")

    init_db()

    storage = LocalStorageService()
    pipeline_service = VideoPipelineService(plugin_manager) 

    worker = JobWorker(
        storage=storage,
        pipeline_service=pipeline_service,
    )

    logger.info("👷 JobWorker thread initialized")
    worker.run_forever()



def main():
    """CLI entrypoint for standalone worker process."""
    try:
        logger.info("🚀 Starting JobWorker (standalone)...")

        init_db()

        worker = JobWorker()

        logger.info("👷 JobWorker initialized")
        worker.run_forever()

    except Exception as e:
        logger.error(f"❌ JobWorker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⛔ JobWorker stopped by user")
        sys.exit(0)


/home/rogermt/forgesyte/server/app/workers/worker.py
:

```python
def run_on_file(self, file_path: str, plugin_id: str, tools: List[str])
```

So we fix this **in the worker**, right where it calls `run_on_file`.

---

### 1. Update the `PipelineService` protocol to match the real service

In `worker.py`, change this:

```python
class PipelineService(Protocol):
    """Protocol for pipeline service (allows dependency injection)."""

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ):
        """Execute pipeline on video file."""
        ...
```

to this:

```python
class PipelineService(Protocol):
    """Protocol for pipeline service (allows dependency injection)."""

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        tools,
    ):
        """Execute pipeline on video file."""
        ...
```

(You can tighten `tools` to `List[str]` if you like, but structurally this is the important change.)

---

### 2. Pass `tools` when calling `run_on_file`

In `_execute_pipeline`, change:

```python
# Execute pipeline on video file
results = self._pipeline_service.run_on_file(
    str(input_file_path),
    job.pipeline_id,
)
```

to:

```python
# Execute pipeline on video file
results = self._pipeline_service.run_on_file(
    str(input_file_path),
    job.pipeline_id,
    job.tools,  # or job.pipeline_tools if that's the field name
)
```

Use whichever field on `Job` actually holds the tools list (likely `job.tools` given your Phase‑13 design).

---

After these two changes:

- The worker calls `run_on_file(file_path, plugin_id, tools)`
- `VideoPipelineService.run_on_file(self, file_path, plugin_id, tools)` matches exactly
- No more “missing 1 required positional argument: 'tools'”
- The pipeline will finally execute with the tools list you stored on the job