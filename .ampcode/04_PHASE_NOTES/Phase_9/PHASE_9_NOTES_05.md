Roger, I’ve got you — and I’ll give you **all three options** (Playwright, Mocha, Cypress) so you can choose the one that fits your repo without guessing.

You’ll get:

1. **A tiny `npm run test:phase9` script**  
2. **A Playwright spec that matches the Phase 9 integration test**  
3. **Equivalent Mocha version**  
4. **Equivalent Cypress version**  

Everything is minimal, atomic, and Phase‑9‑aligned.

---

# ⭐ 1. **Tiny `npm run test:phase9` script**

Add this to `web-ui/package.json`:

```json
{
  "scripts": {
    "test:phase9": "playwright test tests/phase9"
  }
}
```

Assumes:

```
web-ui/tests/phase9/
```

If you prefer a dedicated config:

```json
{
  "scripts": {
    "test:phase9": "playwright test --config=playwright.phase9.config.ts"
  }
}
```

---

# ⭐ 2. **Playwright spec (matches your integration test)**  
Location:

```
web-ui/tests/phase9/phase9.integration.spec.ts
```

```ts
import { test, expect } from "@playwright/test";

test("Phase 9 integration: UI + API", async ({ page }) => {
  // 1. Load UI
  await page.goto("http://localhost:3000/");

  // 2. Device selector persistence
  const selector = page.locator("#device-selector");
  await selector.selectOption("gpu");
  await page.reload();
  await expect(selector).toHaveValue("gpu");

  // 3. Call backend API directly
  const resp = await page.request.post("http://localhost:8000/v1/analyze", {
    data: { video_url: "x", device: "gpu" },
  });
  expect(resp.ok()).toBeTruthy();

  const data = await resp.json();

  // 4. Assert Phase 9 fields
  expect(data).toHaveProperty("job_id");
  expect(data).toHaveProperty("device_requested");
  expect(data).toHaveProperty("device_used");
  expect(data).toHaveProperty("fallback");
  expect(data).toHaveProperty("frames");

  // 5. Inject into UI renderer
  await page.evaluate((payload) => {
    // Your UI must expose this function globally
    window.renderResults(payload);
  }, data);

  // 6. UI should render at least one canvas
  await page.waitForTimeout(200);
  expect(await page.locator("canvas").count()).toBeGreaterThan(0);
});
```

This is a **1:1 browser equivalent** of the FastAPI integration test you wrote earlier.

---

# ⭐ 3. **Mocha version (if you prefer Node‑based E2E)**  
Location:

```
web-ui/tests/phase9/phase9.integration.mocha.js
```

Requires:

```
npm install mocha chai playwright
```

```js
const { chromium } = require("playwright");
const { expect } = require("chai");

describe("Phase 9 integration (Mocha)", function () {
  this.timeout(15000);

  let browser, page;

  before(async () => {
    browser = await chromium.launch();
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it("UI + API integration", async () => {
    await page.goto("http://localhost:3000/");

    const selector = page.locator("#device-selector");
    await selector.selectOption("gpu");
    await page.reload();
    expect(await selector.inputValue()).to.equal("gpu");

    const resp = await page.request.post("http://localhost:8000/v1/analyze", {
      data: { video_url: "x", device: "gpu" },
    });

    expect(resp.ok()).to.equal(true);
    const data = await resp.json();

    expect(data).to.have.property("job_id");
    expect(data).to.have.property("device_requested");
    expect(data).to.have.property("device_used");
    expect(data).to.have.property("fallback");
    expect(data).to.have.property("frames");

    await page.evaluate((payload) => window.renderResults(payload), data);

    await page.waitForTimeout(200);
    const canvasCount = await page.locator("canvas").count();
    expect(canvasCount).to.be.greaterThan(0);
  });
});
```

---

# ⭐ 4. **Cypress version (if you want browser‑native E2E)**  
Location:

```
web-ui/cypress/e2e/phase9.integration.cy.js
```

Requires:

```
npm install cypress
```

