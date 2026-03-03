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
