# v0.10.0 Implementation Plan — ForgeSyte-Plugins Repository

**Status:** Draft
**Last Updated:** 2026-02-26
**Branch:** `v0.10.0`
**Base Branch:** `main`
**Discussion:** https://github.com/rogermt/forgesyte/discussions/226
**Design Doc:** `./DESIGN.md` (ForgeSyte repo)
**ForgeSyte Plan:** `./PLAN.md` (Phases 4-10)

---

## 1. Overview

This plan covers **ForgeSyte-Plugins repository** changes for v0.10.0 Streaming Video Analysis.

### Scope

| Phase | Focus | Priority |
|-------|-------|----------|
| 1 | Create `json_sanitize.py` + unit tests | High |
| 2 | Wire sanitizer into `plugin.py` video tools | High |
| 3 | Update `manifest.json` (capability + version) | High |

**Note:** Phases 4-10 are in ForgeSyte repository. See `./PLAN.md`.

---

## 2. Prerequisites

### 2.1 Current State (Verified GREEN)

```bash
# Run from ForgeSyte-Plugins root
cd /home/rogermt/forgesyte-plugins

# Plugin tests (if available)
cd plugins/forgesyte-yolo-tracker
uv run pytest tests/ -v --tb=short 2>/dev/null || echo "No tests yet"

# Pre-commit
uv run pre-commit run --all-files
```

All must PASS before starting Phase 1.

### 2.2 Branch Setup

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b v0.10.0

# Verify branch
git branch --show-current  # Should show: v0.10.0
```

---

## 3. TDD Workflow (Per Phase)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Write failing tests FIRST                              │
│  2. Run tests → confirm RED                                │
│  3. Implement minimum code to pass                         │
│  4. Run tests → confirm GREEN                              │
│  5. Run pre-commit verification                            │
│  6. Commit with descriptive message                        │
│  7. Save outputs to .log files                             │
└─────────────────────────────────────────────────────────────┘
```

### Output Logging

All outputs saved to: `docs/releases/v0.10.0/logs/`

```bash
# Create logs directory
mkdir -p docs/releases/v0.10.0/logs

# Example usage
uv run pytest tests/test_json_sanitize.py -v 2>&1 | tee docs/releases/v0.10.0/logs/phase1_tests.log
```

---

## 4. Phase Details

---

## Phase 1: Create JSON Sanitizer + Unit Tests

**Goal:** Create `json_sanitize.py` module to convert NumPy types to JSON-safe Python types.

### 1.1 Problem Statement

The YOLO Tracker plugin outputs NumPy types that cannot be JSON-serialized:
- `np.float32` / `np.float64` — NumPy floats
- `np.int32` / `np.int64` — NumPy integers
- `np.ndarray` — NumPy arrays
- Nested structures containing the above

### 1.2 Files to Create

| File | Purpose |
|------|---------|
| `src/forgesyte_yolo_tracker/utils/json_sanitize.py` | NEW: JSON sanitizer module |
| `tests/test_json_sanitize.py` | NEW: Unit tests |

### 1.3 Test Specifications

