import { describe, it, expect } from "vitest";
import { detectToolType } from "./detectToolType";
import type { PluginManifest } from "../types/plugin";

const mockManifest: PluginManifest = {
  id: "test-plugin",
  name: "Test Plugin",
  version: "1.0.0",
  entrypoint: "test.plugin",
  tools: {
    stream_tool: {
      inputs: { stream_id: "string" },
      outputs: { result: "string" },
    },
    frame_tool: {
      inputs: { frame_base64: "string" },
      outputs: { detections: "array" },
    },
    image_tool: {
      inputs: { image_url: "string" },
      outputs: { analysis: "string" },
    },
  },
};

describe("detectToolType", () => {
  it("returns 'stream' when stream_id in inputs", () => {
    const result = detectToolType(mockManifest, "stream_tool");
    expect(result).toBe("stream");
  });

  it("returns 'frame' when frame_base64 in inputs", () => {
    const result = detectToolType(mockManifest, "frame_tool");
    expect(result).toBe("frame");
  });

  it("returns 'image' for other inputs", () => {
    const result = detectToolType(mockManifest, "image_tool");
    expect(result).toBe("image");
  });

  it("returns 'unknown' for missing tool", () => {
    const result = detectToolType(mockManifest, "nonexistent_tool");
    expect(result).toBe("unknown");
  });
});

// -------------------------------------------------------------------------
// v0.13.12: REGRESSION TESTS - Tool ID vs Capability Mismatch
// These tests catch the bug where toolList used tool IDs but ToolSelector
// displayed capabilities, causing auto-selection to reset user choices.
// -------------------------------------------------------------------------

describe("detectToolType - capability lookup (v0.13.12 regression prevention)", () => {
  // Manifest structure matching REAL yolo manifest
  const realYoloManifest: PluginManifest = {
    id: "yolo",
    name: "YOLO",
    version: "1.0.0",
    entrypoint: "plugin.py",
    tools: {
      detect_objects: {
        description: "Detect objects in image using YOLO",
        input_types: ["image_bytes"],
        output_types: ["detections"],
        capabilities: ["object_detection"],
        inputs: { image: { type: "string" } },
        outputs: { detections: { type: "array" } },
      },
      video_player_detection: {
        title: "Video Player Detection",
        description: "Run player detection on every frame of a video.",
        input_types: ["video"],
        output_types: ["video_detections"],
        capabilities: ["player_detection"],
        inputs: { video_path: { type: "string" } },
        outputs: { frames: { type: "array" } },
      },
    },
  };

  it("finds tool by capability name when tool ID differs", () => {
    // Tool ID is "video_player_detection", capability is "player_detection"
    const result = detectToolType(realYoloManifest, "player_detection");
    expect(result).toBe("frame"); // Video tool = frame type
  });

  it("finds tool by capability for image tool", () => {
    // Tool ID is "detect_objects", capability is "object_detection"
    const result = detectToolType(realYoloManifest, "object_detection");
    expect(result).toBe("image"); // Image tool = image type
  });

  it("still works with direct tool ID lookup", () => {
    const result = detectToolType(realYoloManifest, "video_player_detection");
    expect(result).toBe("frame");
  });

  it("returns 'unknown' for non-existent capability", () => {
    const result = detectToolType(realYoloManifest, "nonexistent_capability");
    expect(result).toBe("unknown");
  });

  it("CRITICAL: capability lookup finds video tool (not image tool)", () => {
    // This test catches the v0.13.11 bug where player_detection would resolve
    // to detect_objects (image tool) instead of video_player_detection (video tool)
    const result = detectToolType(realYoloManifest, "player_detection");
    // If this returns "image" instead of "frame", the bug is back
    expect(result).toBe("frame");
  });
});