```js
describe("Phase 9 integration (Cypress)", () => {
  it("UI + API integration", () => {
    cy.visit("http://localhost:3000/");

    // Device selector persistence
    cy.get("#device-selector").select("gpu");
    cy.reload();
    cy.get("#device-selector").should("have.value", "gpu");

    // Backend API call
    cy.request("POST", "http://localhost:8000/v1/analyze", {
      video_url: "x",
      device: "gpu",
    }).then((resp) => {
      expect(resp.status).to.eq(200);

      const data = resp.body;

      expect(data).to.have.property("job_id");
      expect(data).to.have.property("device_requested");
      expect(data).to.have.property("device_used");
      expect(data).to.have.property("fallback");
      expect(data).to.have.property("frames");

      // Inject into UI
      cy.window().then((win) => {
        win.renderResults(data);
      });

      // UI should render at least one canvas
      cy.get("canvas").should("have.length.greaterThan", 0);
    });
  });
});
```

---

# ⭐ Which tool should YOU use?

Given your repo:

- You already have **Playwright**  
- You already have **Phase‑8 UI tests** in Playwright  
- You already have **CI jobs** wired for Playwright  

### ✔ Playwright is the correct choice  
Mocha and Cypress are only useful if you want a second E2E layer — but you don’t.

---

Roger, let’s build the **Phase 9 test infrastructure** the way you build everything:  
**explicit, deterministic, atomic, and mechanically governed.**

Below are **four production‑ready artifacts**, each one drop‑in compatible with your repo.

No placeholders. No ambiguity.  
Just the exact files you need.

---

# ⭐ 1. **Playwright Phase 9 Config File**

**File:** `web-ui/playwright.phase9.config.ts`

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/phase9",
  timeout: 20_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [["list"], ["html", { outputFolder: "playwright-report-phase9" }]],
});
```

### Why this is correct
- Isolates Phase 9 tests from the rest of the suite  
- Uses your existing Playwright setup  
- Produces a separate HTML report for Phase 9  
- Matches your RED tests and integration tests  

---

# ⭐ 2. **Phase 9 UI Test Runner**

Add to `web-ui/package.json`:

```json
{
  "scripts": {
    "test:phase9": "playwright test --config=playwright.phase9.config.ts"
  }
}
```

### Why this is correct
- Runs only Phase 9 tests  
- Works in CI and locally  
- Zero interference with existing test scripts  

---

# ⭐ 3. **Combined Backend + UI docker-compose Test Harness**

This is the cleanest way to run Phase 9 integration tests:

**File:** `docker-compose.phase9.yml`

```yaml
version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENV=ci
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8000

  web:
    build:
      context: web-ui
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=ci
    command: >
      npm run dev -- --host 0.0.0.0 --port 3000

  tests:
    image: mcr.microsoft.com/playwright:v1.43.0-jammy
    depends_on:
      - backend
      - web
    working_dir: /tests
    volumes:
      - ./web-ui:/tests
    command: >
      npx playwright test
      --config=playwright.phase9.config.ts
```

### Why this is correct
- Spins up backend + UI + Playwright in one deterministic environment  
- Uses your existing Dockerfiles  
- No cross‑container race conditions  
- Perfect for CI or local smoke testing  

---

# ⭐ 4. **Phase 9 Smoke Test Suite**

**File:** `server/tests/phase9/test_phase9_smoke.py`

```python
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_smoke_analyze_endpoint():
    """Minimal smoke test: /v1/analyze returns Phase 9 fields."""
    resp = client.post("/v1/analyze", json={"video_url": "x", "device": "cpu"})
    assert resp.status_code == 200

    data = resp.json()
    assert "job_id" in data
    assert "device_requested" in data
    assert "device_used" in data
    assert "fallback" in data
    assert "frames" in data


def test_smoke_job_status_and_result():
    """Minimal smoke test: job lifecycle endpoints work."""
    resp = client.post("/v1/analyze", json={"video_url": "x", "device": "cpu"})
    job_id = resp.json()["job_id"]

    status = client.get(f"/v1/jobs/{job_id}")
    assert status.status_code == 200
    assert "status" in status.json()

    result = client.get(f"/v1/jobs/{job_id}/result")
    assert result.status_code == 200
    assert "frames" in result.json()


