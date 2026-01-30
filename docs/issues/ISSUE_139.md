# Issue #139: Implement Backend API Surface for Plugin Tools (Video-Tracker)

## Summary

This PR implements the missing backend API surface required by AGENTS.md Week 1 for plugin tools, including YOLO video:

- `/plugins/{id}/manifest` (GET) — expose plugin tool schemas
- `/plugins/{id}/tools/{tool}/run` (POST) — execute tools with input
- `ManifestCacheService` — TTL-based manifest caching
- CPU-only integration tests for manifest + YOLO video tool

The frontend contract tests already exist; this PR brings the backend in line with that contract.

---

## What’s included

### 1. Plugins router

- `GET /plugins/{plugin_id}/manifest`
- `POST /plugins/{plugin_id}/tools/{tool_name}/run`

Both endpoints delegate to the existing `PluginManager` and enforce JSON-safe, dict-shaped outputs.

### 2. ManifestCacheService

- Simple in-memory cache keyed by `plugin_id`
- TTL-based invalidation
- Used by the manifest endpoint to avoid repeated plugin introspection

### 3. Integration tests (CPU-only)

- `test_get_plugin_manifest_returns_schema` — validates manifest structure and tool schemas
- `test_run_yolo_video_tool_returns_valid_json` — validates video tool execution and JSON-safe output

---

## Why this matters

- Unblocks video tool contract tests
- Aligns backend with AGENTS.md Week 1
- Provides a stable API surface for the frontend to discover tools and schemas
- Keeps everything CPU-only and deterministic for CI

---

## Follow-ups

- Extend tests to cover OCR and other plugins
- Add negative-path tests (unknown plugin/tool, invalid input)
- Optionally promote ManifestCacheService to a shared singleton if needed

