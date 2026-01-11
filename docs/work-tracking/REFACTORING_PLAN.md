# Post-Migration Refactoring & Code Quality Plan

**Status**: In Progress
**Priority**: Before adding new features
**Goal**: Improve test coverage, code quality, maintainability

---

## Phase 1: Fix Failing Tests (0-1 hour)

**Status**: ✅ COMPLETE

**Current**: 311 passing, 0 failing

**Fixed Tests** (Gemini Integration):
- ✅ test_gemini_cli_tools_list_returns_all_plugins
- ✅ test_gemini_cli_tools_have_required_metadata  
- ✅ test_gemini_cli_tools_have_input_output_types
- ✅ test_gemini_cli_full_workflow_sequence

**Issue Fixed**: Tests were expecting old MCPTool format (id, title, inputs, outputs), but tools/list returns new MCP format (name, description, inputSchema). Updated all assertions to match new format.

**Work Done**:
- [x] Update test assertions to match new tools/list response format
- [x] Verify all 311 tests pass

---

## Phase 2: Type Safety & Imports (1-2 hours)

**Current Issues**:
- Missing type stubs for pydantic, fastapi, numpy, PIL, httpx, pytesseract
- websocket_manager has untyped functions
- Plugin implementations lack type hints

**Work**:
- [ ] Add missing type stub packages to requirements
- [ ] Add type hints to websocket_manager
- [ ] Add comprehensive type hints to plugin base classes
- [ ] Run `mypy server/app/ --no-site-packages` - target 100% compliance
- [ ] Document type annotation patterns for future plugins

---

## Phase 3: Test Coverage Analysis (1-2 hours)

**Current**: ~80% estimated coverage

**Priority Areas** (likely gaps):
- [ ] Error handling paths (exception cases)
- [ ] Edge cases in MCP handlers
- [ ] Plugin loader failure scenarios
- [ ] WebSocket disconnect/reconnect
- [ ] API endpoints (job retrieval, status checks)
- [ ] Task processor edge cases

**Work**:
- [ ] Run pytest with coverage: `pytest --cov=server/app server/tests/`
- [ ] Identify files <80% coverage
- [ ] Add missing tests to reach 80%+ overall
- [ ] Document coverage gaps

---

## Phase 4: Code Organization & Clarity (2-3 hours)

**Current Strengths**:
- ✅ Clear separation of concerns (models, adapters, handlers, routes)
- ✅ Good docstrings on major functions
- ✅ Consistent naming conventions

**Improvement Areas**:

### A. MCP Module Organization
- [ ] Consolidate related MCP code (mcp_*, mcp_handlers, mcp_routes, mcp_adapter)
- [ ] Consider: `server/app/mcp/` subdirectory with `__init__.py`, `protocol.py`, `handlers.py`, `routes.py`, `adapter.py`
- [ ] Benefits: Better encapsulation, easier to navigate, clear MCP boundaries

### B. Plugin System Clarity  
- [ ] Document plugin interface (base class contract)
- [ ] Add plugin development checklist
- [ ] Consider: `server/app/plugins/__init__.py` with plugin registry pattern
- [ ] Add plugin validation helpers

### C. WebSocket & Streaming
- [ ] Clarify WebSocket message types and flow
- [ ] Document stream format for real-time analysis
- [ ] Add streaming protocol helpers

### D. Authentication & Authorization
- [ ] Review auth.py for consistency
- [ ] Document API key validation
- [ ] Clarify who validates what (auth.py vs routes)

---

## Phase 5: Documentation Improvements (1 hour)

**Current**: Good README, ARCHITECTURE.md exists

**Work**:
- [ ] Update ARCHITECTURE.md with post-migration structure
- [ ] Add API endpoint documentation (auto-generated from FastAPI)
- [ ] Document MCP protocol implementation
- [ ] Create TESTING.md (how to run tests, coverage targets)
- [ ] Add PLUGIN_DEVELOPMENT.md enhancements with type hints

---

## Phase 6: Performance & Observability (1-2 hours)

**Areas**:
- [ ] Review logging (is everything necessary logged?)
- [ ] Check for n+1 queries or inefficient loops
- [ ] Verify caching is effective (manifest caching)
- [ ] Add performance metrics to slow operations
- [ ] Consider structured logging format

---

## Success Criteria

- ✅ All 311 tests passing
- ✅ 100% mypy compliance (or documented exceptions)
- ✅ 80%+ code coverage
- ✅ No ruff violations
- ✅ Clear, documented code organization
- ✅ Updated architecture documentation

---

## Estimated Timeline

| Phase | Hours | Status |
|-------|-------|--------|
| Phase 1: Fix Tests | 0.25 | ✅ DONE |
| Phase 2: Type Safety | 2 | TODO |
| Phase 3: Coverage | 2 | TODO |
| Phase 4: Organization | 3 | TODO |
| Phase 5: Docs | 1 | TODO |
| Phase 6: Performance | 2 | TODO |
| **Total** | **10.25** | **IN PROGRESS** |

---

## Priority Order

1. **Phase 1** (tests) - Unblock other phases
2. **Phase 2** (types) - Build confidence in codebase
3. **Phase 3** (coverage) - Identify gaps
4. **Phase 4** (org) - Improve maintainability
5. **Phase 5** (docs) - Share knowledge
6. **Phase 6** (perf) - Optimize before scaling
