# Phase 12 — Migration Checklist

## Remove Legacy Execution Paths
- [ ] No direct plugin.run() calls
- [ ] All execution routed through ToolRunner

## Add Execution Governance
- [ ] Input validation implemented
- [ ] Output validation implemented
- [ ] Structured error envelopes added
- [ ] Timing measurement added
- [ ] Registry metric updates added

## Registry
- [ ] success_count increments
- [ ] error_count increments
- [ ] last_execution_time_ms updated
- [ ] avg_execution_time_ms updated
- [ ] last_used updated

## Observability
- [ ] Execution logs added
- [ ] Error logs added
- [ ] Timing logs added

## Tests
- [ ] All Phase 12 RED tests GREEN
- [ ] No Phase 11 regressions

## Documentation
- [ ] Execution-path diagrams updated
- [ ] ToolRunner lifecycle documented
- [ ] Error envelope schema documented
