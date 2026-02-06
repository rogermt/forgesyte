# Phase 12 — Completion Criteria

Phase 12 is complete only when ALL criteria below are satisfied.

---

# 1. Execution Path Criteria

- [ ] All plugin execution flows through ToolRunner.
- [ ] No direct plugin.run() calls exist anywhere in the codebase.
- [ ] Execution timing is measured for every plugin invocation.
- [ ] All exceptions are converted to structured error envelopes.
- [ ] No raw tracebacks appear in API responses.

---

# 2. Input Validation Criteria

- [ ] Empty image bytes rejected.
- [ ] Invalid MIME types rejected.
- [ ] Undecodable payloads rejected.

---

# 3. Output Validation Criteria

- [ ] Plugin output validated before returning.
- [ ] None is rejected.
- [ ] Invalid schema rejected.

---

# 4. Registry Criteria

- [ ] success_count increments on success.
- [ ] error_count increments on failure.
- [ ] last_execution_time_ms updated.
- [ ] avg_execution_time_ms updated.
- [ ] last_used timestamp updated.
- [ ] lifecycle state updated correctly.

---

# 5. Observability Criteria

- [ ] Execution logs emitted.
- [ ] Error logs emitted.
- [ ] Timing logs emitted.

---

# 6. Test Criteria

- [ ] All Phase 12 RED tests pass.
- [ ] No Phase 11 regressions.
- [ ] No API surface changes.

---

# 7. Documentation Criteria

- [ ] Execution-path diagram updated.
- [ ] ToolRunner lifecycle updated.
- [ ] Plugin execution flow updated.

---

# 8. Merge Criteria

- [ ] PR uses PHASE_12_PR_TEMPLATE.md.
- [ ] All invariants satisfied.
- [ ] All reviewers approve.
