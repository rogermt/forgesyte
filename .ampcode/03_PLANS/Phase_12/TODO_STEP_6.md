# Phase 12 Step 6 - Scanner + CI Implementation

## Overview
Step 6 implements the Mechanical Scanner and CI Pipeline for execution governance enforcement.

## Step 5 Status: ✅ COMPLETE
- All 84 execution tests pass
- Integration tests verified
- Service layer complete

## Step 6 Implementation Checklist

| Task | Description | Status |
|------|-------------|--------|
| 1 | Create Mechanical Scanner | ⏳ Pending |
| 2 | Create CI Workflow | ⏳ Pending |
| 3 | Run Scanner Locally | ⏳ Pending |
| 4 | Verify CI Workflow | ⏳ Pending |

---

## Step 6.1 - Mechanical Scanner

### File: `scripts/scan_execution_violations.py`

Scanner must enforce:
- No direct `plugin.run()` outside ToolRunner
- ToolRunner.run() must contain a `finally` block
- update_execution_metrics() must be called inside that finally
- Only valid lifecycle states: `LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE`
- No SUCCESS/ERROR lifecycle states

### Verification Command:
```bash
python scripts/scan_execution_violations.py
```

---

## Step 6.2 - CI Workflow

### File: `.github/workflows/execution-ci.yml`

CI must:
- Run on pull requests and pushes to main
- Run execution scanner
- Run Phase 11 tests
- Run all execution tests
- Fail on any violation

---

## Success Criteria

| Criterion | Status |
|-----------|--------|
| Scanner created and working | ⏳ Pending |
| CI workflow created | ⏳ Pending |
| Scanner passes (no violations) | ⏳ Pending |
| CI workflow valid YAML | ⏳ Pending |

---

## Quick Commands

```bash
# Run the mechanical scanner
python scripts/scan_execution_violations.py

# Run all execution tests
cd server && uv run pytest tests/execution -v

# Run Phase 11 tests
cd server && uv run pytest tests/phase_11 -v
```

---

## Related Documents

- `.ampcode/04_PHASE_NOTES/Phase_12/Updates/PHASE_12_NOTES_01_STEP6.md`
- `.ampcode/03_PLANS/Phase_12/TODO.md`

