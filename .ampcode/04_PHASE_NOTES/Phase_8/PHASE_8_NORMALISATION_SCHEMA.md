# Canonical Normalisation Schema (Phase 8, Step 3)

## Purpose

All plugin outputs **must normalise** to this canonical schema before:
- Being stored in metrics
- Being rendered as overlays
- Being returned to the UI
- Being passed downstream

This ensures ForgeSyte has **one unified interface** for all plugin types.

---

## Canonical Schema

```json
{
  "frames": [
    {
      "frame_index": 0,
      "boxes": [
        { "x1": 10.0, "y1": 20.0, "x2": 30.0, "y2": 40.0 }
      ],
      "scores": [0.95],
      "labels": ["player"]
    }
  ]
}
```

---

## Field Definitions

### `frames` (required)
- Type: `list[dict]`
- Always present, even for single-frame plugins
- Each frame represents one image/video frame

### `frame_index` (required)
- Type: `int`
- Sequential frame number (0-indexed)
- Used for multi-frame correlation

### `boxes` (required)
- Type: `list[dict]`
- Each box is `{x1, y1, x2, y2}` in absolute pixel coordinates
- `x1, y1`: top-left corner (float)
- `x2, y2`: bottom-right corner (float)
- Must match length of `scores` and `labels`

### `scores` (required)
- Type: `list[float]`
- Confidence scores in range `[0.0, 1.0]`
- Must match length of `boxes` and `labels`

### `labels` (required)
- Type: `list[str]`
- Class/category labels
- Must match length of `boxes` and `scores`

---

## Validation Rules

1. **All required fields must be present**
   - Missing any of `boxes`, `scores`, `labels` → Error
   - Empty lists → Error

2. **Lengths must match**
   - `len(boxes) == len(scores) == len(labels)`
   - Mismatch → Error

3. **Box coordinates**
   - Each box must have exactly 4 values: `[x1, y1, x2, y2]`
   - Invalid number of coords → Error
   - Coords must be numeric (int or float)

4. **Scores**
   - Must be floats
   - Range: `0.0 ≤ score ≤ 1.0`
   - Out-of-range → Error

5. **Labels**
   - Must be strings
   - Cannot be empty strings
   - Any falsy value (None, empty) → Error

---

## Implementation

**File:** `server/app/schemas/normalisation.py`

**Function:** `normalise_output(raw: dict[str, Any]) -> NormalisedOutput`

**Raises:**
- `ValueError` if any validation rule fails

---

## Plugin Integration

Every plugin must call `normalise_output()` before returning:

```python
from app.schemas.normalisation import normalise_output

# Plugin produces output
raw_output = plugin.run(frame)

# Normalise before returning
normalised = normalise_output(raw_output)

return normalised
```

---

## Multi-Frame Support (Future)

Currently supports single-frame plugins. Future versions will:
- Accept list of frames
- Preserve `frame_index` for each
- Validate each frame independently

**Current limitation:** Only frame_index=0 is created (single-frame).

---

## Backwards Compatibility

No existing plugins are breaking changes. All plugins already output `boxes`, `scores`, `labels`.

The normalisation layer simply wraps these in the canonical `frames[]` structure.

---

## Enforcement

- ✅ All tests in `tests/normalisation/` validate the schema
- ✅ CI guardrail (`scripts/ci/test_normalisation_guardrails.py`) enforces schema drift detection
- ✅ Job pipeline must call `normalise_output()` before response
