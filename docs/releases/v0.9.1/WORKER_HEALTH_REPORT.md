# Worker Health Endpoint Report

**Endpoint:** `GET /v1/worker/health`
**Symptom:** Always returned `{"alive": false, "last_heartbeat": 0.0}`
**Date:** 2026-02-20
**Status:** ✅ Fixed — Issue #207, commit `ae0e7e9`

---

## How It Works

1. **`worker_state.py`** — Module-level singleton `worker_last_heartbeat = WorkerHeartbeat()` with `timestamp = 0.0`
2. **`main.py` lifespan (lines 248–256)** — Starts a daemon thread running `run_worker_forever()`
3. **`worker.py:run_forever()`** — Calls `worker_last_heartbeat.beat()` each loop iteration, setting `timestamp = time.time()`
4. **`worker_health.py`** — Reads that same singleton to check `is_recent()` and `timestamp`

Since the worker runs as a daemon **thread** (not a separate process), it shares the same module singleton — `beat()` updates the timestamp the health endpoint reads.

---

## Root Cause: Worker Thread Crashed Silently Before `beat()` Was Ever Called

`last_heartbeat: 0.0` meant `beat()` was **never called even once** — `run_forever()` never executed. The daemon thread died silently during setup inside `run_worker_forever()`.

### Issue 1: Bad Import Path in `run_job_worker.py` (line 19)

```python
# BEFORE (broken)
from server.app.workers.worker import JobWorker

# AFTER (fixed)
from app.workers.worker import JobWorker
```

All other imports in the file used the `app.` prefix. The `server.app.` path caused an `ImportError` when the module was loaded via relative import from `main.py`.

### Issue 2: Duplicate `init_db()` Call in `run_worker_forever()` (line 37)

```python
# BEFORE (broken) — called init_db() again inside the thread
def run_worker_forever(plugin_manager: PluginRegistry):
    init_db()          # ← DuckDB single-writer conflict
    storage = ...

# AFTER (fixed) — lifespan already initializes DB before spawning thread
def run_worker_forever(plugin_manager: PluginRegistry):
    storage = ...
```

The lifespan already calls `init_db()` at `main.py:168`. Calling it again from the daemon thread triggered a DuckDB `TransactionContext Error: Conflict on update!`.

### Issue 3 (Previously Fixed): Stale Code in `main.py` (lines 173–176)

A previous commit had left a duplicate `worker_thread.start()` referencing an undefined variable inside the database `except` handler, plus a duplicate `except Exception` clause. This was dead code under normal operation but caused ruff F821/B025 and mypy errors. Already removed prior to this fix.

---

## Why It Was Silent

Daemon threads swallow unhandled exceptions — Python does not propagate them to the main thread. The thread crashed, but no error appeared in stdout. The `except` block in `main.py` only catches errors during `threading.Thread()` construction or `.start()`, not errors inside the thread's target function.

---

## Fix Applied

| Change | File | Line |
|--------|------|------|
| Import path `server.app.` → `app.` | `run_job_worker.py` | 19 |
| Remove duplicate `init_db()` | `run_job_worker.py` | 37 |
| Remove stale dead code (prior fix) | `main.py` | 173–176 |

**Validation:**
- `uv run ruff check --fix app/` — ✅ All checks passed
- `uv run mypy app/ --no-site-packages` — ✅ 0 errors (130 files)
- `uv run pytest tests/` — ✅ 1334 passed

---

## Files Involved

| File | Role |
|------|------|
| `server/app/workers/worker_state.py` | Heartbeat singleton |
| `server/app/api_routes/routes/worker_health.py` | Health endpoint |
| `server/app/workers/worker.py` | Worker loop with `beat()` call |
| `server/app/workers/run_job_worker.py` | Worker thread entry point (crash site — **fixed**) |
| `server/app/main.py` | Lifespan — thread startup (stale code — **fixed**) |
