Here’s a tight, all‑in‑one pack of the four Phase 14 docs you asked for.

---

## 📘 Phase 14 pipeline design guide  
`docs/phase_14_pipeline_design_guide.md`

### 1. Purpose

This guide defines how to design **Phase 14 DAG pipelines** that are:

- valid  
- type‑safe  
- debuggable  
- cross‑plugin compatible  

It assumes plugins expose `input_types`, `output_types`, and `capabilities`.

---

### 2. Core concepts

- **Node:** `(plugin_id, tool_id)` pair with a unique `id`.
- **Edge:** Directed link `from_node → to_node`.
- **Entry nodes:** Nodes with no incoming edges.
- **Output nodes:** Nodes whose outputs form the final pipeline result.
- **Run ID:** Unique ID per pipeline execution.

---

### 3. Design principles

- **Single responsibility per node:** Each node should do one clear thing (detect, track, OCR, render, etc.).
- **Explicit data types:** Every tool must declare `input_types` and `output_types`.
- **Linearizable reasoning:** Even though it’s a DAG, you should be able to explain the pipeline as a sequence of logical stages.
- **No hidden side effects:** Nodes should not mutate global state; all data flows via payloads.

---

### 4. Typical patterns

#### 4.1 Detection → Tracking → Visualization

```text
[ yolo.detect_players ] → [ reid.track_ids ] → [ viz.render_overlay ]
```

- `detect_players.output_types` includes `detections`
- `track_ids.input_types` includes `detections`
- `track_ids.output_types` includes `tracks`
- `render_overlay.input_types` includes `video_frame`, `tracks`

#### 4.2 OCR pipeline

```text
[ ocr.extract_text ] → [ nlp.classify_text ]
```

- `extract_text.output_types` includes `text_blocks`
- `classify_text.input_types` includes `text_blocks`

---

### 5. Design checklist

- [ ] All nodes have unique IDs  
- [ ] All edges reference valid nodes  
- [ ] Graph is acyclic  
- [ ] Entry/output nodes are defined and valid  
- [ ] For every edge, `output_types ∩ input_types ≠ ∅`  
- [ ] Capabilities chain makes semantic sense  
- [ ] Final output nodes produce the data the caller expects  

---

## 🐞 Phase 14 DAG debugging guide  
`docs/phase_14_dag_debugging_guide.md`

### 1. Purpose

This guide explains how to debug Phase 14 DAG pipelines using:

- structured logs  
- DuckDB  
- pipeline + plugin metadata  

---

### 2. First questions to ask

- Did the pipeline start? (`pipeline_started` event)  
- Did it complete or fail? (`pipeline_completed` / `pipeline_failed`)  
- Which node failed? (`pipeline_node_failed`)  
- What was the payload into that node? (reconstruct via predecessors)  

---

### 3. Debugging flow

#### 3.1 Identify the failing run

Query logs (or DuckDB):

```sql
SELECT *
FROM logs
WHERE pipeline_id = 'player_tracking_v1'
ORDER BY timestamp DESC
LIMIT 50;
```

Look for `pipeline_failed` and note `run_id` and `failed_node_id`.

#### 3.2 Inspect node‑level events

```sql
SELECT *
FROM logs
WHERE pipeline_id = 'player_tracking_v1'
  AND run_id = '<run-id>'
ORDER BY timestamp;
```

Check:

- `pipeline_node_started` / `pipeline_node_completed` sequence  
- The last `pipeline_node_failed` event  

#### 3.3 Reconstruct payload flow

Use the DAG definition:

- For the failing node, list its predecessors.  
- Inspect their outputs (if logged or inferred from tool behavior).  
- Verify that the types match the failing node’s `input_types`.

---

### 4. Common failure modes

- **Unknown plugin/tool:** mis‑typed IDs in pipeline definition.  
- **Type mismatch:** edge connects tools with incompatible types.  
- **Runtime exception:** plugin raises due to unexpected payload shape.  
- **Missing context:** predecessor node didn’t run or failed silently (should be prevented by Phase 14 invariants).

---

### 5. Debugging checklist

- [ ] Confirm pipeline ID and run ID  
- [ ] Identify failing node ID  
- [ ] Check plugin + tool existence  
- [ ] Check type compatibility on incoming edges  
- [ ] Check plugin logs for stack traces  
- [ ] Verify pipeline definition matches intended design  

---

## 🧩 Phase 14 plugin metadata schema  
`docs/phase_14_plugin_metadata_schema.md`

### 1. Purpose

This schema defines the **required metadata** for all plugins and tools in Phase 14.

---

### 2. Manifest structure (conceptual)

```jsonc
{
  "id": "ocr",
  "name": "OCR Plugin",
  "tools": {
    "extract_text": {
      "handler": "ocr.extract_text",
      "input_types": ["image", "video_frame"],
      "output_types": ["text_blocks"],
      "capabilities": ["ocr", "text_extraction"]
    }
  }
}
```

---

### 3. Field requirements

- **`id` (plugin):**  
  - type: string  
  - unique across all plugins  

- **`tools` (plugin):**  
  - type: object  
  - keys: tool IDs  

- **`handler` (tool):**  
  - type: string  
  - Python import path or identifier used by plugin loader  

- **`input_types` (tool):**  
  - type: array of strings  
  - non‑empty  
  - examples: `video_frame`, `image`, `detections`, `text_blocks`  

- **`output_types` (tool):**  
  - type: array of strings  
  - non‑empty  

- **`capabilities` (tool):**  
  - type: array of strings  
  - non‑empty  
  - examples: `ocr`, `player_detection`, `tracking`, `visualization`  

---

### 4. Invariants

- Every tool must have all three: `input_types`, `output_types`, `capabilities`.  
- Types must be reused consistently across plugins (no synonyms like `detection` vs `detections`).  
- Capabilities must describe behavior, not implementation details.

---

## 🔍 Phase 14 cross‑plugin compatibility report  
`docs/phase_14_cross_plugin_compatibility_report.md`

### 1. Purpose

This report summarizes **which tools can feed which other tools**, based on their declared types.  
It’s the high‑level map of cross‑plugin interoperability.

---

### 2. Compatibility definition

Tool A is **compatible as a predecessor** of tool B if:

```text
A.output_types ∩ B.input_types ≠ ∅
```

---

### 3. Example compatibility table

| Source Plugin.Tool | Output Types | Compatible Target Plugin.Tool | Input Types |
|--------------------|-------------|-------------------------------|------------|
| `yolo.detect_players` | `detections` | `reid.track_ids` | `detections` |
| `reid.track_ids` | `tracks` | `viz.render_overlay` | `video_frame`, `tracks` |
| `ocr.extract_text` | `text_blocks` | `nlp.classify_text` | `text_blocks` |

---

### 4. Cross‑plugin chains

#### 4.1 Player tracking chain

```text
yolo.detect_players → reid.track_ids → viz.render_overlay
```

- `detect_players.output_types` includes `detections`  
- `track_ids.input_types` includes `detections`  
- `track_ids.output_types` includes `tracks`  
- `render_overlay.input_types` includes `tracks`  

#### 4.2 OCR + NLP chain

```text
ocr.extract_text → nlp.classify_text
```

---

### 5. Governance rules

- New tools must declare types that fit into existing chains or clearly define new ones.  
- Type changes in one plugin must be reflected in:  
  - pipeline validator  
  - capability matrix  
  - compatibility report  

