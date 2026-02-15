### 🔥 Phase‑17 kickoff (streaming architecture)

One‑page kickoff you can drop into `Phase_17/OVERVIEW.md`:

```markdown
# Phase‑17 Kickoff — Real‑Time Streaming Inference

## Purpose
Phase‑17 introduces a real‑time streaming layer on top of the stable Phase‑15/16 batch + async foundations.

## Core Additions
- WebSocket endpoint: `/ws/video/stream`
- Session manager: one session per connection
- Real‑time inference loop: frame → pipeline → result
- Backpressure: drop frames / send slow‑down signals
- Ephemeral results: no persistence, no job table

## Non‑Goals (Stay in Phase‑18+)
- Recording or storing streams
- Historical queries
- Multi‑client fan‑out
- GPU scheduling
- Distributed workers

## High‑Level Flow
1. Client opens WebSocket session.
2. Client sends frames (JPEG/binary).
3. Server validates and runs Phase‑15 pipeline per frame.
4. Server pushes `{frame_index, result}` back over WebSocket.
5. Session ends; no state persisted.

Phase‑17 builds on Phase‑16’s correctness but changes the time model: from jobs to live streams.
```
