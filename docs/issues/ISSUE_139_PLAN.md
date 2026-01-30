# ISSUE_139 Implementation Plan

**Issue:** Backend Plugin API Surface (YOLO Tracker + OCR Contract Tests)

**Objective:** Implement missing backend endpoints for plugin discovery and execution:
- `GET /v1/plugins/{id}/manifest` - retrieve plugin tool schemas
- `POST /v1/plugins/{id}/tools/{tool}/run` - execute plugin tools
- `ManifestCacheService` - TTL-based manifest caching
- CPU-only integration tests for YOLO Tracker manifest and player_detection tool

**GitHub Issue:** rogermt/forgesyte#139

**Status:** Ready for implementation

---

## Senior Developer Approach

This plan follows **Test-Driven Development (TDD)** with **atomic commits** - each commit is:
- ✅ Minimal and focused
- ✅ Passes all tests
- ✅ Passes lint/type-check
- ✅ Can be understood independently
- ✅ Ready for code review

Estimated duration: **4-5 commits**, ~1-2 hours of work.

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feat/plugin-api-endpoints

# After each commit, verify:
# 1. All tests pass
# 2. No lint/type errors
# 3. Pre-commit hooks pass

# After all commits, create PR
git push -u origin feat/plugin-api-endpoints
gh pr create --title "feat(api): add plugin manifest and tool run endpoints"
```

---

## Implementation Plan (5 Atomic Commits)

**⚠️ IMPORTANT: CPU-Only Tests**

All tests in this plan are **CPU-only** (no `RUN_MODEL_TESTS=1` needed):
- Use dummy/synthetic frames (zeros arrays)
- No real YOLO models loaded
- No GPU required
- Fast CI execution
- Pass on this machine immediately

GPU integration tests will be added separately in Week 3 with real models on Kaggle.

---

### Commit 1: Create `ManifestCacheService` with tests

**TDD: Write tests FIRST**

**File:** `server/tests/unit/test_manifest_cache.py`

Create unit tests for caching behavior (CPU-only):
- ✅ Test `get()` returns `None` for unknown plugin
- ✅ Test `set()` and `get()` stores/retrieves manifest
- ✅ Test TTL expiration (cache hit before expiry, miss after expiry)
- ✅ Test `dep()` classmethod returns new instance
- ✅ Test concurrent gets/sets don't corrupt cache

```bash
# Step 1: Write tests (will fail, manifest_cache.py doesn't exist)
# Step 2: Implement server/app/services/manifest_cache.py
# Step 3: Run tests until all pass (NO RUN_MODEL_TESTS=1 needed)
uv run pytest tests/unit/test_manifest_cache.py -v
# Step 4: Run lint/type-check/pre-commit
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
# Step 5: Commit
git add .
git commit -m "test(services): add ManifestCacheService with TTL-based caching

Create server/app/services/manifest_cache.py with:
- Simple in-memory TTL cache for plugin manifests
- get(plugin_id): returns cached manifest or None if expired
- set(plugin_id, manifest): stores manifest with TTL
- dep() classmethod for FastAPI dependency injection

Tests cover expiration, concurrent access, and edge cases.

CPU-only tests (no model loading required)."
```

---

### Commit 2: Create `api_plugins.py` router with GET /manifest endpoint

**TDD: Write integration tests FIRST (CPU-only)**

**File:** `server/tests/integration/test_plugins_manifest_yolo.py`

Create test for manifest endpoint (no GPU required):
- ✅ Test GET `/v1/plugins/yolo-tracker/manifest` returns 200
- ✅ Test manifest has correct shape: `id`, `name`, `version`, `tools`
- ✅ Test all expected YOLO tools present: player_detection, player_tracking, ball_detection, pitch_detection, radar
- ✅ Test each tool has `description`, `inputs`, `outputs`
- ✅ Test 404 for unknown plugin

**Note:** This test only validates manifest JSON structure, no model loading.

```bash
# Step 1: Write tests (will fail, endpoint doesn't exist)
# Step 2: Create server/app/api_plugins.py with GET /manifest endpoint
#         - Use PluginManagementService.get_plugin_manifest()
#         - Use ManifestCacheService for caching
#         - Handle 404 properly
# Step 3: Wire router into main.py
# Step 4: Run tests until they pass (NO RUN_MODEL_TESTS=1 needed)
uv run pytest tests/integration/test_plugins_manifest_yolo.py -v
# Step 5: Verify lint/type-check
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
# Step 6: Commit
git add .
git commit -m "feat(api): add GET /v1/plugins/{id}/manifest endpoint