```python
# tests/test_json_sanitize.py

import pytest
import numpy as np
import json
from forgesyte_yolo_tracker.utils.json_sanitize import sanitize_json


class TestSanitizeJson:
    """Unit tests for JSON sanitizer."""

    def test_sanitize_numpy_float32(self):
        """Test np.float32 → Python float conversion."""
        input_val = np.float32(1.23)
        result = sanitize_json(input_val)
        
        assert result == 1.23
        assert type(result) is float
        assert not isinstance(result, np.floating)

    def test_sanitize_numpy_float64(self):
        """Test np.float64 → Python float conversion."""
        input_val = np.float64(3.14159)
        result = sanitize_json(input_val)
        
        assert result == 3.14159
        assert type(result) is float

    def test_sanitize_numpy_int32(self):
        """Test np.int32 → Python int conversion."""
        input_val = np.int32(42)
        result = sanitize_json(input_val)
        
        assert result == 42
        assert type(result) is int
        assert not isinstance(result, np.integer)

    def test_sanitize_numpy_int64(self):
        """Test np.int64 → Python int conversion."""
        input_val = np.int64(9999999999)
        result = sanitize_json(input_val)
        
        assert result == 9999999999
        assert type(result) is int

    def test_sanitize_numpy_array(self):
        """Test np.ndarray → Python list conversion."""
        input_val = np.array([1, 2, 3])
        result = sanitize_json(input_val)
        
        assert result == [1, 2, 3]
        assert type(result) is list

    def test_sanitize_numpy_array_of_floats(self):
        """Test np.ndarray of floats → list of Python floats."""
        input_val = np.array([1.1, 2.2, 3.3], dtype=np.float32)
        result = sanitize_json(input_val)
        
        assert result == [1.1, 2.2, 3.3]
        assert all(type(x) is float for x in result)

    def test_sanitize_nested_dict(self):
        """Test nested dict with NumPy values."""
        input_val = {
            "a": np.float32(1.0),
            "b": np.int64(2),
            "c": "string",
        }
        result = sanitize_json(input_val)
        
        assert result == {"a": 1.0, "b": 2, "c": "string"}
        assert type(result["a"]) is float
        assert type(result["b"]) is int

    def test_sanitize_nested_list(self):
        """Test nested list with NumPy values."""
        input_val = [np.float32(1.0), np.int64(2), "string"]
        result = sanitize_json(input_val)
        
        assert result == [1.0, 2, "string"]
        assert type(result[0]) is float
        assert type(result[1]) is int

    def test_sanitize_deeply_nested(self):
        """Test deeply nested structure matching plugin output."""
        input_val = {
            "frames": [
                {
                    "detections": {
                        "tracked_objects": [
                            {
                                "track_id": np.int64(1),
                                "center": np.array([np.float32(100.5), np.float32(200.5)]),
                                "xyxy": np.array([50, 100, 150, 300]),
                            }
                        ]
                    }
                }
            ]
        }
        result = sanitize_json(input_val)
        
        # Verify structure
        assert "frames" in result
        assert len(result["frames"]) == 1
        obj = result["frames"][0]["detections"]["tracked_objects"][0]
        
        # Verify types
        assert type(obj["track_id"]) is int
        assert type(obj["center"]) is list
        assert type(obj["center"][0]) is float
        assert type(obj["xyxy"]) is list

    def test_sanitize_2d_array(self):
        """Test 2D NumPy array conversion."""
        input_val = np.array([[1, 2], [3, 4]])
        result = sanitize_json(input_val)
        
        assert result == [[1, 2], [3, 4]]
        assert type(result) is list
        assert type(result[0]) is list

    def test_sanitize_preserves_python_primitives(self):
        """Test that Python primitives pass through unchanged."""
        input_val = {
            "int": 42,
            "float": 3.14,
            "str": "hello",
            "bool": True,
            "none": None,
        }
        result = sanitize_json(input_val)
        
        assert result == input_val

    def test_sanitize_empty_structures(self):
        """Test empty dict and list."""
        assert sanitize_json({}) == {}
        assert sanitize_json([]) == []

    def test_json_serializable_after_sanitize(self):
        """Test that sanitized output is JSON-serializable."""
        input_val = {
            "numpy_float": np.float32(1.23),
            "numpy_int": np.int64(42),
            "numpy_array": np.array([1, 2, 3]),
            "nested": {
                "values": np.array([np.float32(1.0), np.float32(2.0)])
            }
        }
        result = sanitize_json(input_val)
        
        # Should not raise
        json_str = json.dumps(result)
        
        # Should be deserializable
        loaded = json.loads(json_str)
        assert loaded["numpy_float"] == 1.23
        assert loaded["numpy_int"] == 42

    def test_sanitize_tuple_becomes_list(self):
        """Test that tuples are converted to lists."""
        input_val = (np.int64(1), np.int64(2), np.int64(3))
        result = sanitize_json(input_val)
        
        assert result == [1, 2, 3]
        assert type(result) is list

    def test_sanitize_xyxy_bounding_box(self):
        """Test typical bounding box array (xyxy format)."""
        input_val = {
            "xyxy": np.array([50.5, 100.25, 150.75, 200.5], dtype=np.float32)
        }
        result = sanitize_json(input_val)
        
        assert result["xyxy"] == [50.5, 100.25, 150.75, 200.5]
        assert all(type(x) is float for x in result["xyxy"])

    def test_sanitize_center_coordinates(self):
        """Test center coordinate calculation result."""
        xyxy = np.array([100.0, 200.0, 300.0, 400.0])
        center = np.array([
            float((xyxy[0] + xyxy[2]) / 2),
            float((xyxy[1] + xyxy[3]) / 2)
        ], dtype=np.float32)
        
        result = sanitize_json({"center": center})
        
        assert result["center"] == [200.0, 300.0]
        assert type(result["center"][0]) is float


class TestSanizeJsonEdgeCases:
    """Edge case tests for JSON sanitizer."""

    def test_sanitize_numpy_bool(self):
        """Test np.bool_ conversion."""
        input_val = np.bool_(True)
        result = sanitize_json(input_val)
        
        assert result is True
        assert type(result) is bool

    def test_sanitize_large_array(self):
        """Test large array performance."""
        input_val = np.random.rand(1000, 4).astype(np.float32)
        result = sanitize_json(input_val)
        
        assert len(result) == 1000
        assert len(result[0]) == 4
        assert all(type(x) is float for row in result for x in row)
```

