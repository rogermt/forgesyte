Roger, you’re building a real governance system here — so let’s give you the **full Phase 12 operational layer**: CI pipeline, pre‑commit hook, GitHub Actions workflow, and a governance README that ties the whole phase together.  

Everything below is **ready to drop into your repo**.  
No fluff. No filler. Just the real thing.

---

# 🚦 **PHASE 12 CI PIPELINE CONFIG**  
*(GitHub Actions — runs tests + scanner + lint)*

```yaml
# .github/workflows/phase12-ci.yml

name: Phase 12 CI

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  phase12-ci:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run Phase 12 Mechanical Scanner
        run: |
          python scripts/scan_phase_12_violations.py

      - name: Run Phase 11 Tests
        run: |
          pytest server/tests/phase_11 --maxfail=1 --disable-warnings

      - name: Run Phase 12 Tests
        run: |
          pytest server/tests/phase_12 --maxfail=1 --disable-warnings
```

This pipeline enforces:

- No direct `plugin.run()` calls  
- ToolRunner invariants  
- Registry metrics invariants  
- Phase 11 backward compatibility  
- Phase 12 correctness  

---

# 🧹 **PRE‑COMMIT HOOK (LOCAL)**  
*(Runs scanner before every commit)*

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running Phase 12 mechanical scanner..."
python scripts/scan_phase_12_violations.py
SCAN_STATUS=$?

if [ $SCAN_STATUS -ne 0 ]; then
  echo "❌ Phase 12 scanner failed. Commit aborted."
  exit 1
fi

echo "✔ Phase 12 scanner passed."
exit 0
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

This prevents ANY commit that violates Phase 12 governance.

---

# 🛠 **GITHUB ACTIONS WORKFLOW (FULL PIPELINE)**  
*(Adds caching + matrix + coverage)*

```yaml
# .github/workflows/phase12-full.yml

name: Phase 12 Full Pipeline

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.10", "3.11" ]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Phase 12 Mechanical Scanner
        run: python scripts/scan_phase_12_violations.py

      - name: Run Phase 11 Tests
        run: pytest server/tests/phase_11 --disable-warnings

      - name: Run Phase 12 Tests
        run: pytest server/tests/phase_12 --disable-warnings

      - name: Upload Coverage
        run: |
          pip install coverage
          coverage run -m pytest
          coverage xml
        continue-on-error: true
```

This is the **production‑grade** CI pipeline.

---

# 📘 **PHASE 12 GOVERNANCE README**  
*(This is the authoritative document for contributors)*

```md
# Phase 12 — Execution Governance & Safety Layer

Phase 12 introduces a governed execution pipeline for all plugins.  
This phase ensures safety, consistency, observability, and backward compatibility.

---

# 1. Execution Path Invariant

All plugin execution MUST follow this path:

API → AnalysisService → JobManagementService → PluginManagementService → ToolRunner → plugin.run()

No other execution path is allowed.

ToolRunner is the **single choke point** for:
- input validation
- output validation
- error wrapping
- lifecycle state
- registry metrics
- execution timing

---

# 2. Validation

## Input Validation
Performed BEFORE plugin execution:
- image must be non-empty
- mime_type must be a valid string

## Output Validation
Performed AFTER plugin execution:
- plugin output must be a dict
- None or non-dict → structured error

---

# 3. Structured Error Envelopes

All exceptions MUST be wrapped in:

```
{
  "error": {
    "type": "...",
    "message": "...",
    "details": {},
    "plugin": "<name>",
    "timestamp": "<iso8601>"
  },
  "_internal": {
    "traceback": "<string>"
  }
}
```

No raw exceptions may escape ToolRunner.

---

# 4. Registry Metrics

After every execution, ToolRunner MUST call:

```
update_execution_metrics(plugin_name, state, elapsed_ms, had_error)
```

Metrics include:
- success_count
- error_count
- last_execution_time_ms
- avg_execution_time_ms
- last_used
- state

---

# 5. Service Layer Rules

## PluginManagementService
- MUST call ToolRunner
- MUST NOT call plugin.run()

## JobManagementService
- MUST call PluginManagementService
- MUST NOT call ToolRunner or plugin.run()

## AnalysisService
- MUST call JobManagementService

---

# 6. API Layer Rules

`/v1/analyze` MUST:
- return structured success
- return structured error via HTTP 400
- never expose raw exceptions

---

# 7. Mechanical Enforcement

The following MUST pass before merging:

- Phase 12 mechanical scanner
- Phase 11 tests
- Phase 12 tests
- CI pipeline

---

# 8. Forbidden Patterns

The following patterns are PROHIBITED:

- `plugin.run(` outside ToolRunner
- try/except around ToolRunner
- returning raw exceptions
- bypassing registry metrics
- bypassing validation

---

# 9. Completion Criteria

Phase 12 is complete when:

- All invariants are enforced mechanically
- All tests pass
- Scanner passes
- CI pipeline passes
- No Phase 11 behavior is broken
```

---

Roger — this is the **full governance layer** for Phase 12.  
You now have:

- ✔ CI pipeline  
- ✔ Pre‑commit hook  
- ✔ GitHub Actions workflow  
- ✔ Governance README  
- ✔ Mechanical scanner  

