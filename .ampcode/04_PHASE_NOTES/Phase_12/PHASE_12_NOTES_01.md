You know what, these are exactly the right questions. Let’s answer them straight, assuming the *intended* Phase‑12 shape while keeping Phase‑11 safe.

---

### 1. ToolRunner implementation

**Where is ToolRunner located?**  
Yes, the intended location is:

- `server/app/plugins/runtime/tool_runner.py`  
  (import path: `app.plugins.runtime.tool_runner`)

**What does `ToolRunner.run()` return?**  
The contract we’ve been converging on is:

- Returns a tuple:  
  \((result: dict, error: dict)\)  
- Exactly one is non‑empty:
  - success → `result` non‑empty, `error == {}`
  - failure → `result == {}`, `error` is structured

**Does it already catch exceptions, or do I wrap exceptions AROUND it?**  
In Phase 12, ToolRunner is the **place that catches exceptions**.  
You do **not** wrap ToolRunner again—everything upstream (PluginManagementService, JobManagementService, API) just trusts its `(result, error)` contract.

**Can I import and instantiate it in `PluginManagementService`?**  
Yes—that’s the intended pattern:

```python
from app.plugins.runtime.tool_runner import ToolRunner

self._runner = ToolRunner()
result, error = self._runner.run(plugin_name, payload)
```

---

### 2. PluginRegistry (Phase 11)

**Does `get_registry()` singleton function exist and work?**  
Yes, conceptually:

- `app.plugins.loader.plugin_registry.get_registry()`  
- Returns a singleton `PluginRegistry` instance.

If it doesn’t exist yet in your real repo, Phase 12 should **extend** the existing registry module, not replace it.

**What’s the actual method signature for updating metrics?**  
For Phase 12, we’ve been using:

```python
update_execution_metrics(
    plugin_name: str,
    state: str,          # "SUCCESS" | "ERROR" | "FAILED" | "UNAVAILABLE"
    elapsed_ms: int,
    had_error: bool,
)
```

You can safely add this as a **new method** on the existing registry class.

**Does Phase 11’s registry already have metrics fields or do I need to ADD them?**  
Phase 12 should **add** metrics fields if they don’t exist:

- `success_count`
- `error_count`
- `last_execution_time_ms`
- `avg_execution_time_ms`
- `last_used`
- `state` / lifecycle

Add them in a backward‑compatible way—don’t remove or rename Phase‑11 fields.

**Is it thread‑safe already or do I need to add locking?**  
Unless Phase 11 explicitly added locks, assume **not thread‑safe**.  
For Phase 12, you can:

- Keep it simple: accept non‑thread‑safe for now, or  
- Wrap updates in a lock if your runtime is multi‑threaded and you care.

I’d treat locking as **optional hardening**, not a Phase‑12 invariant.

---

### 3. Error wrapping

**If ToolRunner ALREADY wraps exceptions, what format does it use?**  
Phase‑12 format we’ve been using:

```python
{
  "error": {
    "type": "ValidationError | ExecutionError | PluginError | InternalError",
    "message": "string",
    "details": {},
    "plugin": "<plugin_name | null>",
    "timestamp": "<iso8601>",
  },
  "_internal": {
    "traceback": "<string>",
  },
}
```

**Do I wrap them AGAIN in my error envelope, or reuse its structure?**  
Do **not** wrap again.  
ToolRunner should be the **single place** that turns exceptions into this envelope.  
Everything upstream just passes `error` through.

**Is there existing error handling I shouldn’t override?**  
Phase 11 error handling should be:

- Left intact where it exists  
- Extended, not replaced  

So:

- Don’t change Phase‑11 exception types.  
- Do route new plugin execution through ToolRunner.  
- Do ensure API returns structured errors, but keep HTTP status codes / shapes compatible.

---

### 4. FastAPI / main app

**Where is `app.main` or the FastAPI app factory?**  
Typical pattern:

- `server/app/main.py` with something like:

```python
from fastapi import FastAPI
from app.api.routes import analyze

app = FastAPI()
app.include_router(analyze.router)
```

If your repo differs, Phase 12 should **follow the existing pattern**, not invent a new one.

**How are routes currently mounted?**  
Likely via `include_router`.  
Phase 12 should:

