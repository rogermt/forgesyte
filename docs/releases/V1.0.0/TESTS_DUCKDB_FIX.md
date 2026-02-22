Below is the **complete, single set of changes** you need to make to permanently eliminate the DuckDB lock + `job-worker-thread` warnings during pytest, based on the **exact code you pasted** (`app/main.py`, `app/core/database.py`, `run_job_worker.py`, `worker.py`) and the **exact error** (`Could not set lock on file data/foregsyte.duckdb`).

The root cause is:

- `app/main.py` **always starts** the JobWorker thread in lifespan
- `worker.py` uses `SessionLocal` from `app.core.database`
- `app/core/database.py` hardcodes `duckdb:///data/foregsyte.duckdb`
- if any other process (dev server) has that DB open, DuckDB file locking triggers the thread exception warning

We fix this by:
1) making the DB URL configurable
2) forcing pytest to use a unique temp DuckDB file
3) disabling workers in pytest
4) adding a defensive “don’t run worker” guard inside `run_worker_forever`
5) fixing your test SessionLocal patch to be thread-safe

---

## 1) Change `app/core/database.py` to use an environment variable for the DB

**File:** `server/app/core/database.py`

Replace the hardcoded engine URL with this env-driven setup:

```py
"""DuckDB SQLAlchemy database configuration."""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base: Any = declarative_base()

DEFAULT_DB_URL = "duckdb:///data/foregsyte.duckdb"
DATABASE_URL = os.getenv("FORGESYTE_DATABASE_URL", DEFAULT_DB_URL)

def _ensure_parent_dir(db_url: str) -> None:
    # Ensure parent directory exists for file-based DuckDB URLs
    if db_url in ("duckdb:///:memory:", "duckdb:///:memory"):
        return
    prefix = "duckdb:///"
    if db_url.startswith(prefix):
        db_path = db_url[len(prefix):]
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)

_ensure_parent_dir(DATABASE_URL)

engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def init_db():
    try:
        from ..models.job import Job  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise RuntimeError(f"Could not initialize database schema: {e}") from e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Outcome:** production still defaults to `data/foregsyte.duckdb`, but tests can redirect it.

---

## 2) Disable worker thread + force a unique temp DuckDB file during pytest

**File:** `server/tests/conftest.py`  
Put this **at the top of the file**, right after your API key env vars and before importing anything from `app.*`:

```py
import tempfile
import uuid

# Do NOT start background JobWorker threads during tests
os.environ.setdefault("FORGESYTE_ENABLE_WORKERS", "0")

# Make the app use an isolated DuckDB file (never data/foregsyte.duckdb)
test_db_file = os.path.join(
    tempfile.gettempdir(),
    f"forgesyte_pytest_{uuid.uuid4().hex}.duckdb",
)
os.environ.setdefault("FORGESYTE_DATABASE_URL", f"duckdb:///{test_db_file}")
```

**Outcome:** even if you forget to stop your dev server, pytest won’t touch the same DB file.

---

## 3) Gate the worker thread start in `app/main.py` lifespan

**File:** `server/app/main.py`

Replace your current “Start JobWorker thread” block with this:

```py
# Start JobWorker thread (disabled in tests via FORGESYTE_ENABLE_WORKERS=0)
enable_workers = os.getenv("FORGESYTE_ENABLE_WORKERS", "1") == "1"

if enable_workers:
    try:
        from .workers.run_job_worker import run_worker_forever

        worker_thread = threading.Thread(
            target=run_worker_forever,
            args=(plugin_manager,),
            name="job-worker-thread",
            daemon=True,
        )
        worker_thread.start()
        app.state.worker_thread = worker_thread  # optional
        logger.info("JobWorker thread started")
    except Exception as e:
        logger.error("Failed to start JobWorker thread", extra={"error": str(e)})
else:
    logger.info("JobWorker thread disabled (FORGESYTE_ENABLE_WORKERS=0)")
