# Final Streamlined Plan

## Objective
Add the 5 high-value missing tests to achieve comprehensive coverage for the plugin_loader module.

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

## Work Units

### WU-01: Update PluginLoader with Dual-Mode Implementation
- **Time estimate**: 1 hour
- **Status**: Pending
- **Action**: Replace existing plugin_loader.py with dual-mode version from architecture document
- **Purpose**: Enable both entry-point and local plugin loading
- **Implementation**: Replace server/app/plugin_loader.py with the hybrid implementation
- **Commit Message**: 
  ```
  feat(WU-01): implement dual-mode PluginManager with entry-point and local loading
  
  - Replace plugin_loader.py with hybrid implementation supporting both entry-point and local plugins
  - Support entry-point plugins via importlib.metadata.entry_points
  - Support local development plugins via file-based loading
  - Maintain PluginInterface compatibility
  - Enable server to work without plugins loaded from disk
  ```

### WU-02: Write Test for PluginManager with None Directory
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Test**: `test_plugin_manager_with_none_plugins_dir()`
- **Purpose**: Ensures PluginManager handles None cleanly - a real-world scenario
- **Implementation**: Test PluginManager initialization with None plugins_dir parameter
- **Commit Message**:
  ```
  test(WU-02): add test for PluginManager with None directory
  
  - Add test to verify PluginManager handles None plugins_dir gracefully
  - Test load_plugins() behavior with None directory
  - Verify all PluginManager methods work with empty plugin set
  ```

### WU-03: Write Test for PluginManager with Non-existent Directory
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Test**: `test_plugin_manager_with_nonexistent_plugins_dir()`
- **Purpose**: Prevents crashes when someone misconfigures the path
- **Implementation**: Test PluginManager with non-existent directory path
- **Commit Message**:
  ```
  test(WU-03): add test for PluginManager with non-existent directory
  
  - Add test to verify PluginManager handles non-existent plugins_dir gracefully
  - Test load_plugins() behavior with non-existent directory
  - Verify no crashes occur when path is misconfigured
  ```

### WU-04: Write Test for Loading from Empty Directory
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Test**: `test_load_local_plugins_empty_directory()`
- **Purpose**: Ensures the loader doesn't blow up on empty dirs
- **Implementation**: Test load_local_plugins with empty directory
- **Commit Message**:
  ```
  test(WU-04): add test for loading from empty directory
  
  - Add test to verify PluginManager handles empty plugins directory gracefully
  - Test load_local_plugins() behavior with empty directory
  - Verify no errors occur when directory exists but has no plugins
  ```

### WU-05: Write Test for Safe Uninstall of Non-existent Plugin
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Test**: `test_uninstall_plugin_nonexistent()`
- **Purpose**: Ensures uninstall is idempotent and safe
- **Implementation**: Test uninstall_plugin method with non-existent plugin name
- **Commit Message**:
  ```
  test(WU-05): add test for safe uninstall of non-existent plugin
  
  - Add test to verify uninstall_plugin handles non-existent plugins gracefully
  - Test idempotent behavior when uninstalling non-existent plugins
  - Verify no errors occur when plugin doesn't exist
  ```

### WU-06: Write Test for Loading Plugins with No Directory Specified
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Test**: `test_load_plugins_no_directory_specified()`
- **Purpose**: Ensures entry-point loading works even without local plugins
- **Implementation**: Test load_plugins when no directory is specified
- **Commit Message**:
  ```
  test(WU-06): add test for loading plugins with no directory specified
  
  - Add test to verify load_plugins works when no plugins directory specified
  - Test that entry-point plugins still load when local directory is None
  - Verify graceful handling of missing local plugins
  ```

### WU-07: Run Full Test Suite and Verify Coverage
- **Time estimate**: 0.5 hours
- **Status**: Pending
- **Action**: Run all tests (existing + new) and verify coverage reaches 80%+
- **Verification**: Confirm all 5 new tests pass and overall coverage meets target
- **Commit Message**:
  ```
  test(WU-07): verify full test suite and coverage
  
  - Run full test suite to ensure no regressions
  - Verify all new tests pass
  - Confirm coverage meets 80%+ requirement
  ```

## Prerequisites for Each Work Unit

### WU-02 Prerequisites
- Complete WU-01 (updated plugin_loader.py)

### WU-03 Prerequisites
- Complete WU-01 (updated plugin_loader.py)

### WU-04 Prerequisites
- Complete WU-01 (updated plugin_loader.py)

### WU-05 Prerequisites
- Complete WU-01 (updated plugin_loader.py)

### WU-06 Prerequisites
- Complete WU-01 (updated plugin_loader.py)

### WU-07 Prerequisites
- Complete WU-01 through WU-06

## Success Criteria
- PluginLoader updated with dual-mode implementation
- All 5 new high-value tests pass
- Combined test suite achieves 80%+ coverage
- No regressions in existing functionality
- PluginManager handles edge cases gracefully