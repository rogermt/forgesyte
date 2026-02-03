# Phase 7 – PR Guardrail Script

This script runs all Phase 7 guardrails in sequence to validate a PR before submission.

## Purpose

Orchestrates all Phase 7 checks:

1. Forbidden file check (useVideoProcessor, client.ts, etc.)
2. Skipped tests check (no `.skip`, `.only`, etc.)
3. Baseline verification (tests, lint, types, pre-commit)

If any check fails, the script stops and reports the failure.

## Usage

```bash
# Run full Phase 7 guardrail suite
bash scripts/phase7/pr-guardrail.sh

# Or as an npm script
npm run check:phase7

# Before opening a PR
npm run check:phase7 && git push origin feature/phase7-my-component
```

## Script (Bash)

```bash
#!/usr/bin/env bash

###############################################################################
# Phase 7 PR Guardrail Script
#
# Runs all Phase 7 checks in sequence:
# 1. Forbidden file changes
# 2. Skipped tests
# 3. Baseline verification
#
# Exit codes:
#   0 = All guardrails passed
#   1 = One or more guardrails failed
###############################################################################

set -e

echo "=== Phase 7 PR Guardrail Suite ==="
echo ""

cd "$(git rev-parse --show-toplevel)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FAILED=0

# Guard 1: Forbidden file check
echo -e "${BLUE}[1/3]${NC} Phase 7 – Forbidden File Check"
if ts-node scripts/phase7/forbidden-file-check.ts; then
  echo -e "${GREEN}✔ Passed${NC}\n"
else
  echo -e "${RED}✗ Failed${NC}\n"
  FAILED=1
fi

# Guard 2: Skipped tests check
echo -e "${BLUE}[2/3]${NC} Phase 7 – Skipped Tests Check"
if ts-node scripts/phase7/skipped-tests-check.ts; then
  echo -e "${GREEN}✔ Passed${NC}\n"
else
  echo -e "${RED}✗ Failed${NC}\n"
  FAILED=1
fi

# Guard 3: Baseline verification
echo -e "${BLUE}[3/3]${NC} Phase 7 – Baseline Verification"
if bash scripts/phase7/baseline-verify.sh; then
  echo -e "${GREEN}✔ Passed${NC}\n"
else
  echo -e "${RED}✗ Failed${NC}\n"
  FAILED=1
fi

# Summary
echo "=== Phase 7 PR Guardrail Summary ==="
if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✔ All guardrails passed${NC}"
  echo ""
  echo "Your PR is ready for submission."
  echo ""
  echo "Next steps:"
  echo "  1. Push branch: git push origin feature/phase7-..."
  echo "  2. Open PR on GitHub"
  echo "  3. Fill in PHASE_7_PR_TEMPLATE.md"
  exit 0
else
  echo -e "${RED}✗ One or more guardrails failed${NC}"
  echo ""
  echo "Fix issues above before submitting PR."
  exit 1
fi
```

## How to Integrate

### Option 1: As an npm Script

Add to `web-ui/package.json`:

```json
{
  "scripts": {
    "check:phase7": "bash ../scripts/phase7/pr-guardrail.sh"
  }
}
```

Or root `package.json`:

```json
{
  "scripts": {
    "check:phase7": "bash scripts/phase7/pr-guardrail.sh"
  }
}
```

### Option 2: Pre-push Hook

Create `.git/hooks/pre-push`:

```bash
#!/usr/bin/env bash
if [[ $(git symbolic-ref --short HEAD) == feature/phase7-* ]]; then
  bash scripts/phase7/pr-guardrail.sh
fi
```

Make executable:

```bash
chmod +x .git/hooks/pre-push
```

### Option 3: GitHub Actions

Add to `.github/workflows/pr-checks.yml`:

```yaml
- name: Phase 7 – Run guardrails
  if: contains(github.head_ref, 'phase7')
  run: bash scripts/phase7/pr-guardrail.sh
```

## Typical Output (Success)

```
=== Phase 7 PR Guardrail Suite ===

[1/3] Phase 7 – Forbidden File Check
✔ No forbidden file changes detected.

✔ Passed

[2/3] Phase 7 – Skipped Tests Check
✔ No skipped tests found.

✔ Passed

[3/3] Phase 7 – Baseline Verification

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

✔ Passed

=== Phase 7 PR Guardrail Summary ===
✔ All guardrails passed

Your PR is ready for submission.
```

## Typical Output (Failure)

```
=== Phase 7 PR Guardrail Suite ===

[1/3] Phase 7 – Forbidden File Check
❌ Phase 7 Guardrail Violation:

The following forbidden files were modified in this PR:

  - web-ui/src/hooks/useVideoProcessor.ts

📛 These files are LOCKED during Phase 7 CSS Modules migration.

💡 If a logic change is required, use PHASE_7_ESCALATION_TEMPLATE.md

✗ Failed

=== Phase 7 PR Guardrail Summary ===
✗ One or more guardrails failed

Fix issues above before submitting PR.
```

## Exit Codes

- `0` – All guardrails passed (ready for PR)
- `1` – One or more guardrails failed (fix issues first)

## Notes

- The script is idempotent (safe to run multiple times)
- Designed to be dev-friendly with clear error messages
- Should be run **immediately before pushing**
- Takes ~30 seconds to run (mostly tests)
- All subscripts can be run individually if needed
