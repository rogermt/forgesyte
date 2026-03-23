# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForgeSyte Web UI is a React 18 + TypeScript application that provides a real-time camera streaming interface with plugin-based analysis. It connects to a ForgeSyte backend server via REST API and WebSocket for live video processing.

**Key Features**: Real-time camera streaming via WebSocket, plugin/plugin manifest loading, multi-tool support, video upload and processing, job polling with progress tracking, and artifact viewing.

## Common Commands

```bash
# Development
npm run dev          # Start Vite dev server (port 3000, proxies /v1 and /ws to localhost:8000)
npm run build        # Production build to dist/
npm run preview      # Preview production build

# Code Quality
npm run lint         # ESLint check
npm run type-check   # TypeScript type checking
npm run check        # Lint + type-check combined

# Testing (Vitest)
npm run test          # Run all tests (watch mode)
npm run test:ui       # Run tests with Vitest UI browser
npm run test:coverage # Generate coverage report
```

**Single test file**: `npx vitest run src/api/client.test.ts`

## Architecture

### Stack
- **React 18** with TypeScript (ESM modules)
- **Vite** for bundling and dev server
- **Vitest** for testing (ESM-native, jsdom environment)
- **React Testing Library** for component tests
- CSS variables for theming (no CSS framework)

### Directory Structure
```
src/
├── api/client.ts        # ForgeSyteAPIClient - REST API calls to backend
├── components/          # React UI components
│   ├── App.tsx          # Root component - view routing, state management
│   ├── PluginSelector   # Plugin dropdown
│   ├── ToolSelector     # Multi-tool selection
│   ├── CameraPreview    # WebRTC camera capture
│   ├── VideoTracker     # Video file frame extraction
│   ├── VideoUpload      # Video file upload UI
│   ├── JobList          # Job history list
│   ├── JobStatus        # Job progress display
│   ├── ResultsPanel     # Stream results or job results display
│   ├── ArtifactViewer   # Lazy-loads job artifacts/pagination
│   └── ...
├── hooks/
│   ├── useWebSocket.ts  # WebSocket connection management (auto-reconnect)
│   ├── useManifest.ts   # Plugin manifest fetching
│   ├── useJobProgress.ts
│   └── useVideoProcessor.ts
├── realtime/            # RealtimeContext + useRealtime (alternative to useWebSocket)
├── types/plugin.ts     # PluginManifest, Tool, Detection types
├── utils/
│   ├── detectToolType.ts   # Determines if tool is "frame" or "video" type
│   └── ...
└── test/setup.ts       # Vitest global setup (testing-library imports)
```

### API Client (`src/api/client.ts`)

The `ForgeSyteAPIClient` class provides all backend communication:
- `getPlugins()` - List available plugins
- `getPluginManifest(pluginId)` - Fetch manifest with tools
- `submitImage(file, pluginId, tools, onProgress, useLogicalIds)` - Upload image
- `submitVideoJob(pluginId, videoPath, tools)` - Start video processing job
- `listJobs(limit, skip, status)` / `getJob(jobId)` - Job management
- `pollJob(jobId)` - Wait for job completion (polls until done)
- `getHealth()` - Server health check

**Environment variables** (`VITE_*` prefix required for Vite):
- `VITE_API_URL` - Backend API URL (default: `/v1`)
- `VITE_API_KEY` - Optional API key
- `VITE_WS_BACKEND_URL` - WebSocket URL (default: `ws://localhost:8000`)

### WebSocket Integration

The `useWebSocket` hook (`src/hooks/useWebSocket.ts`) manages real-time streaming:
- Auto-reconnect with exponential backoff
- Connection states: `connected`, `connecting`, `reconnecting`, `failed`, `disconnected`
- Sends frames via `sendFrame(imageData)` when streaming enabled
- `switchPlugin(pluginId)` to change active plugin mid-stream

### Job System

Jobs go through status transitions: `pending` → `running` → `completed`/`failed`. The UI polls for status updates:
- `selectedJob` - Job displayed in JobStatus panel
- `uploadResult` - Most recent upload job result
- `lockedTools` - Tools locked after upload (prevent mid-session changes)

### Plugin Manifest

Plugin manifests define available tools. The manifest format supports two structures:
- **Phase-12+ format**: `tools` is an array with `capabilities: string[]`
- **Legacy format**: `tools` is an object keyed by tool ID

The `isUsingLogicalIds` flag in App.tsx tracks which format is in use.

### View Modes

App.tsx routes between: `stream`, `upload`, `jobs`, `video-upload`, `video-stream`

Performance note: `ResultsPanel` is not rendered in `video-upload`/`video-stream` modes to avoid UI freeze from large job results.

## Testing Conventions

Tests co-located with source files: `*.test.ts` or `*.test.tsx`.

Mock pattern for API client tests:
```typescript
global.fetch = vi.fn();
client = new ForgeSyteAPIClient("http://localhost:3000/v1");
global.fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ plugins: [] }),
});
```

Path aliases: `@/` maps to `src/`, configured in both `vite.config.ts` and `vitest.config.ts`.
