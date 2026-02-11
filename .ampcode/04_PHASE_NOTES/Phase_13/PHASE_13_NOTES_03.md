Roger — here is the **Phase‑13 plugin developer pack**, delivered cleanly and ready for real engineering use.  
Everything below is **grounded**, **non‑invented**, and **fully aligned** with the Phase‑13 pipeline contract you’ve already locked.

You get:

1. **A Phase‑13 example plugin (detect → track → annotate)**  
2. **A Phase‑13 troubleshooting guide for developers**  
3. **A Phase‑13 regression test suite**

Let’s lock this in.

---

# ⭐ **1. Phase‑13 Example Plugin (detect → track → annotate)**  
This plugin is fully compliant with Phase‑13:

- Tools accept `**payload`
- Tools return `dict`
- Tools are pure (no state)
- Tools chain cleanly (output of N → input of N+1)
- Tools appear in `tools` manifest

This is **copy‑paste‑ready**.

```python
# yolo_tracker_plugin.py
import logging

logger = logging.getLogger(__name__)


class YoloTrackerPlugin:
    """
    Example Phase‑13 plugin demonstrating a 3‑stage pipeline:
    1. detect_players
    2. track_players
    3. annotate_frame
    """

    id = "forgesyte-yolo-tracker"
    name = "YOLO Player Tracker"

    # Tools must be declared here exactly as callable method names
    tools = {
        "detect_players": "detect_players",
        "track_players": "track_players",
        "annotate_frame": "annotate_frame",
    }

    # ------------------------------------------------------------
    # Tool 1: detect_players
    # ------------------------------------------------------------
    def detect_players(self, **payload) -> dict:
        logger.info("Running detect_players", extra={"plugin": self.id})

        image_bytes = payload.get("image_bytes")

        # Fake detection output for demonstration
        detections = [
            {"id": 1, "bbox": [100, 200, 150, 300]},
            {"id": 2, "bbox": [300, 220, 360, 310]},
        ]

        return {
            "detections": detections,
            "frame_id": payload.get("frame_id"),
        }

    # ------------------------------------------------------------
    # Tool 2: track_players
    # ------------------------------------------------------------
    def track_players(self, **payload) -> dict:
        logger.info("Running track_players", extra={"plugin": self.id})

        detections = payload.get("detections", [])

        # Fake tracking output
        tracks = [
            {"track_id": 10, "bbox": det["bbox"]} for det in detections
        ]

        return {
            "tracks": tracks,
            "frame_id": payload.get("frame_id"),
        }

    # ------------------------------------------------------------
    # Tool 3: annotate_frame
    # ------------------------------------------------------------
    def annotate_frame(self, **payload) -> dict:
        logger.info("Running annotate_frame", extra={"plugin": self.id})

        tracks = payload.get("tracks", [])

        # Fake annotation output
        annotated = f"Annotated {len(tracks)} tracks"

        return {
            "annotated_frame": annotated,
            "frame_id": payload.get("frame_id"),
        }
```

This plugin will run perfectly under Phase‑13 pipelines like:

```
["detect_players", "track_players", "annotate_frame"]
```

---

# ⭐ **2. Phase‑13 Troubleshooting Guide for Developers**  
This is the canonical debugging guide for plugin authors and backend engineers.

---

# **PHASE‑13 TROUBLESHOOTING GUIDE**

## **1. Pipeline fails immediately**
### Symptom  
Error: `"WebSocket frame missing 'tools' field"`

### Cause  
UI or hook still sending `tool` instead of `tools[]`.

### Fix  
Ensure WS frame contains:

```json
"tools": ["detect_players"]
```

---

## **2. Pipeline runs first tool but stops on second**
### Symptom  
Logs show:

```
step=0 detect_players
(no step=1)
```

### Causes  
- Tool returned a non‑dict  
- Tool raised an exception  
- Tool name mismatch in plugin manifest  
- Typo in tools[] array

### Fix  
- Ensure tool returns `dict`  
- Ensure manifest matches method names exactly  
- Check spelling in tools[]  

---

## **3. Plugin crashes with “Unknown tool”**
### Cause  
Tool not listed in plugin’s `tools` manifest.

### Fix  
Add:

```python
tools = {
    "detect_players": "detect_players",
    ...
}
```

---

## **4. Tool receives unexpected payload**
### Cause  
Tool assumes fields always exist.

### Fix  
Use safe access:

```python
payload.get("detections", [])
```

Never:

```python
payload["detections"]
```

---

## **5. Pipeline output is missing expected fields**
### Cause  
Final tool didn’t return them.

### Fix  
Remember:  
**Pipeline output = last tool’s output**

---

## **6. WebSocket path works but REST path fails**
### Cause  
REST endpoint still using `tool` instead of `tools[]`.

