# ForgeSyte Migration Commit Strategy

## Overview
This document outlines a step-by-step commit strategy to transform the vision-mcp codebase into the ForgeSyte implementation with atomic, testable commits.

## Phase 1: Project Setup and Configuration (Commits 1-3)

### Commit 1: "feat: Initialize ForgeSyte project structure"
- Create new directory structure: `server/`, `example_plugins/`, `web-ui/`
- Move existing server code to `server/app/`
- Create initial `server/pyproject.toml` with basic uv configuration
- Create `docs/design/transformation/` directory for migration docs

### Commit 2: "chore: Add uv configuration and dependencies"
- Complete `pyproject.toml` with all dependencies from requirements.txt
- Add Ruff, pytest, and mypy configurations to pyproject.toml
- Add proper project metadata for ForgeSyte
- Create initial `uv.lock` file

### Commit 3: "refactor: Move plugins to separate example_plugins directory"
- Move all plugins from `server/app/plugins/` to `example_plugins/`
- Update plugin loading logic to look in new location
- Update import paths as needed

## Phase 2: Core Code Transformation (Commits 4-7)

### Commit 4: "feat: Update branding from Vision-MCP to ForgeSyte"
- Change all references from "Vision MCP Server" to "ForgeSyte"
- Update server names in API endpoints and MCP manifest
- Update root endpoint and health check responses
- Update MCP adapter to use "forgesyte" server name

### Commit 5: "refactor: Update environment variables to FORGESYTE_ prefix"
- Replace `VISION_PLUGINS_DIR` with `FORGESYTE_PLUGINS_DIR`
- Replace `VISION_ADMIN_KEY` with `FORGESYTE_ADMIN_KEY`
- Replace `VISION_USER_KEY` with `FORGESYTE_USER_KEY`
- Update all configuration and documentation references

### Commit 6: "refactor: Update API endpoints and documentation"
- Update README.md to reflect ForgeSyte branding and uv workflow
- Update all API examples to use new naming conventions
- Update installation instructions to use uv commands
- Update plugin development documentation

### Commit 7: "test: Add basic tests for transformed codebase"
- Add basic API tests to ensure endpoints still work
- Add plugin loading tests
- Add MCP manifest validation tests
- Ensure all tests pass after transformation

## Phase 3: Advanced Features and Validation (Commits 8-10)

### Commit 8: "feat: Update Docker configuration for uv workflow"
- Create/update Dockerfile to use uv for dependency installation
- Update docker-compose.yml to reflect new structure
- Ensure Docker setup works with new plugin directory structure

### Commit 9: "chore: Add code quality tooling and configurations"
- Add pre-commit hooks if desired
- Update contribution guidelines to reflect new tooling
- Ensure Ruff and type checking pass on all code
- Add proper type hints where missing

### Commit 10: "docs: Update all documentation to reflect ForgeSyte"
- Update ARCHITECTURE.md with current structure
- Update PLUGIN_DEVELOPMENT.md with new paths
- Update CONTRIBUTING.md with uv workflow
- Add any missing documentation for new structure

## Phase 4: Final Validation (Commits 11-12)

### Commit 11: "test: Complete end-to-end validation"
- Run full test suite ensuring everything works
- Test plugin loading from new location
- Test MCP manifest generation
- Test all API endpoints function correctly

### Commit 12: "chore: Final cleanup and optimization"
- Remove any temporary files or unused imports
- Optimize any performance regressions introduced
- Ensure all documentation is consistent
- Update version numbers and release notes

## Best Practices for Each Commit

1. **Atomic Changes**: Each commit should address one specific aspect of the transformation
2. **Test After Each Commit**: Ensure the codebase remains functional after each commit
3. **Clear Messages**: Use conventional commit messages that clearly describe the change
4. **Documentation**: Update relevant documentation in the same commit as the code change
5. **Small Steps**: Keep each commit focused to make rollbacks easier if needed

## Rollback Strategy

If any commit introduces issues:
1. Identify the problematic commit
2. Use `git revert` to undo that specific change
3. Fix the issue before proceeding to the next commit
4. Continue with the transformation once resolved

## Verification Checklist for Each Phase

- [ ] All tests pass
- [ ] Server starts successfully
- [ ] API endpoints respond correctly
- [ ] Plugins load from new location
- [ ] MCP manifest generates correctly
- [ ] Documentation is updated
- [ ] Build system works with uv