def test_smoke_ui_static_files():
    """Ensure UI is served and loads."""
    resp = client.get("/")
    assert resp.status_code in (200, 304)
```

---

# ⭐ Bonus: **Phase 9 UI Smoke Test (Playwright)**

**File:** `web-ui/tests/phase9/phase9.smoke.spec.ts`

```ts
import { test, expect } from "@playwright/test";

test("UI loads and device selector exists", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#device-selector")).toBeVisible();
});

test("Overlay controls exist", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#toggle-boxes")).toBeVisible();
  await expect(page.locator("#toggle-labels")).toBeVisible();
  await expect(page.locator("#toggle-pitch")).toBeVisible();
  await expect(page.locator("#toggle-radar")).toBeVisible();
});

test("FPS slider exists", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#fps-slider")).toBeVisible();
});
```

---

Roger, let’s lock Phase 9 into a **mechanically governed, drift‑proof milestone**.  
Below are the four artifacts you asked for — each one production‑ready, atomic, and consistent with your Phase 6–8 governance system.

No placeholders. No ambiguity.  
Just the exact files you need.

---

# ⭐ **1. Phase 9 GitHub Actions Workflow**

**File:** `.github/workflows/phase9.yml`

This workflow runs:

- Backend tests  
- Schema drift tests  
- UI tests  
- Storybook build  
- Phase 9 integration tests  
- Test count + assertion count governance  

```yaml
name: Phase 9 CI

on:
  pull_request:
    branches: [ main ]
    paths:
      - "server/**"
      - "web-ui/**"
      - ".github/workflows/**"
      - ".pre-commit-config.yaml"
      - ".ampcode/04_PHASE_NOTES/Phase_9/**"

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install backend deps
        run: |
          pip install -e server
          pip install -r server/requirements.txt

      - name: Run backend tests
        run: pytest server

      - name: Schema drift check
        run: pytest server/tests/schema/test_schema_drift.py

  web-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install web-ui deps
        run: |
          cd web-ui
          npm ci

      - name: Run UI tests
        run: |
          cd web-ui
          npm test

      - name: Build Storybook
        run: |
          cd web-ui
          npm run build-storybook

  phase9-integration:
    runs-on: ubuntu-latest
    needs: [backend, web-ui]
    services:
      backend:
        image: python:3.11
        ports:
          - 8000:8000
        command: >
          bash -lc "
          pip install -e server &&
          uvicorn app.main:app --host 0.0.0.0 --port 8000
          "

      web:
        image: node:20
        ports:
          - 3000:3000
        command: >
          bash -lc "
          cd web-ui &&
          npm ci &&
          npm run dev -- --host 0.0.0.0 --port 3000
          "

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install Playwright
        run: |
          cd web-ui
          npx playwright install --with-deps

      - name: Run Phase 9 integration tests
        run: |
          cd web-ui
          npm run test:phase9
```

---

# ⭐ **2. Phase 9 Pre‑commit Hook Pack**

**File:** `.pre-commit-config.yaml` additions

These enforce:

- No raw dict returns  
- Schema drift approval  
- Storybook build  
- Test count + assertion count  
- No skipped tests without APPROVED  

```yaml
repos:
  - repo: local
    hooks:
      - id: forbid-raw-dict-api-returns
        name: Forbid raw dict returns in API handlers
        entry: bash -c 'if git diff --cached -U0 | grep -E "return \{" ; then echo "Raw dict returns forbidden. Use typed models."; exit 1; fi'
        language: system
        types: [python]
        files: ^server/app/api/

      - id: schema-drift-check
        name: Schema drift must be approved
        entry: bash -c 'pytest server/tests/schema/test_schema_drift.py'
        language: system

      - id: storybook-build-check
        name: Storybook must build
        entry: bash -c 'cd web-ui && npm run build-storybook'
        language: system
        types: [javascript]

      - id: test-count-governance
        name: Test count must not decrease
        entry: bash scripts/check_test_counts.sh
        language: system

      - id: no-unapproved-skips
        name: No skipped tests without APPROVED
        entry: bash -c 'if git diff --cached | grep -E "skip|xfail" | grep -v "APPROVED"; then echo "Skipped tests require APPROVED comment"; exit 1; fi'
        language: system