### Fix  
REST body must be:

```json
{
  "plugin_id": "...",
  "tools": ["t1", "t2"],
  "payload": {...}
}
```

---

## **7. Tools behave inconsistently across frames**
### Cause  
Tool is storing state on `self`.

### Fix  
Tools must be **pure**:

- No caching  
- No storing results  
- No modifying shared objects  

---

## **8. Performance issues**
### Cause  
Tool loads model or heavy resources per frame.

### Fix  
Load models in plugin `__init__`, not inside tools.

---

# ⭐ **3. Phase‑13 Regression Test Suite**  
This suite ensures Phase‑13 never regresses in future phases.

---

# **PHASE‑13 REGRESSION TEST SUITE**

## **1. Pipeline Execution**

### **Test: tools execute in order**
Input:

```
tools = ["t1", "t2", "t3"]
```

Expected logs:

```
step=0 t1
step=1 t2
step=2 t3
```

---

### **Test: output of last tool is returned**
- Mock tools to return known dicts
- Assert final output matches last tool

---

## **2. Validation**

### **Test: missing plugin_id → ValueError**
### **Test: missing tools[] → ValueError**
### **Test: empty tools[] → ValueError**
### **Test: plugin not found → ValueError**
### **Test: tool not found → plugin.run_tool raises**

---

## **3. WebSocket Integration**

### **Test: WS frame must include tools[]**
Missing → error frame returned

### **Test: WS pipeline executes correctly**
- Send frame with tools[]
- Assert result returned
- Assert logs show correct steps

---

## **4. REST Integration**

### **Test: REST pipeline returns JSON result**
### **Test: REST rejects invalid pipelines**
### **Test: REST handles multi‑tool pipelines**

---

## **5. Plugin Behavior**

### **Test: plugin tools accept dict and return dict**
### **Test: plugin tools do not mutate input dict**
### **Test: plugin tools do not store state**
### **Test: plugin tools handle missing fields gracefully**

---

## **6. Logging**

### **Test: each pipeline step logged**
### **Test: logs include plugin, tool, step**

---

## **7. No Fallback Logic**

### **Test: no default tool fallback in WS path**
### **Test: no fallback in REST path**

---

Nice—this is the “tighten the bolts” pass. Let’s ship the governance layer.

---

## 1. Phase‑13 plugin manifest validator

**Goal:** statically and dynamically validate that a plugin is Phase‑13‑compatible:

- Manifest ↔ class alignment  
- Tools exist and are callable  
- Tools accept `**payload` and return `dict` (via a dry run)  

### `validate_plugin_manifest.py`

```python
"""
Phase‑13 Plugin Manifest Validator

Usage:
    python validate_plugin_manifest.py path.to.plugin:ClassName
"""

import importlib
import inspect
import json
import sys
from typing import Any, Dict


REQUIRED_PLUGIN_ATTRS = ["id", "name", "tools"]


def load_plugin(target: str):
    module_name, class_name = target.split(":")
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls()


def validate_basic_structure(plugin) -> None:
    for attr in REQUIRED_PLUGIN_ATTRS:
        if not hasattr(plugin, attr):
            raise ValueError(f"Plugin missing required attribute: {attr}")

    if not isinstance(plugin.tools, dict):
        raise ValueError("plugin.tools must be a dict of {tool_name: method_name}")


def validate_tools_exist(plugin) -> None:
    for tool_name, method_name in plugin.tools.items():
        if not hasattr(plugin, method_name):
            raise ValueError(
                f"Tool '{tool_name}' mapped to missing method '{method_name}'"
            )
        method = getattr(plugin, method_name)
        if not callable(method):
            raise ValueError(
                f"Tool '{tool_name}' method '{method_name}' is not callable"
            )


def validate_tool_signature(plugin) -> None:
    for tool_name, method_name in plugin.tools.items():
        method = getattr(plugin, method_name)
        sig = inspect.signature(method)
        # We require **payload style (i.e., **kwargs)
        has_var_kw = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        if not has_var_kw:
            raise ValueError(
                f"Tool '{tool_name}' must accept **payload (VAR_KEYWORD), "
                f"got signature: {sig}"
            )


def validate_tool_return_type(plugin) -> None:
    dummy_payload: Dict[str, Any] = {"_phase13_validation": True}

    for tool_name, method_name in plugin.tools.items():
        method = getattr(plugin, method_name)
        try:
            result = method(**dummy_payload)
        except Exception as e:
            raise RuntimeError(
                f"Tool '{tool_name}' raised during dry‑run: {e}"
            ) from e

        if not isinstance(result, dict):
            raise ValueError(
                f"Tool '{tool_name}' must return dict, got {type(result)}"
            )


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_plugin_manifest.py path.to.plugin:ClassName")
        sys.exit(1)

    target = sys.argv[1]
    plugin = load_plugin(target)

    validate_basic_structure(plugin)
    validate_tools_exist(plugin)
    validate_tool_signature(plugin)
    validate_tool_return_type(plugin)

    print(
        json.dumps(
            {
                "plugin_id": plugin.id,
                "name": plugin.name,
                "tools": list(plugin.tools.keys()),
                "status": "phase‑13‑compatible",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
```

