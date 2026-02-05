# Phase 11 PR Template

**Updated PR template for Phase 11 governance.** Use this for all PRs during Phase 11.

Save as: `.github/pull_request_template.md`

---

```markdown
# Phase 11 PR: [Feature/Fix Description]

## Type
- [ ] Feature
- [ ] Bug Fix
- [ ] Refactor
- [ ] Documentation
- [ ] Test

---

## Summary

Brief description of what this PR does.

---

## Phase 11 Stability Requirements

### ✅ Server Tests (MANDATORY)

**Have you run tests locally?**

```bash
cd server && uv run pytest -v
```

- [ ] All server tests pass
- [ ] No regressions from Phase 9/10
- [ ] NEW tests added for new functionality

**Test coverage:**
- Number of tests added: ___
- Coverage for new code: ___%

### ✅ Plugin Execution Safety

**Does this PR touch plugin execution?**

If YES, verify:
- [ ] All plugin calls use `run_plugin_sandboxed()`
- [ ] No direct `plugin.run()` calls
- [ ] `PluginRegistry.mark_failed()` called on errors
- [ ] `PluginRegistry.record_success()` called on success

**Example:**
```python
# ✗ Not acceptable
result = plugin.run(args)

# ✓ Correct
result = run_plugin_sandboxed(plugin.run, args)
if not result.ok:
    registry.mark_failed(plugin_name, result.error)
```

### ✅ Plugin Registry State

**Is plugin state being updated?**

If YES, verify:
- [ ] Plugins registered with `registry.register()`
- [ ] Failed plugins marked with `registry.mark_failed()`
- [ ] Unavailable plugins marked with `registry.mark_unavailable()`
- [ ] Success/error counts tracked

### ✅ Health API (If applicable)

**Does this touch the health API?**

If YES, verify:
- [ ] `/v1/plugins` returns correct state
- [ ] `/v1/plugins/{name}/health` returns correct state
- [ ] Health endpoints never return 500
- [ ] Tests verify 200 and 404 responses only

### ✅ Error Messages

**Are error messages clear and actionable?**

Test with:
```bash
curl http://localhost:8000/v1/plugins/broken_plugin/health
```

Expected format:
```json
{
  "name": "broken_plugin",
  "state": "FAILED",
  "reason": "ImportError: No module named 'torch' (install with: pip install torch)"
}
```

NOT:
```json
{
  "reason": "Error"
}
```

- [ ] Error messages include what went wrong
- [ ] Error messages are actionable (how to fix)
- [ ] FAILED vs UNAVAILABLE used correctly

### ✅ Thread Safety (If applicable)

**Does this modify shared state?**

If YES, verify:
- [ ] All access protected by locks
- [ ] No race conditions
- [ ] Tests verify concurrent access

**Example:**
```python
# ✗ Not thread-safe
self._plugins[name] = ...

# ✓ Thread-safe
with self._lock:
    self._plugins[name] = ...
```

### ✅ VideoTracker (If applicable)

**Does this touch VideoTracker?**

If YES, verify:
- [ ] Manifest includes `requires_gpu: true`
- [ ] Manifest includes `dependencies` list
- [ ] GPU check doesn't crash (marked UNAVAILABLE instead)
- [ ] Missing models don't crash (marked UNAVAILABLE instead)
- [ ] Tests verify graceful failure scenarios

### ✅ No Crashes Guarantee

**Can you verify that plugins can't crash the server?**

Manual verification:
1. Start server
2. Load plugin that will fail
3. Verify server stays running
4. Verify `/v1/plugins` shows plugin status
5. Verify health API accessible

- [ ] Tested with intentionally broken plugin
- [ ] Server stayed running
- [ ] Health API still accessible
- [ ] Error properly reported (not hidden)

---

## Testing

### Unit Tests
- [ ] All new code has unit tests
- [ ] All edge cases covered
- [ ] RED tests written before implementation

### Integration Tests
- [ ] ToolRunner sandbox integration verified
- [ ] Health API endpoints tested
- [ ] Plugin loader tested with failing plugins

### Manual Testing
- [ ] Tested locally with realistic data
- [ ] Tested failure scenarios
- [ ] Verified no regressions

**Test results:**
```
Tests run: ___
Tests passed: ___
Tests failed: ___
Coverage: ___%
```

---

## Phase 9/10 Compatibility

- [ ] No UI controls broken
- [ ] No realtime messaging broken
- [ ] No video tracker functionality broken
- [ ] Backward compatible with existing plugins

**If breaking change:** Justify below

---

## Checklist

- [ ] Code follows Phase 11 developer contract
- [ ] All tests pass locally (`pytest -v`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] No console errors or warnings
- [ ] Commit messages follow format
- [ ] PR description is clear
- [ ] Screenshots/logs attached (if applicable)

---

## Reviewer Notes

### For Code Reviewers

Check:
1. **Plugin safety**: All plugin calls sandboxed
2. **Error handling**: No unhandled exceptions
3. **State tracking**: Registry state updated correctly
4. **Health API**: Endpoints never return 500
5. **Thread safety**: Shared state protected
6. **Tests**: Comprehensive coverage
7. **Messages**: Clear, actionable error messages

### Automated Checks

This PR will be checked by:
- ✅ Server tests (must pass)
- ✅ Web-UI tests (must pass)
- ✅ Plugin safety scan (no direct plugin.run() calls)
- ✅ Registry state scan (state updated on all paths)
- ✅ Error message scan (no generic "Error" messages)

If any check fails, PR cannot merge.

---

## Related Issues

Closes #___

Related to Phase 11: #___

---

## Additional Context

Any additional information:
- Breaking changes (and why they're necessary)
- Known limitations
- Future work
- Screenshots or logs

---

## Deployment Notes

**For ops/deployment team:**
- [ ] No database migrations needed
- [ ] No config changes needed
- [ ] Backward compatible
- [ ] Safe to roll back

**If NOT backward compatible:**
Explain mitigation strategy below.

---

## Performance Impact

- [ ] No performance impact
- [ ] Minor impact (< 5%)
- [ ] Significant impact (> 5%)

If significant, explain below.

---

## Labels

Add appropriate labels:
- `phase-11`
- `plugin-stability`
- `bug-fix` / `feature` / `refactor`
- `critical` / `high` / `medium` / `low`

---

## Final Checklist

Before submitting:

- [ ] Branch is up to date with main
- [ ] All commits squashed or organized logically
- [ ] Commit messages are descriptive
- [ ] No debugging code left in
- [ ] No console.log/print statements
- [ ] No TODO comments without context
- [ ] All tests passing
- [ ] PR template filled out completely

**Ready for review:** YES / NO

If NO, what needs to be done?

---

## Sign-off

I confirm that:
- ✅ This PR follows the Phase 11 developer contract
- ✅ All server tests pass locally
- ✅ No plugin can crash the server as a result of this code
- ✅ All failures are observable via the health API
- ✅ Error messages are clear and actionable

Signed: _________
Date: _________
```

