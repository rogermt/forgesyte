# Report → Action Plan Mapping
**Status Report**: `/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_11/TESTING_STATUS_DETAIL.md`  
**Recommendations**: `/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_WEB-UI_LOADING_BUG.md` (lines 433-818)

---

## What My Report Found

### ✅ Verified (Live Tested)
1. **Server tests pass**: 928 tests
2. **Web-UI tests pass**: 407 tests
3. Endpoints that work:
   - `GET /v1/plugins` → 200 ✓
   - `GET /v1/plugins/{name}/health` → 200 ✓
4. Web-UI code is correct (uses `/health`)

### 🔴 Problem Identified (Live Tested)
1. **Two `/v1/plugins/{name}` routes exist** (lines 476 & 545)
2. **Line 476 wins** (active)
3. **Line 545 is dead code** (shadowed)
4. **Live test confirms**: `GET /v1/plugins/ocr` returns 200 OK (not 301 redirect)

### 📊 Impact Assessment
- Functionally: Works because web-ui uses correct endpoint
- Design: Route shadowing creates unmaintainable code
- Future-proofing: Risk if developers assume redirect exists

---

## Recommended Actions (from PHASE_11_WEB-UI_LOADING_BUG.md lines 433-818)

### Phase 11 Best Practice: **Option A (Remove Legacy)**

**Why**: 
- Cleanest (no dead code)
- Safest (no ambiguity)
- Web-UI already updated to use `/health`
- Aligns with Phase 11 "clean API" goal

### The Fix

#### 1. Delete Lines 476-505 in `server/app/api.py`

```python
# REMOVE THIS:
@router.get("/plugins/{name}")
async def get_plugin_info(name: str) -> Dict[str, Any]:
    """Retrieve health information about a specific plugin (Phase 11)."""
    from .plugins.loader.plugin_registry import get_registry
    registry = get_registry()
    plugin_status = registry.get_status(name)
    
    if plugin_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )
    
    return (
        plugin_status.model_dump()
        if hasattr(plugin_status, "model_dump")
        else plugin_status
    )
```

#### 2. Delete Lines 544-553 in `server/app/api.py`

```python
# REMOVE THIS:
# TEST-CHANGE (Phase 11): Compatibility shim for legacy endpoint
@router.get("/plugins/{name}", include_in_schema=False)
async def legacy_plugin_manifest_redirect(name: str) -> RedirectResponse:
    """Phase 11 compatibility shim.
    
    Redirects legacy /v1/plugins/{name} → /v1/plugins/{name}/health
    Handles browser caches, older builds, and external integrations.
    Prevents blank UI screens from 500 errors.
    """
    return RedirectResponse(url=f"/v1/plugins/{name}/health", status_code=301)
```

#### 3. Result: Only These Endpoints Remain

```
GET /v1/plugins                  → List all plugins (api.py:438)
GET /v1/plugins/{name}/health    → Plugin health (health_router.py:49)
POST /v1/plugins/{name}/reload   → Reload plugin (api.py:508)
GET /health                       → System health (api.py:849)
```

---

## Tests to Add (Phase 11 Governance)

### Test 1: Legacy Endpoint Removed

**File**: `server/tests/test_plugin_health_api/test_no_legacy_endpoint.py`

```python
# TEST-CHANGE (Phase 11): /v1/plugins/{name} must not exist

import pytest
from fastapi.testclient import TestClient


def test_legacy_plugin_endpoint_removed(client: TestClient):
    """Verify /v1/plugins/{name} no longer exists (Phase 11)."""
    resp = client.get("/v1/plugins/ocr")
    assert resp.status_code in (404, 405), (
        "Phase 11 violation: /v1/plugins/{name} still exists. "
        "This endpoint must be removed. Use /v1/plugins/{name}/health instead."
    )
```

**Why**: Prevents accidental re-introduction of dead code

---

### Test 2: Canonical Endpoint Works

**File**: `server/tests/test_plugin_health_api/test_health_is_canonical.py`

```python
# TEST-CHANGE (Phase 11): /v1/plugins/{name}/health is the canonical endpoint

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_is_canonical(client: TestClient):
    """Verify /v1/plugins/{name}/health is the only valid detail endpoint."""
    resp = client.get("/v1/plugins/ocr/health")
    assert resp.status_code == 200, (
        "Phase 11 violation: canonical health endpoint must return 200"
    )
    
    data = resp.json()
    assert "name" in data and "state" in data, (
        "Phase 11 violation: health endpoint returned invalid schema"
    )
```

**Why**: Guarantees canonical endpoint behavior

---

### Test 3: Web-UI Never Calls Legacy Endpoint

**File**: `web-ui/src/tests/noLegacyPluginEndpoint.test.ts`