Create server/app/api_plugins.py with:
- GET /{plugin_id}/manifest: retrieve plugin manifest by ID
- Backed by PluginManagementService.get_plugin_manifest()
- Manifest caching via ManifestCacheService (60s TTL)
- Returns 404 for unknown plugins, 503 if service unavailable

Wire plugins router into app/main.py under /v1/plugins prefix.

Tests verify (CPU-only):
- Manifest structure matches contract
- All YOLO tools present (player_detection, etc.)
- Each tool has description, inputs, outputs
- No model loading required"
```

---

### Commit 3: Add POST /tools/{tool}/run endpoint (sync execution)

**TDD: Write integration tests FIRST (CPU-only)**

**File:** `server/tests/integration/test_plugins_run_yolo_player_detection.py`

Create test for tool execution endpoint (dummy frames, no GPU):
- ✅ Test POST `/v1/plugins/yolo-tracker/tools/player_detection/run` returns 200
- ✅ Test response has correct shape: `{"output": {...}}`
- ✅ Test output contains expected keys: `detections`, `annotated_frame_base64`
- ✅ Test accepts base64-encoded frame in input
- ✅ Test 400 for unknown plugin/tool
- ✅ Test 500 for tool execution error
- ✅ Test request validation: input is dict

**Note:** Uses dummy 10x10 synthetic frames (zeros), no real model inference.

```bash
# Step 1: Write tests (will fail, endpoint doesn't exist)
# Step 2: Implement POST endpoint in server/app/api_plugins.py
#         - Define ToolRunRequest, ToolRunResponse models
#         - Use PluginManagementService.run_plugin_tool()
#         - Catch ValueError (bad plugin/tool) → 400
#         - Catch Exception (execution error) → 500
#         - Validate output is dict
# Step 3: Run tests until they pass (NO RUN_MODEL_TESTS=1 needed)
uv run pytest tests/integration/test_plugins_run_yolo_player_detection.py -v
# Step 4: Verify lint/type-check/pre-commit
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
uv run pre-commit run --all-files
# Step 5: Commit with TEST-CHANGE annotation
git add .
git commit -m "TEST-CHANGE: feat(api): add POST /v1/plugins/{id}/tools/{tool}/run endpoint

