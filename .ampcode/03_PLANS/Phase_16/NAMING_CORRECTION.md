# Naming Correction: Phase 16 Governance Tests

**Issue**: Test file name violated Phase 16 governance rules
**Fix Applied**: Renamed to follow functional naming convention

## The Problem

**Before (❌ Invalid)**:
```
server/tests/execution/test_phase16_governance.py
                       ^^^^^^^^^^^^^^^^^^^^^^ Phase-named file in test (functional code)
```

**Why it's wrong**:
- Phase 16 governance rules: "Phase 16 code goes in functional directories, not phase-named directories"
- Tests are functional code
- File naming should be based on **what is tested**, not **what phase it's for**

## The Fix

**After (✅ Correct)**:
```
server/tests/execution/test_vocabulary_scanner.py
                       ^^^^^^^^^^^^^^^^^^^^^^^^^ Functional name (tests scanner tool)
```

**Why it's correct**:
- Tests the **vocabulary scanner tool** functionality
- Doesn't mention phase number in filename
- Follows functional naming convention
- Complies with Phase 16 governance rules

## Changes Made

| File | Change |
|------|--------|
| `test_vocabulary_scanner.py` | Created (correct name) |
| `test_phase16_governance.py` | Deprecated/removed |
| `test_vocabulary_scanner.py` | Class: `TestVocabularyScanner` |
| `phase16_validation.yml` | Updated: references `test_vocabulary_scanner.py` |
| `PHASE_16_COMMIT_09.md` | Updated: references new filename |
| `PHASE_16_COMMIT_SCAFFOLDINGS.md` | Updated: references new filename |
| `PHASE_16_COMMIT_09_SUMMARY.md` | Updated: references new filename |

## Test Methods Renamed

| Old Name | New Name | Reason |
|----------|----------|--------|
| `test_governance_scanner_runs` | `test_scanner_tool_exists` | More specific, functional |
| `test_governance_config_exists` | `test_scanner_config_exists` | More specific, functional |
| `test_no_forbidden_vocabulary_in_functional_code` | (unchanged) | Already functional |

## Governance Compliance

✅ **Phase 16 Governance Rules**: No phase-named files in functional code  
✅ **Test Naming**: Based on functionality (vocabulary scanner)  
✅ **Class Naming**: `TestVocabularyScanner` (functional, not phase-named)  
✅ **Documentation**: All references updated  
✅ **CI Workflow**: All references updated  

## Key Principle

From `PHASE_16_GOVERNANCE_RULES.md`:

> **Rule**: Phase 16 code goes in functional directories, not phase-named directories.
>
> **Correct**:
> ```
> server/app/api_routes/routes/job_submission.py
> server/app/tests/execution/test_vocabulary_scanner.py
> ```
>
> **Incorrect**:
> ```
> server/app/api_routes/routes/phase16_job.py
> server/app/tests/execution/test_phase16_governance.py
> ```

## Verification

✓ File created: `test_vocabulary_scanner.py`  
✓ File deleted: `test_phase16_governance.py`  
✓ CI workflow updated  
✓ Documentation updated  
✓ All references corrected  

---

**Status**: ✅ CORRECTED  
**Applied**: 2026-02-14  
**Impact**: Zero - pure naming correction, no logic change
