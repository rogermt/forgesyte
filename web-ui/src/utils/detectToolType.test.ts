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
