### Phase 13 acceptance tests

#### 1. REST pipeline execution

**Test:** `test_video_pipeline_rest_executes_tools_in_order`

- **Given:**  
  - Plugin `forgesyte-yolo-tracker` with tools: `["detect_players", "track_players", "annotate_frames"]`.  
  - Each tool appends its name to `payload["steps"]`.
- **When:**  
  - `POST /video/pipeline` with:
    ```json
    {
      "plugin_id": "forgesyte-yolo-tracker",
      "tools": ["detect_players", "track_players", "annotate_frames"],
      "payload": { "steps": [] }
    }
    ```
- **Then:**  
  - Response `200`.  
  - `result["steps"] == ["detect_players", "track_players", "annotate_frames"]`.

---

**Test:** `test_video_pipeline_rest_rejects_empty_tools`

- **Given:** valid plugin_id, empty tools array.
- **When:** `POST /video/pipeline` with `"tools": []`.
- **Then:** HTTP `422` or `400` with message “tools must be non-empty”.

---

**Test:** `test_video_pipeline_rest_rejects_unknown_tool`

- **Given:** plugin with tools `["detect_players"]`.
- **When:** `"tools": ["detect_players", "nonexistent_tool"]`.
- **Then:** HTTP error with message “Unknown tool 'nonexistent_tool' for plugin '…'”.

---

#### 2. WebSocket pipeline execution

**Test:** `test_video_pipeline_ws_executes_tools_in_order`

- **Given:**  
  - WebSocket connected to vision analysis endpoint.  
  - Same “steps”‑appending tools as above.
- **When:**  
  - Send frame:
    ```json
    {
      "type": "frame",
      "frame_id": "f1",
      "image_data": "…",
      "plugin_id": "forgesyte-yolo-tracker",
      "tools": ["detect_players", "track_players"]
    }
    ```
- **Then:**  
  - Response JSON contains `frame_id: "f1"`.  
  - `result["steps"] == ["detect_players", "track_players"]`.

---

**Test:** `test_video_pipeline_ws_missing_tools_rejected`

- **When:** frame without `tools` field.
- **Then:** server closes or responds with error “WebSocket frame missing 'tools'”.

---

#### 3. Validation & governance

**Test:** `test_pipeline_rejects_cross_plugin_tools`

- **Given:**  
  - Plugin A with tool `a1`.  
  - Plugin B with tool `b1`.  
- **When:** pipeline request with `plugin_id="A"` and `"tools": ["a1", "b1"]`.
- **Then:** error “Tool 'b1' not found in plugin 'A'”.

---

**Test:** `test_pipeline_logs_each_step`

- **Given:** pipeline with 3 tools.
- **When:** run pipeline.
- **Then:** logs contain 3 entries with:
  - `plugin_id=…`
  - `tool_name` matching each tool
  - `step` = 0, 1, 2.

---

