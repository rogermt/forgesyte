# Agent Commands and Conventions

This document defines standard commands, workflows, and conventions for agents working on the Forgesyte project.

## Git Workflow

### Creating and Merging Branches

```bash
# Create a feature branch
git checkout -b feature-name

# Commit changes
git add .
git commit -m "Description of changes"

# Push to origin
git push origin feature-name

# Merge to main locally, then push
git checkout main
git merge feature-name
git push origin main
```

### Branch Naming

- Feature branches: `feature-name` or `feature/description`
- Bugfix branches: `fix-issue-name`
- Setup/init branches: `init-setup`
- Documentation: `docs-update`

### Important: Never Commit Directly to Main

All changes must go through a feature branch and be merged to main. Direct commits to main are strictly prohibited:

- Always create a feature branch for your work
- Make commits to the feature branch
- Push the feature branch to origin
- Merge to main locally and push after verification
- Never use `git push origin main` to push commits made directly on main

## Project Structure

- `/scratch/` - Temporary files and experiments (ignored in git)
- `/scripts/` - Utility scripts and automation
- `/docs/` - Generated documentation
- Root level docs: `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `PLUGIN_DEVELOPMENT.md`, `BRANDING.md`

## Python Conventions

### Environment

- Use `.venv/` for virtual environment
- Activate: `source .venv/bin/activate`
- Python 3.8+ required
- Use `uv` for running Python and managing dependencies (faster alternative to pip/venv)

### Running Python with uv

```bash
# Run a Python script
uv run script.py

# Run Python with arguments
uv run script.py --arg value

# Create/use virtual environment
uv venv

# Install dependencies
uv pip install package-name

# Sync dependencies from requirements.txt
uv sync
```

### Code Style

- Follow PEP 8
- Use type hints where practical
- Format with `black` (if configured)
- Lint with `ruff` (cache in `.ruff_cache/`)

### Linting and Type Checking

This project enforces strict code quality with automated tools:

**Setup (one-time)**:
```bash
uv pip install pre-commit
uv run pre-commit install
```

**Version pinning** - Versions matter for consistency:
- black==24.1.1
- ruff==0.9.1
- mypy==1.14.0
- types-Pillow (stub package for PIL type hints)

**Workflow before committing**:
1. **Black formatting** - Automatically formats code on commit
   - If files are modified, the commit fails - review changes and commit again
   - Runs automatically via pre-commit hook
2. **Ruff linting** - Checks for code quality issues
   - Run manually: `uv run ruff check --fix .`
   - Auto-fixes most issues (unused imports, trailing whitespace, etc.)
3. **Mypy type checking** - Enforces type safety
   - Run manually: `uv run mypy . --no-site-packages`
   - Use `cast()` from typing module for type inference issues
   - Add `# type: ignore[error-code]` only as last resort

**Common issues and fixes**:
- **"Undefined name" with Optional/Dict** - Add imports: `from typing import Optional, Dict, cast`
- **Generator type errors** - Use `cast(type, value)` for complex type inference
- **Missing type stubs** - Add to `additional_dependencies` in `.pre-commit-config.yaml`
- **Local/remote version mismatch** - Ensure `.pre-commit-config.yaml` versions match requirements-lint.txt

**Running locally before push** (required):
```bash
# Everything runs automatically on commit via pre-commit
# But you can manually run all hooks:
uv run pre-commit run --all-files

# Or individual tools:
uv run black . --exclude original_vision_mcp
uv run ruff check --fix . --exclude original_vision_mcp
uv run mypy . --exclude original_vision_mcp --no-site-packages
```

### Dependencies

- Document in `requirements.txt` or `pyproject.toml`
- Pin major versions for stability
- Use lock files for reproducibility

## File Operations

### Reading Files
- Use `Read` tool for viewing complete files
- Use `Grep` for searching patterns
- Use `finder` for semantic code searches

### Creating/Editing Files
- Use `create_file` when replacing entire file contents
- Use `edit_file` for targeted changes to specific sections
- Always use absolute paths

### Formatting
- Run `format_file` after making large edits
- Respect existing code style

## Testing and Validation

- Run tests before committing: `pytest` or project-specific test command
- Check diagnostics: `get_diagnostics path/to/file`
- Validate git status before pushing

## Test-Driven Development (TDD)

TDD is the required development methodology for this project:

1. **Write tests first** - Before implementing any feature or fix, write failing tests that define the expected behavior
2. **Run and verify failure** - Confirm the tests fail before any implementation
3. **Implement code** - Write minimal code to make the tests pass
4. **Refactor** - Clean up and optimize code while keeping tests passing
5. **Commit after green tests** - Only commit when all tests pass

### Test File Conventions

- Test files: `test_*.py` or `*_test.py` in the same directory as code
- Use `pytest` framework and fixtures for test organization
- Use descriptive test names that explain the behavior being tested
- Aim for high test coverage (80%+ minimum)
- Include unit tests, integration tests, and edge cases

### Best Practices

- Write one assertion per test where possible
- Use fixtures for common test setup
- Mock external dependencies
- Test both success and failure paths
- Keep tests independent and idempotent

## Documentation

- Update relevant `.md` files when making architectural changes
- Keep `ARCHITECTURE.md` current with major changes
- Document new plugins in `PLUGIN_DEVELOPMENT.md`
- Update `CONTRIBUTING.md` if development workflow changes

## Common Issues

### Ignored Directories

