/**
 * Tests for useVideoProcessor hook - Phase 13 tools[] update
 *
 * Issue #348: UI freezes after video upload due to infinite render loop.
 * Root cause: tools array reference changes on every parent render,
 * triggering interval recreation in useEffect.
 */

import { RefObject } from "react";
import { renderHook } from "@testing-library/react";
import { useVideoProcessor } from "./useVideoProcessor";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

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

// ---------------------------------------------------------------------------
// Issue #348: Regression test for infinite render loop
// This test will FAIL before the fix and PASS after.
// ---------------------------------------------------------------------------
describe("useVideoProcessor - Issue #348: Interval stability", () => {
  let setIntervalSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setIntervalSpy = vi.spyOn(window, "setInterval");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should NOT recreate interval when parent rerenders with same tools VALUES (new reference)", () => {
    // This test catches the bug: tools array with same values but new reference
    // triggers interval recreation, causing infinite render loop.

    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    // Use a callback pattern so we can control the props
    const { rerender } = renderHook(
      ({ tools }: { tools: string[] }) =>
        useVideoProcessor({
          videoRef,
          pluginId: "test-plugin",
          tools,
          fps: 30,
          device: "cpu",
          enabled: true, // Enable to start interval
        }),
      { initialProps: { tools: ["tool1"] } }
    );

    // Initial render should create ONE interval
    expect(setIntervalSpy).toHaveBeenCalledTimes(1);

    // Reset the spy to count new calls
    setIntervalSpy.mockClear();

    // Rerender with NEW array reference but SAME values
    // This is what happens in App.tsx: lockedTools ?? selectedTools
    rerender({ tools: ["tool1"] }); // New array, same values
    rerender({ tools: ["tool1"] }); // Another new array
    rerender({ tools: ["tool1"] }); // Another new array

    // BUG: Currently this creates new intervals because tools is in deps
    // FIX: After using ref pattern, setInterval should NOT be called again
    expect(setIntervalSpy).toHaveBeenCalledTimes(0);
  });

  it("should only recreate interval when fps changes", () => {
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { rerender } = renderHook(
      ({ fps }: { fps: number }) =>
        useVideoProcessor({
          videoRef,
          pluginId: "test-plugin",
          tools: ["tool1"],
          fps,
          device: "cpu",
          enabled: true,
        }),
      { initialProps: { fps: 30 } }
    );

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
    setIntervalSpy.mockClear();

    // Change fps - this SHOULD recreate interval
    rerender({ fps: 60 });

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
  });

  it("should only recreate interval when enabled changes from false to true", () => {
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) =>
        useVideoProcessor({
          videoRef,
          pluginId: "test-plugin",
          tools: ["tool1"],
          fps: 30,
          device: "cpu",
          enabled,
        }),
      { initialProps: { enabled: false } }
    );

    // Not enabled, no interval created
    expect(setIntervalSpy).toHaveBeenCalledTimes(0);

    // Enable - should create interval
    rerender({ enabled: true });

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
  });

  it("should NOT recreate interval when device changes", () => {
    // Issue #348: device was in deps array causing unnecessary interval recreation
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { rerender } = renderHook(
      ({ device }: { device: string }) =>
        useVideoProcessor({
          videoRef,
          pluginId: "test-plugin",
          tools: ["tool1"],
          fps: 30,
          device,
          enabled: true,
        }),
      { initialProps: { device: "cpu" } }
    );

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
    setIntervalSpy.mockClear();

    // Change device - should NOT recreate interval
    rerender({ device: "cuda" });

    expect(setIntervalSpy).toHaveBeenCalledTimes(0);
  });

  it("should NOT recreate interval when pluginId changes", () => {
    // Issue #348: pluginId was in deps array causing unnecessary interval recreation
    const videoRef: RefObject<HTMLVideoElement> = { current: null };

    const { rerender } = renderHook(
      ({ pluginId }: { pluginId: string }) =>
        useVideoProcessor({
          videoRef,
          pluginId,
          tools: ["tool1"],
          fps: 30,
          device: "cpu",
          enabled: true,
        }),
      { initialProps: { pluginId: "plugin-a" } }
    );

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
    setIntervalSpy.mockClear();

    // Change pluginId - should NOT recreate interval
    rerender({ pluginId: "plugin-b" });

    expect(setIntervalSpy).toHaveBeenCalledTimes(0);
  });
});