---

## Using This Template

### Option 1: Copy to Repository

Save the above markdown to `.github/pull_request_template.md` in your repo:

```bash
mkdir -p .github
cat > .github/pull_request_template.md << 'EOF'
# Phase 11 PR: [Feature/Fix Description]
# ... (copy content above)
EOF

git add .github/pull_request_template.md
git commit -m "docs: Add Phase 11 PR template"
```

### Option 2: Reference the Template

Add to GitHub repo settings → Pull Requests:

**Default PR template body:**
```
See PHASE_NOTES/Phase_11/PHASE_11_PR_TEMPLATE.md for required checklist
```

---

## Enforcement

### Pre-submission

- [ ] Run locally: `cd server && uv run pytest`
- [ ] Fill out entire checklist
- [ ] Mark "Ready for review: YES"

### Automated Checks

GitHub Actions will verify:
1. Server tests pass
2. Web-UI tests pass
3. No direct plugin.run() calls (code scan)
4. All error messages actionable (code scan)
5. Thread safety (code analysis)

### Code Review

Reviewers will check:
1. All checklist items verified
2. No plugin execution outside sandbox
3. Registry state updated correctly
4. Health API returns correct status
5. Error messages are clear

### Merge Requirements

✅ **ALL of:**
- [ ] Tests pass
- [ ] Code review approved
- [ ] Checklist complete
- [ ] No Phase 9/10 regressions
- [ ] No unhandled exceptions possible

---

## Example: Good PR

```markdown
# Phase 11 PR: Add plugin timeout guards

## Summary
Add timeout guards to sandbox runner to prevent plugins from hanging indefinitely.

## Phase 11 Stability Requirements

### ✅ Server Tests (MANDATORY)
- [x] All server tests pass
- [x] No regressions from Phase 9/10
- [x] NEW tests added for new functionality

Tests added: 8
Coverage: 94%

### ✅ Plugin Execution Safety
- [x] All plugin calls use `run_plugin_sandboxed()`
- [x] No direct `plugin.run()` calls
- [x] `PluginRegistry.mark_failed()` called on timeout errors
- [x] Timeout errors recorded in registry

### ✅ Plugin Registry State
- [x] Failed plugins marked with timeout reason
- [x] Success/error counts tracked
- [x] Tests verify state transitions

### ✅ Error Messages
- [x] Error messages: "Plugin timeout (exceeded 30s)"
- [x] Actionable for operators
- [x] Clear distinction from other errors

...

Signed: Roger
Date: 2026-02-15
```

---

## Example: Bad PR

```markdown
# Phase 11 PR: Fix VideoTracker issue

## Summary
Fixed some bugs in VideoTracker.

## Phase 11 Stability Requirements

### ✅ Server Tests (MANDATORY)
- [ ] All server tests pass  ← MISSING
- [ ] No regressions from Phase 9/10
- [ ] NEW tests added for new functionality

...

Ready for review: NO

REASON: Tests not run. Must run `pytest` locally first.
```

This PR will be rejected by reviewers.

---

## Key Points

✅ **Always run tests locally first**
```bash
cd server && uv run pytest -v
```

✅ **Always sandbox plugin execution**
```python
result = run_plugin_sandboxed(plugin.run, args)
```

✅ **Always update registry state**
```python
if result.ok:
    registry.record_success(name)
else:
    registry.mark_failed(name, error)
```

✅ **Always use clear error messages**
```python
# ✗ Bad
reason = "Error"

# ✓ Good
reason = "ImportError: No module named 'torch' (install with: pip install torch)"
```

---

**This template enforces Phase 11 governance.**

Follow it exactly. No shortcuts.

**Phase 11 = No plugin crashes server.**
