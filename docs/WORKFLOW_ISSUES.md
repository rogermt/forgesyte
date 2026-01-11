# Common Issues When Local Workflows Don't Match CI/Production

This document captures common issues discovered during the Python Standards refactoring that may work locally but fail in CI/CD or production environments.

## Issues Found During Refactoring

### 1. LogRecord Reserved Fields Causing KeyError

**Issue**: Using `"message"` as a key in `logger.extra={...}` causes a KeyError at runtime.

```python
# ❌ WRONG - Will cause: KeyError("Attempt to overwrite 'message' in LogRecord")
logger.warning("Transport error", extra={"message": e.message, "code": e.code})

# ✅ CORRECT - Use alternative names
logger.warning("Transport error", extra={"error": e.message, "code": e.code})
```

**Why Local Works But CI Fails**:
- Local testing might not hit the exact logging code path
- CI runs full test suite more thoroughly
- Runtime behavior differs from type checking

**Lesson**: LogRecord has reserved fields that cannot be overwritten:
- `message` (formatted by logging)
- `asctime` (timestamp)
- `levelname` (DEBUG, INFO, etc.)
- `name` (logger name)
- `pathname`, `filename`, `module` (file info)

**Solution**: Use alternative field names:
- Instead of `message`: use `error`, `detail`, `description`
- Instead of `exception`: use `error_type`, `failure`, `exception_info`

---

### 2. Black Formatting Not Applied Before Commit

**Issue**: Code passes all checks locally but black formatting reveals differences in CI.

```bash
# Local: Tests pass, no formatting issues visible
$ uv run pytest server/tests/ -q
# All pass

# CI: Black fails because whitespace wasn't caught
$ black --check .
would reformat server/tests/conftest.py
```

**Why Local Works But CI Fails**:
- Local editor might hide trailing whitespace
- Pre-commit hooks might not be installed
- Running black in check mode reveals issues edit_file doesn't catch

**Lesson**: Always run black before committing:

```bash
# Format all files
uv run black server/app server/tests

# Then verify no changes needed
uv run black --check server/app server/tests
```

**Prevention**:
- Install pre-commit hooks: `uv run pre-commit install`
- Always format files with `create_file` for docstrings (cleaner)
- Run black check in CI before tests

---

### 3. Reserved Fields in Type Ignore Comments

**Issue**: Mypy expects specific error codes but blanket `# type: ignore` gets caught.

```python
# ❌ WRONG - Too broad, mypy may report as unused ignore
from pytesseract import pytesseract  # type: ignore

# ✅ CORRECT - Specific error code
from pytesseract import pytesseract  # type: ignore[import-not-found]
```

**Why Local Works But CI Fails**:
- Local mypy config might be more lenient
- CI mypy config warns on unused type: ignore comments
- Different mypy versions have different rules

**Lesson**: Always use specific error codes in type ignore comments.

Common mypy error codes:
- `[import-not-found]` - Module not found
- `[no-redef]` - Name already defined
- `[assignment]` - Type assignment mismatch
- `[arg-type]` - Wrong argument type
- `[return-value]` - Wrong return type

---

### 4. Test Fixtures Not Properly Isolated

**Issue**: Tests pass locally in isolation but fail when run together in CI.

```bash
# ✅ Local: Run single test file
uv run pytest server/tests/mcp/test_mcp_http_endpoint.py

# ❌ CI: Run full test suite
uv run pytest server/tests/
# Failures due to shared state
```

**Why Local Works But CI Fails**:
- State leaks between test modules
- Fixture scopes not properly set
- Global state not reset between tests
- Different test execution order in CI

**Lesson**: Use proper pytest fixture scopes:

```python
# ❌ WRONG - Session scope causes state leakage
@pytest.fixture(scope="session")
def shared_resource():
    return {}

# ✅ CORRECT - Function scope isolates tests
@pytest.fixture(scope="function")
def isolated_resource():
    return {}

# ✅ BETTER - Class/module scope for related tests
@pytest.fixture(scope="class")
def class_resource():
    return {}
```

---

### 5. Environment Variables Missing in CI

**Issue**: Code works locally with environment setup but fails in CI container.

```python
# ❌ WRONG - Assumes environment variable exists
plugins_dir = os.getenv("FORGESYTE_PLUGINS_DIR")
plugin_manager = PluginManager(plugins_dir)  # None!

# ✅ CORRECT - Provide sensible default
plugins_dir = os.getenv("FORGESYTE_PLUGINS_DIR", "../example_plugins")
plugin_manager = PluginManager(plugins_dir)
```

**Why Local Works But CI Fails**:
- .env file not available in CI container
- CI doesn't load shell environment variables
- Different working directory in CI

**Lesson**: Always provide defaults for optional environment variables.

---

### 6. Absolute vs Relative Path Issues

**Issue**: Code uses relative paths that work locally but fail in CI.

```python
# ❌ WRONG - Relative path breaks if working directory differs
plugins_dir = "./plugins"

# ✅ CORRECT - Use pathlib with explicit resolution
from pathlib import Path
plugins_dir = Path(__file__).parent / "plugins"
```

**Why Local Works But CI Fails**:
- CI runs tests from different directory
- Docker containers have different working directory
- Relative paths change meaning in different contexts

**Lesson**: Use pathlib with `__file__` for relative paths:

```python
from pathlib import Path

# Get directory where this file is located
SCRIPT_DIR = Path(__file__).parent

# Get file relative to script location
PLUGINS_DIR = SCRIPT_DIR / "plugins"

# Ensure path exists
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
```

