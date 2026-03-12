/**
 * Tests for resolveVideoTools utility
 */

import { describe, it, expect } from "vitest";
import { resolveVideoTools } from "./resolveVideoTools";
import type { PluginManifest } from "../types/plugin";

describe("resolveVideoTools", () => {
  it("returns logical tools unchanged when manifest is null", () => {
    const logicalTools = ["player_detection", "ball_detection"];
    const result = resolveVideoTools(logicalTools, null);
    expect(result).toEqual(logicalTools);
  });

  it("returns logical tools unchanged when manifest has no tools", () => {
    const manifest = {
      id: "test",
      name: "test",
      version: "1.0.0",
      entrypoint: "test",
      tools: {},
    } as PluginManifest;
    const logicalTools = ["player_detection"];
    const result = resolveVideoTools(logicalTools, manifest);
    expect(result).toEqual(logicalTools);
  });

  it("maps logical capability to video tool ID using input_types and capabilities", () => {
    const manifest: PluginManifest = {
      id: "yolo-tracker",
      name: "YOLO Tracker",
      version: "1.0.0",
      entrypoint: "yolo",
      tools: {
        player_detection: {
          id: "player_detection",
          title: "Image Player Detection",
          input_types: ["image_bytes"],
          capabilities: ["player_detection"],
          inputs: {},
          outputs: {},
        },
        video_player_tracking: {
          id: "video_player_tracking",
          title: "Video Player Tracking",
          input_types: ["video"],
          capabilities: ["player_detection", "streaming_video_analysis"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["player_detection"], manifest);
    expect(result).toEqual(["video_player_tracking"]);
  });

  it("handles array manifest format", () => {
    const manifest = {
      id: "yolo-tracker",
      name: "YOLO Tracker",
      version: "1.0.0",
      entrypoint: "yolo",
      tools: [
        {
          id: "video_player_tracking",
          title: "Video Player Tracking",
          input_types: ["video"],
          capabilities: ["player_detection"],
          inputs: {},
          outputs: {},
        },
        {
          id: "video_ball_detection",
          title: "Video Ball Detection",
          input_types: ["video"],
          capabilities: ["ball_detection"],
          inputs: {},
          outputs: {},
        },
      ],
    } as unknown as PluginManifest;

    const result = resolveVideoTools(["player_detection", "ball_detection"], manifest);
    expect(result).toEqual(["video_player_tracking", "video_ball_detection"]);
  });

  it("handles object manifest format", () => {
    const manifest: PluginManifest = {
      id: "yolo-tracker",
      name: "YOLO Tracker",
      version: "1.0.0",
      entrypoint: "yolo",
      tools: {
        video_player_tracking: {
          id: "video_player_tracking",
          title: "Video Player Tracking",
          input_types: ["video"],
          capabilities: ["player_detection"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["player_detection"], manifest);
    expect(result).toEqual(["video_player_tracking"]);
  });

  it("falls back to logical tool when no video tool found", () => {
    const manifest: PluginManifest = {
      id: "ocr",
      name: "OCR",
      version: "1.0.0",
      entrypoint: "ocr",
      tools: {
        analyze: {
          id: "analyze",
          title: "Image Analysis",
          input_types: ["image_bytes"],
          capabilities: ["text_extraction"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["player_detection"], manifest);
    expect(result).toEqual(["player_detection"]);
  });

  it("ignores tools without capabilities", () => {
    const manifest: PluginManifest = {
      id: "test",
      name: "test",
      version: "1.0.0",
      entrypoint: "test",
      tools: {
        video_tool: {
          id: "video_tool",
          title: "Video Tool",
          input_types: ["video"],
          // No capabilities
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["player_detection"], manifest);
    expect(result).toEqual(["player_detection"]); // Falls back
  });

  it("ignores tools without video input_types", () => {
    const manifest: PluginManifest = {
      id: "test",
      name: "test",
      version: "1.0.0",
      entrypoint: "test",
      tools: {
        image_tool: {
          id: "image_tool",
          title: "Image Tool",
          input_types: ["image_bytes"],
          capabilities: ["player_detection"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["player_detection"], manifest);
    expect(result).toEqual(["player_detection"]); // Falls back
  });

  it("maps multiple logical tools to video tools", () => {
    const manifest: PluginManifest = {
      id: "yolo-tracker",
      name: "YOLO Tracker",
      version: "1.0.0",
      entrypoint: "yolo",
      tools: {
        video_player_tracking: {
          id: "video_player_tracking",
          title: "Video Player Tracking",
          input_types: ["video"],
          capabilities: ["player_detection"],
          inputs: {},
          outputs: {},
        },
        video_ball_detection: {
          id: "video_ball_detection",
          title: "Video Ball Detection",
          input_types: ["video"],
          capabilities: ["ball_detection"],
          inputs: {},
          outputs: {},
        },
        video_pitch_detection: {
          id: "video_pitch_detection",
          title: "Video Pitch Detection",
          input_types: ["video"],
          capabilities: ["pitch_detection"],
          inputs: {},
          outputs: {},
        },
        video_radar: {
          id: "video_radar",
          title: "Video Radar",
          input_types: ["video"],
          capabilities: ["radar"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(
      ["player_detection", "ball_detection", "pitch_detection", "radar"],
      manifest
    );
    expect(result).toEqual([
      "video_player_tracking",
      "video_ball_detection",
      "video_pitch_detection",
      "video_radar",
    ]);
  });
});

// -------------------------------------------------------------------------
// v0.13.12: REGRESSION TESTS - Real Manifest Format
// These tests use the ACTUAL manifest structure from plugins/yolo/manifest.json
// to catch bugs where tool ID ≠ capability name.
// -------------------------------------------------------------------------

describe("resolveVideoTools - real manifest format (v0.13.12 regression prevention)", () => {
  // EXACT structure from plugins/yolo/manifest.json
  const realYoloManifest: PluginManifest = {
    id: "yolo",
    name: "yolo",
    version: "1.0.0",
    description: "YOLO object detection plugin (Phase 15)",
    entrypoint: "plugin.py",
    tools: {
      detect_objects: {
        description: "Detect objects in image using YOLO",
        input_types: ["image_bytes"],
        output_types: ["detections"],
        capabilities: ["object_detection"],
        inputs: {},
        outputs: {},
      },
      video_player_detection: {
        title: "Video Player Detection",
        description: "Run player detection on every frame of a video.",
        input_types: ["video"],
        output_types: ["video_detections"],
        capabilities: ["player_detection"],
        inputs: {
          video_path: { type: "string" },
          device: { type: "string", default: "cpu" },
          annotated: { type: "boolean", default: false },
        },
        outputs: {
          frames: { type: "array" },
          summary: { type: "object" },
        },
      },
    },
  };

  it("CRITICAL: player_detection capability maps to video_player_detection tool ID", () => {
    // This is the EXACT bug we fixed in v0.13.12
    // If this test fails, someone broke the capability→tool ID mapping
    const result = resolveVideoTools(["player_detection"], realYoloManifest);
    expect(result).toEqual(["video_player_detection"]);
  });

  it("CRITICAL: does NOT map player_detection to detect_objects (image tool)", () => {
    // This catches the v0.13.11 bug where resolveVideoTools returned ["detect_objects"]
    // because detect_objects was the first tool in the manifest
    const result = resolveVideoTools(["player_detection"], realYoloManifest);
    // Should NEVER return detect_objects for player_detection capability
    expect(result).not.toContain("detect_objects");
  });

  it("maps object_detection capability correctly (no video tool)", () => {
    // object_detection only has image tool, should fall back
    const result = resolveVideoTools(["object_detection"], realYoloManifest);
    // Falls back because detect_objects has input_types: ["image_bytes"], not ["video"]
    expect(result).toEqual(["object_detection"]);
  });

  it("handles multiple capabilities with mixed tool types", () => {
    // player_detection → video tool, object_detection → falls back
    const result = resolveVideoTools(
      ["player_detection", "object_detection"],
      realYoloManifest
    );
    expect(result).toEqual(["video_player_detection", "object_detection"]);
  });

  it("preserves tool ID from object key in legacy format", () => {
    // The v0.13.11 fix: Object.entries preserves the key as tool ID
    // This test ensures we don't regress to Object.values() which loses the key
    const manifestWithObjectTools: PluginManifest = {
      id: "test",
      name: "test",
      version: "1.0.0",
      entrypoint: "test",
      tools: {
        my_video_tool: {
          // This key IS the tool ID
          title: "My Video Tool",
          input_types: ["video"],
          capabilities: ["my_capability"],
          inputs: {},
          outputs: {},
        },
      },
    };

    const result = resolveVideoTools(["my_capability"], manifestWithObjectTools);
    // Must return the OBJECT KEY as tool ID, not some other value
    expect(result).toEqual(["my_video_tool"]);
  });
});