Create POST endpoint for synchronous tool execution:
- POST /{plugin_id}/tools/{tool_name}/run
- Input: {\"input\": {...}} where input is tool-specific dict
- Output: {\"output\": {...}} where output is JSON-safe dict
- Backed by PluginManagementService.run_plugin_tool()
- Error handling: 400 for unknown plugin/tool, 500 for execution errors

Request/response models:
- ToolRunRequest: validates 'input' field is dict
- ToolRunResponse: validates 'output' field is dict

CPU-only tests (dummy frames):
- Player_detection tool returns valid JSON structure
- Output matches manifest contract
- Base64-encoded frames accepted
- Error cases handled correctly
- No real model inference required"
```

---

### Commit 4: Add CPU-only tests for all YOLO tools

**TDD: Write tests FIRST** (optional, can combine with Commit 3)

**Files:**
- `server/tests/integration/test_plugins_run_yolo_player_tracking.py`
- `server/tests/integration/test_plugins_run_yolo_ball_detection.py`
- `server/tests/integration/test_plugins_run_yolo_pitch_detection.py`
- `server/tests/integration/test_plugins_run_yolo_radar.py`

**All use dummy synthetic frames** (no RUN_MODEL_TESTS=1 needed):

```bash
# Step 1: Create test files for remaining YOLO tools
#         - Pattern same as player_detection (dummy/synthetic frame, check output shape)
#         - Focus on JSON contract validation, not model inference
#         - Use np.zeros((10, 10, 3)) for frames (10x10 synthetic)
# Step 2: Run tests until all pass (NO RUN_MODEL_TESTS=1 needed)
uv run pytest tests/integration/test_plugins_run_yolo_*.py -v
# Step 3: Verify all quality checks pass
uv run pytest tests/integration/ -v
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
# Step 4: Commit
git add .
git commit -m "TEST-CHANGE: test(integration): add CPU-only contract tests for all YOLO tools

Create contract validation tests for all YOLO Tracker tools:
- test_plugins_run_yolo_player_tracking.py
- test_plugins_run_yolo_ball_detection.py
- test_plugins_run_yolo_pitch_detection.py
- test_plugins_run_yolo_radar.py

Each test uses dummy synthetic 10x10 frames and verifies:
- Tool endpoint returns 200
- Response structure: {\"output\": {...}}
- Output contains expected keys per manifest schema
- Works with base64-encoded frame input
- CPU-only (no GPU/models required)

These are contract tests - validate JSON output schema,
not model accuracy. GPU inference tests come Week 3 on Kaggle."
```

---

### Commit 5: Update wire-up in main.py + verify all tests pass

**Verification Commit (CPU-only)**

Ensure plugins router is properly wired into FastAPI app in `main.py`:

```python
from .api_plugins import router as plugins_router

# In routing section:
app.include_router(plugins_router, prefix=settings.api_prefix)
```

```bash
# Step 1: Verify main.py imports api_plugins and wires router
# Step 2: Run ALL tests (unit + integration, CPU-only)
# ⚠️ NO RUN_MODEL_TESTS=1 - these are CPU contract tests only
uv run pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=term-missing
# Step 3: Verify no lint/type errors
uv run black app/ tests/
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
# Step 4: Run full pre-commit
uv run pre-commit run --all-files
# Step 5: Commit
git add .
git commit -m "chore: verify plugin API endpoints integration and quality gates

Finalize backend API implementation (CPU-only):
- Confirm api_plugins router wired in main.py
- All unit + integration tests pass (CPU contract tests)
- Lint/type-check clean
- Pre-commit hooks pass
- Ready for PR review

GPU integration tests (Week 3):
- Run separately: RUN_MODEL_TESTS=1 pytest tests/contract/ -v
- Uses real YOLO models on Kaggle"
```

---

## Verification Checklist

After all commits (CPU-only):

```bash
cd /home/rogermt/forgesyte/server

# 1. Run all tests (NO RUN_MODEL_TESTS=1)
# These are CPU contract tests only - they pass on this machine
uv run pytest tests/ -v --cov=app --cov-report=term-missing

# 2. Run lint
uv run ruff check --fix app/ tests/

# 3. Run type-check
uv run mypy app/ --no-site-packages

# 4. Run pre-commit hooks
uv run pre-commit run --all-files

# 5. Verify Git history
git log --oneline -5
# Should show:
# chore: verify plugin API endpoints integration and quality gates
# TEST-CHANGE: test(integration): add CPU-only contract tests for all YOLO tools
# TEST-CHANGE: feat(api): add POST /v1/plugins/{id}/tools/{tool}/run
# feat(api): add GET /v1/plugins/{id}/manifest endpoint
# test(services): add ManifestCacheService with TTL-based caching
```

**⚠️ GPU Tests Separate:**

GPU integration tests run ONLY on Kaggle (Week 3) with real models:
```bash
# On Kaggle with GPU + real YOLO models:
cd /kaggle/working/forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/contract/ -v
```

---

## PR Checklist

When ready to create PR:

```bash
git push -u origin feat/plugin-api-endpoints

gh pr create \
  --title "feat(api): add plugin manifest and tool run endpoints" \
  --body "## Summary

Implements missing backend API surface for plugin discovery and execution (ISSUE #139).

## Changes

- Add GET /v1/plugins/{id}/manifest endpoint
- Add POST /v1/plugins/{id}/tools/{tool}/run endpoint
- Introduce ManifestCacheService with TTL-based caching
- CPU-only integration tests for YOLO Tracker

## Testing

- All tests pass: \`uv run pytest tests/ -v\`
- Lint clean: \`uv run ruff check --fix app/ tests/\`
- Type-check clean: \`uv run mypy app/ --no-site-packages\`
- Pre-commit hooks pass

## Next Steps

- Week 2: Web-UI implementation (useManifest hook, VideoTracker component)
- Week 3: GPU integration tests (RUN_MODEL_TESTS=1)
- Add OCR manifest + tests (per Lead Designer suggestion)"
```

---

## Files Summary

| File | Type | Purpose |
|------|------|---------|
| `server/app/services/manifest_cache.py` | New | TTL-based manifest caching |
| `server/app/api_plugins.py` | New | FastAPI router for plugin endpoints |
| `server/tests/unit/test_manifest_cache.py` | New | Unit tests for cache service |
| `server/tests/integration/test_plugins_manifest_yolo.py` | New | Integration test: GET /manifest |
| `server/tests/integration/test_plugins_run_yolo_player_detection.py` | New | Integration test: POST /run (player detection) |
| `server/tests/integration/test_plugins_run_yolo_player_tracking.py` | New | Integration test: POST /run (player tracking) |
| `server/tests/integration/test_plugins_run_yolo_ball_detection.py` | New | Integration test: POST /run (ball detection) |
| `server/tests/integration/test_plugins_run_yolo_pitch_detection.py` | New | Integration test: POST /run (pitch detection) |
| `server/tests/integration/test_plugins_run_yolo_radar.py` | New | Integration test: POST /run (radar) |
| `server/app/main.py` | Modified | Wire plugins router under /v1/plugins |

---

## Key Design Decisions

1. **TDD-First:** Write failing tests before implementing code
2. **Atomic Commits:** Each commit is minimal, testable, independent
3. **CPU-Only:** Tests don't require GPU or YOLO models (use dummy frames)
4. **TTL Cache:** 60-second TTL keeps manifests fresh while reducing file I/O
5. **Error Handling:** Proper HTTP status codes (400 for bad input, 500 for execution)
6. **JSON Contract:** Output must be JSON-safe dict (validate before response)
7. **FastAPI Deps:** Use dependency injection for service and cache

---

## Estimated Effort

| Commit | Task | Duration |
|--------|------|----------|
| 1 | ManifestCacheService + unit tests | 20 min |
| 2 | GET /manifest endpoint + integration tests | 20 min |
| 3 | POST /run endpoint + test suite | 25 min |
| 4 | Additional YOLO tool tests | 15 min |
| 5 | Verification + integration check | 10 min |
| **Total** | **Full implementation** | **~90 min** |

---

## Failure Recovery

If any step fails:

1. **Test fails:** Debug the test assertion or implementation logic
2. **Lint fails:** Run `uv run ruff check --fix` to auto-fix, then review
3. **Type-check fails:** Add proper type hints or use `# type: ignore` with comment
4. **Pre-commit fails:** Fix the issue, then `uv run pre-commit run --all-files`
5. **Need to undo:** `git reset --soft HEAD~1` to keep changes but undo commit

---

## Following AGENTS.md Guidelines

✅ **TDD Workflow:** Tests written first, implementation second  
✅ **Pre-commit Safety:** Never use `--no-verify`  
✅ **Commit Format:** `type(scope): subject` with body for test justification  
✅ **Code Quality:** Black, Ruff, Mypy all pass  
✅ **Branch Naming:** `feat/` prefix for feature branches  
✅ **PR Ready:** Clear PR title, description with testing section

---

## Next Steps After Merge

Once this PR merges to `main`:

1. **Week 2 - Web-UI:** Implement `useManifest` hook, ToolSelector component, VideoTracker page
2. **Week 3 - GPU Tests:** Run `RUN_MODEL_TESTS=1 pytest tests/integration/ -v` on Kaggle
3. **Follow-up PR:** Add OCR manifest + run tests (per Lead Designer suggestion)

---

**Created:** 2026-01-30  
**Lead:** Senior Python Developer (40+ years experience)  
**Methodology:** TDD + Atomic Commits + Git Workflow
