# Phase 11 — Folder Scaffolding
Plugin Stability • Plugin Loader v2 • Sandbox • Lifecycle • Health API

This scaffolding introduces new backend modules required for Plugin Loader v2,
plugin sandboxing, lifecycle tracking, and plugin health reporting.

All names are descriptive of behavior, not phases.

---

# 1. Backend Folder Structure

```
server/
└── app/
    ├── plugins/
    │   ├── loader/                     # Plugin Loader v2
    │   │   ├── __init__.py
    │   │   ├── plugin_loader.py        # Safe import + initialization
    │   │   ├── plugin_registry.py      # Registry of plugin metadata + states
    │   │   ├── dependency_checker.py   # GPU/deps validation
    │   │   └── plugin_errors.py        # Structured plugin error types
    │   │
    │   ├── sandbox/                    # Plugin execution sandbox
    │   │   ├── __init__.py
    │   │   ├── sandbox_runner.py       # try/except wrapper for plugin.run()
    │   │   ├── timeout.py              # Optional execution timeout
    │   │   └── memory_guard.py         # Optional memory guard
    │   │
    │   ├── lifecycle/                  # Plugin lifecycle state machine
    │   │   ├── __init__.py
    │   │   ├── lifecycle_state.py      # LOADED/INITIALIZED/RUNNING/FAILED
    │   │   └── lifecycle_manager.py    # State transitions + tracking
    │   │
    │   ├── health/                     # Plugin health API + status reporting
    │   │   ├── __init__.py
    │   │   ├── health_router.py        # /v1/plugins + /v1/plugins/{name}/health
    │   │   └── health_model.py         # PluginHealthResponse
    │   │
    │   └── inspector/                  # Existing Phase 10 inspector (unchanged)
    │       ├── __init__.py
    │       └── inspector_service.py
    │
    ├── api/
    │   ├── plugins_api.py              # Mounts health_router + registry endpoints
    │   └── __init__.py
    │
    └── tests/
        ├── test_plugin_loader/         # RED tests for Loader v2
        │   ├── test_import_failures.py
        │   ├── test_init_failures.py
        │   ├── test_dependency_checker.py
        │   └── test_registry_state.py
        │
        ├── test_plugin_sandbox/        # RED tests for sandbox execution
        │   ├── test_runtime_exceptions.py
        │   ├── test_timeout.py
        │   └── test_memory_guard.py
        │
        ├── test_plugin_lifecycle/      # RED tests for lifecycle transitions
        │   ├── test_state_transitions.py
        │   └── test_failure_states.py
        │
        ├── test_plugin_health_api/     # RED tests for health endpoints
        │   ├── test_list_plugins.py
        │   ├── test_plugin_health.py
        │   └── test_failed_plugin_health.py
        │
        └── test_videotracker_stability/ # RED tests for VideoTracker crash fixes
            ├── test_missing_gpu.py
            ├── test_missing_model.py
            └── test_runtime_failure.py
```

---

# 2. Frontend Folder Structure (Optional for Phase 11)

```
web-ui/
└── src/
    ├── plugins/                        # Optional: plugin health UI
    │   ├── PluginHealthPanel.tsx
    │   └── usePluginHealth.ts
    │
    └── tests/
        └── plugin_health/              # RED tests for health UI
            ├── plugin_health_panel.spec.ts
            └── plugin_health_hook.spec.ts
```

---

# 3. Naming Principles

- **No phase‑based names** — No "Phase11", "v11", or "P11" prefixes
- **All names describe behavior, not chronology** — `loader/`, `sandbox/`, `lifecycle/`, `health/`
- **All new folders map directly to key Phase 11 features**:
  - `Plugin Loader v2` → `loader/`
  - `Sandbox` → `sandbox/`
  - `Lifecycle` → `lifecycle/`
  - `Health API` → `health/`
- **Zero drift, zero ambiguity, zero future confusion**

---

# 4. Implementation Notes

- No existing Phase 9 or Phase 10 folders are modified.
- All new modules are additive and backward-compatible.
- This scaffolding supports:
  - Plugin Loader v2 with safe import + initialization
  - Plugin sandboxing with timeout and memory guards
  - Lifecycle state machine (LOADED → INITIALIZED → RUNNING → FAILED)
  - Health API endpoints for plugin status reporting
  - VideoTracker stability improvements
- `inspector/` folder remains unchanged (Phase 10 work)
- All new code follows TDD: RED tests written first

---

# 5. Phase 11 Goals Met by This Structure

✅ Plugin Stability  
✅ Plugin Loader v2  
✅ Sandbox Safety  
✅ Lifecycle Tracking  
✅ Health API  
✅ VideoTracker Crash Prevention  

---

This scaffolding is the exact foundation Phase 11 needs.
