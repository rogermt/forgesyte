# Python Standards Refactoring Plan - Issue #12

## Overview

The server codebase has deviations from `PYTHON_STANDARDS.md`. This plan outlines how to bring it into full compliance.

---

## Current State Assessment

### What's Missing

| Standard | Current State | Gap |
|----------|---------------|-----|
| **Separation of Concerns** | Business logic mixed with endpoints | Need service layer abstraction |
| **Protocol-Based Design** | Direct implementation dependencies | Need Protocol interfaces |
| **Retry Pattern** | No retries on external calls | Need `tenacity` for resilience |
| **Structured Logging** | Mix of print and logger | Need consistent logger throughout |
| **Specific Exceptions** | Some generic Exception catches | Need custom exception types |
| **Type Hints** | Incomplete on some functions | Need 100% type coverage |
| **Docstrings** | Missing Raises sections | Need complete Google-style docstrings |
| **Path Management** | Some `os.path` usage | Need `pathlib.Path` everywhere |
| **Health Checks** | Basic endpoint only | Need detailed health check service |
| **Input Validation** | Basic FastAPI validation | Need Pydantic constraints and custom validators |

### Files Needing Refactoring

**Core Application Files:**
- `server/app/__init__.py` - Module initialization
- `server/app/api.py` - REST endpoints (service layer + DI)
- `server/app/auth.py` - AuthService + type hints + logging
- `server/app/main.py` - FastAPI app setup + lifespan manager
- `server/app/models.py` - Pydantic models + field descriptions + validators
- `server/app/plugin_loader.py` - PluginManager + pathlib + logging
- `server/app/tasks.py` - TaskProcessor + exception handling + logging
- `server/app/websocket_manager.py` - ConnectionManager + Pydantic messages + retry logic

**MCP Module Files:**
- `server/app/mcp/__init__.py` - Module exports + docstrings
- `server/app/mcp/adapter.py` - MCPAdapter + type hints + docstrings
- `server/app/mcp/handlers.py` - Request handlers + type hints + logging
- `server/app/mcp/jsonrpc.py` - JSON-RPC protocol + type hints + docstrings
- `server/app/mcp/routes.py` - MCP routes + docstrings + error handling
- `server/app/mcp/transport.py` - HTTP transport + type hints + logging

**Plugin System Files:**
- `server/app/plugins/__init__.py` - Plugin package initialization
- `server/app/plugins/block_mapper/plugin.py` - Plugin implementation + type hints + docstrings
- `server/app/plugins/moderation/plugin.py` - Plugin implementation + type hints + docstrings
- `server/app/plugins/motion_detector/plugin.py` - Plugin implementation + type hints + docstrings
- `server/app/plugins/ocr_plugin/plugin.py` - Plugin implementation + type hints + docstrings

**Server Root Files:**
- `server/__init__.py` - Package initialization
- `server/pyproject.toml` - Dependencies verification
- `server/README.md` - Documentation (no code changes)

---

## Refactoring Strategy

### Approach: Service Layer Pattern

1. **Define abstractions** (Protocols) that endpoints depend on
2. **Extract business logic** from endpoints into service classes
3. **Implement services** with proper error handling, logging, retry logic
4. **Update endpoints** to be thin wrappers using dependency injection
5. **Harden support modules** with type hints, logging, docstrings
6. **Update tests** to work with service layer

### Why This Approach?

- ✅ Aligns with "Separation of Concerns" principle
- ✅ Makes code testable (mock services via Protocols)
- ✅ Reduces endpoint complexity
- ✅ Encapsulates resilience patterns (retries, error handling)
- ✅ Follows established PYTHON_STANDARDS patterns

---

## Work Breakdown

### Phase 1: Foundation & Abstractions (WU-1, WU-2)

**WU-1: Create Protocols & Services (2.5 hours)**
- Create `server/app/protocols.py` with JobStore, TaskProcessor, PluginRegistry
- Create `server/app/services/` package with:
  - ImageAcquisitionService (retry logic, exponential backoff)
  - VisionAnalysisService (image orchestration)
  - HealthCheckService (health monitoring)
- Create `server/app/exceptions.py` with custom exception types

**WU-2: Core Application Files (2 hours)**
- `server/app/__init__.py` - Module initialization + docstrings
- `server/app/models.py` - Complete Pydantic models with field descriptions + validators
- `server/app/main.py` - FastAPI app with lifespan manager + type hints + docstrings

---

### Phase 2: API & Auth Layer (WU-3, WU-4)

**WU-3: API Refactoring (2.5 hours)**
- `server/app/api.py` - Service layer + dependency injection + complete docstrings
- Add all endpoints with thin wrappers (5-10 lines)
- Type hints on all functions
- Structured logging with context

**WU-4: Authentication & Authorization (2 hours)**
- `server/app/auth.py` - AuthService + Pydantic settings + type hints + logging
- Complete docstrings with Raises sections
- Specific exception handling

---

### Phase 3: Task & WebSocket Management (WU-5, WU-6)