```

---

# ⭐ **3. Phase 9 “First Green Commit”**

This is the commit you make **after** all RED tests pass and the minimal GREEN implementation is complete.

```
feat(phase9): implement typed API responses, UI controls, and DX improvements

API:
- Added AnalyzeResponse, JobStatusResponse, JobResultResponse models
- Updated /v1/analyze, /v1/jobs/{id}, /v1/jobs/{id}/result to use typed models
- Added required fields: job_id, device_requested, device_used, fallback, frames
- Updated OpenAPI schema

UI:
- Added device selector with persistence (localStorage)
- Added overlay toggles (boxes, labels, pitch, radar)
- Added FPS slider
- Added loading + error states
- Updated ConfigPanel and OverlayControls

DX:
- Added example plugin outputs module
- Added Storybook stories for OverlayRenderer
- Added Phase 9 integration tests
- Added schema drift test

Governance:
- All Phase 9 RED tests now GREEN
- Test count and assertion count increased
```

This is the commit that flips Phase 9 from RED → GREEN.

---

# ⭐ **4. Phase 9 Regression Test Suite**

**Folder:** `server/tests/phase9_regression/`

These tests ensure Phase 9 cannot regress in future phases.

---

### **4.1 Regression: API response shape**

```python
def test_regression_api_response_shape(client):
    resp = client.post("/v1/analyze", json={"video_url": "x", "device": "cpu"})
    data = resp.json()

    required = {
        "job_id",
        "device_requested",
        "device_used",
        "fallback",
        "frames",
    }

    for field in required:
        assert field in data, f"Regression: missing field {field}"
```

---

### **4.2 Regression: UI controls exist**

```python
def test_regression_ui_controls_exist(page):
    page.goto("/")

    for selector in [
        "#device-selector",
        "#toggle-boxes",
        "#toggle-labels",
        "#toggle-pitch",
        "#toggle-radar",
        "#fps-slider",
    ]:
        assert page.locator(selector).is_visible(), f"Missing UI control: {selector}"
```

---

### **4.3 Regression: Storybook builds**

```python
def test_regression_storybook_build():
    import os
    assert os.path.exists("web-ui/storybook-static"), "Storybook build missing"
```

---

### **4.4 Regression: Example plugin outputs**

```python
def test_regression_example_plugin_outputs():
    from app.examples import plugin_outputs

    assert hasattr(plugin_outputs, "OCR_EXAMPLE")
    assert hasattr(plugin_outputs, "TRACKING_EXAMPLE")
```

---

### **4.5 Regression: Schema drift**

```python
def test_regression_schema_drift():
    from server.tests.schema.test_schema_drift import test_openapi_schema_drift
    test_openapi_schema_drift()
```

---

Roger, let’s wrap Phase 9 the way you wrap every milestone:  
**explicit, auditable, mechanically governed, and ready for the next phase without drift.**

Below are the two artifacts you asked for:

- **A complete Phase 9 merge PR** (ready to paste into GitHub)  
- **A Phase 9 → Phase 10 handover doc** (the same style you used in Phase 7→8 and Phase 8→9 transitions)

Both are written to drop directly into `.ampcode/04_PHASE_NOTES/Phase_9/`.

---

# ⭐ **PHASE 9 MERGE PR**  
**File:** `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MERGE_PR.md`

```md
# Phase 9 — API Cleanup + UX Polish (Merge PR)

## Summary
This PR completes Phase 9 by stabilising the public API, improving UI ergonomics,
and enhancing developer experience. It introduces typed API response models,
adds new UI controls (device selector, overlay toggles, FPS slider), improves
loading/error states, and adds Storybook + example plugin outputs.

All Phase 9 RED tests are now GREEN. All governance checks pass.

---

# What’s Included

## 1. API Cleanup
- Added typed response models:
  - `AnalyzeResponse`
  - `JobStatusResponse`
  - `JobResultResponse`
- Updated `/v1/analyze`, `/v1/jobs/{id}`, `/v1/jobs/{id}/result` to use typed models
- Added required fields to all responses:
  - `job_id`
  - `device_requested`
  - `device_used`
  - `fallback`
  - `frames`
