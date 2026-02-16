# 🔥 **1. fullstack-ci.yml (FINAL VERSION — NO E2E)**  
This workflow handles:

- Backend lint + typecheck + tests  
- Frontend lint + typecheck + tests + build  
- **No E2E**  
- **Does NOT touch your existing ci.yml**  
- Safe to add alongside your existing workflows  

Place in:

```
.github/workflows/fullstack-ci.yml
```

```yaml
name: Fullstack CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend:
    name: Backend CI
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: server

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint
        run: |
          ruff check .
          black --check .

      - name: Type check
        run: mypy app

      - name: Run backend tests
        run: pytest tests --maxfail=1 --disable-warnings

  frontend:
    name: Frontend CI
    runs-on: ubuntu-latest
    needs: backend
    defaults:
      run:
        working-directory: web-ui

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: web-ui/package.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Run frontend tests
        run: npm test -- --run

      - name: Coverage
        run: npm test -- --coverage

      - name: Build frontend
        run: npm run build
```

This is **clean**, **fast**, **safe**, and **Phase‑17 compliant**.

---

# 🔥 **2. e2e-tests.yml (OPTIONAL — ONLY IF YOU WANT AUTOMATED E2E)**  
This workflow:

- Runs **ONLY** when manually triggered  
- Runs your `scripts/run_e2e.sh`  
- Does NOT slow down normal CI  
- Does NOT interfere with your existing ci.yml  

Place in:

```
.github/workflows/e2e-tests.yml
```

```yaml
name: E2E Tests

on:
  workflow_dispatch:   # manual trigger only

jobs:
  e2e:
    name: End-to-End Test Suite
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install backend dependencies
        working-directory: server
        run: pip install -r requirements.txt

      - name: Install frontend dependencies
        working-directory: web-ui
        run: npm ci

      - name: Run E2E tests
        run: bash scripts/run_e2e.sh

      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-logs
          path: logs/
```

This workflow is **completely isolated** from your main CI.

---

# 🔥 **3. Workflow Relationship Diagram**

Here’s the architecture you now have — clean, safe, and scalable:

```
.github/workflows/
│
├── ci.yml                 ← your existing huge CI (KEEP, DO NOT TOUCH)
│
├── fullstack-ci.yml       ← NEW: Phase‑17 backend + frontend CI (NO E2E)
│       ├── backend job
│       └── frontend job (depends on backend)
│
└── e2e-tests.yml          ← OPTIONAL: manual E2E workflow
        └── runs scripts/run_e2e.sh
```

Or visually:

```
                ┌──────────────────────────────┐
                │          ci.yml              │
                │  (existing, >10k lines)      │
                │  DO NOT MODIFY               │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │      fullstack-ci.yml        │
                │  Backend CI → Frontend CI    │
                │  NO E2E                      │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │       e2e-tests.yml          │
                │  OPTIONAL manual workflow     │
                │  Runs scripts/run_e2e.sh      │
                └───────────────────────────────┘
```

This is the **correct**, **safe**, **enterprise‑grade** setup.

---

# ⭐ Final Summary

You now have:

### ✔ `fullstack-ci.yml` — backend + frontend CI (no E2E)  
### ✔ `e2e-tests.yml` — optional manual E2E workflow  
### ✔ A diagram showing how all workflows relate  
### ✔ Zero changes to your existing `ci.yml`  

This is the **final, stable, production‑ready Phase‑17 CI architecture**.
