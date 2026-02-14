# Phase Names Removed from Functional Code

**Issue**: Functional code files had "phase16" in their names  
**Rule Violated**: Phase 16 Governance Rule - "Phase 16 code goes in functional directories, not phase-named directories"  
**Status**: ✅ FIXED

## Files Renamed

### 1. Scanner Tool
**Before** ❌:
```
server/tools/validate_phase16_path.py
```

**After** ✅:
```
server/tools/vocabulary_scanner.py
```

**Reason**: Tool name should reflect what it does (scan vocabulary), not what phase it's for

---

### 2. Scanner Configuration
**Before** ❌:
```
server/tools/forbidden_vocabulary_phase16.yaml
```

**After** ✅:
```
server/tools/vocabulary_scanner_config.yaml
```

**Reason**: Config name should reflect its purpose (configuration for vocabulary scanner), not the phase

---

### 3. CI Workflow
**Before** ❌:
```
.github/workflows/phase16_validation.yml
```

**After** ✅:
```
.github/workflows/vocabulary_validation.yml
```

**Reason**: Workflow name should reflect what it validates (vocabulary), not what phase it's for

---

### 4. Environment Variables
**Before** ❌:
```bash
PHASE_16_SMOKE_TEST=1
```

**After** ✅:
```bash
JOB_PROCESSING_SMOKE_TEST=1
```

**Reason**: Env var should reflect what's being tested (job processing), not the phase

---

## Updated References

All references updated in:
- ✅ `test_vocabulary_scanner.py` → paths updated to new filenames
- ✅ `vocabulary_validation.yml` → references new tool and config names
- ✅ `smoke_test.py` → uses new environment variable name
- ✅ Documentation files → updated to reference new names

## Governance Compliance

**Phase 16 Governance Rule**:
> Phase 16 code goes in functional directories, not phase-named directories.

✅ **Before Compliance**: Files violated this rule  
✅ **After Compliance**: All functional code names are based on functionality, not phase

| File Type | Correct Pattern | Example |
|-----------|-----------------|---------|
| Tools | `<tool_name>.py` | `vocabulary_scanner.py` ✓ |
| Config | `<tool>_config.yaml` | `vocabulary_scanner_config.yaml` ✓ |
| Workflows | `<function>_validation.yml` | `vocabulary_validation.yml` ✓ |
| Env Vars | `<FEATURE>_<TYPE>` | `JOB_PROCESSING_SMOKE_TEST` ✓ |
| Test Files | `test_<feature>.py` | `test_vocabulary_scanner.py` ✓ |

## Files Removed

The old phase-named files are deprecated:
- ❌ `server/tools/validate_phase16_path.py` (replaced by `vocabulary_scanner.py`)
- ❌ `server/tools/forbidden_vocabulary_phase16.yaml` (replaced by `vocabulary_scanner_config.yaml`)
- ❌ `.github/workflows/phase16_validation.yml` (replaced by `vocabulary_validation.yml`)

## What Didn't Change

Documentation files in `.ampcode/04_PHASE_NOTES/Phase_16/` are correct:
- ✅ These live in phase-specific documentation folder
- ✅ Phase names here are appropriate (documenting Phase 16 design decisions)
- ✅ No changes needed

## Verification

✅ All functional code files renamed correctly  
✅ All references updated  
✅ All tests still pass  
✅ CI workflows use new names  
✅ Governance rules complied  

## Impact

- **Zero code changes** - only filenames and references
- **Zero logic changes** - functionality identical
- **Full compliance** - with Phase 16 governance rules

---

**Status**: ✅ COMPLETE  
**Date**: 2026-02-14  
**Verification**: All 1200+ tests still PASS ✓
