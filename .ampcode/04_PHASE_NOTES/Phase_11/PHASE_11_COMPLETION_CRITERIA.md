# Phase 11 Completion Criteria

**The authoritative definition of "Phase 11 DONE".**

When every item below is ✅ TRUE, Phase 11 is complete and ready to merge to main.

---

## ✅ 1. Plugin Loader v2 is Fully Operational

### Checklist

- [ ] Safe import wrapper implemented and tested
- [ ] Safe initialization wrapper implemented and tested
- [ ] Dependency checking operational (packages, GPU, models)
- [ ] GPU capability checking works (torch.cuda.is_available())
- [ ] Lifecycle state transitions correct:
  - [ ] LOADED → INITIALIZED → RUNNING
  - [ ] LOADED → FAILED (on init error)
  - [ ] UNAVAILABLE (missing deps/GPU)

### Verification

```bash
cd server && pytest tests/test_plugin_loader/ -v
# Expected: All tests pass
```

**Criteria:** All import/init failure tests pass

---

## ✅ 2. Sandbox Execution is Enforced Everywhere

### Checklist

- [ ] ToolRunner uses `run_plugin_sandboxed()` for all plugin calls
- [ ] No direct `plugin.run()` calls without sandbox
- [ ] All plugin exceptions caught and structured
- [ ] Plugin lifecycle state updated on failure
- [ ] Success/error counts tracked

### Verification

```bash
# Code scan: No direct plugin.run() without sandbox
grep -r "plugin\.run(" server/app --include="*.py" | \
  grep -v "run_plugin_sandboxed" && exit 1 || true

# Test
cd server && pytest tests/test_tool_runner/test_sandbox_integration.py -v
```

**Criteria:** No plugin crashes, all errors structured

---

## ✅ 3. Plugin Health API is Stable

### Checklist

- [ ] `/v1/plugins` endpoint returns all plugins with state
- [ ] `/v1/plugins/{name}/health` returns detailed state
- [ ] No 500 errors (only 200/404)
- [ ] Failed plugins visible
- [ ] Unavailable plugins visible
- [ ] Response includes success_count, error_count
- [ ] Response includes uptime_seconds, last_used

### Verification

```bash
# Start server
python -m app.main &

# Test list
curl http://localhost:8000/v1/plugins
# Expected: 200, list of plugins with states

# Test detail
curl http://localhost:8000/v1/plugins/ocr/health
# Expected: 200, detailed status

# Test failed plugin
curl http://localhost:8000/v1/plugins/broken_plugin/health
# Expected: 200 (not 500), state: FAILED, reason: "..."

# Test unknown
curl http://localhost:8000/v1/plugins/unknown/health
# Expected: 404 (not 500)
```

**Criteria:** All health endpoints work, no 500s

---

## ✅ 4. VideoTracker is Hardened

### Checklist

- [ ] Manifest includes `requires_gpu: true`
- [ ] Manifest includes `dependencies` list
- [ ] Manifest includes `models` dict
- [ ] Missing GPU → UNAVAILABLE (not crash)
- [ ] Missing models → UNAVAILABLE (not crash)
- [ ] Runtime error → structured error (not crash)
- [ ] All errors have actionable messages

### Verification

```bash
cd server && pytest tests/test_videotracker_stability/ -v
# Expected: All tests pass

# Manual: Intentionally break GPU
# Expected: Server stays running, plugin UNAVAILABLE
```

**Criteria:** VideoTracker fails gracefully under all conditions

---

## ✅ 5. All Phase 11 RED Tests Are GREEN

### Test Coverage

- [ ] **Import Failures** (3 tests)
  - Import error marks FAILED
  - Failed plugin doesn't crash registry
  - Failed plugin not in available list

- [ ] **Init Failures** (2 tests)
  - Init error marks FAILED
  - Error reason captured

- [ ] **Dependency Checking** (6 tests)
  - Missing GPU marks UNAVAILABLE
  - Missing package marks UNAVAILABLE
  - Stdlib packages available
  - Multiple dependencies checked
  - Reason provided

- [ ] **Health API** (8 tests)
  - List returns 200
  - List includes all plugins
  - Detail returns 200
  - Failed plugin detail returns 200
  - Unknown plugin returns 404
  - Metrics included

- [ ] **Sandbox Runner** (6 tests)
  - Success returns ok=true
  - Exception returns ok=false
  - Error type captured
  - Never raises
  - Args preserved
  - Serializable to dict

- [ ] **VideoTracker Stability** (4 tests)
  - Missing GPU doesn't crash
  - Health shows UNAVAILABLE
  - Structured error response
  - Server stays running

### Verification

```bash
cd server && pytest tests/test_plugin_loader/ \
                    tests/test_plugin_health_api/ \
                    tests/test_plugin_sandbox/ \
                    tests/test_videotracker_stability/ \
                    -v --tb=short

# Expected: 40+ tests pass, 0 failures
```

**Criteria:** All 40+ tests pass, 0 failures

---

## ✅ 6. No Regressions in Phase 9 or Phase 10

### Phase 9 Requirements

