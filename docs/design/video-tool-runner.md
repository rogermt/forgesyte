# Video Tool Runner (Canonical UI Specification)

This document defines the authoritative, non-negotiable UI layout and scope
for the Video Tool Runner inside the `forgesyte` repository.

It is the single source of truth for all developers.

No features may be added, removed, or modified without explicit approval.


## ASCII UI Diagram (Exact Specification)

```
┌──────────────────────────────────────────────────────────────┐
│                Video Tool Runner (Generic)                    │
├──────────────────────────────────────────────────────────────┤
│  Video Source:                                                │
│  [ Upload Video ]  [ Use Webcam ]                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  <video> element showing the match                     │   │
│  │                                                        │   │
│  │  <canvas overlay> draws:                               │   │
│  │   - player boxes                                       │   │
│  │   - track IDs                                          │   │
│  │   - ball                                               │   │
│  │   - pitch lines                                        │   │
│  │   - radar (small corner)                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  Controls:                                                    │
│  [ Play ] [ Pause ] [ FPS: 5 ▼ ] [ Device: CPU ▼ ]           │
│  [ Players ✓ ] [ Tracking ✓ ] [ Ball ✓ ] [ Pitch ✓ ] [ Radar ✓ ] │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```


## Out-of-Scope (Explicitly Forbidden)

The following features are **NOT** part of the Video Tool Runner
and must not be implemented, referenced, scaffolded, or partially added:

- No record button  
- No video export  
- No WebM/MP4 saving  
- No model selector  
- No backend model dropdown  
- No WebSocket mode selector  
- No timeline scrubber  
- No multi-video comparison  
- No analytics panels  
- No heatmaps  
- No charts  
- No extra UI panels beyond the diagram above  

Any PR containing these features must be rejected.


## Purpose

This UI is used for running frame-based video tools (e.g., YOLO tracker)
and rendering their detections on a canvas overlay.

It is intentionally minimal and must remain so.


## Status

Approved as the canonical UI specification.
