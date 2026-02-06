# Phase 11 Governance Addendum — Server Test Enforcement

This document locks Phase 11 governance rules that prevent regressions and ensure deterministic CI/CD behavior.

---

## Rule 1 — Server Tests MUST Run in Pre-Commit

All commits MUST pass the FastAPI server test suite via:

```bash
cd server && uv run pytest
```

This rule ensures:

- **API contract stability**: Response schemas match models
- **Model field stability**: All required fields present
- **No silent regressions**: Tests catch breaking changes
- **Phase 9 invariants held**: Device selection, observability intact
- **Phase 10 invariants held**: Real-time infrastructure works

**Enforcement**: `.pre-commit-config.yaml` includes `server-tests` hook.

---

## Rule 2 — Web-UI Tests MUST NOT Run Locally

Playwright tests MUST run only when `CI=true`.

```bash
# Locally: SKIPPED (fast pre-commit)
uv run pre-commit run web-ui-tests

# In CI: RUNS (full test suite)
CI=true uv run pre-commit run web-ui-tests
```

This rule ensures:

- **Fast local workflow**: Pre-commit runs in <5 seconds
- **Safe dependencies**: No npm resolution blocking commits
- **CI owns Playwright**: Browser-based tests run only in CI pipeline

**Enforcement**: `.pre-commit-config.yaml` includes CI guard on `web-ui-tests` hook.

---

## Rule 3 — CI MUST Run All Tests

GitHub Actions CI workflow MUST run:

1. **Server tests** (all platforms)
2. **Web-UI tests** (Playwright)
3. **Integration tests** (end-to-end)
4. **Contract tests** (OCR on CPU, all plugins on GPU/Kaggle)

Failure in ANY test category fails the PR.

---

## Rule 4 — API Contract Stability

The following API contracts are **FROZEN** and require RFC approval to change:

| Endpoint | Response Model | Required Fields |
|----------|---|---|
| `POST /v1/analyze` | `AnalyzeResponse` | job_id, device_requested, device_used, fallback |
| `GET /v1/jobs` | `JobResponse[]` | job_id, status, created_at, plugin |
| `GET /v1/jobs/{id}` | `JobStatusResponse` | job_id, status, device_requested, device_used |
| `GET /v1/jobs/{id}/result` | `JobResultResponse` | job_id, result, error |

Adding fields = **Additive Change** (OK, backwards compatible)
Removing fields = **Breaking Change** (Requires RFC)
Changing types = **Breaking Change** (Requires RFC)

---

## Rule 5 — Pre-Commit Hook Contract

The `.pre-commit-config.yaml` hooks MUST be:

```yaml
- id: server-tests
  name: Server Tests (FastAPI + Pytest)
  entry: bash -c 'cd server && uv run pytest -q'
  language: system
  pass_filenames: false

- id: web-ui-tests
  name: Web UI Tests (CI only)
  entry: bash -c 'if [ "$CI" != "true" ]; then echo "Skipping Playwright tests locally"; exit 0; fi; cd web-ui && npm run test:e2e'
  language: system
  pass_filenames: false
```

Changes to these hooks require Phase 11+ RFC approval.

---

## Rule 6 — Test Changes Require Justification

When modifying tests, include `TEST-CHANGE:` in commit message explaining:

- **WHY** the test changed
- **WHAT** invariant it enforces
- **WHO** should be aware

Example:

```
TEST-CHANGE: Fix test_single_job_endpoint schema validation

The endpoint returns JobStatusResponse, not JobResponse.
Tests now expect correct schema (job_id, status, device_*).
Prevents regression if someone removes status field.
```

---

## Rule 7 — Repository-Wide API Drift Detection

A scanner script (`scripts/scan_api_contracts.py`) runs:

- Detects missing required fields
- Detects type mismatches
- Detects default value drift
- Can be run locally: `python scripts/scan_api_contracts.py`

This is a **mechanical guardrail** — exactly like Phase 10's test validation.

---

## Summary

These rules lock Phase 11 into:

- **Deterministic testing**: All tests run before commit
- **API stability**: Contracts frozen, changes require RFC
- **Fast workflow**: Pre-commit <5s locally, full suite in CI
- **Mechanical governance**: No human judgment needed

This is the foundation for Phase 12+.
