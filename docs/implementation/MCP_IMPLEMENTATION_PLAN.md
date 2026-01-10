# MCP Adapter Implementation Plan (Issue #11)

**Status**: In Planning  
**Start Date**: TBD  
**Target Completion**: TBD  
**Total Effort**: ~3-4 weeks (5 work units × 3-4 days each)

---

## Overview

This plan breaks down the implementation of the MCP (Model Context Protocol) adapter into small, manageable work units. Each unit produces working, testable code and includes a clear commit strategy.

**Reference**: See `docs/design/MCP.md` for the complete design specification.

---

## Work Units

### WU-01: Core MCP Adapter Implementation (3 days)

**Goal**: Implement the core MCP adapter module with manifest generation

**Deliverables**:
- `server/app/mcp_adapter.py` - Complete MCPAdapter class
- MCP data models (Pydantic models for MCPTool, MCPManifest, MCPServerInfo)
- Plugin metadata to MCP tool conversion logic
- Dynamic manifest generation from plugin registry

**Commits**:
1. `feat: Add MCP data models and MCPAdapter class`
   - MCPTool, MCPManifest, MCPServerInfo Pydantic models
   - Helper functions for metadata conversion
   - Basic MCPAdapter structure

2. `feat: Implement dynamic manifest generation`
   - `build_mcp_manifest()` function
   - Plugin discovery and enumeration
   - Error handling for invalid plugins

**Testing**:
- Unit tests for data models (validation)
- Unit tests for metadata conversion
- Unit tests for manifest building
- Edge cases: empty plugin list, missing metadata fields

**Acceptance Criteria**:
- [ ] MCPAdapter generates valid manifest JSON
- [ ] All Pydantic models validate correctly
- [ ] Plugin discovery finds all loaded plugins
- [ ] Invalid plugins handled gracefully (logged, skipped)
- [ ] Unit tests pass with >80% coverage

---

### WU-02: API Endpoints for MCP (2 days)

**Goal**: Add MCP endpoints to FastAPI application

**Deliverables**:
- `/v1/mcp-manifest` - GET endpoint returns MCP manifest
- `/v1/mcp-version` - GET endpoint returns MCP protocol version
- Integration with existing FastAPI app structure

**Commits**:
1. `feat: Add MCP manifest endpoint to API`
   - `GET /v1/mcp-manifest` endpoint
   - Manifest caching (optional, for performance)
   - Error handling and logging

2. `feat: Add MCP version endpoint`
   - `GET /v1/mcp-version` endpoint
   - Version information response format
   - Future hook for version negotiation

**Testing**:
- Integration tests for manifest endpoint
- Test manifest response format and structure
- Test version endpoint response
- Test error scenarios (500 errors)

**Acceptance Criteria**:
- [ ] `/v1/mcp-manifest` returns valid JSON matching schema
- [ ] `/v1/mcp-version` returns MCP protocol version
- [ ] Both endpoints handle errors gracefully
- [ ] Integration tests pass
- [ ] Endpoints documented in API docs

---

### WU-03: Plugin Metadata Schema & Validation (2 days)

**Goal**: Define and enforce strict plugin metadata schema

**Deliverables**:
- Pydantic `PluginMetadata` model with validation rules
- Schema documentation for plugin developers
- Validation integration in adapter

**Commits**:
1. `feat: Add PluginMetadata schema with validation`
   - Pydantic model defining required fields
   - Field validators (e.g., name format, version semantics)
   - Documentation comments for each field

2. `refactor: Integrate metadata validation in MCP adapter`
   - Update manifest generation to validate all plugin metadata
   - Improve error messages for invalid metadata
   - Log validation failures with details

**Testing**:
- Unit tests for PluginMetadata validation
- Test valid and invalid metadata samples
- Test default value handling
- Test error message clarity

**Acceptance Criteria**:
- [ ] PluginMetadata schema documented
- [ ] All required fields enforced
- [ ] Validation errors provide clear guidance
- [ ] Unit tests cover all validation rules
- [ ] Documentation updated with schema requirements

---

### WU-04: MCP Testing Framework (2-3 days)

**Goal**: Build comprehensive testing script and integration tests

**Deliverables**:
- `server/tests/test_mcp.py` - MCP protocol validation tests
- `server/scripts/test_mcp.py` - Manual testing script
- Integration tests for full MCP flow

**Commits**:
1. `test: Add MCP unit tests`
   - Tests for MCPAdapter functionality
   - Tests for manifest generation
   - Tests for error handling

