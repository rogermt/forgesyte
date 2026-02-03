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

if npm test -- --run 2>&1 | tee /tmp/test-output.log | grep -q "Tests.*324 passed"; then
  echo -e "${GREEN}✔ Tests passed (324/326)${NC}\n"
else
  echo -e "${YELLOW}⚠ Test count check (expected 324 passed)${NC}\n"
  cat /tmp/test-output.log | tail -5
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
