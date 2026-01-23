# Web-UI: Plugin & Manifest TypeScript Types

**File:** `forgesyte/web-ui/src/types/plugin.ts` (NEW)  
**Purpose:** Define types for plugin manifest, tools, and video processing  
**Status:** Ready to implement  

---

## Overview

Strongly-typed interfaces for:
- Plugin metadata
- Tool schemas (inputs/outputs)
- Frame processing
- Track persistence
- Result rendering

---

## Implementation

**Location:** `forgesyte/web-ui/src/types/plugin.ts` (NEW FILE)

```typescript
/**
 * Plugin and manifest type definitions.
 * 
 * These types ensure type safety when working with plugin data
 * discovered from the backend manifest endpoint.
 */

/**
 * Tool input/output field definition.
 */
export interface ToolField {
  type: string;
  description?: string;
  required?: boolean;
}

/**
 * Single tool in a plugin.
 */
export interface PluginTool {
  description: string;
  inputs: Record<string, ToolField | string>;
  outputs: Record<string, ToolField | string>;
  render_hints?: {
    overlay_type?: "bounding_box" | "circle" | "line" | "points";
    color?: string;
    label_field?: string;
    confidence_field?: string;
    line_width?: number;
  };
}

/**
 * Plugin manifest (from GET /plugins/{id}/manifest).
 */
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  license?: string;
  capabilities?: string[];
  tools: Record<string, PluginTool>;
}

/**
 * Plugin run request body.
 */
export interface PluginToolRunRequest {
  args: Record<string, unknown>;
}

/**
 * Plugin run response body.
 */
export interface PluginToolRunResponse {
  tool_name: string;
  plugin_id: string;
  result: Record<string, unknown>;
  processing_time_ms: number;
}

/**
 * Bounding box detection.
 */
export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence?: number;
  class_name?: string;
  class_id?: number;
  track_id?: string | number;
  label?: string;
  color?: string;
}

/**
 * Ball detection result.
 */
export interface BallDetection {
  x: number;
  y: number;
  confidence?: number;
  radius?: number;
}

/**
 * Track history for persistence across frames.
 */
export interface TrackHistory {
  track_id: string | number;
  x: number;
  y: number;
  lastSeen: number; // frame index
  lastSeenTime: number; // timestamp ms
  fadeOut: boolean;
  confidence?: number;
}

/**
 * Processed video frame with results.
 */
export interface ProcessedFrame {
  frameIndex: number;
  frameId: string;
  result: Record<string, unknown>;
  processing_time_ms: number;
  timestamp: number;
  confidenceThreshold?: number;
}

/**
 * Frame buffer (ring FIFO).
 */
export interface FrameBuffer {
  frames: ProcessedFrame[];
  maxSize: number;
  add(frame: ProcessedFrame): void;
  getLast(count: number): ProcessedFrame[];
  clear(): void;
}

/**
 * Video processor options.
 */
export interface UseVideoProcessorOptions {
  pluginId: string;
  toolName: string;
  device?: "cpu" | "cuda";
  annotated?: boolean;
  fps?: number;
  maxFrames?: number; // max frames to buffer
  confidenceThreshold?: number;
}

/**
 * Video processor state.
 */
export interface UseVideoProcessorState {
  isProcessing: boolean;
  frames: ProcessedFrame[];
  trackMap: Map<string | number, TrackHistory>;
  error: string | null;
}

/**
 * Result overlay options.
 */
export interface ResultOverlayOptions {
  canvas: HTMLCanvasElement;
  frameWidth: number;
  frameHeight: number;
  detections: BoundingBox[];
  trackMap: Map<string | number, TrackHistory>;
  layers: {
    players: boolean;
    ball: boolean;
    pitch: boolean;
    radar: boolean;
  };
  confidenceThreshold: number;
}

/**
 * Overlay render hints (from manifest).
 */
export interface RenderHints {
  overlay_type?: "bounding_box" | "circle" | "line" | "points";
  color?: string;
  label_field?: string;
  confidence_field?: string;
  line_width?: number;
}
```