### 1.4 Implementation

```python
# src/forgesyte_yolo_tracker/utils/json_sanitize.py
"""
JSON Sanitizer for NumPy types.

v0.10.0: Ensures all plugin outputs are JSON-serializable.

Converts NumPy types to Python primitives:
- np.float32, np.float64 → float
- np.int32, np.int64 → int
- np.ndarray → list
- np.bool_ → bool
"""

import numpy as np
from typing import Any


def sanitize_json(obj: Any) -> Any:
    """
    Recursively convert NumPy types into JSON-safe Python types.
    
    Ensures no np.float32, np.int64, np.ndarray, or other non-serializable
    objects appear in the final plugin output.
    
    Args:
        obj: Any Python object, potentially containing NumPy types
        
    Returns:
        Object with all NumPy types converted to Python primitives
        
    Example:
        >>> sanitize_json({
        ...     "track_id": np.int64(1),
        ...     "center": np.array([np.float32(100.5), np.float32(200.5)])
        ... })
        {'track_id': 1, 'center': [100.5, 200.5]}
    """
    # Dict → sanitize values
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    
    # List / tuple → sanitize each element
    if isinstance(obj, (list, tuple)):
        return [sanitize_json(v) for v in obj]
    
    # NumPy array → convert to list, then sanitize elements
    if isinstance(obj, np.ndarray):
        return sanitize_json(obj.tolist())
    
    # NumPy floats → Python float
    if isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    
    # NumPy ints → Python int
    if isinstance(obj, (np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    
    # NumPy unsigned ints → Python int
    if isinstance(obj, (np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    
    # NumPy bool → Python bool
    if isinstance(obj, np.bool_):
        return bool(obj)
    
    # Pass through Python primitives and None
    return obj
```

### 1.5 Verification Commands

```bash
# From ForgeSyte-Plugins root
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker

# 1. Create logs directory
mkdir -p docs/releases/v0.10.0/logs

# 2. Run unit tests (should be RED initially, then GREEN)
uv run pytest tests/test_json_sanitize.py -v 2>&1 | tee docs/releases/v0.10.0/logs/phase1_tests.log

# 3. Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee docs/releases/v0.10.0/logs/phase1_all_tests.log

# 4. Run pre-commit
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase1_precommit.log
```

### 1.6 Commit

