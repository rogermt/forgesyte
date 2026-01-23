/**
 * Tests for useManifest hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useManifest } from "./useManifest";
import { apiClient } from "../api/client";

// Mock API client method
vi.spyOn(apiClient, "getPluginManifest");

const mockManifest = {
    id: "test-plugin",
    name: "Test Plugin",
    version: "1.0.0",
    description: "Test plugin",
    tools: {
        detect: {
            description: "Detect objects",
            inputs: { frame_base64: { type: "string" } },
            outputs: { detections: { type: "array" } },
        },
    },
};

describe("useManifest", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should load manifest on plugin ID change", async () => {
        vi.mocked(apiClient.getPluginManifest).mockResolvedValue(mockManifest);

        const { result } = renderHook(() => useManifest("test-plugin"));

        expect(result.current.loading).toBe(true);

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.manifest).toEqual(mockManifest);
        expect(apiClient.getPluginManifest).toHaveBeenCalledWith("test-plugin");
    });

    it("should return null when plugin ID is null", () => {
        const { result } = renderHook(() => useManifest(null));

        expect(result.current.manifest).toBeNull();
        expect(result.current.loading).toBe(false);
    });

    it("should handle errors gracefully", async () => {
         const errorMessage = "Failed to fetch manifest";
         vi.mocked(apiClient.getPluginManifest).mockRejectedValueOnce(
             new Error(errorMessage)
         );

        const { result } = renderHook(() => useManifest("test-plugin-error"));

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        // Error should be captured
        expect(result.current.manifest).toBeNull();
    });

    it("should return different manifests for different plugins", async () => {
        const manifest1 = {
            ...mockManifest,
            id: "plugin-1",
        };
        const manifest2 = {
            ...mockManifest,
            id: "plugin-2",
        };

        vi.mocked(apiClient.getPluginManifest)
            .mockResolvedValueOnce(manifest1)
            .mockResolvedValueOnce(manifest2);

        const { result: result1 } = renderHook(() => useManifest("plugin-1"));

        await waitFor(() => {
            expect(result1.current.loading).toBe(false);
        });

        expect(result1.current.manifest?.id).toBe("plugin-1");

        const { result: result2 } = renderHook(() => useManifest("plugin-2"));

        await waitFor(() => {
            expect(result2.current.loading).toBe(false);
        });

        expect(result2.current.manifest?.id).toBe("plugin-2");
    });
});