```

**Outcome:** no job-worker-thread in pytest, therefore no DuckDB lock errors from the worker thread.

---

## 4) Add a “belt and suspenders” guard inside `run_worker_forever`

Even with the main.py gate, it’s wise to guard the worker too (prevents accidental starts anywhere else).

**File:** `server/app/workers/run_job_worker.py`

### A) Add import
Add:

```py
import os
```

### B) Change `run_worker_forever` to:

```py
def run_worker_forever(plugin_manager: PluginRegistry):
    """Run the JobWorker loop (used by FastAPI lifespan thread)."""
    if os.getenv("FORGESYTE_ENABLE_WORKERS", "1") != "1":
        logger.info("👷 JobWorker thread disabled (FORGESYTE_ENABLE_WORKERS=0)")
        return

    logger.info("🚀 Starting JobWorker thread...")

    storage = LocalStorageService()
    plugin_service = PluginManagementService(plugin_manager)

    worker = JobWorker(
        storage=storage,
        plugin_service=plugin_service,
    )

    logger.info("👷 JobWorker thread initialized")
    worker.run_forever()
```

Optional (but good): also gate `main()` similarly.

---

## 5) Fix the thread-unsafe SessionLocal monkeypatch in tests (TestClient runs app in another thread)

Right now, your autouse fixture returns the **same session object** from pytest into FastAPI request threads. That is unsafe.

**File:** `server/tests/conftest.py`

Replace your current `mock_session_local` fixture with:

```py
@pytest.fixture(autouse=True)
def mock_session_local(test_engine, monkeypatch):
    """Patch SessionLocal in endpoints to use the test engine (thread-safe)."""
    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(bind=test_engine)

    monkeypatch.setattr(
        "app.api_routes.routes.video_submit.SessionLocal",
        TestingSessionLocal,
    )
```

If you have other routes using their own `SessionLocal` imports, patch them too (same idea).

---

## 6) (Not DuckDB, but will break CI) Remove the hardcoded absolute sys.path

**File:** `server/tests/tasks/test_task_processor_get_result.py`  
Remove:

```py
sys.path.insert(0, "/home/rogermt/forgesyte/server")
```

This is guaranteed to fail anywhere except your machine.

---

## 7) Verify it worked

Run:

```bash
pytest -q
```

You should no longer see:

- `PytestUnhandledThreadExceptionWarning: Exception in thread job-worker-thread`
- `Could not set lock on file ".../data/foregsyte.duckdb"`

As a quick confirmation before code changes, you can also test:

```bash
FORGESYTE_ENABLE_WORKERS=0 pytest -q
```

If the warning disappears, that confirms the diagnosis (your main.py thread-start is the trigger).

---

### Why this fully solves your exact failure
- The worker thread is the thing crashing (stack trace shows `run_job_worker.py -> worker.py -> SessionLocal -> DuckDB lock`)
- You prevent it from starting in pytest (`FORGESYTE_ENABLE_WORKERS=0`)
- You ensure even if it did start, it connects to a unique temp DB (`FORGESYTE_DATABASE_URL`)
- You remove the hardcoded production DB URL from `database.py`

A clean shutdown pattern for your `JobWorker` thread has two parts:

1) **A stop signal** that the main app can trigger (a `threading.Event` is ideal)  
2) **A `join()` on shutdown** so pytest / uvicorn doesn’t leave threads running and doesn’t produce unhandled thread exceptions

Right now your worker loop is:

```py
while self._running:
    processed = self.run_once()
    if not processed:
        time.sleep(0.5)
```

That can be made cleanly stoppable without relying on OS signals (signals won’t fire in a non-main thread anyway).

Below is a drop-in approach that matches your codebase.

---

## 1) Update `JobWorker` to support a stop event + stop() method

### File: `server/app/workers/worker.py`

Make these changes:

### A) Add an optional `stop_event` to `__init__` and a `stop()` method

```py
import threading
import time
# ... existing imports ...

class JobWorker:
    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
        storage: Optional[StorageService] = None,
        plugin_service=None,
        stop_event: Optional[threading.Event] = None,   # NEW
    ) -> None:
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._plugin_service = plugin_service

        self._running = True
        self._stop_event = stop_event or threading.Event()  # NEW

        # Keep your signal handler logic for standalone mode only:
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)

    def stop(self) -> None:
        """Request the worker to stop gracefully."""
        self._running = False
        self._stop_event.set()
```

### B) Change `run_forever()` to wait on the event instead of sleeping

This avoids a “stuck sleeping” thread during shutdown and makes stop immediate.

```py
def run_forever(self) -> None:
    """Run the worker loop until shutdown is requested."""
    logger.info("Worker started")
    while self._running and not self._stop_event.is_set():
        worker_last_heartbeat.beat()

        processed = self.run_once()
        if not processed:
            # Wait up to 0.5s, but wake immediately on stop
            self._stop_event.wait(0.5)

    logger.info("Worker stopped")
