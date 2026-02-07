# Phase 12 Governance: Tool Name Contract

## Overview

During Phase 12, a critical regression was identified and fixed: **Issue #164 — OCR plugin fails with "Unknown tool: default"**.

The API was defaulting `tool_name` to the string `"default"`, which is not a valid tool for any plugin. This caused runtime failures.

## Architectural Decision

**The API is now the single source of truth for tool selection.**

- The Web‑UI **never sends** `tool_name`
- The API **always validates** `tool_name` against the plugin manifest
- Plugins **declare tools** in their manifest
- Invalid tool names are **rejected before job creation**

## Governance Rule: Tool Name Contract Enforcement

### Summary

> **The API must never assign a hardcoded or fallback tool name.  
> The only valid source of truth for tool selection is the plugin manifest.  
> No code may introduce fallback tool_name logic.**

### Requirements

#### 1. API Must
- Validate `tool_name` against `plugin.tools`
- Default to the plugin's first tool when none is provided
- Reject invalid tool names **before** job creation
- Never default to `"default"` or any arbitrary string

#### 2. Web‑UI Must
- Never send `tool_name` in analyze requests
- Rely on API for tool selection

#### 3. Plugins Must
- Declare all tools in their manifest
- Reject unknown tool names with clear error messages
- Optionally accept `"default"` as backward-compatible alias (for robustness)

#### 4. CI Must
- Block any reintroduction of `"default"` tool_name logic
- Block any fallback tool_name logic
- Block any job creation with invalid tool_name

### Forbidden Patterns

The following patterns are **strictly forbidden** and detected by the scanner:

```python
# ❌ FORBIDDEN: Hardcoded default
args.get("tool_name", "default")
tool_name = "default"
tool_name = 'default'

# ❌ FORBIDDEN: Fallback logic
tool_name or "default"
tool_name or 'default'

# ❌ FORBIDDEN: If-statement fallbacks
if not tool_name:
    tool_name = "default"
```

### Allowed Patterns

```python
# ✅ ALLOWED: Extract, no default
tool_name = args.get("tool_name")

# ✅ ALLOWED: Validate against manifest
if tool_name and tool_name not in plugin.tools:
    raise ValueError(f"Unknown tool: {tool_name}")

# ✅ ALLOWED: Default to first tool
if not tool_name:
    tool_name = list(plugin.tools.keys())[0]
```

## Enforcement Mechanisms

### 1. Scanner (`scripts/scan_execution_violations.py`)
Automatically blocks PRs that reintroduce forbidden patterns.

### 2. Execution Tests (`tests/execution/`)
- Verify API validates tool_name correctly
- Verify plugins reject unknown tools
- Verify first-tool fallback works

### 3. CI Workflow (`.github/workflows/execution-ci.yml`)
- Runs scanner on every push/PR
- Blocks merge if violations detected
- Runs execution tests as gate

## Incident Report: Issue #164

### What Happened
1. Phase 12 introduced `tool_name = args.get("tool_name", "default")`
2. OCR plugin only recognizes tool `"analyze"`, not `"default"`
3. Jobs failed at runtime with `ValueError: Unknown tool: default`
4. Web‑UI was blocked (critical regression)

### Root Cause
API defaulted to a tool name that doesn't exist in any plugin manifest.

### Fix Applied
1. Removed hardcoded `"default"` from API
2. API now validates against plugin manifest
3. OCR plugin accepts `"default"` as backward-compatible alias
4. Scanner prevents regression

### Impact
- ✅ OCR plugin works again
- ✅ Web‑UI functional
- ✅ Architecture protected forever
- ✅ No future tool_name regressions possible

## Key Learnings

1. **Hardcoded defaults are dangerous** — they break when plugins change
2. **Manifests are the source of truth** — always validate against them
3. **Scanners catch regressions** — mechanical enforcement works
4. **Test the contract** — not just the code

## References

- Issue #164: https://github.com/rogermt/forgesyte/issues/164
- Scanner: `scripts/scan_execution_violations.py`
- Tests: `server/tests/execution/test_*.py`
- CI Workflow: `.github/workflows/execution-ci.yml`
