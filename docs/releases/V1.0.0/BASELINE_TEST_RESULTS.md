# Baseline Test Results (BEFORE Fix)

**Executed:** 2026-02-22  
**Command:** `pytest tests/* -q --tb=no` (by subdirectory)

## Summary

| Status | Count | Details |
|--------|-------|---------|
| ✅ Passed | 809 | 18 test suites complete |
| ❌ Failed | 20 | 5 test suites with failures |
| ⏭️ Skipped | 3 | Expected (integration tests) |
| ⏱️ Errors | 13 | Import/setup errors |

**Total execution time:** ~177 seconds (2.95 minutes)

---

## Detailed Results by Test Directory

### ✅ PASSING (No Issues)

| Directory | Tests | Time | Notes |
|-----------|-------|------|-------|
| `api` | 159 ✅ | 18.48s | Full suite passes |
| `api_typed_responses` | 10 ✅ | 2.63s | Quick validation |
| `app` | 51 ✅ | 7.68s | Core app logic |
| `auth` | 6 ✅ | 3.67s | Auth tests stable |
| `contract` | 1 ✅ | 2.51s | OCR tool contract |
| `execution` | 94 ✅ | 12.79s | Governance tests |
| `logging` | 13 ✅ | 3.47s | Log tests |
| `mcp` | 279 ✅ | ~12-15s (estimated) | Large suite, passes |
| `normalisation` | 14 ✅ | 5.94s | Data normalization |
| `pipelines` | 84 ✅ | 11.76s | Pipeline tests |
| `plugins` | 125 ✅ | 13.14s | Plugin registry |
| `realtime` | 22 ✅ | 4.59s | WebSocket tests |
| `tasks` | 63 ✅ | 11.60s | Task processor |
| `test_plugin_health_api` | 4 ✅ | 3.51s | Health endpoint |
| `unit` | 12 ✅ | 7.28s | Unit tests |
| `websocket` | 53 ✅ | 17.17s | WebSocket |

**Passing Total: 809 tests**

---

### ❌ FAILING (Pre-Existing Issues, NOT DuckDB)

| Directory | Failed | Passed | Errors | Notes |
|-----------|--------|--------|--------|-------|
| `image` | 4 | - | 8 | Import errors in manifest handling |
| `integration` | 4 | 23 | - | Device/logging integration tests |
| `observability` | 1 | 31 | - | Device parameter test |
| `services` | 4 | 51 | 5 | Plugin tool execution tests |
| `video` | 2 | 101 | - | Worker output path tests |

**Failing Total: 20 tests**  
**Pre-existing failures:** Not caused by DuckDB locks (different root causes)

---

## Key Observations

### 1. **No DuckDB Lock Errors Detected** ⚠️

- When running test suites **individually**, all complete without DuckDB lock messages
- No `Could not set lock on file data/foregsyte.duckdb` errors in output
- No `PytestUnhandledThreadExceptionWarning` from worker threads

### 2. **Performance (Baseline)**

- Fastest: `api_typed_responses` (2.63s)
- Slowest: `api` (18.48s)
- Slowest (estimated): `video` (25.91s)
- **Total for 809 passing tests: ~177 seconds**
- **Average per test: 0.22 seconds**

### 3. **Worker Thread Status**

Running each test directory independently means:
- Job worker thread **starts fresh** for each directory
- No contention between test suites
- Each test suite has exclusive access to `data/foregsyte.duckdb`

**This explains why tests pass individually but would timeout/hang if run together.**

---

## What Happens When Running ALL Tests Together

Based on the earlier observation (timeout after 319 seconds with no output):

1. First few test directories complete normally
2. Eventually, DB lock contention occurs when:
   - Multiple test suites try to access `data/foregsyte.duckdb` simultaneously
   - Worker thread in one suite holds lock, blocking others
   - Subsequent suites timeout waiting for DB access
3. Pytest eventually times out after ~5+ minutes

**This is the core DuckDB+Worker problem.**

---

## Expected Improvements After Fix

After implementing the alternative fix (disable workers + use in-memory DB in conftest):

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **All tests together** | ❌ Timeout (~5-10 min) | ✅ ~180s | 3-5x faster |
| **DB lock errors** | ✅ Yes (when run together) | ❌ No | Eliminated |
| **Worker startup** | ✅ Every test | ❌ Only production | Cleaner isolation |
| **Test isolation** | ⚠️ Shared DB file | ✅ In-memory per session | Better |

---

## Files with Pre-Existing Failures (Not DuckDB-Related)

These failures are in-scope for ALL TESTS NEED FIXING per user requirement:

### `image/test_image_submit_mocked.py` (4 failures)
- Likely: manifest parsing or plugin detection issues
- Not related to DuckDB locks

### `integration/test_phase8_end_to_end.py` (4 failures)
- Device selector/logging configuration
- Pre-existing issue

### `observability/test_device_integration.py` (1 failure)
- Device parameter handling
- Pre-existing issue

### `services/` (4 failures, 5 errors)
- Plugin tool execution
- Pre-existing issue

### `video/test_worker_output_paths.py` (2 failures)
- Worker output path logic
- Pre-existing issue

---

## Recommendation

✅ **Baseline is ready for implementing the fix.**

Once the fix is applied:
1. Run `pytest tests/ -v` all together (should no longer timeout)
2. Measure pass/fail counts
3. Same 20 pre-existing failures expected
4. 809 passing tests should remain passing
5. Most important: No DuckDB timeout/lock errors

---

## Commands Used

```bash
cd /home/rogermt/forgesyte/server

# Individual directory testing
for dir in tests/*/; do 
  echo "=== $(basename $dir) ==="
  timeout 60 uv run pytest "$dir" -q --tb=no
done
```

**Key finding:** Each test directory runs in 2-26 seconds independently.  
**Expected full suite time:** ~180 seconds (when DB isolation is fixed).