```

That’s it: now you can shut it down from FastAPI lifespan without signals.

---

## 2) Update `run_worker_forever()` to accept a stop event

### File: `server/app/workers/run_job_worker.py`

Add `import os` and `import threading`, then modify `run_worker_forever`:

```py
import os
import threading
# ... existing imports ...

def run_worker_forever(plugin_manager: PluginRegistry, stop_event: threading.Event):
    """Run the JobWorker loop (used by FastAPI lifespan thread)."""
    if os.getenv("FORGESYTE_ENABLE_WORKERS", "1") != "1":
        logger.info("👷 JobWorker thread disabled (FORGESYTE_ENABLE_WORKERS=0)")
        return

    logger.info("🚀 Starting JobWorker thread...")

    storage = LocalStorageService()
    plugin_service = PluginManagementService(plugin_manager)

    worker = JobWorker(
        storage=storage,
        plugin_service=plugin_service,
        stop_event=stop_event,   # NEW
    )

    logger.info("👷 JobWorker thread initialized")
    worker.run_forever()
```

(You can keep `main()` as-is; for standalone, the signal handler will still work.)

---

## 3) Start worker with stop_event, and join it on FastAPI shutdown

### File: `server/app/main.py` in `lifespan`

Replace your worker startup block with the version below (includes clean shutdown):

```py
# Start JobWorker thread (DuckDB requires same process)
enable_workers = os.getenv("FORGESYTE_ENABLE_WORKERS", "1") == "1"
worker_thread = None
worker_stop_event = None

if enable_workers:
    try:
        from .workers.run_job_worker import run_worker_forever

        worker_stop_event = threading.Event()

        worker_thread = threading.Thread(
            target=run_worker_forever,
            args=(plugin_manager, worker_stop_event),
            name="job-worker-thread",
            daemon=False,  # IMPORTANT: allow join/clean shutdown
        )
        worker_thread.start()

        app.state.worker_thread = worker_thread
        app.state.worker_stop_event = worker_stop_event

        logger.info("JobWorker thread started")
    except Exception as e:
        logger.error("Failed to start JobWorker thread", extra={"error": str(e)})
else:
    logger.info("JobWorker thread disabled (FORGESYTE_ENABLE_WORKERS=0)")

yield

# Shutdown: stop + join worker thread
try:
    stop_event = getattr(app.state, "worker_stop_event", None)
    thread = getattr(app.state, "worker_thread", None)

    if stop_event is not None:
        stop_event.set()

    if thread is not None and thread.is_alive():
        thread.join(timeout=5.0)
        if thread.is_alive():
            logger.warning("JobWorker thread did not stop within timeout")
        else:
            logger.info("JobWorker thread stopped cleanly")
except Exception as e:
    logger.error("Error during JobWorker shutdown", extra={"error": str(e)})
```

### Why `daemon=False`?
- Daemon threads can be killed abruptly at interpreter shutdown.
- You *want* a clean stop + join, especially in pytest and CI.

(If you insist on daemon threads, you can still try to stop/join, but it’s less reliable.)

---

## 4) Optional: Make `run_once()` responsive to shutdown mid-DB work
If you want to stop faster during long jobs, add checks in `run_once()` / `_execute_pipeline()` like:

```py
if self._stop_event.is_set():
    return False
```

But the above is already a good clean shutdown baseline.

---

## 5) What this solves for your tests
- No more background thread continuing after tests
- No more “unhandled thread exception” warnings during teardown
- Much less flakiness due to DB locks and lingering threads

Your current `/v1/worker/health` endpoint only checks the **heartbeat** (`worker_last_heartbeat.is_recent()`). That’s good, but once you add a clean shutdown (stop_event + join), it’s very useful to expose:

- whether workers are **enabled**
- whether the worker thread is **running**
- whether shutdown has been **requested** (`stop_event.is_set()`)

You can do that without breaking backward compatibility by keeping the existing fields (`alive`, `last_heartbeat`) and adding extra fields.

Below is a clean, practical implementation.

---

## 1) Store thread + stop_event in `app.state` (required for health reporting)

In your `app/main.py` lifespan worker startup (the version you already have), make sure you set:

```py
app.state.worker_thread = worker_thread
app.state.worker_stop_event = worker_stop_event
```

And on shutdown you set the stop_event and join. (As previously described.)

This gives the health endpoint something real to introspect.

---

## 2) Update the worker health endpoint to include thread/stop state

### File: `server/app/api_routes/routes/worker_health.py`

Replace your file with:

```py
"""Worker health endpoint."""