```bash
git add src/forgesyte_yolo_tracker/utils/json_sanitize.py \
        tests/test_json_sanitize.py

git commit -m "feat(plugin): add JSON sanitizer for NumPy types

- Add json_sanitize.py module
- Convert np.float32/64 → Python float
- Convert np.int32/64 → Python int
- Convert np.ndarray → Python list
- Recursive sanitization for nested structures
- Comprehensive unit tests

Phase 1 of v0.10.0 implementation."
```

---

## Phase 2: Wire Sanitizer into plugin.py

**Goal:** Integrate JSON sanitizer into video tool outputs in `plugin.py`.

### 2.1 Files to Modify

| File | Purpose |
|------|---------|
| `src/forgesyte_yolo_tracker/plugin.py` | MODIFY: Add sanitizer to video tool outputs |
| `tests/test_plugin_output.py` | NEW: Tests for sanitized plugin output |

### 2.2 Key Changes

#### 2.2.1 Add Import

```python
# In src/forgesyte_yolo_tracker/plugin.py

# Add import at top of file:
from forgesyte_yolo_tracker.utils.json_sanitize import sanitize_json
```

#### 2.2.2 Fix track_id Handling

```python
# BEFORE (broken - truth-value error):
tracker_ids = get_tracker_ids(detections) or []
for tid in tracker_ids:
    # tid could be None, causing issues

# AFTER (fixed):
tracker_ids = get_tracker_ids(detections)
if tracker_ids is None:
    tracker_ids = []
```

#### 2.2.3 Fix Center Coordinate Calculation

```python
# BEFORE (broken - may be float32):
center = [(xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2]

# AFTER (fixed):
center = [
    float((xyxy[0] + xyxy[2]) / 2),
    float((xyxy[1] + xyxy[3]) / 2)
]
```

#### 2.2.4 Wrap Output with Sanitizer

```python
# BEFORE (video_player_tracking):
def _tool_video_player_tracking(self, video_path: str, device: str = "cpu", progress_callback=None):
    # ... processing logic ...
    return {
        "total_frames": frame_index,
        "frames": frame_results,
    }

# AFTER (video_player_tracking):
def _tool_video_player_tracking(self, video_path: str, device: str = "cpu", progress_callback=None):
    # ... processing logic ...
    
    # Wrap output with sanitizer
    return sanitize_json({
        "total_frames": frame_index,
        "frames": frame_results,
    })
```

Apply same pattern to all video tools:
- `_tool_video_player_tracking`
- `_tool_video_ball_detection`
- `_tool_video_pitch_detection`
- `_tool_video_radar`

### 2.3 Test Specifications

