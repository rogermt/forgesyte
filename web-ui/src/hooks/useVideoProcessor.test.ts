/**
 * Tests for useVideoProcessor hook - Phase 13 tools[] update
 */

import { RefObject } from "react";
import { renderHook } from "@testing-library/react";
import { useVideoProcessor } from "./useVideoProcessor";
import { describe, it, expect } from "vitest";

describe("useVideoProcessor - Phase 13 tools[]", () => {

  it("accepts tools array parameter", () => {
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "test-plugin",
        tools: ["detect_players"],
        fps: 30,
        device: "cpu",
        enabled: false,
        bufferSize: 5,
      })
    );

    expect(result.current).toBeDefined();
    expect(result.current.error).toBeNull();
  });

  it("accepts multiple tools", () => {
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo",
        tools: ["detect_players", "track_players"],
        fps: 30,
        device: "cuda",
        enabled: false,
        bufferSize: 5,
      })
    );

    expect(result.current).toBeDefined();
  });

  it("type definition accepts tools array", () => {
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "test-plugin",
        tools: ["tool1", "tool2", "tool3"],
        fps: 30,
        device: "cpu",
        enabled: false,
      })
    );

    expect(result.current).toBeDefined();
  });
});

