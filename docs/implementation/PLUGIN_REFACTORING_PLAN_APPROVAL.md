# ForgeSyte Plugin Refactoring Plan - TDD Approach

## Objective
Make plugins optional in the ForgeSyte architecture so the server can function without plugins loaded from disk.

## Branch Strategy
- Create feature branch: `feature/wu-26-refactor-plugin-loader`
- Each work unit will have its own focused commit
- Verify functionality after each commit before proceeding

## Commit Strategy (Following TDD)
1. Write failing tests that verify the desired behavior
2. Run tests to confirm they fail (red phase)
3. Make minimal code changes to pass tests (green phase)
4. Refactor if needed while keeping tests passing
5. Run full test suite to ensure no regressions
6. Commit with descriptive message
7. Repeat for next work unit

## Work Units (WU)

### WU-01: Analyze Current Plugin Loading Mechanism
- **Time estimate**: 1 hour
- **Status**: To do
- **Description**: Document all dependencies on plugin loading in the current codebase
- **Deliverable**: Complete dependency analysis
- **Verification**: Complete dependency mapping

### WU-02: Write Unit Tests for PluginManager with Empty State
- **Time estimate**: 1 hour
- **Status**: To do
- **Description**: Create unit tests that verify PluginManager functionality in isolation
- **Tasks**:
  - Create test file: `server/tests/test_plugin_manager_unit.py`
  - Write tests that verify PluginManager initializes with None directory
  - Write tests that verify PluginManager.load_plugins handles None directory
  - Write tests that verify PluginManager operations work with empty plugin set
  - Write tests that verify PluginManager handles missing directories gracefully
  - Run tests to confirm they pass (PluginManager should already handle this)
- **Files to create**: `server/tests/test_plugin_manager_unit.py`
- **Verification**: Unit tests pass, confirming PluginManager works in isolation

### WU-03: Update PluginManager Constructor to Handle None Directory
- **Time estimate**: 1.5 hours
- **Status**: To do
- **Description**: Modify PluginManager to handle when no directory is specified
- **Tasks**:
  - Update PluginManager.__init__ to handle None plugins_dir
  - Update load_plugins() to handle missing directory gracefully
  - Ensure all PluginManager methods work with empty plugin set
- **Files to modify**: `server/app/plugin_loader.py`
- **Verification**: Tests from WU-02 pass for PluginManager operations

### WU-04: Update Server Startup to Handle Empty Plugins
- **Time estimate**: 2 hours
- **Status**: To do
- **Description**: Modify server startup to work when no plugins are loaded
- **Tasks**:
  - Update lifespan function in main.py to work with empty plugin manager
  - Ensure VisionAnalysisService can initialize without plugins
  - Verify all services can start with empty plugin manager
- **Files to modify**: `server/app/main.py`, `server/app/services/`
- **Verification**: Server starts successfully with no plugins

### WU-05: Update Plugin-Related API Endpoints
- **Time estimate**: 1.5 hours
- **Status**: To do
- **Description**: Ensure plugin endpoints handle empty plugin sets gracefully
- **Tasks**:
  - Update GET /v1/plugins to return empty list when no plugins
  - Ensure plugin analysis endpoints handle missing plugins
  - Add proper error handling for missing plugins
- **Files to modify**: `server/app/api.py`, `server/app/services/plugin_management_service.py`
- **Verification**: API endpoints return appropriate responses with no plugins

### WU-06: Update WebSocket Streaming for Empty Plugins
- **Time estimate**: 2 hours
- **Status**: To do
- **Description**: Ensure WebSocket streaming works when no plugins are available
- **Tasks**:
  - Update VisionAnalysisService to handle missing plugins
  - Add default/fallback behavior when no plugins available
  - Ensure WebSocket connection doesn't break without plugins
- **Files to modify**: `server/app/services/vision_analysis_service.py`, `server/app/main.py`
- **Verification**: WebSocket endpoint exists and responds appropriately

### WU-07: Run Full Test Suite
- **Time estimate**: 1 hour
- **Status**: To do
- **Description**: Verify all tests pass after changes
- **Tasks**:
  - Run unit tests
  - Run integration tests
  - Run E2E tests
  - Run linting and type checking
- **Verification**: All tests pass

## Prerequisites for Each Work Unit

### WU-02 Prerequisites
- Complete WU-01
- Understanding of current PluginManager implementation
- Knowledge of PluginInterface protocol

### WU-03 Prerequisites
- Complete WU-02
- Failing tests that demonstrate current dependency on plugins

### WU-04 Prerequisites
- Complete WU-03
- Working PluginManager that doesn't load from disk

### WU-05 Prerequisites
- Complete WU-04
- Server that can start without plugins

### WU-06 Prerequisites
- Complete WU-04
- Server that can start without plugins

### WU-07 Prerequisites
- Complete WU-02 through WU-06
- All changes implemented

## Detailed Commit Messages for Each Work Unit

### WU-02 Commit
```
test(WU-02): add unit tests for PluginManager with empty state

- Add unit tests that verify PluginManager initializes with None directory
- Add unit tests that verify PluginManager.load_plugins handles None directory
- Add unit tests that verify PluginManager operations work with empty plugin set
- Add unit tests that verify PluginManager handles missing directories gracefully
- All tests pass, confirming PluginManager works in isolation
```

### WU-03 Commit
```
feat(WU-03): update PluginManager to handle None directory

- Update PluginManager constructor to handle None plugins_dir
- Update load_plugins() to handle missing directory gracefully
- Ensure all PluginManager methods work with empty plugin set
- Tests from WU-02 now pass for PluginManager operations
```

### WU-04 Commit
```
feat(WU-04): update server startup to handle empty plugins

- Update lifespan function in main.py to work with empty plugin manager
- Ensure VisionAnalysisService can initialize without plugins
- Verify all services can start with empty plugin manager
- Server now starts successfully with no plugins
```

## Success Criteria

1. Server starts successfully without any plugins loaded from disk
2. All existing functionality works when plugins are available
3. Appropriate fallback behavior when plugins are not available
4. All tests pass (unit, integration, E2E)
5. No breaking changes to existing API contracts
6. Plugin endpoints handle empty plugin sets gracefully
7. WebSocket endpoint works appropriately with no plugins

## Dependencies Analysis

### Current Dependencies on Plugin Loading:
1. Server startup (lifespan function in main.py)
2. VisionAnalysisService (requires plugins for frame analysis)
3. PluginManagementService (manages plugin operations)
4. API endpoints (expose plugin functionality)
5. MCP layer (generates tools from plugins)
6. Frontend (expects certain plugins to be available)

### Existing Test Coverage:
1. `tests/plugins/test_plugin_metadata.py` - Tests for PluginMetadata model
2. `tests/services/test_plugin_management_service.py` - Tests for PluginManagementService
3. `tests/mcp/test_mcp_endpoints.py` - Tests for MCP endpoints with empty plugins (test_mcp_manifest_with_empty_plugins, test_mcp_version_with_empty_plugins)
4. Various other integration and API tests

### Gap in Current Implementation:
While there are tests for empty plugins at the API/MCP layer, the core issue is that the server startup process in main.py tries to load plugins from disk during initialization. If the plugin directory doesn't exist or plugins fail to load, the server won't start. The existing tests use mocked plugin managers, but the real server startup still requires the plugin loading mechanism to work.

### Desired State:
1. Server can start without plugins loaded from disk
2. Services gracefully handle empty plugin sets
3. API endpoints return appropriate responses with no plugins
4. MCP layer works with or without plugins
5. Frontend handles empty plugin scenarios gracefully