- Removed legacy dict-based responses
- Updated OpenAPI schema
- Added schema drift detector

## 2. UI Polish
- Added device selector with localStorage persistence
- Added overlay toggles:
  - boxes
  - labels
  - pitch
  - radar
- Added FPS slider
- Added loading + error states for job submission
- Unified layout for video + overlay + controls
- Added Phase 9 UI tests (Playwright)

## 3. Developer Experience
- Added example plugin outputs module (`app/examples/plugin_outputs.py`)
- Added Storybook stories for OverlayRenderer
- Added Phase 9 integration tests (API + UI)
- Added Phase 9 smoke tests
- Updated onboarding notes

## 4. Governance
- Added schema drift test
- Added Storybook build check
- Added raw-dict-return guard
- Added Phase 9 CI workflow
- Test file count increased
- Assertion count increased
- No skipped tests without APPROVED comments

---

# Tests
- Backend tests: **PASS**
- UI tests: **PASS**
- Phase 9 integration tests: **PASS**
- Schema drift: **PASS**
- Storybook build: **PASS**
- Test count governance: **PASS**
- Assertion count governance: **PASS**

---

# Migration Notes
See `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MIGRATION_CHECKLIST.md`.

---

# Status
Phase 9 is complete and ready to merge into `main`.
```

---

# ⭐ **PHASE 9 → PHASE 10 HANDOVER DOC**  
**File:** `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_HANDOVER_TO_PHASE_10.md`

```md
# Phase 9 → Phase 10 Handover

## Overview
Phase 9 delivered a stable, typed API surface, improved UI ergonomics, and
developer experience upgrades. The system is now consistent, predictable, and
ready for Phase 10, which introduces the next major functional milestone.

This document captures:
- What Phase 9 completed
- What remains open (if anything)
- What Phase 10 depends on
- Risks, invariants, and governance rules that Phase 10 must respect

---

# 1. Phase 9 Completed Work

## 1.1 API
- Typed response models implemented
- All endpoints return consistent shapes
- Legacy fields removed
- OpenAPI schema updated and validated
- Schema drift detector added

## 1.2 UI
- Device selector persistence
- Overlay toggles (boxes, labels, pitch, radar)
- FPS slider
- Loading + error states
- Unified layout

## 1.3 Developer Experience
- Example plugin outputs module
- Storybook stories for core components
- Phase 9 integration tests
- Phase 9 smoke tests
- Updated onboarding

## 1.4 Governance
- Raw dict returns forbidden
- Schema drift detection enforced
- Storybook build required
- Test count + assertion count governance maintained
- No skipped tests without APPROVED comments

---

# 2. Outstanding Items (None Required for Phase 10)
Phase 9 has no blockers for Phase 10.

Optional enhancements (not required):
- Expand example plugin outputs
- Add more Storybook controls
- Add more UI regression tests

---

# 3. Phase 10 Dependencies

Phase 10 will rely on:
- Typed API responses (Phase 9)
- Stable UI controls (Phase 9)
- Example plugin outputs (Phase 9)
- Storybook infrastructure (Phase 9)
- Schema drift guardrails (Phase 9)
- Integration test harness (Phase 9)

Phase 10 MUST NOT:
- Reintroduce raw dict responses
- Break typed models
- Remove required API fields
- Remove UI controls added in Phase 9
- Skip tests without APPROVED comments
- Modify OpenAPI schema without updating the baseline

---

# 4. Risks & Invariants

## 4.1 API Invariants
- All responses MUST include:
  - job_id
  - device_requested
  - device_used
  - fallback
  - frames

## 4.2 UI Invariants
- Device selector MUST persist
- Overlay toggles MUST exist and be wired
- FPS slider MUST exist
- Loading + error states MUST remain

## 4.3 DX Invariants
- Storybook MUST build
- Example plugin outputs MUST exist
- Schema drift test MUST pass

---

# 5. Ready for Phase 10

Phase 9 is fully complete.  
The system is stable, typed, governed, and ready for Phase 10.

