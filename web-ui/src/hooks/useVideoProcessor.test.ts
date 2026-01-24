/**
 * Tests for useVideoProcessor hook
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useVideoProcessor } from "./useVideoProcessor";
import type { VideoProcessorConfig } from "../types/video-tracker";
import { apiClient } from "../api/client";

// Mock API client method
vi.spyOn(apiClient, "runPluginTool");

const mockConfig: VideoProcessorConfig = {
    pluginId: "test-plugin",
    toolName: "detect",
    device: "cpu",
    annotated: false,
};

const mockResponse = {
    tool_name: "detect",
    plugin_id: "test-plugin",
    result: {
        detections: [
            {
                x: 100,
                y: 100,
                width: 50,
                height: 100,
                confidence: 0.95,
                class: "object",
            },
        ],
    },
    processing_time_ms: 42,
};

describe("useVideoProcessor", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should initialize with default state", () => {
        const { result } = renderHook(() => useVideoProcessor(null));

        expect(result.current.state.isProcessing).toBe(false);
        expect(result.current.state.frameCount).toBe(0);
        expect(result.current.frames).toEqual([]);
        expect(result.current.detections).toEqual([]);
    });

    it("should process a single frame", async () => {
        vi.mocked(apiClient.runPluginTool).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useVideoProcessor(mockConfig));

        act(() => {
            result.current.start();
        });

        act(() => {
            result.current.processFrame("base64encodedframe");
        });

        await waitFor(() => {
            expect(result.current.state.isProcessing).toBe(false);
        });

        expect(result.current.state.frameCount).toBe(1);
        expect(result.current.detections).toHaveLength(1);
        expect(result.current.detections[0].x).toBe(100);
    });

    it("should maintain frame buffer up to max size", async () => {
        vi.mocked(apiClient.runPluginTool).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useVideoProcessor(mockConfig));

        act(() => {
            result.current.start();
        });

        // Process more frames than buffer size
        for (let i = 0; i < 15; i++) {
            act(() => {
                result.current.processFrame(`frame${i}`);
            });
        }

        await waitFor(() => {
            expect(result.current.frames.length).toBeLessThanOrEqual(10);
        });
    });

    it("should handle errors gracefully", async () => {
        const errorMessage = "API error";
        vi.mocked(apiClient.runPluginTool).mockRejectedValueOnce(
            new Error(errorMessage)
        );

        const { result } = renderHook(() => useVideoProcessor(mockConfig));

        act(() => {
            result.current.start();
        });

        act(() => {
            result.current.processFrame("base64encodedframe");
        });

        await waitFor(() => {
            expect(result.current.state.isProcessing).toBe(false);
        });

        expect(result.current.state.error).toBe(errorMessage);
    });

    it("should return null config when config is null", async () => {
        vi.mocked(apiClient.runPluginTool).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useVideoProcessor(null));

        act(() => {
            result.current.processFrame("base64encodedframe");
        });

        expect(result.current.state.error).toBe("No config provided");
    });

    it("should clear buffers on clear()", () => {
        vi.mocked(apiClient.runPluginTool).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useVideoProcessor(mockConfig));

        act(() => {
            result.current.start();
            result.current.processFrame("frame1");
        });

        act(() => {
            result.current.clear();
        });

        expect(result.current.frames).toEqual([]);
        expect(result.current.detections).toEqual([]);
        expect(result.current.state.frameCount).toBe(0);
    });
});
