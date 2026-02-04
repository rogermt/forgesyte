# ⭐ **1. Phase 10 Folder Scaffolding**  
### *File:* `PHASE_10_FOLDER_SCAFFOLDING.md`

```md
# Phase 10 — Folder Scaffolding

This document defines the initial folder and file structure for Phase 10.
These directories and placeholder files ensure a clean, predictable layout
for real-time features, plugin pipeline upgrades, and extended job models.

---

# 1. Server-Side Scaffolding

server/
└── app/
    ├── realtime/
    │   ├── __init__.py
    │   ├── websocket_router.py        # WebSocket/SSE endpoint stub
    │   ├── message_types.py           # WebSocketMessage extensions
    │   └── connection_manager.py      # Client/session tracking
    │
    ├── plugins/
    │   ├── inspector/
    │   │   ├── __init__.py
    │   │   └── inspector_service.py   # Plugin metadata + timing collector
    │   └── runtime/
    │       ├── __init__.py
    │       └── tool_runner.py         # Real-time tool execution
    │
    ├── models_phase10.py              # Additive models (progress, timings, warnings)
    └── api_phase10.py                 # Real-time endpoints (stub)

server/tests/phase10/
    ├── __init__.py
    ├── test_realtime_endpoint.py      # RED test: endpoint exists
    ├── test_job_progress_field.py     # RED test: progress field exists
    └── test_plugin_timing_field.py    # RED test: plugin_timings exists

---

# 2. Web-UI Scaffolding

web-ui/
└── src/
    ├── realtime/
    │   ├── RealtimeClient.ts          # WebSocket/SSE client stub
    │   ├── RealtimeContext.tsx        # React context for streaming data
    │   └── useRealtime.ts             # Hook for subscribing to streams
    │
    ├── components/
    │   ├── RealtimeOverlay.tsx        # Real-time overlay renderer
    │   ├── ProgressBar.tsx            # Job progress UI
    │   └── PluginInspector.tsx        # Plugin metadata + timings
    │
    └── stories/
        └── RealtimeOverlay.stories.tsx  # Phase 10 Storybook story

web-ui/tests/phase10/
    ├── __init__.ts
    ├── realtime_endpoint.spec.ts       # RED test: connection opens
    ├── progress_bar.spec.ts            # RED test: progress UI exists
    └── plugin_inspector.spec.ts        # RED test: inspector loads

---

# 3. Notes

- Phase 10 does NOT modify Phase 9 files.
- All new models go into `models_phase10.py` (additive only).
- All real-time logic is isolated under `realtime/`.
- The failing web-ui pre-commit hook will be fixed here.
```

---

