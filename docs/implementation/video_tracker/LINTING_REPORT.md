# Linting & Type Check Report
Generated: 2026-01-16

## Summary

| Component | Ruff | Mypy | ESLint | TypeScript |
|-----------|------|------|--------|-----------|
| **forgesyte/server** | ✅ PASS | ✅ PASS | N/A | N/A |
| **forgesyte/web-ui** | N/A | N/A | ✅ PASS | ✅ PASS |
| **forgesyte-plugins** | ⚠️ FIXED (4) | ❌ 20 errors | N/A | N/A |

---

## FORGESYTE SERVER

### Ruff ✅
```
All checks passed!
```
- Deprecated config warning (minor): `extend-ignore` → `lint.extend-ignore` in `server/pyproject.toml`

### Mypy ✅
```
Success: no issues found in 23 source files
```

---

## FORGESYTE WEB-UI

### ESLint ✅
No issues found.

### TypeScript (tsc --noEmit) ✅
No issues found.

---

## FORGESYTE-PLUGINS

### Ruff
**Status**: ⚠️ FIXED (4 fixable errors auto-corrected)
```
W292 [*] No newline at end of file (4 instances)
  - plugins/plugin_template/src/forgesyte_plugin_template/plugin.py:118
  - plugins/plugin_template/src/tests/__init__.py:1
  - plugins/plugin_template/src/tests/confest.py:26
  - plugins/plugin_template/src/tests/test_plugin.py:88
```
**Action Taken**: `ruff check --fix` applied.

### Mypy ❌
**Status**: 20 errors across 9 files

#### Category 1: Untyped Decorators (11 errors)
Pytest fixtures lack return type hints
- `plugins/ocr/src/forgesyte_ocr/tests/test_plugin.py:25` - `plugin` fixture
- `plugins/ocr/src/forgesyte_ocr/tests/test_plugin.py:30` - `sample_image_bytes` fixture
- `plugins/ocr/src/forgesyte_ocr/tests/test_plugin.py:38` - `mock_pytesseract_data` fixture
- `plugins/motion_detector/src/tests/test_plugin.py:23` - `plugin` fixture
- `plugins/motion_detector/src/tests/test_plugin.py:28` - `sample_static_image_bytes` fixture
- `plugins/motion_detector/src/tests/test_plugin.py:36` - `sample_high_contrast_motion_image` fixture
- `plugins/moderation/src/tests/test_plugin.py:23` - `plugin` fixture
- `plugins/moderation/src/tests/test_plugin.py:28` - `sample_image_bytes` fixture
- `plugins/moderation/src/tests/test_plugin.py:36` - `unsafe_image_bytes` fixture
- `plugins/block_mapper/src/tests/test_plugin.py:23` - `plugin` fixture
- `plugins/block_mapper/src/tests/test_plugin.py:28` - `sample_image_bytes` fixture
- `plugins/plugin_template/src/tests/test_plugin.py:19` - `plugin` fixture

**Fix**: Add `-> TYPE` return annotation to fixture decorators.

#### Category 2: BaseModel Import Type Issues (9 errors)
Mypy cannot resolve `BaseModel` from pydantic (type inference issue)
- `plugins/ocr/src/forgesyte_ocr/plugin.py:28,48,60` - OCRConfig, OCRResult, OCROptions
- `plugins/motion_detector/src/forgesyte_motion/plugin.py:23,32` - MotionResult, MotionOptions
- `plugins/moderation/src/forgesyte_moderation/plugin.py:30` - ModerationResult
- `plugins/block_mapper/src/forgesyte_block_mapper/plugin.py:29,37` - BlockMapperResult, BlockMapperOptions

**Fix**: Add `# type: ignore[misc]` or ensure pydantic stubs are available (`types-pydantic` package).

---

## Recommendations

### Priority 1 (Required for CI)
1. **Fix pytest decorator type hints** across all plugins:
   ```python
   @pytest.fixture
   def plugin() -> Plugin:  # Add return type
       return Plugin()
   ```

2. **Resolve BaseModel typing** - Either:
   - Install: `uv pip install types-pydantic`
   - Or suppress: `# type: ignore[misc]` on class definitions

### Priority 2 (Maintenance)
- Update `server/pyproject.toml`: Migrate linter config to `[tool.lint]` section
- Add ESLint/TypeScript checks to plugins repo (currently absent)
- Document mypy config in `pyproject.toml` for plugins repo

### Priority 3 (Optional)
- Add `# type: ignore` suppression list to `pyproject.toml` if BaseModel issue persists

---

## Command Reference

Run all checks locally before committing:

**Forgesyte Server**:
```bash
cd server
uv run ruff check .
uv run mypy app/ --no-site-packages
```

**Forgesyte Web-UI**:
```bash
cd web-ui
npm run lint
npm run type-check
```

**Forgesyte-Plugins**:
```bash
uv run ruff check . --fix
uv run mypy plugins/ --no-site-packages
```