import os
from typing import Any, Optional

from fastapi import APIRouter, Request

from ...workers.worker_state import worker_last_heartbeat

router = APIRouter()


@router.get("/v1/worker/health")
def get_worker_health(request: Request) -> dict[str, Any]:
    """
    Check if the in-process video worker thread is alive.

    Backward compatible fields:
      - alive: bool
      - last_heartbeat: float|None

    Extra diagnostic fields:
      - enabled: bool
      - thread_alive: bool
      - stopping: bool
      - heartbeat_recent: bool
    """
    enabled = os.getenv("FORGESYTE_ENABLE_WORKERS", "1") == "1"

    thread = getattr(request.app.state, "worker_thread", None)
    stop_event = getattr(request.app.state, "worker_stop_event", None)

    thread_alive = bool(thread and getattr(thread, "is_alive", lambda: False)())
    stopping = bool(stop_event and getattr(stop_event, "is_set", lambda: False)())

    heartbeat_recent = worker_last_heartbeat.is_recent()

    # Define "alive" as: enabled + thread alive + heartbeat fresh + not stopping
    alive = bool(enabled and thread_alive and heartbeat_recent and not stopping)

    return {
        "alive": alive,
        "last_heartbeat": worker_last_heartbeat.timestamp,
        "enabled": enabled,
        "thread_alive": thread_alive,
        "stopping": stopping,
        "heartbeat_recent": heartbeat_recent,
    }
