### Phase 13 architecture diagram (ASCII)

```text
┌──────────────────────────────────────────────────────────────┐
│                        VideoTracker UI                       │
├──────────────────────────────────────────────────────────────┤
│  - Select Plugin (single)                                    │
│  - Select Tools (ordered list)                               │
│      [ detect_players ] → [ track_players ] → [ annotate ]   │
│                                                              │
│  Background Path:                                            │
│    POST /video/pipeline                                      │
│      { plugin_id, tools[], payload }                         │
│                                                              │
│  Streaming Path:                                             │
│    WS frame:                                                 │
│      { type:"frame", frame_id, image_data,                   │
│        plugin_id, tools[] }                                  │
└──────────────────────────────────────────────────────────────┘
                │                          │
                ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    Server: VideoPipelineService              │
├──────────────────────────────────────────────────────────────┤
│  validate(plugin_id, tools[])                                │
│  result = payload                                            │
│  for each tool in tools:                                     │
│      log(plugin_id, tool, step)                              │
│      result = run_plugin_tool(plugin_id, tool, result)       │
│  return result                                               │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                        Plugin (Single)                       │
├──────────────────────────────────────────────────────────────┤
│  def detect_players(**payload) -> dict                       │
│  def track_players(**payload) -> dict                        │
│  def annotate_frames(**payload) -> dict                      │
│                                                              │
│  Each tool:                                                  │
│    - accepts dict payload                                    │
│    - returns dict payload                                    │
│    - no global state                                         │
└──────────────────────────────────────────────────────────────┘
```

---

