Here we go—four concrete pieces you can drop straight into the repo.

---

### 1. Schema‑drift detector

**File:** `server/tests/schema/test_schema_drift.py`

```python
import json
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASELINE_PATH = Path("server/tests/schema/openapi_baseline.json")


def test_openapi_schema_drift():
    """Detect unintended OpenAPI schema drift."""
    current = client.get("/openapi.json").json()

    if not BASELINE_PATH.exists():
        # First run: write baseline and fail to force explicit approval
        BASELINE_PATH.write_text(json.dumps(current, indent=2, sort_keys=True))
        raise AssertionError(
            "Baseline OpenAPI schema created. Commit it and rerun tests."
        )

    baseline = json.loads(BASELINE_PATH.read_text())

    assert current == baseline, (
        "OpenAPI schema drift detected. If changes are intentional, "
        "update openapi_baseline.json and include TEST-CHANGE justification."
    )
```

---

### 2. Storybook build test

**CI only**—no Python needed.

In `.github/workflows/ci.yml` (or your main CI file), ensure:

```yaml
  web-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install dependencies
        run: |
          cd web-ui
          npm ci
      - name: Run web-ui tests
        run: |
          cd web-ui
          npm test
      - name: Build Storybook
        run: |
          cd web-ui
          npm run build-storybook
```

This makes Storybook build a **hard requirement**.

---

### 3. Combined backend+UI CI job

Add a **Phase 9 integration job** that runs both sides in one workflow.

```yaml
jobs:
  phase9-integration:
    runs-on: ubuntu-latest
    services:
      backend:
        image: python:3.11
        ports:
          - 8000:8000
        options: >-
          --health-cmd "curl -f http://localhost:8000/docs || exit 1"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 20
        command: >
          bash -lc "
          pip install -e . &&
          uvicorn app.main:app --host 0.0.0.0 --port 8000
          "
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install web-ui deps
        run: |
          cd web-ui
          npm ci

      - name: Run Phase 9 integration tests
        run: |
          # assumes Playwright tests use http://localhost:3000 and backend at 8000
          cd web-ui
          npm run test:phase9
```

(Adjust the Playwright command to your actual script name.)

---

### 4. Phase 9 merge checklist

**File:** `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MERGE_CHECKLIST.md`

```md
# Phase 9 — Merge Checklist

## API
- [ ] /v1/analyze returns typed AnalyzeResponse
- [ ] /v1/jobs/{id} returns typed JobStatusResponse
- [ ] /v1/jobs/{id}/result returns typed JobResultResponse
- [ ] All responses include: job_id, device_requested, device_used, fallback, frames
- [ ] OpenAPI schema updated and valid
- [ ] Schema drift test passing

## UI
- [ ] Device selector present and persists across reloads
- [ ] Overlay toggles (boxes, labels, pitch, radar) present and wired
- [ ] FPS slider present and functional
- [ ] Loading state shown during job submission
- [ ] User-friendly error messages displayed on failure
- [ ] Phase 9 UI tests passing

## Developer Experience
- [ ] Example plugin outputs module exists and is used in tests
- [ ] Storybook builds successfully in CI
- [ ] Stories exist for OverlayRenderer and VideoTracker
- [ ] Onboarding docs updated for new API + UI

## Governance
- [ ] Test file count not decreased
- [ ] Assertion count not decreased
- [ ] No skipped tests without APPROVED comment
- [ ] Schema drift baseline updated with TEST-CHANGE justification (if changed)
- [ ] No raw dict returns in API handlers

## Final
- [ ] All CI jobs green (backend, UI, Storybook, schema, integration)
- [ ] Phase 9 notes updated with any deviations
- [ ] PR uses Phase 9 PR template
```

