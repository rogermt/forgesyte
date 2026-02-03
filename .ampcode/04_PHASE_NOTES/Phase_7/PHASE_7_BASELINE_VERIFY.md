# Phase 7 – Baseline Verification Script

This script verifies that the Phase 6 baseline remains intact before and after each Phase 7 PR.

## Purpose

Runs all quality checks to confirm:

1. Tests pass (exactly 8/8)
2. Linting passes (no errors)
3. Type checking passes
4. Pre-commit hooks all pass

## Usage

```bash
# Run full baseline verification
bash scripts/phase7/baseline-verify.sh

# Or run individual checks
cd web-ui && npm test -- --run
cd web-ui && npm run lint
cd web-ui && npm run type-check
cd /path/to/forgesyte && uv run pre-commit run --all-files
```

## Script (Bash)

```bash
#!/usr/bin/env bash

###############################################################################
# Phase 7 Baseline Verification Script
#
# Verifies that:
# - Tests pass (8/8)
# - Lint passes
# - Type check passes
# - Pre-commit hooks pass (7/7)
#
# Exit codes:
#   0 = All checks passed
#   1 = One or more checks failed
###############################################################################

set -e

echo "=== Phase 7 Baseline Verification ==="
echo ""

cd "$(git rev-parse --show-toplevel)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Test 1: Run web-ui tests
echo "→ Running web-ui tests"
cd web-ui

if npm test -- --run 2>&1 | tee /tmp/test-output.log | grep -q "Tests.*8 passed"; then
  echo -e "${GREEN}✔ Tests passed (8/8)${NC}\n"
else
  echo -e "${RED}✗ Test count mismatch or failed${NC}\n"
  cat /tmp/test-output.log | tail -20
  FAILED=1
fi

# Test 2: Lint
echo "→ Running web-ui lint"
if npm run lint > /tmp/lint-output.log 2>&1; then
  echo -e "${GREEN}✔ Lint passed${NC}\n"
else
  echo -e "${RED}✗ Lint failed${NC}\n"
  cat /tmp/lint-output.log
  FAILED=1
fi

# Test 3: Type check
echo "→ Running type-check"
if npm run type-check > /tmp/typecheck-output.log 2>&1; then
  echo -e "${GREEN}✔ Type check passed${NC}\n"
else
  echo -e "${RED}✗ Type check failed${NC}\n"
  cat /tmp/typecheck-output.log
  FAILED=1
fi

# Test 4: Pre-commit hooks
echo "→ Running pre-commit hooks"
cd ..

if uv run pre-commit run --all-files > /tmp/precommit-output.log 2>&1; then
  echo -e "${GREEN}✔ Pre-commit hooks passed (7/7)${NC}\n"
else
  echo -e "${RED}✗ Pre-commit hooks failed${NC}\n"
  cat /tmp/precommit-output.log | tail -30
  FAILED=1
fi

# Summary
echo "=== Baseline Verification Summary ==="
if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✔ All checks passed${NC}"
  echo ""
  echo "Phase 6 baseline is intact and ready for Phase 7 work."
  exit 0
else
  echo -e "${RED}✗ One or more checks failed${NC}"
  echo ""
  echo "Fix issues above before proceeding with Phase 7 PRs."
  exit 1
fi
```

## How to Integrate

### Option 1: As a Dev Script

Save to: `scripts/phase7/baseline-verify.sh`

Make executable:

```bash
chmod +x scripts/phase7/baseline-verify.sh
```

Add to `package.json`:

```json
{
  "scripts": {
    "verify:phase7-baseline": "bash scripts/phase7/baseline-verify.sh"
  }
}
```

### Option 2: Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: phase7-baseline-verify
  name: Phase 7 – Baseline verification
  entry: bash scripts/phase7/baseline-verify.sh
  language: system
  pass_filenames: false
  stages: [commit]
```

### Option 3: GitHub Actions

Add to `.github/workflows/pr-checks.yml`:

```yaml
- name: Phase 7 – Verify baseline
  run: bash scripts/phase7/baseline-verify.sh
```

## What It Checks

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Tests | `npm test -- --run` | `Tests  8 passed` |
| Lint | `npm run lint` | No errors |
| Types | `npm run type-check` | 0 errors |
| Pre-commit | `uv run pre-commit run --all-files` | All 7 hooks pass |

## Exit Codes

- `0` – All checks passed (OK to proceed)
- `1` – One or more checks failed (stop and fix)

## Typical Output (Success)

```
=== Phase 7 Baseline Verification ===

→ Running web-ui tests
✔ Tests passed (8/8)

→ Running web-ui lint
✔ Lint passed

→ Running type-check
✔ Type check passed

→ Running pre-commit hooks
✔ Pre-commit hooks passed (7/7)

=== Baseline Verification Summary ===
✔ All checks passed

Phase 6 baseline is intact and ready for Phase 7 work.
```

## Notes

- Logs are written to `/tmp/` for easier debugging
- If any check fails, relevant output is printed
- The script uses `set -e` to fail fast on errors
- Should be run **after each Phase 7 PR** before merge