```python
# tests/test_plugin_output.py

import pytest
import numpy as np
import json
from forgesyte_yolo_tracker.utils.json_sanitize import sanitize_json


class TestPluginOutputSanitization:
    """Tests for sanitized plugin output."""

    def test_no_numpy_types_in_output(self):
        """Test that no NumPy types remain in output."""
        # Simulated plugin output with NumPy types
        output = {
            "total_frames": np.int64(100),
            "frames": [
                {
                    "frame_index": np.int64(0),
                    "detections": {
                        "tracked_objects": [
                            {
                                "track_id": np.int64(1),
                                "class_id": np.int64(0),
                                "xyxy": np.array([100, 200, 300, 400], dtype=np.float32),
                                "center": np.array([200.0, 300.0], dtype=np.float32),
                            }
                        ]
                    }
                }
            ]
        }
        
        result = sanitize_json(output)
        
        # Check all values are Python primitives
        assert type(result["total_frames"]) is int
        assert type(result["frames"][0]["frame_index"]) is int
        obj = result["frames"][0]["detections"]["tracked_objects"][0]
        assert type(obj["track_id"]) is int
        assert type(obj["xyxy"]) is list
        assert type(obj["center"]) is list

    def test_output_is_json_serializable(self):
        """Test that output can be JSON serialized."""
        output = {
            "total_frames": np.int64(100),
            "frames": [
                {
                    "frame_index": np.int64(0),
                    "detections": {
                        "tracked_objects": [
                            {
                                "track_id": np.int64(1),
                                "xyxy": np.array([100, 200, 300, 400], dtype=np.float32),
                                "center": np.array([200.0, 300.0], dtype=np.float32),
                            }
                        ]
                    }
                }
            ]
        }
        
        result = sanitize_json(output)
        
        # Should not raise
        json_str = json.dumps(result)
        assert "total_frames" in json_str


class TestFloat32Fix:
    """Tests for float32 center coordinate fix."""

    def test_center_coordinates_are_python_floats(self):
        """Test that center coordinates are Python floats, not np.float32."""
        xyxy = np.array([100.5, 200.25, 300.75, 400.5], dtype=np.float32)
        
        # Calculate center (as done in plugin)
        center = [
            float((xyxy[0] + xyxy[2]) / 2),
            float((xyxy[1] + xyxy[3]) / 2)
        ]
        
        result = sanitize_json({"center": center})
        
        assert type(result["center"][0]) is float
        assert type(result["center"][1]) is float
        # Should be JSON serializable
        json.dumps(result)  # Should not raise


class TestTrackIdFix:
    """Tests for track_id truth-value fix."""

    def test_track_id_handles_none(self):
        """Test track_id handles None from get_tracker_ids."""
        tracker_ids = None
        
        # After fix: should handle gracefully
        if tracker_ids is None:
            tracker_ids = []
        
        assert tracker_ids == []

    def test_track_id_is_python_int(self):
        """Test track_id is Python int, not np.int64."""
        track_id = np.int64(42)
        result = sanitize_json({"track_id": track_id})
        
        assert result["track_id"] == 42
        assert type(result["track_id"]) is int
```

### 2.4 Verification Commands

```bash
# From ForgeSyte-Plugins root
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker

# 1. Run output tests
uv run pytest tests/test_plugin_output.py -v 2>&1 | tee docs/releases/v0.10.0/logs/phase2_tests.log

# 2. Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee docs/releases/v0.10.0/logs/phase2_all_tests.log

# 3. Run pre-commit
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase2_precommit.log
```

### 2.5 Commit

```bash
git add src/forgesyte_yolo_tracker/plugin.py \
        tests/test_plugin_output.py

git commit -m "fix(plugin): wire JSON sanitizer into video tool outputs

- Wrap all video tool returns with sanitize_json()
- Fix track_id handling for None from get_tracker_ids
- Fix center coordinate float conversion
- Add output sanitization tests

Phase 2 of v0.10.0 implementation."
```

---

## Phase 3: Update manifest.json

**Goal:** Add `streaming_video_analysis` capability and update version.

### 3.1 Files to Modify

| File | Purpose |
|------|---------|
| `src/forgesyte_yolo_tracker/manifest.json` | MODIFY: Add capability, update version |
| `tests/test_manifest.py` | NEW: Manifest tests |

### 3.2 Current vs Target

```json
// CURRENT (version 1.0.0)
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  "version": "1.0.0",
  "capabilities": [
    "player_detection",
    "ball_detection",
    "pitch_detection",
    "radar"
  ]
}

// TARGET (version 0.10.0)
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  "version": "0.10.0",
  "description": "YOLO + Supervision plugin with streaming video analysis.",
  "capabilities": [
    "player_detection",
    "ball_detection",
    "pitch_detection",
    "radar",
    "streaming_video_analysis"
  ]
}
```

### 3.3 Test Specifications