---

## Usage in Components

```typescript
// In a component
import { PluginManifest, ProcessedFrame, BoundingBox } from '@/types/plugin';

export function MyComponent() {
  const [manifest, setManifest] = useState<PluginManifest | null>(null);
  const [frames, setFrames] = useState<ProcessedFrame[]>([]);
  const [trackMap, setTrackMap] = useState<Map<string, TrackHistory>>(new Map());

  // Now TypeScript knows the shape of manifest, frames, etc.
  const tools = manifest?.tools ?? {};
  
  frames.forEach((frame) => {
    console.log(frame.result); // Properly typed
    console.log(frame.processing_time_ms); // Known property
  });

  trackMap.forEach((history) => {
    console.log(history.track_id); // Known property
  });
}
```

---

## Testing

**Location:** `forgesyte/web-ui/src/types/plugin.test.ts` (NEW)

```typescript
/**
 * Type validation tests (compile-time checks).
 */

import { describe, it, expect } from 'vitest';
import type {
  PluginManifest,
  ProcessedFrame,
  BoundingBox,
  TrackHistory,
} from './plugin';

describe('Plugin Types', () => {
  it('should validate PluginManifest type', () => {
    const manifest: PluginManifest = {
      id: 'test-plugin',
      name: 'Test Plugin',
      version: '1.0.0',
      tools: {
        detect: {
          description: 'Detect objects',
          inputs: {
            frame_base64: { type: 'string' },
          },
          outputs: {
            detections: { type: 'array' },
          },
        },
      },
    };

    expect(manifest.id).toBe('test-plugin');
    expect(manifest.tools).toHaveProperty('detect');
  });

  it('should validate ProcessedFrame type', () => {
    const frame: ProcessedFrame = {
      frameIndex: 0,
      frameId: 'frame-0',
      result: { detections: [] },
      processing_time_ms: 42,
      timestamp: Date.now(),
    };

    expect(frame.processing_time_ms).toBeGreaterThan(0);
  });

  it('should validate BoundingBox type', () => {
    const box: BoundingBox = {
      x1: 100,
      y1: 200,
      x2: 150,
      y2: 350,
      confidence: 0.92,
      track_id: '1',
    };

    expect(box.x1 < box.x2).toBe(true);
  });

  it('should validate TrackHistory type', () => {
    const track: TrackHistory = {
      track_id: '1',
      x: 100,
      y: 200,
      lastSeen: 5,
      lastSeenTime: Date.now(),
      fadeOut: false,
    };

    expect(track.track_id).toBe('1');
  });
});
```

**Run tests:**
```bash
cd forgesyte/web-ui
npm run test -- src/types/plugin.test.ts
```

---

## Integration with API Client

**Update:** `forgesyte/web-ui/src/api/client.ts`

```typescript
import { PluginManifest, PluginToolRunResponse, PluginToolRunRequest } from '@/types/plugin';

export class ForgeSyteAPIClient {
  // ... existing methods ...

  async getPluginManifest(pluginId: string): Promise<PluginManifest> {
    const result = await this.fetch(`/plugins/${pluginId}/manifest`);
    return result as PluginManifest;
  }

  async runPluginTool(
    pluginId: string,
    toolName: string,
    request: PluginToolRunRequest
  ): Promise<PluginToolRunResponse> {
    const result = await this.fetch(
      `/plugins/${pluginId}/tools/${toolName}/run`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    return result as PluginToolRunResponse;
  }
}
```

---

## Related Files

- [HOOK_USE_MANIFEST.md](./HOOK_USE_MANIFEST.md) — Uses PluginManifest type
- [HOOK_USE_VIDEO_PROCESSOR.md](./HOOK_USE_VIDEO_PROCESSOR.md) — Uses ProcessedFrame, TrackHistory
- All component files use these types
