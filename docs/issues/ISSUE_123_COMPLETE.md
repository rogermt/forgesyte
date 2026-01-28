# Issue #123: Reject Invalid Plugins with Explicit Errors

**Status:** COMPLETED ✅

---

## Summary

Implemented strict rejection of invalid plugins with explicit, human-readable error messages. This is a critical architectural requirement for the plugin ecosystem.

Invalid plugins are now rejected at **load time** with clear errors covering:
- ✅ Missing handler
- ✅ Missing description  
- ✅ Missing schemas
- ✅ Non-dict schemas
- ✅ Non-JSON-serializable schemas
- ✅ Duplicate plugin names
- ✅ validate() hook failures
- ✅ Non-BasePlugin subclasses

---

## What Was Changed

### 1. BasePlugin Refactor ✅

**File:** `server/app/plugins/base.py`

Tools must now be metadata dicts with:
- `handler`: callable
- `description`: string
- `input_schema`: dict
- `output_schema`: dict

Contract enforcement validates all fields immediately on instantiation.

**Commit:** `10ebf67`

### 2. PluginRegistry.register() ✅

**File:** `server/app/plugin_loader.py`

Now enforces:
- BasePlugin contract
- Tool metadata structure
- Schema validation (Pydantic ToolSchema)
- JSON-serializability
- Duplicate plugin name detection
- validate() hook error surfacing

**Commit:** `10ebf67`

### 3. ToolSchema Pydantic Model ✅

**File:** `server/app/plugins/schemas.py`

Canonical schema validator ensuring:
- `description: str`
- `input_schema: dict`
- `output_schema: dict`
- No unknown fields (forbid)

**Commit:** `10ebf67`

### 4. Entry-Point Loader Error Surfacing ✅

**File:** `server/app/plugin_loader.py`

Entry-point loader now:
- Catches all exceptions during plugin loading
- Records errors in `errors` dict
- Logs structured error messages
- Returns both `loaded` and `errors` to caller

**Commit:** `10ebf67`

### 5. Regression Tests ✅

**Files:**
- `server/tests/plugins/test_base_plugin_contract.py` (10 tests)
- `server/tests/plugins/test_plugin_schema_validation.py` (6 tests)

Tests cover:
- Valid schemas load successfully
- Missing handler is rejected
- Non-callable handler is rejected
- Missing description is rejected
- Non-string description is rejected
- Missing input_schema is rejected
- Non-dict input_schema is rejected
- Missing output_schema is rejected
- Non-dict output_schema is rejected
- Non-JSON-serializable schemas are rejected

All 16 tests passing.

**Commit:** `10ebf67`

### 6. AGENTS.md Documentation ✅

**File:** `AGENTS.md`

Added pre-commit hook safety guidelines including:
- Exact TEST-CHANGE message format
- How to debug hook failures
- Why bypassing hooks defeats their purpose

**Commit:** `a03ce2c`

---

## Commits

| Hash | Message |
|------|---------|
| `10ebf67` | TEST-CHANGE: refactor BasePlugin tools to metadata dicts and validate schemas |
| `7602e73` | TEST-CHANGE: Merge milestone_1a schema validation |
| `a03ce2c` | docs(agents): Add exact TEST-CHANGE message format |

---

## Testing

All tests passing:

```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/plugins/test_base_plugin_contract.py tests/plugins/test_plugin_schema_validation.py -v
```

Result: **16 passed in 0.13s** ✅

---

## Why This Matters

This guarantees:

1. **`/v1/plugins` always returns valid metadata**  
   Invalid plugins never reach the REST API

2. **MCP manifest generation is safe**  
   All schemas are valid and serializable

3. **Web-UI never receives malformed schemas**  
   Dynamic form generation is guaranteed to work

4. **Plugin authors get immediate feedback**  
   Load-time errors instead of runtime crashes

5. **No invalid plugin can ever be registered**  
   Contract enforcement is non-negotiable

---

## Architecture Impact

### Before
- Tools were `Dict[str, Callable]`
- Invalid plugins could partially load
- Errors surfaced at runtime
- No schema metadata available

### After
- Tools are `Dict[str, Dict[str, Any]]` with required fields
- Invalid plugins rejected at load time
- Clear, structured error messages
- Schema metadata always available
- Full validation pipeline

---

## Next Steps

1. ✅ Migrate OCR plugin to new tools structure
2. ✅ Migrate YOLO plugin to new tools structure
3. ✅ Update API endpoints to use new schema metadata
4. ✅ Update MCP adapter to use new schema metadata
5. ✅ Update Web-UI to use new schema metadata

---

## References

- **Branch:** `milestone_1a`
- **PR:** Merged to `main` (commits 10ebf67, 7602e73, a03ce2c)
- **Issue:** #122 (Schema validation)
- **Related:** Plugin ecosystem architecture