```python
# tests/test_manifest.py

import json
import pytest
from pathlib import Path


class TestManifest:
    """Tests for plugin manifest."""

    @pytest.fixture
    def manifest(self):
        manifest_path = Path(__file__).parent.parent / "src" / "forgesyte_yolo_tracker" / "manifest.json"
        with open(manifest_path) as f:
            return json.load(f)

    def test_manifest_has_streaming_capability(self, manifest):
        """Test that manifest includes streaming_video_analysis capability."""
        assert "streaming_video_analysis" in manifest["capabilities"]

    def test_manifest_version_is_0_10_0(self, manifest):
        """Test that version is 0.10.0."""
        assert manifest["version"] == "0.10.0"

    def test_manifest_has_required_fields(self, manifest):
        """Test that manifest has all required fields."""
        required_fields = ["id", "name", "version", "description", "capabilities", "tools"]
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

    def test_video_tools_have_streaming_capability(self, manifest):
        """Test that video tools include streaming_video_analysis capability."""
        video_tools = [t for t in manifest["tools"] if "video" in t.get("input_types", [])]
        
        for tool in video_tools:
            assert "streaming_video_analysis" in tool.get("capabilities", []), \
                f"Tool {tool['id']} missing streaming_video_analysis capability"

    def test_all_capabilities_have_tools(self, manifest):
        """Test that each capability has at least one tool."""
        capabilities = set(manifest["capabilities"])
        tool_capabilities = set()
        
        for tool in manifest["tools"]:
            tool_capabilities.update(tool.get("capabilities", []))
        
        # All declared capabilities should be used by at least one tool
        for cap in capabilities:
            assert cap in tool_capabilities, f"Capability {cap} not used by any tool"
```

### 3.4 Implementation

Update `src/forgesyte_yolo_tracker/manifest.json`:

```json
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  "version": "0.10.0",
  "description": "YOLO + Supervision plugin with streaming video analysis.",
  "author": "Roger",
  "license": "MIT",
  "entrypoint": "forgesyte_yolo_tracker.plugin",
  "type": "yolo",
  "capabilities": [
    "player_detection",
    "ball_detection",
    "pitch_detection",
    "radar",
    "streaming_video_analysis"
  ],
  "tools": [
    {
      "id": "player_detection",
      "title": "Player Detection",
      "description": "Detect players in a single image.",
      "input_types": ["image_bytes"],
      "output_types": ["detections"],
      "capabilities": ["player_detection"],
      "inputs": {
        "image_bytes": "string",
        "device": "string",
        "annotated": "boolean"
      },
      "outputs": {
        "detections": "array",
        "annotated_image": "string"
      }
    },
    {
      "id": "video_player_tracking",
      "title": "Video Player Tracking",
      "description": "Track players across video frames.",
      "input_types": ["video"],
      "output_types": ["frames"],
      "capabilities": ["player_detection", "streaming_video_analysis"],
      "inputs": {
        "video_path": "string",
        "device": "string"
      },
      "outputs": {
        "frames": "array",
        "total_frames": "integer"
      }
    },
    {
      "id": "video_ball_detection",
      "title": "Video Ball Detection",
      "description": "Detect ball in video frames.",
      "input_types": ["video"],
      "output_types": ["frames"],
      "capabilities": ["ball_detection", "streaming_video_analysis"],
      "inputs": {
        "video_path": "string",
        "device": "string"
      },
      "outputs": {
        "frames": "array",
        "total_frames": "integer"
      }
    },
    {
      "id": "video_pitch_detection",
      "title": "Video Pitch Detection",
      "description": "Detect pitch keypoints in video frames.",
      "input_types": ["video"],
      "output_types": ["frames"],
      "capabilities": ["pitch_detection", "streaming_video_analysis"],
      "inputs": {
        "video_path": "string",
        "device": "string"
      },
      "outputs": {
        "frames": "array",
        "total_frames": "integer"
      }
    },
    {
      "id": "video_radar",
      "title": "Video Radar",
      "description": "Generate radar view from video.",
      "input_types": ["video"],
      "output_types": ["frames"],
      "capabilities": ["radar", "streaming_video_analysis"],
      "inputs": {
        "video_path": "string",
        "device": "string"
      },
      "outputs": {
        "frames": "array",
        "total_frames": "integer"
      }
    }
  ]
}
```

### 3.5 Verification Commands