**WU-5: Task Processing (2 hours)**
- `server/app/tasks.py` - TaskProcessor service + exception handling + logging
- Type hints throughout
- Complete docstrings
- Add get_result() method per Protocol

**WU-6: WebSocket Management (2 hours)**
- `server/app/websocket_manager.py` - ConnectionManager with Pydantic messages
- Retry logic for message delivery
- Structured logging throughout
- Type hints on all methods

---

### Phase 4: Plugin System (WU-7, WU-8)

**WU-7: Plugin Loader (1.5 hours)**
- `server/app/plugin_loader.py` - pathlib.Path + structured logging + complete docstrings
- Type hints throughout
- Specific exception handling
- Protocol enforcement

**WU-8: Plugin Implementations (1.5 hours)**
- `server/app/plugins/__init__.py` - Package initialization + docstrings
- `server/app/plugins/*/plugin.py` - All 4 plugins:
  - block_mapper, moderation, motion_detector, ocr_plugin
  - Add type hints, docstrings, logging

---

### Phase 5: MCP Module (WU-9, WU-10)

**WU-9: MCP Core (2 hours)**
- `server/app/mcp/__init__.py` - Module exports + docstrings
- `server/app/mcp/jsonrpc.py` - JSON-RPC protocol + type hints + docstrings
- `server/app/mcp/adapter.py` - MCPAdapter + type hints + logging

**WU-10: MCP Routes & Transport (2 hours)**
- `server/app/mcp/handlers.py` - Request handlers + type hints + logging + docstrings
- `server/app/mcp/routes.py` - MCP routes + error handling + docstrings
- `server/app/mcp/transport.py` - HTTP transport + type hints + logging

---

### Phase 6: Server Root & Tests (WU-11, WU-12)

**WU-11: Server Root Files (1 hour)**
- `server/__init__.py` - Package initialization
- `server/pyproject.toml` - Verify dependencies
- `server/README.md` - Update if needed

**WU-12: Test Layer (2 hours)**
- Update `server/tests/conftest.py` - Protocol-compatible mocks
- Update all test files - Mock services instead of implementations
- Add tests for new service classes
- Verify 80%+ coverage maintained

---

### Phase 7: Final Validation (WU-13)

**WU-13: Code Quality Validation (1.5 hours)**
- Run `black` formatting
- Run `ruff` linting
- Run `mypy` type checking
- Run `pytest` with coverage
- Manual review of samples

---

## Total Effort Estimate

| Phase | Work Units | Hours | Notes |
|-------|-----------|-------|-------|
| 1: Foundation & Abstractions | WU-1, WU-2 | 4.5 | Protocols + core files |
| 2: API & Auth Layer | WU-3, WU-4 | 4.5 | API endpoints + authentication |
| 3: Task & WebSocket | WU-5, WU-6 | 4 | Task processing + messaging |
| 4: Plugin System | WU-7, WU-8 | 3 | Plugin loader + implementations |
| 5: MCP Module | WU-9, WU-10 | 4 | JSON-RPC + routes + transport |
| 6: Server Root & Tests | WU-11, WU-12 | 3 | Root files + test fixtures |
| 7: Final Validation | WU-13 | 1.5 | Code quality checks |
| **TOTAL** | **13 WUs** | **~24 hours** | Over 4-5 sessions |

---

## Success Metrics

✅ **Type Safety**: 100% type hints across all server modules
✅ **Logging**: All print statements replaced, structured logging used
✅ **Separation**: No business logic in endpoint functions
✅ **Resilience**: All external API calls use retry pattern
✅ **Documentation**: Complete docstrings with Raises sections
✅ **Path Handling**: pathlib.Path used throughout
✅ **Error Handling**: Specific exception types, no generic catches
✅ **Tests**: All pass, 80%+ coverage
✅ **Linting**: No ruff, black, or mypy errors
✅ **Design**: Protocol-based abstractions, service layer pattern

---

## Implementation Strategy

### Branch Management
- Create feature branch: `refactor/python-standards`
- Each WU = 1 commit
- Push after each WU for checkpoints
- Final PR to main after all WUs complete

### Risk Mitigation
- Each WU is independently testable
- Can pause/resume between WUs
- Easy rollback if issues found
- Existing tests validate throughout

### Knowledge Transfer
- Document patterns used in each WU
- Example implementations guide future code
- Update CONTRIBUTING.md if patterns differ

---

## Dependencies & Blockers

**None identified**. All work is self-contained within server/ codebase.

---

## References

- `docs/development/PYTHON_STANDARDS.md` - Full standards document
- `scratch/refactor_server/app/` - Example implementations
- `AGENTS.md` - Development workflow guidelines
- `ARCHITECTURE.md` - System design context

---

## Approval Checkpoint

**Ready for review and approval.**

Questions for approval:
- ✓ Does this strategy align with your vision?
- ✓ Are the work unit breakdowns appropriate?
- ✓ Should timeline/effort estimates be adjusted?
- ✓ Any additional standards to address?