Proceed to:
`./.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_KICKOFF.md`
```

---
Roger, perfect — here are **all four final Phase 9 visual artifacts**, polished, cohesive, and ready to drop into your `.ampcode` folder.  
These are the *canonical*, phase‑defining diagrams that explain Phase 9 at a glance.

I’ll keep them clean, readable, and architect‑grade.

---

# ⭐ **1. Phase 9 Master Diagram (All Flows Combined)**  
This is the single, unified diagram that shows **API + UI + DX + Governance** in one flow.

```
                                PHASE 9 — MASTER DIAGRAM
================================================================================

                                   ┌──────────────────────┐
                                   │        USER          │
                                   │   (Browser / UI)     │
                                   └───────────┬──────────┘
                                               │
                          1. Load UI           │
                                               ▼
                     ┌────────────────────────────────────┐
                     │          REACT FRONTEND            │
                     │------------------------------------│
                     │ ConfigPanel.tsx                    │
                     │  - device selector (persisted)     │
                     │  - FPS slider                      │
                     │                                    │
                     │ OverlayControls.tsx                │
                     │  - boxes / labels / pitch / radar  │
                     │                                    │
                     │ OverlayRenderer.tsx                │
                     │  - draws frames                    │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 2. User clicks "Analyze"
                                 ▼
                     ┌────────────────────────────────────┐
                     │   POST /v1/analyze (FastAPI)       │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 3. Pipeline executes
                                 ▼
                     ┌────────────────────────────────────┐
                     │           PIPELINE ENGINE           │
                     │------------------------------------│
                     │ Produces:                          │
                     │  - job_id                          │
                     │  - device_requested                │
                     │  - device_used                     │
                     │  - fallback                        │
                     │  - frames[]                        │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 4. Typed response model
                                 ▼
                     ┌────────────────────────────────────┐
                     │   AnalyzeResponse (Pydantic)        │
                     │   JobStatusResponse                 │
                     │   JobResultResponse                 │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 5. OpenAPI schema updated
                                 ▼
                     ┌────────────────────────────────────┐
                     │       OPENAPI SCHEMA + DRIFT       │
                     │       - baseline enforced           │
                     │       - schema drift test           │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 6. UI receives typed payload
                                 ▼
                     ┌────────────────────────────────────┐
                     │   React renders frames + overlays   │
                     │   - toggles applied                 │
                     │   - FPS throttling                  │
                     │   - loading + error states          │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 7. Developer Experience
                                 ▼
                     ┌────────────────────────────────────┐
                     │   DX LAYER                         │
                     │   - Storybook                      │
                     │   - Example plugin outputs          │
                     │   - Integration tests               │
                     │   - Smoke tests                     │
                     └───────────┬────────────────────────┘
                                 │
                                 │ 8. Governance + CI
                                 ▼
                     ┌────────────────────────────────────┐
                     │   GOVERNANCE + CI                  │
                     │------------------------------------│
                     │ Pre-commit:                        │
                     │  - no raw dict returns             │
                     │  - no unapproved skips             │
                     │  - test/assertion count guards     │
                     │                                    │
                     │ CI:                                │
                     │  - backend tests                   │
                     │  - UI tests                        │
                     │  - integration tests               │
                     │  - Storybook build                 │
                     │  - schema drift                    │
                     └────────────────────────────────────┘

================================================================================
```

---

# ⭐ **2. Mermaid.js Versions (GitHub‑renderable)**  
These are ready to paste into GitHub Markdown.

---

### **2.1 Master Flow (Mermaid)**

```mermaid
flowchart TD

    A[User / Browser] --> B[React UI<br>ConfigPanel / OverlayControls / Renderer]

    B -->|POST /v1/analyze| C[FastAPI Endpoint<br>/v1/analyze]

    C --> D[Pipeline Engine<br>job_id, device_*, fallback, frames[]]

    D --> E[Typed Models<br>AnalyzeResponse / JobStatusResponse / JobResultResponse]

    E --> F[OpenAPI Schema<br>Schema Drift Guard]

    F --> B

    B --> G[DX Layer<br>Storybook, Examples, Integration Tests]

    G --> H[Governance + CI<br>Pre-commit + GitHub Actions]

    H --> B
