### 1. Plugin manifest structure

- **Extend manifest.json:**  
  Yes—extend the existing `manifest.json` format to include `input_types`, `output_types`, and `capabilities` per tool. That keeps all plugin metadata in one canonical place.
- **Existing plugins:**  
  OCR/YOLO almost certainly **don’t** have this metadata yet—you should add it for **all** plugins, even if it’s minimal (e.g., `["video_frame"] → ["detections"]`). Phase 14 only works if every tool has a declared contract.

---

### 2. Pipeline storage location

- **Location:**  
  Yes: `server/app/pipelines/` as JSON files is the right default. It’s explicit, greppable, and easy to review.
- **Version control vs DB:**  
  For Phase 14, **version-control them in git**. DB-backed pipelines can be a later phase. Right now you want pipelines to be code-reviewed artifacts, not runtime surprises.

---

### 3. WebSocket integration

- **Modify or new message type?**  
  Reuse the existing WS protocol but **add a `pipeline_id` field**. Don’t invent a whole new message type unless the current one is already a mess.
- **Message format:**  
  Something like:

  ```json
  {
    "type": "frame",
    "pipeline_id": "player_tracking_v1",
    "frame_id": "123",
    "image_bytes": "...",
    "metadata": { ... }
  }
  ```

  If `pipeline_id` is present → use DAG. If only `tools[]` is present → Phase 13 linear pipeline. That gives you a clean compatibility bridge.

---

### 4. Backward compatibility

- **Single-tool execution:**  
  Yes, keep Phase 13 single-/multi-tool execution working for now. Don’t force everything onto DAGs in one jump.
- **Wrapper or parallel path?**  
  Best: treat single-tool/multi-tool as a **separate execution path** for now. If you want, you can later add a thin adapter that wraps a single tool into a 1-node pipeline—but don’t overcomplicate Phase 14 with that migration yet. Keep DAG engine focused on named pipelines.

---

### 5. Type system

- **Fixed set vs custom:**  
  Use a **core vocabulary** (e.g., `"video_frame"`, `"detections"`, `"tracks"`, `"overlay"`) but allow plugins to define additional types. Core types give you interoperability; custom types give you flexibility.
- **Matching rule:**  
  Start simple: **intersection-based**. An edge is valid if:

  ```text
  nodeA.output_types ∩ nodeB.input_types ≠ ∅
  ```

  That’s enough for Phase 14. You can add richer rules later if needed.

---

### 6. Error handling

- **Node failure behavior:**  
  For Phase 14, be strict: **fail the entire pipeline** if any node fails. That keeps semantics simple and debuggable.
- **Reporting failures:**  
  Yes—log failed nodes and include error info in the final response, e.g.:

  ```json
  {
    "error": {
      "node_id": "n2",
      "plugin_id": "reid",
      "tool_id": "track_ids",
      "message": "…"
    }
  }
  ```

  But still return a 4xx/5xx so callers know it’s not a partial success.

---

### 7. Testing strategy

- **Mock vs real plugins:**  
  Use **mock/fake plugins** for core DAG/registry tests (deterministic, fast), and add **a small number of integration tests** using real plugins (e.g., OCR + YOLO) to prove cross-plugin wiring works.
- **Cross-plugin availability:**  
  If you have at least 2 real plugins (OCR, YOLO), use them in one or two high-level tests. Otherwise, create two fake plugins in tests that simulate cross-plugin behavior.

---

### 8. UI integration

- **PipelineSelector vs tool selector:**  
  For Phase 14, make `PipelineSelector` an **additional option**, not a replacement. E.g., a toggle:

  - Mode A: “Manual tools (Phase 13)”
  - Mode B: “Named pipeline (Phase 14)”

  That lets you migrate gradually.
- **Pipeline metadata in UI:**  
  Add at least: `name`, `description`, maybe `tags`. You can derive capabilities (e.g., “produces tracks”) from the DAG’s tools, but for now just show name + description in the selector.

---

### 9. Performance

- **Parallel execution:**  
  For Phase 14, keep it **strictly sequential topological order**. Parallelism adds complexity (threading, shared state, ordering) and isn’t needed to prove the architecture.
- **Timeouts:**  
  Add a **global per-request timeout** at the API layer (e.g., via server config) rather than baking timeouts into the DAG engine itself. You can later add per-node timeouts if needed, but don’t start there.

---

### 10. Existing code

- **Existing pipeline-related code:**  
  Yes: you already have Phase 13’s `VideoPipelineService` and any ad-hoc “pipeline” helpers. You must ensure Phase 14’s DAG engine doesn’t silently conflict with or duplicate them.
- **Check for DAG/workflow code:**  
  Do a quick scan for anything named `pipeline`, `workflow`, `graph`, `dag`, `orchestrator`. If you find ad-hoc graph logic, either:
  - delete it in favor of the new DAG engine, or  
  - clearly mark it as legacy and keep it out of Phase 14.

---