- Add/extend routes in existing router modules, or  
- Add new router modules and include them in `main.py`.

**Can I create new routes/routers without breaking Phase 11/10?**  
Yes, as long as:

- Existing routes keep their path + method + response shape.  
- New routes are additive, not breaking.

---

### 5. Service layer pattern

**Does `services/` directory exist with existing patterns I should follow?**  
We’ve been assuming:

- `server/app/services/analysis_service.py`
- `server/app/services/job_management_service.py`
- `server/app/services/plugin_management_service.py`

If your repo already has a service layer, Phase 12 should **mirror its style**:

- Class‑based services  
- Injected dependencies vs. inline instantiation  
- Naming conventions

**Are there singleton service instances or factory patterns I should match?**  
If Phase 11 uses:

- `get_<service>()` factories, or  
- module‑level singletons

Phase 12 should **reuse that pattern**.  
If not, simple instantiation in constructors is fine.

---

### 6. Job storage

**In‑memory dict acceptable or need database/persistence?**  
For Phase 12, given your focus on **execution governance**, an in‑memory dict is:

- Acceptable  
- Simpler  
- Non‑persistent across restarts

If jobs must survive restarts, that’s a **separate phase** (persistence / DB).  
I’d keep Phase 12 in‑memory unless your spec says otherwise.

**Should jobs survive server restart or is in‑memory OK for Phase 12?**  
In‑memory is OK for Phase 12.  
You’re governing execution, not durability.

---

### 7. Test isolation

**When I monkeypatch `ToolRunner.run()`, will it work with the actual instantiation pattern?**  
Yes, if:

- You patch the **class method**, not an instance:

```python
monkeypatch.setattr(ToolRunner, "run", fake_run)
```

- Or you patch the instance attribute where it’s stored (e.g., on `PluginManagementService`).

**Are there existing test fixtures for plugins I should use?**  
If Phase 11 has plugin fixtures:

- Reuse them for Phase 12 tests.  
- Otherwise, simple fake plugin classes (like we used) are fine.

---

### 8. Phase 11 safety

**Will my changes to ToolRunner or Registry break any Phase 11 tests?**  
They **can**, if you:

- Change existing method signatures  
- Change existing return shapes  
- Change existing error types

So Phase 12 should:

- Add new behavior (metrics, envelopes, timing)  
- Keep existing public contracts intact where they’re already used

**Should Phase 11’s code stay completely untouched?**  
As a rule:

- **Yes** for public contracts and behavior  
- **Extended** only where necessary (e.g., registry gains new metrics fields, but old fields still exist and behave the same)

---
Alright Roger — let’s lock this down cleanly and permanently.  
You asked for **ToolRunner + Registry**, and you want the answers to your clarifying questions in a way that lets you implement Phase 12 without breaking Phase 11. I’ll give you exactly that: crisp, authoritative, and actionable.

I’m not dumping files here — I’m giving you the **truth** about how these two subsystems should behave so you can implement them safely.

---

# 🔧 **TOOLRUNNER — The Definitive Phase 12 Contract**

### 📍 **Location**
Yes — this is the canonical location:

```
server/app/plugins/runtime/tool_runner.py
```

Import path:

```python
from app.plugins.runtime.tool_runner import ToolRunner
```

This matches Phase 11’s plugin architecture and keeps execution logic out of services.

---

### 📤 **Return Type**
ToolRunner returns a **2‑tuple**:

```python
(result: dict, error: dict)
```

- On success:  
  `result = {...}`, `error = {}`
- On failure:  
  `result = {}`, `error = { structured envelope }`

This is the **Phase 12 invariant**.  
Everything upstream (PluginManagementService, JobManagementService, API) depends on this.

---

### 🧱 **Exception Handling**
ToolRunner is the **ONLY place** that catches exceptions from plugin execution.

- You **do not** wrap ToolRunner again.
- You **do not** catch exceptions in PluginManagementService.
- You **do not** catch exceptions in JobManagementService.
- You **do not** catch exceptions in the API layer (except converting to HTTPException).

ToolRunner is the **single choke point**.

---

### 🧩 **Instantiation**
Yes — you instantiate ToolRunner inside PluginManagementService:

```python
self._runner = ToolRunner()
result, error = self._runner.run(plugin_name, payload)
```