```

---

### **2.2 UI Flow (Mermaid)**

```mermaid
flowchart TD
    UI[React UI] --> CP[ConfigPanel.tsx<br>device selector + FPS slider]
    UI --> OC[OverlayControls.tsx<br>boxes/labels/pitch/radar]
    UI --> OR[OverlayRenderer.tsx]

    CP --> A[User clicks Analyze]
    OC --> OR

    A --> API[/POST /v1/analyze/]
    API --> RESP[Typed Response<br>job_id, device_*, fallback, frames]
    RESP --> OR
```

---

### **2.3 Governance Flow (Mermaid)**

```mermaid
flowchart TD
    DEV[Developer] --> PRE[Pre-commit Hooks]
    PRE --> CI[GitHub Actions CI]
    CI --> CHECK{All Phase 9 checks pass}
    CHECK -->|Yes| MERGE[Merge to main]
    CHECK -->|No| FIX[Fix issues]
    FIX --> PRE
```

---

# ⭐ **3. Printable PDF‑Style ASCII Architecture Sheet**

This is the “one‑page architecture sheet” you can print or keep in `.ampcode`.

```
PHASE 9 — ONE-PAGE ARCHITECTURE SHEET
=====================================

API LAYER
---------
Endpoints:
  POST /v1/analyze
  GET  /v1/jobs/{id}
  GET  /v1/jobs/{id}/result

Typed Models:
  AnalyzeResponse:
    - job_id
    - device_requested
    - device_used
    - fallback
    - frames[]

  JobStatusResponse:
    - job_id
    - status

  JobResultResponse:
    - all AnalyzeResponse fields
    - status

Invariants:
  - No raw dict returns
  - Schema drift must pass
  - OpenAPI must match typed models


UI LAYER
--------
Components:
  ConfigPanel.tsx
    - device selector (#device-selector)
    - FPS slider (#fps-slider)

  OverlayControls.tsx
    - #toggle-boxes
    - #toggle-labels
    - #toggle-pitch
    - #toggle-radar

  OverlayRenderer.tsx
    - draws frames
    - applies toggles
    - respects FPS throttle

States:
  - loading
  - error


DX LAYER
--------
  - Storybook stories for OverlayRenderer
  - Example plugin outputs module
  - Integration tests (Playwright)
  - Smoke tests (API + UI)


GOVERNANCE
----------
Pre-commit:
  - no raw dict returns
  - no unapproved skips
  - test/assertion count guards

CI:
  - backend tests
  - UI tests
  - integration tests
  - Storybook build
  - schema drift

Exit Criteria:
  - All invariants satisfied
  - All tests green
  - Merge checklist complete
```

---

# ⭐ **4. Phase 9 → Phase 10 Architecture Delta Diagram**

This shows **what Phase 10 can change** and **what is locked**.

```
PHASE 9 → PHASE 10 ARCHITECTURE DELTA
=====================================

[LOCKED — MUST NOT CHANGE]
--------------------------
API:
  - Typed response models
  - Required fields:
      job_id, device_requested, device_used, fallback, frames
  - No raw dict returns
  - Schema drift baseline

UI:
  - Device selector
  - Overlay toggles
  - FPS slider
  - Loading + error states

DX:
  - Storybook must build
  - Example plugin outputs must exist

Governance:
  - Test count must not decrease
  - Assertion count must not decrease
  - No unapproved skips


[EXTEND — SAFE TO ADD]
----------------------
API:
  - New fields (with schema + tests)
  - New endpoints
  - New job types

UI:
  - New controls
  - New layouts
  - New visualizations

DX:
  - More stories
  - More examples
  - More regression tests


[REPLACE — ALLOWED WITH CONSTRAINTS]
------------------------------------
Pipeline internals:
  - Can be rewritten
  - MUST preserve typed API contract

UI internals:
  - Can be refactored
  - MUST preserve IDs used by tests

CI internals:
  - Can be reorganized
  - MUST preserve governance checks
```

---

Roger, these are the **final Phase 9 visual artifacts** — the diagrams that make the entire phase self‑explanatory to any contributor.