---

### 7. Async/Await Timing Issues

**Issue**: Async code works locally but times out in CI.

```python
# ❌ WRONG - No timeout, hangs in CI
async def slow_operation():
    await some_external_call()

# ✅ CORRECT - Add explicit timeout
import asyncio

async def reliable_operation():
    try:
        return await asyncio.wait_for(some_external_call(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        raise
```

**Why Local Works But CI Fails**:
- Local machine faster, CI slower
- Local network faster, CI might be remote
- CI has multiple test runs competing for resources

**Lesson**: Always add explicit timeouts for async operations.

---

### 8. Import Order and Circular Dependencies

**Issue**: Import order works locally but fails in CI due to different Python path.

```bash
# ❌ WRONG - Circular import not caught locally
# app/services/__init__.py imports from app.api
# app/api imports from app.services

# ✅ CORRECT - Import from specific modules
from app.services.image_acquisition import ImageAcquisitionService
from app.api.endpoints import create_router
```

**Why Local Works But CI Fails**:
- Python import caching might mask circular imports locally
- Different sys.path in CI containers
- CI removes caches between runs

**Lesson**: Use explicit module imports instead of package imports.

---

### 9. Type Stub Files Missing from Wheel

**Issue**: Types work locally but fail when installed as wheel in CI.

```bash
# Local development: types-Pillow installed
$ pip list | grep types-Pillow
types-Pillow     10.0.0.2

# CI wheel install: might not include dev dependencies
$ pip install dist/forgesyte-0.1.0-py3-none-any.whl
# types-Pillow not installed!
```

**Why Local Works But CI Fails**:
- Development installs include dev dependencies
- Wheel installation only uses main dependencies
- CI doesn't run tests with dev dependencies

**Lesson**: Add type stubs to optional-dependencies for CI:

```toml
[project.optional-dependencies]
types = [
    "types-Pillow==10.0.0.2",
    "types-requests==2.31.0.10",
]
```

---

### 10. Mock Objects Not Matching Production Behavior

**Issue**: Tests pass with mocks but fail with real services in CI integration tests.

```python
# ❌ WRONG - Mock doesn't match real behavior
class MockJobStore:
    async def create(self, plugin_name: str, request_data: dict) -> str:
        return "job-id"  # Always succeeds

# ✅ CORRECT - Mock matches real error behavior
class MockJobStore:
    async def create(self, plugin_name: str, request_data: dict) -> str:
        if not plugin_name:
            raise ValueError("plugin_name required")
        return str(uuid.uuid4())
```

**Why Local Works But CI Fails**:
- Unit tests with mocks pass but don't test real behavior
- Integration tests in CI use real services
- Mocks don't enforce contracts that real services enforce

**Lesson**: Make mocks implement the full Protocol including error cases:

```python
from typing import Protocol, Optional

class JobStore(Protocol):
    async def create(self, plugin_name: str, request_data: dict) -> str: ...

class MockJobStore:
    """Must implement ENTIRE JobStore protocol"""
    async def create(self, plugin_name: str, request_data: dict) -> str:
        if not plugin_name:
            raise ValueError("plugin_name required")
        return str(uuid.uuid4())
```

---

## Checklist for Avoiding CI/Production Issues

Before pushing to CI, verify:

### Code Quality
- [ ] Run `black --check .` to verify formatting
- [ ] Run `ruff check .` to verify linting
- [ ] Run `mypy . --no-site-packages` for type checking
- [ ] Run `pytest` to verify all tests pass

### Configuration
- [ ] Check for hardcoded paths (use pathlib)
- [ ] Check for missing environment variable defaults
- [ ] Check for reserved LogRecord field names
- [ ] Check for circular imports

### Testing
- [ ] Tests pass both individually and together
- [ ] Mocks implement full Protocol interface
- [ ] Async operations have explicit timeouts
- [ ] Fixtures use proper scopes (function, not session)

### Documentation
- [ ] Type hints are 100% complete
- [ ] Type ignore comments have specific error codes
- [ ] Docstrings are complete with Raises sections
- [ ] LogRecord field names are not reserved

### Deployment
- [ ] pyproject.toml has correct dependencies
- [ ] optional-dependencies include types packages
- [ ] Environment variables have sensible defaults
- [ ] Relative paths use pathlib and __file__

---

## Running Pre-Commit Locally

Always run the full pre-commit pipeline before pushing:

```bash
# Install pre-commit hooks (one-time)
uv pip install pre-commit
uv run pre-commit install

# Run all hooks on staged files
git add .
uv run pre-commit run

# Force run on all files
uv run pre-commit run --all-files

# Individual tools
uv run black .
uv run ruff check --fix .
uv run mypy . --no-site-packages
```

---

## Summary

The most common issues when local workflows don't match CI are:

1. **Reserved LogRecord fields** - Use "error" instead of "message"
2. **Black formatting** - Run before commit, always
3. **Test isolation** - Use function scope fixtures, not session
4. **Missing defaults** - Environment variables need fallbacks
5. **Path resolution** - Use pathlib with __file__
6. **Type stubs** - Include in optional-dependencies for CI
7. **Mock behavior** - Must implement full Protocol interface
8. **Async timeouts** - Always add explicit timeouts
9. **Circular imports** - Use explicit module imports
10. **Environment setup** - CI containers don't have .env files

**Key Rule**: What works locally isn't guaranteed to work in CI. Always run the full validation pipeline before pushing.