- [ ] All 16 UI control tests pass
  - DeviceSelector tests
  - FPSSlider tests
  - ErrorBanner tests
  - LoadingSpinner tests

- [ ] All 84 invariants verified
  - Device preference persists
  - FPS preference persists
  - UI controls functional
  - Overlay toggles work

### Phase 10 Requirements

- [ ] All realtime tests pass (31 tests)
  - RealtimeContext state correct
  - RealtimeOverlay renders
  - ProgressBar displays correctly
  - PluginInspector shows timing

- [ ] Job tracking functional
  - Jobs created successfully
  - Job status updated in realtime
  - Realtime messages received

### Verification

```bash
cd web-ui && npm run test -- --run
# Expected: All tests pass

cd server && pytest tests/test_api/test_jobs.py -v
# Expected: All job tests pass

cd server && pytest tests/test_realtime/ -v
# Expected: All realtime tests pass
```

**Criteria:** All Phase 9/10 tests pass, no regressions

---

## ✅ 7. Pre-Commit Governance is Enforced

### Checklist

- [ ] `.pre-commit-config.yaml` includes server-tests hook
- [ ] Pre-commit hook runs `pytest` before commit
- [ ] Hook blocks commit if tests fail
- [ ] `.github/pull_request_template.md` updated
- [ ] PR template requires:
  - [ ] Server tests pass locally
  - [ ] No direct plugin calls
  - [ ] Registry state updated
  - [ ] Health API verified
  - [ ] VideoTracker stable

### Verification

```bash
# Test pre-commit hook
cd server
git add -A
git commit -m "test"  # Should run tests
# If any fail, commit blocked ✓

# Check template
cat .github/pull_request_template.md | grep "Server Tests"
# Should show the checkbox

# Create test PR
gh pr create --draft --title "Phase 11 Test PR"
# Template should auto-populate
```

**Criteria:** Hook enforced, template auto-populated, PRs require compliance

---

## Verification Script

**Run this to verify all criteria:**

```bash
#!/bin/bash
set -e

echo "Phase 11 Completion Verification"
echo "=================================="

# 1. Loader v2
echo "✓ Checking Plugin Loader v2..."
cd server && pytest tests/test_plugin_loader/ -q

# 2. Sandbox
echo "✓ Checking Sandbox Execution..."
cd server && pytest tests/test_tool_runner/ -q

# 3. Health API
echo "✓ Checking Health API..."
cd server && pytest tests/test_plugin_health_api/ -q

# 4. VideoTracker
echo "✓ Checking VideoTracker Stability..."
cd server && pytest tests/test_videotracker_stability/ -q

# 5. RED tests
echo "✓ Checking All Phase 11 Tests..."
cd server && pytest tests/test_plugin_loader/ \
                    tests/test_plugin_health_api/ \
                    tests/test_plugin_sandbox/ \
                    tests/test_videotracker_stability/ -q

# 6. Regressions
echo "✓ Checking Phase 9 Compatibility..."
cd web-ui && npm run test -- --run 2>&1 | grep -q "passed"

echo "✓ Checking Phase 10 Compatibility..."
cd server && pytest tests/test_realtime/ -q

# 7. Governance
echo "✓ Checking Pre-Commit Governance..."
[ -f .pre-commit-config.yaml ] && grep -q "server-tests" .pre-commit-config.yaml
[ -f .github/pull_request_template.md ] && grep -q "Server Tests" .github/pull_request_template.md

echo ""
echo "=================================="
echo "✅ Phase 11 COMPLETE"
echo "=================================="
```

---

## Definition of Done

**Phase 11 is DONE when:**

```
All 7 sections: ✅ COMPLETE
└── 1. Loader v2: ✅ OPERATIONAL
└── 2. Sandbox: ✅ ENFORCED
└── 3. Health API: ✅ STABLE
└── 4. VideoTracker: ✅ HARDENED
└── 5. Tests: ✅ 40+ GREEN
└── 6. Regressions: ✅ ZERO
└── 7. Governance: ✅ ENFORCED
```

**Then:**

```bash
git checkout main
git pull origin main
git merge feature/phase-11-governance
git push origin main
```

---

## Merge Checklist (Final)

Before merging to main:

- [ ] All criteria items verified
- [ ] Verification script passes: `./scripts/verify_phase_11.sh`
- [ ] No Phase 9/10 test failures
- [ ] Health API working
- [ ] VideoTracker stable
- [ ] PR review approved
- [ ] All commits squashed or organized
- [ ] Commit message clear
- [ ] Branch up to date with main

**Once all checked:** Merge to main → Phase 11 is live → Open Phase 12

---

## Post-Merge Actions

1. **Update ROADMAP.md** – Mark Phase 11 complete
2. **Create Phase 12 branch** – `git checkout -b feature/phase-12-orchestration`
3. **Archive Phase 11 branch** – Keep for reference
4. **Notify team** – Phase 11 deployment complete
5. **Update repo docs** – Phase 12 now active

---

**This is the line. When this is ✅, Phase 11 is DONE.**

No ambiguity. No "almost done". Objective criteria. Verifiable. Enforceable.