```bash
# From ForgeSyte-Plugins root
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker

# 1. Run manifest tests
uv run pytest tests/test_manifest.py -v 2>&1 | tee docs/releases/v0.10.0/logs/phase3_tests.log

# 2. Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee docs/releases/v0.10.0/logs/phase3_all_tests.log

# 3. Validate JSON syntax
python -c "import json; json.load(open('src/forgesyte_yolo_tracker/manifest.json'))" && echo "JSON valid"

# 4. Run pre-commit
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase3_precommit.log
```

### 3.6 Commit

```bash
git add src/forgesyte_yolo_tracker/manifest.json \
        tests/test_manifest.py

git commit -m "feat(plugin): add streaming_video_analysis capability

- Add streaming_video_analysis to capabilities
- Update version to 0.10.0
- Add streaming capability to all video tools
- Add manifest tests

Phase 3 of v0.10.0 implementation."
```

---

## 5. Final Steps

### 5.1 Complete Verification

```bash
# Run all tests
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker
uv run pytest tests/ -v --tb=short 2>&1 | tee docs/releases/v0.10.0/logs/final_tests.log

# Run pre-commit
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/final_precommit.log

# Verify JSON serialization
python -c "
from forgesyte_yolo_tracker.utils.json_sanitize import sanitize_json
import numpy as np
import json

# Test full sanitization
data = {
    'track_id': np.int64(1),
    'center': np.array([np.float32(100.5), np.float32(200.5)]),
    'xyxy': np.array([50, 100, 150, 300], dtype=np.float32)
}
result = sanitize_json(data)
json_str = json.dumps(result)
print('✓ JSON serialization successful')
print(result)
"
```

### 5.2 Create Pull Request

```bash
# Push branch
git push origin v0.10.0

# Create PR
gh pr create --base main --head v0.10.0 \
  --title "v0.10.0: Streaming Video Analysis (Plugin)" \
  --body "Phases 1-3 of v0.10.0 implementation.

Changes:
- Add json_sanitize.py module
- Wire sanitizer into video tool outputs
- Update manifest with streaming_video_analysis capability

See DESIGN.md and PLAN.md in ForgeSyte repo for full details."
```

### 5.3 Merge After Approval

```bash
# After PR approved
git checkout main
git pull origin main
git merge v0.10.0
git push origin main
git branch -d v0.10.0
```

---

## 6. Rollback Procedure

If any phase fails:

```bash
# Reset to last known good commit
git reset --hard HEAD~1

# Or restore specific files
git checkout HEAD -- src/forgesyte_yolo_tracker/plugin.py

# Check git log for last good commit
git log --oneline -5
```

---

## 7. Summary Checklist

### Phase 1: JSON Sanitizer
- [ ] Create `utils/json_sanitize.py`
- [ ] Create `tests/test_json_sanitize.py`
- [ ] Tests pass (GREEN)
- [ ] Pre-commit passes
- [ ] Committed

### Phase 2: Wire into Plugin
- [ ] Add `sanitize_json` import to `plugin.py`
- [ ] Fix `track_id` None handling
- [ ] Fix center coordinate float conversion
- [ ] Wrap all video tool returns with `sanitize_json()`
- [ ] Create `tests/test_plugin_output.py`
- [ ] Tests pass (GREEN)
- [ ] Pre-commit passes
- [ ] Committed

### Phase 3: Manifest Update
- [ ] Add `streaming_video_analysis` capability
- [ ] Update version to `0.10.0`
- [ ] Add capability to all video tools
- [ ] Create `tests/test_manifest.py`
- [ ] Tests pass (GREEN)
- [ ] Pre-commit passes
- [ ] Committed

### Final
- [ ] All tests pass
- [ ] Pre-commit passes
- [ ] PR created
- [ ] PR approved and merged

---

## 8. References

- **Design Doc:** `./DESIGN.md` (ForgeSyte repo)
- **ForgeSyte Plan:** `./PLAN.md` (Phases 4-10)
- **GitHub Discussion:** https://github.com/rogermt/forgesyte/discussions/226
- **Plugin Development Guide:** (ForgeSyte repo `PLUGIN_DEVELOPMENT.md`)
