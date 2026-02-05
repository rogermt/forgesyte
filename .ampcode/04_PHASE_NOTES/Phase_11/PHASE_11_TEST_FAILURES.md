# Phase 11 Test Failures Report

**Date:** 2026-02-05  
**Status:** 5 Legacy Test Failures (Expected - API Contract Changed)

## Summary

Phase 10 ended with **ALL GREEN** (911 pass).  
Phase 11 changed `/v1/plugins` API contract (flat list instead of wrapped).  
Phase 9/10 integration tests still expect old format → **5 failures**.

## Failures Detail

### 1. `test_plugins_endpoint_returns_valid_plugins`
**File:** `tests/integration/test_api_contracts.py`  
**Error:** `AssertionError: Response must contain 'plugins' key`  
**Reason:** Test expects `{ "plugins": [...] }` but Phase 11 returns `[...]`

### 2. `test_plugins_endpoint_required_fields`
**File:** `tests/integration/test_api_contracts.py`  
**Error:** `TypeError: list indices must be integers or slices, not str`  
**Reason:** Test tries `data["plugins"]` but Phase 11 returns list directly

### 3. `test_plugins_endpoint_inputs_outputs_are_lists`
**File:** `tests/integration/test_api_contracts.py`  
**Error:** `TypeError: list indices must be integers or slices, not str`  
**Reason:** Same as #2 - accessing dict keys on list

### 4. `test_plugins_endpoint_matches_fixture_schema`
**File:** `tests/integration/test_api_contracts.py`  
**Error:** `AttributeError: 'list' object has no attribute 'get'`  
**Reason:** Fixture expects `{ "plugins": [...] }` structure

### 5. `test_list_plugins_returns_dict` (Unit Test)
**File:** `tests/api/test_api_endpoints.py`  
**Status:** ✅ FIXED (committed with TEST-CHANGE)

## Root Cause

**Phase 10 API (Old):**
```json
{
  "plugins": [
    { "name": "ocr", "description": "...", "version": "1.0.0" }
  ],
  "count": 1
}
```

**Phase 11 API (New - Canonical):**
```json
[
  { "name": "ocr", "state": "INITIALIZED", "description": "...", ... }
]
```

Changes:
- Removed `{ plugins, count }` wrapper
- Flattened to direct list
- Added health fields (state, reason, uptime, execution_time, etc.)
- Each plugin is now PluginHealthResponse dict

## Action Required

### Option A: Update Integration Tests (Recommended)
Update Phase 9/10 tests to expect Phase 11 format:
- Remove `.json()["plugins"]` → just `.json()`
- Expect list, not dict
- Access `data[0].name` instead of `data["plugins"][0]["name"]`
- Update fixtures to match new schema

### Option B: Revert API Change (Not Recommended)
Revert `/v1/plugins` endpoint to old wrapped format.  
Conflicts with Phase 11 design goal (simplify API).

## Phase 11 Status

| Component | Tests | Status |
|-----------|-------|--------|
| Sandbox/Timeout/Memory | 24 | ✅ PASS |
| API Contract Governance | 1 (fixed) | ✅ PASS |
| Integration (Phase 9/10) | 4 | ❌ FAIL (expected) |
| **Total** | **911** | **906 PASS, 5 FAIL** |

## Pydantic Deprecation Warnings (Non-Critical)

Warnings in Phase 10 models (pre-Phase-11):
- `app/models.py:246` - `Field(..., example=...)` → use `json_schema_extra`
- `app/models.py:243,264` - `class Config` → use `ConfigDict`
- `app/plugins/health/health_model.py:14,53` - Same pydantic v2 issues

These are pre-existing (Phase 10), not Phase 11 regressions.

## Next Steps

1. **Decide:** Fix Phase 9/10 tests OR revert API?
2. **If fix:** Update 4 integration tests with proper Phase 11 assertions
3. **If revert:** Restore old endpoint format (loses Phase 11 simplification)

Recommendation: **Fix tests** (aligns with Phase 11 API goals)