The following are intentionally ignored and should not be committed:
- `__pycache__/`
- `.venv/`, `venv/`, `env/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `build/`, `dist/`, `*.egg-info/`
- `scratch/`
- `.vscode/`, `.idea/` (if present locally)

### Before Pushing

1. Verify `git status` is clean or changes are staged
2. Run relevant tests
3. Check for large files (> 100MB shouldn't be committed)
4. Ensure commit messages are descriptive
5. Pull latest changes if merging to main

## Unit Work & Context Management

Large tasks are broken into small work units (1-2 hours each) to respect AI context limits. Each work unit follows this workflow:

### Work Unit Lifecycle

1. **Start Unit**: Read docs/work-tracking/Progress.md to understand current status
2. **Do Work**: Complete the specific tasks for the work unit
3. **Test**: Run verification commands to confirm acceptance criteria
4. **Commit**: Make atomic commit with conventional message (feat:, refactor:, etc.)
5. **Document Learnings**: Update docs/work-tracking/Learnings.md with:
   - What was learned during implementation
   - Unexpected issues encountered
   - Decisions made and rationale
   - Tips for next similar work unit
   - Any blockers or dependencies discovered
6. **Update Progress**: Update docs/work-tracking/Progress.md with:
   - Mark completed unit as done with timestamp
   - Update current context usage
   - Note any blockers or changed estimates
   - List what unit is ready for next session

7. **Thread Boundary**: When context reaches 70-80% usage, the current thread ends
   - Next thread begins with updated Progress.md and Learnings.md as context
   - No need to re-explain completed work
   - Next agent continues from exact point

### Documentation Files

**docs/work-tracking/Progress.md**:
- Current work unit status (in progress, done, blocked, todo)
- Timestamp when each unit started and completed
- Estimated vs actual time spent
- Any blockers or dependencies
- Context usage meter
- Next recommended work unit

**docs/work-tracking/Learnings.md**:
- What was learned in each work unit
- Unexpected issues and solutions
- Code patterns discovered
- Integration points and gotchas
- Tips for future similar work
- Architecture insights

### Progress.md Format

```markdown
# TypeScript Migration Progress

**Last Updated**: [timestamp]
**Current Context Usage**: [50%]
**Overall Progress**: [12/22 units completed]

## Work Unit Status

### Completed
- [x] WU-01: Extract package.json (2 hours, completed [time])
- [x] WU-02: Extract TypeScript config (1.5 hours, completed [time])

### In Progress
- [ ] WU-03: Extract Vite config (45 min elapsed, 0 blockers)

### Blocked
- [ ] WU-15: JobList API integration (blocked on WU-11 completion)

### Todo
- [ ] WU-04: Extract React components
- [ ] WU-05: Extract hooks and API client

## Current Work Unit: WU-03
- **Status**: In Progress
- **Time Elapsed**: 45 minutes
- **Blockers**: None
- **Next Steps**: Extract vite.config.ts and index.html from code2.md

## Notes for Next Session
- WU-03 is 75% complete, needs 15 more minutes
- WU-01 and WU-02 both validated successfully
- No major blockers discovered so far
```

### Learnings.md Format

```markdown
# TypeScript Migration Learnings

## WU-01: Extract package.json

**Completed**: [timestamp]
**Duration**: 30 minutes
**Status**: ✅ Complete

### What Went Well
- Extraction was straightforward
- JSON syntax validation caught no errors
- npm install succeeded on first try

### Challenges & Solutions
- Issue: package-lock.json created, need to ensure node_modules ignored
- Solution: Created comprehensive .gitignore in WU-06

### Key Insights
- ForgeSyte branding should be consistent across all package.json files
- Keep version numbers consistent with backend

### Tips for Similar Work
- Always validate JSON syntax immediately after creation
- Test npm install before proceeding to next dependency-requiring unit

### Blockers Found
- None

---

## WU-02: Extract TypeScript config

**Completed**: [timestamp]
**Duration**: 45 minutes
**Status**: ✅ Complete

### What Went Well
- tsconfig template was well-structured
- Strict mode validation worked immediately

### Challenges & Solutions
- Issue: Had to verify both tsconfig.json and tsconfig.node.json
- Solution: Created clear dependency in WU-03 for Vite config

### Key Insights
- Path aliases need matching in both tsconfig.json and vite.config.ts
- Strict mode catches many issues early

### Tips for Similar Work
- Always test type checking after tsconfig updates
- Verify both tsconfig files are in sync

### Blockers Found
- None
```

### At Work Unit Completion

Before marking a unit done, always:

```bash
# 1. Run verification commands from unit
npm run build        # if applicable
npm run type-check   # if applicable
npm test             # if applicable

# 2. Check git status
git status
git diff

# 3. Create atomic commit
git add .
git commit -m "feat: Complete WU-XX - [description]"

# 4. Update Learnings.md
# Add section for this work unit with:
# - What was learned
# - Unexpected issues
# - Decisions made
# - Tips for similar work
# - Any blockers

# 5. Update Progress.md
# - Mark unit as complete with timestamp
# - Update context usage
# - Note next recommended unit
# - List any changed blockers

# 6. Verify no uncommitted changes
git status  # Should show clean working directory
```

### Context Limit Management

- **Current Thread Limit**: 200k tokens
- **Safe Stopping Point**: 160k tokens (80%)
- **When Approaching Limit**:
  1. Finish current work unit
  2. Make final commit with all changes
  3. Update Progress.md with current status
  4. Update Learnings.md with findings
  5. End thread gracefully

- **Next Thread Start**:
  1. Read Progress.md and Learnings.md first
  2. Continue with next work unit in queue
  3. No re-explanation needed
  4. Build on previously documented learnings

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git status` | Check current branch and changes |
| `git log --oneline -n 10` | View recent commits |
| `git diff` | See unstaged changes |
| `git stash` | Temporarily save changes |
| `source .venv/bin/activate` | Activate Python environment |
| `pytest` | Run tests (if configured) |