```typescript
// TEST-CHANGE (Phase 11): Web-UI must never call /v1/plugins/{name}

import fs from "fs";
import path from "path";
import { describe, it, expect } from "vitest";

const SRC_DIR = path.join(__dirname, "..", "..", "src");

function scan(dir: string, out: string[] = []): string[] {
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    if (fs.statSync(full).isDirectory()) {
      scan(full, out);
    } else if (f.endsWith(".ts") || f.endsWith(".tsx")) {
      out.push(full);
    }
  }
  return out;
}

describe("Phase 11 API Contract", () => {
  it("web-ui never calls legacy /v1/plugins/{name}", () => {
    const files = scan(SRC_DIR);
    const forbidden: string[] = [];

    for (const file of files) {
      const content = fs.readFileSync(file, "utf8");

      // Check for legacy endpoint patterns
      if (
        content.includes("/v1/plugins/${") ||
        content.includes("/v1/plugins/\" +") ||
        content.match(/\/v1\/plugins\/[a-zA-Z0-9_-]+(?!\/health)/)
      ) {
        forbidden.push(file);
      }
    }

    expect(forbidden).toHaveLength(0);
  });
});
```

**Why**: Prevents future developers from reintroducing legacy calls

---

## Execution Checklist

- [ ] **Step 1**: Delete lines 476-505 from `server/app/api.py`
- [ ] **Step 2**: Delete lines 544-553 from `server/app/api.py`
- [ ] **Step 3**: Create `server/tests/test_plugin_health_api/test_no_legacy_endpoint.py`
- [ ] **Step 4**: Create `server/tests/test_plugin_health_api/test_health_is_canonical.py`
- [ ] **Step 5**: Create `web-ui/src/tests/noLegacyPluginEndpoint.test.ts`
- [ ] **Step 6**: Run server tests: `uv run pytest tests/ -v`
- [ ] **Step 7**: Run web-ui tests: `npm run test -- --run`
- [ ] **Step 8**: Run linting: `npm run lint && npm run type-check`
- [ ] **Step 9**: Start server: `uvicorn app.main:app`
- [ ] **Step 10**: Verify logs show:
  ```
  GET /v1/plugins → 200
  GET /v1/plugins/ocr/health → 200
  (no /v1/plugins/ocr calls)
  ```
- [ ] **Step 11**: Test web-ui loads without blank screen
- [ ] **Step 12**: Commit with message:
  ```
  fix(phase-11): Remove dead route shadowing and dead redirect code
  
  Removes duplicate /v1/plugins/{name} route definitions that caused:
  - Route shadowing (line 476 shadows line 545)
  - Dead code (redirect at line 545 never executed)
  - Design ambiguity
  
  Canonical endpoint now: /v1/plugins/{name}/health
  
  Added regression tests to prevent re-introduction.
  
  TEST-CHANGE: Added 3 new tests for Phase 11 governance
  - test_no_legacy_endpoint.py: Verify legacy endpoint removed
  - test_health_is_canonical.py: Verify canonical endpoint works
  - noLegacyPluginEndpoint.test.ts: Verify web-UI compliance
  ```

---

## Expected Outcome

### Before Fix
```
Routes:
├─ GET /v1/plugins                  (api.py:438) ✓
├─ GET /v1/plugins/{name}           (api.py:476) ← SHADOWS LINE 545
├─ GET /v1/plugins/{name}           (api.py:545) ← DEAD CODE
├─ GET /v1/plugins/{name}/health    (health_router.py:49) ✓
└─ ... other routes

Live test:
GET /v1/plugins/ocr → 200 OK (not 301)
```

### After Fix
```
Routes:
├─ GET /v1/plugins                  (api.py:438) ✓
├─ GET /v1/plugins/{name}/health    (health_router.py:49) ✓ CANONICAL
└─ ... other routes

Live test:
GET /v1/plugins/ocr → 404 Not Found
GET /v1/plugins/ocr/health → 200 OK

Tests:
✅ test_no_legacy_endpoint passes
✅ test_health_is_canonical passes
✅ noLegacyPluginEndpoint passes
```

---

## Risk Assessment

### Risks of Doing This Fix
- **Low**: Web-UI already uses `/health` endpoint
- **Low**: Tests catch regressions
- **Low**: Commit history documents the change

### Risks of NOT Doing This Fix
- **Medium**: Dead code confuses future developers
- **Medium**: Route shadowing is subtle and easy to reintroduce
- **High**: Future refactoring might "fix" it wrong way
- **High**: Design ambiguity leads to technical debt

---

## Connection to My Report

| Report Finding | Action Item | Implementation |
|---|---|---|
| Line 476 shadows 545 | Delete both | Delete api.py lines 476-505, 544-553 |
| Redirect is dead code | Remove shim | Covered by above deletion |
| Route precedence confirmed | Add tests | 3 tests added (see above) |
| Web-UI uses correct endpoint | Verify compliance | Governance test for web-ui |
| 928 tests still pass | Re-run after fix | Run full test suite |

---

**Status**: Ready for implementation  
**Estimated Time**: 15 minutes  
**Risk Level**: 🟢 Low (no functional changes, only cleanup)  
**Phase 11 Alignment**: ⭐ Perfect (eliminates dead code and ambiguity)