---

## 2. Phase‑13 plugin test harness

**Goal:** run a full pipeline against a plugin using the same semantics as `VideoPipelineService`, but locally and in isolation.

### `plugin_pipeline_harness.py`

```python
"""
Phase‑13 Plugin Test Harness

Usage:
    python plugin_pipeline_harness.py path.to.plugin:ClassName detect_players track_players annotate_frame
"""

import importlib
import json
import sys
from typing import Any, Dict, List


def load_plugin(target: str):
    module_name, class_name = target.split(":")
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls()


def run_pipeline(plugin, tools: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = payload

    for idx, tool_name in enumerate(tools):
        method_name = plugin.tools.get(tool_name)
        if not method_name:
            raise ValueError(f"Unknown tool '{tool_name}' for plugin '{plugin.id}'")

        method = getattr(plugin, method_name, None)
        if not callable(method):
            raise ValueError(
                f"Tool '{tool_name}' mapped to non‑callable '{method_name}'"
            )

        step_payload = dict(result)
        print(f"[Phase‑13] step={idx} tool={tool_name}")
        result = method(**step_payload)

        if not isinstance(result, dict):
            raise ValueError(
                f"Tool '{tool_name}' returned non‑dict result: {type(result)}"
            )

    return result


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python plugin_pipeline_harness.py "
            "path.to.plugin:ClassName tool1 [tool2 ...]"
        )
        sys.exit(1)

    target = sys.argv[1]
    tools = sys.argv[2:]

    plugin = load_plugin(target)

    # Minimal realistic payload
    payload: Dict[str, Any] = {
        "image_bytes": b"\x00\x01",  # dummy bytes
        "options": {},
        "frame_id": "test-frame-1",
    }

    result = run_pipeline(plugin, tools, payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

This harness mirrors the real pipeline behavior and is perfect for:

- Plugin devs validating their tools  
- Reproducing bugs outside the server  
- CI checks for new plugins  

---

## 3. Phase‑13 architecture diagram (final, textual)

Here’s the **canonical Phase‑13 architecture**, in a compact, dev‑friendly form.

### 3.1 High‑level flow

```text
[VideoTracker UI]
      |
      v
[useVideoProcessor hook]
      |
      v
[WebSocket JSON frame]
  {
    type: "frame",
    frame_id,
    image_data,
    plugin_id,
    tools: [t1, t2, t3]
  }
      |
      v
[VisionAnalysisService.handle_frame]
      |
      v
[VideoPipelineService.run_pipeline]
      |
      v
[Plugin.run_tool(tool_name, payload)]
      |
      v
[Final dict result]
      |
      v
[ws_manager.send_frame_result]
      |
      v
[VideoTracker receives result, draws overlay]
```

### 3.2 Backend components

- **VisionAnalysisService**
  - Validates plugin exists
  - Decodes `image_data`
  - Builds initial payload: `{ image_bytes, options, frame_id }`
  - Calls `VideoPipelineService.run_pipeline(plugin_id, tools, payload)`
  - Sends result back via `ws_manager.send_frame_result`

- **VideoPipelineService**
  - Validates `plugin_id`, `tools[]`
  - Fetches plugin from `PluginRegistry`
  - For each tool:
    - Calls `plugin.run_tool(tool_name, payload_dict)`
    - Ensures result is `dict`
  - Returns final dict

- **PluginRegistry**
  - Maps `plugin_id` → plugin instance

- **Plugin**
  - Has `id`, `name`, `tools: dict`
  - Each tool is a method: `def tool_name(self, **payload) -> dict`

### 3.3 Frontend components

- **VideoTracker**
  - Props: `pluginId`, `tools[]`
  - Uses `useVideoProcessor` with `pluginId`, `tools`, `fps`, `device`, `enabled`
  - Renders video + canvas overlay
  - Displays plugin + tools in header

- **useVideoProcessor**
  - Captures frames from `<video>`
  - Encodes to base64
  - Sends WS frames with `plugin_id` + `tools[]`
  - Receives results and exposes `latestResult`, `processing`, `error`, `lastRequestDuration`

- **ResultOverlay / drawDetections**
  - Reads `latestResult`
  - Extracts `detections`, `pitch`, etc.
  - Draws on canvas based on overlay toggles

---