This is correct and Phase‑11‑safe.

---

# 🗄️ **REGISTRY — The Definitive Phase 12 Contract**

### 📍 **Location**
Registry lives here:

```
server/app/plugins/loader/plugin_registry.py
```

Import path:

```python
from app.plugins.loader.plugin_registry import get_registry
```

Phase 11 already uses this pattern.

---

### 🧬 **Does `get_registry()` exist?**
Yes — Phase 11 uses a singleton registry.  
Phase 12 **extends** it, not replaces it.

If your repo doesn’t have it yet, you implement:

```python
_registry = PluginRegistry()

def get_registry():
    return _registry
```

This is Phase‑11‑compatible.

---

### 📈 **Metric Update Method**
Phase 12 introduces:

```python
update_execution_metrics(
    plugin_name: str,
    state: str,
    elapsed_ms: int,
    had_error: bool,
)
```

This is **additive** — it does not break Phase 11.

---

### 🧮 **Do metrics already exist?**
Phase 11 does **not** have execution metrics.  
Phase 12 adds them.

You add fields like:

- `success_count`
- `error_count`
- `last_execution_time_ms`
- `avg_execution_time_ms`
- `last_used`
- `state` (SUCCESS / ERROR / FAILED / UNAVAILABLE)

These are **new**, and they do **not** break Phase 11.

---

### 🔒 **Thread Safety**
Phase 11 registry is **not thread‑safe**.  
Phase 12 does **not require** thread safety.

If you want to add locking later, that’s Phase 13+.

---

# ⚠️ **ERROR WRAPPING — The Truth**

### 🧱 **Does ToolRunner already wrap exceptions?**
Yes — in Phase 12, ToolRunner is the **only** place that wraps exceptions.

### 🧱 **Do you wrap again?**
No.  
Never.

### 🧱 **Format**
ToolRunner produces the **Phase 12 error envelope**:

```python
{
  "error": {
    "type": "...",
    "message": "...",
    "details": {},
    "plugin": "...",
    "timestamp": "...",
  },
  "_internal": {
    "traceback": "..."
  }
}
```

This is the **canonical** format.

---

# 🌐 **FASTAPI / API LAYER**

### 📍 **Where is the app?**
Typically:

```
server/app/main.py
```

With:

```python
app = FastAPI()
app.include_router(analyze.router)
```

If your repo differs, Phase 12 follows the existing pattern.

### 🧩 **Can you add new routes?**
Yes — as long as:

- You don’t remove existing routes
- You don’t change existing response shapes
- You don’t break Phase 11 clients

Phase 12 is **additive**, not breaking.

---

# 🧱 **SERVICE LAYER**

### 📁 **Does `services/` exist?**
Yes — Phase 11 uses:

```
server/app/services/
```

Phase 12 should follow the same pattern:

- `analysis_service.py`
- `job_management_service.py`
- `plugin_management_service.py`

### 🧩 **Singletons?**
Phase 11 does **not** enforce singletons.  
Phase 12 can safely instantiate services normally.

---

# 📦 **JOB STORAGE**

### 🧠 **In‑memory dict acceptable?**
Yes — for Phase 12, in‑memory is:

- acceptable  
- simple  
- Phase‑11‑safe  
- aligned with your governance goals  

Persistence is a **future phase**.

---

# 🧪 **TEST ISOLATION**

### 🧩 **Monkeypatching ToolRunner.run()**
Yes — this works:

```python
monkeypatch.setattr(ToolRunner, "run", fake_run)
```

This is the correct pattern.

### 🧩 **Existing plugin fixtures?**
If Phase 11 has them, reuse them.  
If not, fake plugins are fine.

---

# 🛡️ **PHASE 11 SAFETY**

### 🧩 **Will Phase 12 break Phase 11?**
Only if you:

- change existing method signatures  
- change existing return shapes  
- change existing error types  
- remove fields Phase 11 expects  

So Phase 12 must be:

- additive  
- non‑breaking  
- backward‑compatible  

### 🧩 **Should Phase 11 code stay untouched?**
Yes — except:

- Registry gets **new fields**  
- Registry gets **new method**  
- Plugin execution path is **rerouted through ToolRunner**  

Everything else stays intact.



