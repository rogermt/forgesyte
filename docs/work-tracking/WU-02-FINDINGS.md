# WU-02: Root Cause Investigation - Findings

**Status**: ✅ Complete  
**Completed**: 2026-01-12  
**Investigation Target**: 500 errors when WebUI calls server

---

## Root Cause Analysis

**The Issue**:
The 500 error was caused by a `RuntimeError: PluginManagementService not initialized` (or similar dependency failure) which bubbled up from `get_plugin_service`.

**The Defect**:
In `server/app/main.py`:
```python
from .tasks import init_task_processor, job_store, task_processor
# ...
init_task_processor(plugin_manager) # Updates global in tasks.py
# ...
if task_processor is None: # Checks global in main.py (which remains None)
    raise RuntimeError("Task processor initialization failed")
```
Python's `from module import variable` imports the *value* at import time. Since `task_processor` starts as `None` in `tasks.py`, `main.py` imports `None`. When `init_task_processor` updates the variable inside `tasks.py`, `main.py`'s reference is **not updated**.

Consequently, `main.py` believed initialization failed (or worse, used `None` to initialize services), causing `AnalysisService` and `JobManagementService` to fail or trigger the explicit `RuntimeError`.

**The Fix**:
Updated `server/app/main.py` to capture the return value of `init_task_processor` into a local variable and use that for service injection.

```python
local_task_processor = init_task_processor(plugin_manager)
# ...
app.state.analysis_service_rest = AnalysisService(local_task_processor, ...)
```

---

## Verification

**Test**:
1. Started server.
2. `curl http://localhost:8000/v1/plugins`

**Result**:
- **Before**: 500 Internal Server Error (RuntimeError in logs)
- **After**: 200 OK with JSON payload `{"plugins": [...], "count": 4}`

**Conclusion**:
The server-side initialization bug is resolved. The API is now functional.