2. `test: Add MCP integration tests`
   - Test `/v1/mcp-manifest` endpoint
   - Test manifest structure and schema compliance
   - Test tool invocation flow (mock plugins)

3. `feat: Add manual MCP testing script`
   - Script to verify manifest generation
   - Script to test tool discovery
   - Script to verify plugin loading

**Testing**:
- All new tests must pass
- Coverage >85% for MCP modules
- Manual script validates real running server

**Acceptance Criteria**:
- [ ] Unit tests for MCP adapter pass
- [ ] Integration tests for API endpoints pass
- [ ] Manual testing script works correctly
- [ ] Coverage >85% for mcp_adapter.py
- [ ] Test documentation included

---

### WU-05: Gemini Extension Manifest & Documentation (2 days)

**Goal**: Create Gemini extension manifest and complete documentation

**Deliverables**:
- `gemini_extension_manifest.json` - Extension manifest for Gemini-CLI
- MCP configuration documentation
- Version negotiation hook documentation
- Implementation guide for plugin developers

**Commits**:
1. `feat: Add gemini_extension_manifest.json`
   - Static manifest file with server metadata
   - Installation instructions
   - Correct manifest URL configuration

2. `docs: Add MCP integration guide`
   - How to configure Gemini-CLI to use ForgeSyte
   - Plugin metadata requirements
   - Example plugin implementation
   - Troubleshooting guide

3. `feat: Add version negotiation hook`
   - Version constant in MCP adapter
   - Version endpoint documentation
   - Future negotiation strategy documented

**Testing**:
- Manual validation of manifest JSON structure
- Verify Gemini-CLI can load manifest
- Documentation examples are correct

**Acceptance Criteria**:
- [ ] `gemini_extension_manifest.json` valid
- [ ] Manifest contains all required fields
- [ ] MCP integration guide complete
- [ ] Version endpoint ready for future negotiation
- [ ] Documentation examples tested

---

## Commit Strategy

### Branch Naming
- Feature branch: `feature/mcp-adapter`
- Sub-branches for each WU (optional): `feature/mcp-wuXX-name`

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `test`, `docs`, `refactor`, `fix`  
**Scope**: `mcp`, `api`, `plugin`, `test`  

**Examples**:
```
feat(mcp): Add MCPAdapter class and data models
test(mcp): Add unit tests for manifest generation
docs(mcp): Add plugin metadata schema documentation
```

### Pre-commit Hooks
All commits must pass:
- `black` formatting
- `ruff` linting
- `mypy` type checking

### Pull Request Strategy
- One PR per 2-3 work units (don't fragment)
- PR description links to issue #11
- All tests must pass before merge
- Code review required before merge

---

## Dependencies & Prerequisites

**Required Before Starting**:
- [ ] Current plugins implement `metadata()` method
- [ ] FastAPI app structure stable in `server/app/main.py`
- [ ] Plugin manager/loader exists and accessible
- [ ] Test infrastructure set up (pytest, fixtures)

**External Dependencies to Add**:
- None (using existing FastAPI, Pydantic, httpx)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Plugin metadata inconsistent | Schema validation in WU-03 catches early |
| Manifest changes break clients | Version negotiation hook in WU-05 |
| Integration tests fail | Comprehensive test suite in WU-04 |
| Manifest generation slow | Optional caching in WU-02 |
| Missing plugin documentation | Developer guide in WU-05 |

---

## Success Metrics

✅ **Completion Checklist**:
- [ ] All 5 work units completed
- [ ] All commits pass pre-commit hooks
- [ ] All tests pass (>80% coverage)
- [ ] MCP manifest valid and discoverable
- [ ] Gemini-CLI can load ForgeSyte manifest
- [ ] Documentation complete and reviewed
- [ ] Manual testing script validates full flow

---

## Timeline (Estimated)

| WU | Effort | Week | Status |
|----|--------|------|--------|
| WU-01 | 3 days | 1 | Planned |
| WU-02 | 2 days | 1 | Planned |
| WU-03 | 2 days | 2 | Planned |
| WU-04 | 2-3 days | 2 | Planned |
| WU-05 | 2 days | 3 | Planned |
| **Total** | **11-12 days** | **3 weeks** | **Planned** |

---

## Next Steps

1. Review this plan with team
2. Assign work units to developers
3. Create feature branch `feature/mcp-adapter`
4. Begin with WU-01 (Core Adapter Implementation)
5. Update this document as work progresses

---

## Related Issues

- **#11**: Implement MCP adapter and Gemini integration (parent issue)
- **#7**: Code coverage reporting
- **#8**: Coverage enforcement in CI/CD
- **#10**: Comprehensive code coverage strategy