```

### Why this is good
- Keeps your original contract (`alive`, `last_heartbeat`)
- Adds high-signal debug info when tests/dev runs are confusing
- Works correctly when workers are disabled in pytest (`enabled=False`, `thread_alive=False`)

---

## 3) Optional: Make “alive” meaningful if you ever run a *separate* worker process
Right now your design runs the worker in the same FastAPI process (thread). If you run the worker as a standalone process (`python -m ...run_job_worker`), then `request.app.state.worker_thread` won’t exist (different process), and your “alive” will show false even though a worker process might be alive.

If you need multi-process health later, you’ll want the heartbeat stored in something shared (DuckDB table, file, Redis). For now, your thread-based approach is correct.

---

## 4) Recommendation: adjust heartbeat semantics during shutdown (optional)
When you set `stop_event`, the thread may still have a “recent” heartbeat for a short time. That’s why the endpoint includes `stopping` and computes `alive = ... and not stopping`.

---




rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$ cd ~/forgesyte/server && FORGESYTE_ENABLE_WORKERS=0 uv run pytest tests/mcp -qv
============================================================================================= test session starts ==============================================================================================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/rogermt/forgesyte/server
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 279 items

tests/mcp/test_mcp.py .......................................                                                                                                                                            [ 13%]
tests/mcp/test_mcp_adapter.py ..................................                                                                                                                                         [ 26%]
tests/mcp/test_mcp_capabilities_update.py ...                                                                                                                                                            [ 27%]
tests/mcp/test_mcp_endpoints.py .............                                                                                                                                                            [ 31%]
tests/mcp/test_mcp_handlers_gemini_integration.py ...........................                                                                                                                            [ 41%]
tests/mcp/test_mcp_handlers_http_endpoint.py .................                                                                                                                                           [ 47%]
tests/mcp/test_mcp_handlers_resources.py .......                                                                                                                                                         [ 50%]
tests/mcp/test_mcp_handlers_tools.py ............                                                                                                                                                        [ 54%]
tests/mcp/test_mcp_jsonrpc.py ............................................................                                                                                                               [ 75%]
tests/mcp/test_mcp_optimization.py .....................                                                                                                                                                 [ 83%]
tests/mcp/test_mcp_protocol_methods.py .............                                                                                                                                                     [ 88%]
tests/mcp/test_mcp_routes_content_length.py ...                                                                                                                                                          [ 89%]
tests/mcp/test_mcp_transport.py .................                                                                                                                                                        [ 95%]
tests/mcp/test_mcp_url_fetch.py ......                                                                                                                                                                   [ 97%]
tests/mcp/test_mcp_version_negotiation.py .......                                                                                                                                                        [100%]

=============================================================================================== warnings summary ===============================================================================================
app/models_pydantic.py:246
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:246: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    args: Dict[str, Any] = Field(

app/models_pydantic.py:243
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:243: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunRequest(BaseModel):

app/models_pydantic.py:264
  /home/rogermt/forgesyte/server/tests/../app/models_pydantic.py:264: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginToolRunResponse(BaseModel):

app/plugins/health/health_model.py:14
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginHealthResponse(BaseModel):

app/plugins/health/health_model.py:53
  /home/rogermt/forgesyte/server/tests/../app/plugins/health/health_model.py:53: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class PluginListResponse(BaseModel):

app/schemas/job.py:10
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobStatusResponse(BaseModel):

app/schemas/job.py:25
  /home/rogermt/forgesyte/server/tests/../app/schemas/job.py:25: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class JobResultsResponse(BaseModel):

app/realtime/message_types.py:49
  /home/rogermt/forgesyte/server/tests/../app/realtime/message_types.py:49: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    class RealtimeMessage(BaseModel):

.venv/lib/python3.13/site-packages/pydantic/_internal/_generate_schema.py:392
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pydantic/_internal/_generate_schema.py:392: PydanticDeprecatedSince20: `json_encoders` is deprecated. See https://docs.pydantic.dev/2.12/concepts/serialization/#custom-serializers for alternatives. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    warnings.warn(

.venv/lib/python3.13/site-packages/pythonjsonlogger/jsonlogger.py:11
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/pythonjsonlogger/jsonlogger.py:11: DeprecationWarning: pythonjsonlogger.jsonlogger has been moved to pythonjsonlogger.json
    warnings.warn(

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_initially_empty
  tests/mcp/test_mcp_optimization.py:144: PytestWarning: The test <Function test_manifest_cache_initially_empty> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_initially_empty(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_stores_manifest
  tests/mcp/test_mcp_optimization.py:149: PytestWarning: The test <Function test_manifest_cache_stores_manifest> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_stores_manifest(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_stores_timestamp
  tests/mcp/test_mcp_optimization.py:157: PytestWarning: The test <Function test_manifest_cache_stores_timestamp> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_stores_timestamp(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_is_valid_within_ttl
  tests/mcp/test_mcp_optimization.py:165: PytestWarning: The test <Function test_manifest_cache_is_valid_within_ttl> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_is_valid_within_ttl(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_manifest_cache_expires_after_ttl
  tests/mcp/test_mcp_optimization.py:172: PytestWarning: The test <Function test_manifest_cache_expires_after_ttl> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_expires_after_ttl(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_get_manifest_uses_cache
  tests/mcp/test_mcp_optimization.py:182: PytestWarning: The test <Function test_get_manifest_uses_cache> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_get_manifest_uses_cache(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_get_manifest_regenerates_after_expiry
  tests/mcp/test_mcp_optimization.py:192: PytestWarning: The test <Function test_get_manifest_regenerates_after_expiry> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_get_manifest_regenerates_after_expiry(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestManifestCaching::test_cache_ttl_configurable
  tests/mcp/test_mcp_optimization.py:215: PytestWarning: The test <Function test_cache_ttl_configurable> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_cache_ttl_configurable(self, adapter: MCPAdapter) -> None:

tests/mcp/test_mcp_optimization.py::TestOptimizationPerformance::test_manifest_cache_reduces_builds
  tests/mcp/test_mcp_optimization.py:324: PytestWarning: The test <Function test_manifest_cache_reduces_builds> is marked with '@pytest.mark.asyncio' but it is not an async function. Please remove the asyncio mark. If the test is not marked explicitly, check for global marks applied via 'pytestmark'.
    def test_manifest_cache_reduces_builds(

tests/mcp/test_mcp_routes_content_length.py::TestContentLengthCorrectness::test_uvicorn_no_content_length_mismatch
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions
    warnings.warn(  # deprecated in 14.0 - 2024-11-09

tests/mcp/test_mcp_routes_content_length.py::TestContentLengthCorrectness::test_uvicorn_no_content_length_mismatch
  /home/rogermt/forgesyte/server/.venv/lib/python3.13/site-packages/uvicorn/protocols/websockets/websockets_impl.py:17: DeprecationWarning: websockets.server.WebSocketServerProtocol is deprecated
    from websockets.server import WebSocketServerProtocol

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================================================================================== 279 passed, 21 warnings in 34.45s =======================================================================================
rogermt@LAPTOP-8B85T8ID:~/forgesyte/server$ cd ~/forgesyte/server && FORGESYTE_ENABLE_WORKERS=0 uv run pytest tests -qv
============================================================================================= test session starts =========================================================