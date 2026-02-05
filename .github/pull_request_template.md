# Phase 11 Pull Request

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

## ✅ Phase 11 Stability Requirements (MANDATORY)

### Server Tests
**Must run before submitting:**
```bash
cd server && uv run pytest -v
```

- [ ] All server tests pass locally
- [ ] No regressions from Phase 9/10
- [ ] NEW tests added (if applicable)

### Plugin Execution Safety
**Does this touch plugin execution?**

If YES:
- [ ] All plugin calls use `run_plugin_sandboxed()`
- [ ] No direct `plugin.run()` calls
- [ ] `PluginRegistry.mark_failed()` on errors
- [ ] `PluginRegistry.record_success()` on success

### Plugin Registry State
**Is plugin state being updated?**

If YES:
- [ ] `registry.register()` for new plugins
- [ ] `registry.mark_failed()` for failures
- [ ] `registry.mark_unavailable()` for missing deps
- [ ] Success/error counts tracked

### Health API (If applicable)
**Does this touch health endpoints?**

If YES:
- [ ] `/v1/plugins` returns correct state
- [ ] `/v1/plugins/{name}/health` returns correct state
- [ ] Endpoints never return 500
- [ ] Tests verify 200 and 404 only

### Error Messages
**Are error messages clear?**

Test format:
```json
{
  "state": "FAILED",
  "reason": "ImportError: No module named 'torch' (install with: pip install torch)"
}
```

NOT generic "Error".

- [ ] Messages explain what went wrong
- [ ] Messages are actionable (how to fix)
- [ ] FAILED vs UNAVAILABLE used correctly

### VideoTracker (If applicable)
**Does this touch VideoTracker?**

If YES:
- [ ] Manifest includes `requires_gpu: true`
- [ ] Manifest includes `dependencies` list
- [ ] GPU check doesn't crash (marked UNAVAILABLE)
- [ ] Missing models don't crash (marked UNAVAILABLE)

### No Crashes Guarantee
**Can plugins fail gracefully?**

Manual verification:
- [ ] Tested with intentionally broken plugin
- [ ] Server stayed running
- [ ] Health API still accessible
- [ ] Error properly reported

---

## Testing

### Unit Tests
- [ ] NEW code has unit tests
- [ ] Edge cases covered
- [ ] RED tests written before implementation

### Integration Tests
- [ ] ToolRunner sandbox integration verified
- [ ] Health API tested
- [ ] Plugin loader tested with failures

**Test results:**
```
Tests passed: ___
Coverage: ___%
```

---

## Phase 9/10 Compatibility

- [ ] No UI controls broken
- [ ] No realtime messaging broken
- [ ] No video tracker functionality broken

---

## Final Checklist

- [ ] Code follows Phase 11 developer contract
- [ ] Tests pass: `cd server && uv run pytest`
- [ ] Linting: `cd server && uv run ruff check --fix`
- [ ] Type check: `cd server && uv run mypy app/`
- [ ] No console errors or warnings
- [ ] Commit messages clear
- [ ] PR description complete

---

## Related Issues

Closes #___

---

## Deployment

- [ ] Backward compatible
- [ ] No database migrations
- [ ] No config changes needed
- [ ] Safe to roll back

---

**✓ Ready for review when all boxes checked.**
