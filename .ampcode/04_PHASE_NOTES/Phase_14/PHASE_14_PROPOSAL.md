### Phase 14 proposal (cross‑plugin pipelines, DAGs, tool capabilities)

#### Theme: From linear, single‑plugin pipelines → graph‑based, cross‑plugin workflows with capabilities.

**Phase 14 goals:**

1. **Cross‑plugin pipelines**
   - Allow pipelines like:
     - `[ yolo.detect_players (plugin A) → reid.track_ids (plugin B) → viz.render_overlay (plugin C) ]`
   - Introduce a pipeline spec that includes `(plugin_id, tool_id)` per step.

2. **DAG‑based workflows**
   - Move from strict linear pipelines to DAGs:
     - Branching (e.g., detections feed both tracking and heatmap).
     - Merging (e.g., combine outputs into a final overlay).
   - Represented as:
     ```json
     {
       "nodes": [{ "id": "n1", "plugin_id": "...", "tool_id": "..." }],
       "edges": [{ "from": "n1", "to": "n2" }]
     }
     ```

3. **Tool capabilities and type contracts**
   - Each tool declares:
     - `input_schema` (or capability tags like `["video_frame", "detections"]`)
     - `output_schema` (or tags like `["detections", "tracks", "overlay"]`)
   - Pipeline builder validates compatibility:
     - Output of step N must be acceptable input for step N+1.

4. **Pipeline registry and reuse**
   - Named pipelines stored server‑side:
     - `player_tracking_pipeline_v1`
     - `ball_tracking_pipeline_v2`
   - UI can select a named pipeline instead of manually wiring tools.

5. **Governance**
   - No implicit cross‑plugin magic:
     - Every step explicitly declares plugin + tool.
   - No runtime guessing of compatibility:
     - Pipelines must validate before execution.
   - Logs include pipeline ID, node ID, plugin, tool, and step order.
