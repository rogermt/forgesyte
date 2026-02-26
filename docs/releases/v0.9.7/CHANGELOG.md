# ⭐ **CHANGELOG — Backend (ForgeSyte) — v0.9.7**

```
## v0.9.7 — Unified Video Pipeline & Multi‑Tool Execution

### Added
- Introduced unified output schema for all job types (image, image_multi, video).
- Added multi‑tool execution pipeline for video jobs.
- Added worker metadata fields:
  - current_tool
  - tools_total
  - tools_completed
- Added progress callback support for video tools.
- Added consistent JSON output format for all video tools.
- Added UI support for multi‑tool video jobs.

### Changed
- Worker now wraps plugin output in the unified v0.9.7 schema.
- Updated API responses to include job metadata and progress.
- Updated tool introspection to expose correct input/output types.
- Updated VideoUpload UI to filter tools by input_types=["video"].
- Updated JobStatus UI to display multi‑tool progress.

### Fixed
- Removed legacy video tools from tool list.
- Removed transitional v0.9.5 video tool (`video_player_detection`).
- Fixed worker returning raw plugin output instead of unified schema.
- Fixed UI showing legacy tools due to incorrect manifest.
- Fixed multi‑tool sequencing logic.
- Fixed incorrect input_types in plugin manifest.
- Fixed inconsistent progress reporting.

### Removed
- Legacy video_path‑based tools.
- Transitional video tool definitions.
- Deprecated worker code paths for legacy video tools.

### Notes
This release finalizes the v0.9.7 contract and prepares the system for v0.9.8 stability improvements.
```