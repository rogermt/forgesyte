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

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git status` | Check current branch and changes |
| `git log --oneline -n 10` | View recent commits |
| `git diff` | See unstaged changes |
| `git stash` | Temporarily save changes |
| `source .venv/bin/activate` | Activate Python environment |
| `pytest` | Run tests (if configured) |
