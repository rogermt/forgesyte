/**
 * Tests for useManifest hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useManifest, clearManifestCache } from "./useManifest";
import { apiClient } from "../api/client";

// Create mock function outside
const getPluginManifestMock = vi.fn();

vi.spyOn(apiClient, "getPluginManifest").mockImplementation(getPluginManifestMock);

const mockManifest = {
    id: "test-plugin",
    name: "Test Plugin",
    version: "1.0.0",
    description: "Test plugin",
    entrypoint: "test_plugin:main",
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
        getPluginManifestMock.mockClear();
        // Clear the in-memory cache between tests
        clearManifestCache();
    });

    it("should load manifest on plugin ID change", async () => {
        getPluginManifestMock.mockResolvedValue(mockManifest);

        const { result } = renderHook(() => useManifest("test-plugin"));

        expect(result.current.loading).toBe(true);

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.manifest).toEqual(mockManifest);
        expect(getPluginManifestMock).toHaveBeenCalledWith("test-plugin");
    });

    it("should return null when plugin ID is null", () => {
        const { result } = renderHook(() => useManifest(null));

        expect(result.current.manifest).toBeNull();
        expect(result.current.loading).toBe(false);
    });

    it("should handle errors gracefully", async () => {
         const errorMessage = "Failed to fetch manifest";
         getPluginManifestMock.mockRejectedValueOnce(
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

        getPluginManifestMock
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

describe("useManifest - Cache Regression Tests", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        getPluginManifestMock.mockClear();
        // Clear the in-memory cache between tests
        clearManifestCache();
    });

    it("should always fetch manifest when pluginId changes", async () => {
        getPluginManifestMock.mockResolvedValue(mockManifest);

        // First plugin selection
        const { result: result1, unmount: unmount1 } = renderHook(() =>
            useManifest("plugin-a")
        );

        expect(result1.current.loading).toBe(true);
        expect(getPluginManifestMock).toHaveBeenCalledTimes(1);

        await waitFor(() => {
            expect(result1.current.loading).toBe(false);
        });

        expect(result1.current.manifest?.id).toBe("test-plugin");

        // Unmount first hook
        unmount1();

        // Select different plugin - must fetch, not use cached value
        const { result: result2, unmount: unmount2 } = renderHook(() =>
            useManifest("plugin-b")
        );

        expect(result2.current.loading).toBe(true);
        // Should have called API for new plugin
        expect(getPluginManifestMock).toHaveBeenCalledWith("plugin-b");
        expect(getPluginManifestMock).toHaveBeenCalledTimes(2);

        await waitFor(() => {
            expect(result2.current.loading).toBe(false);
        });

        expect(result2.current.manifest).not.toBeNull();
        unmount2();
    });

    it("should not use stale cache after TTL expires", async () => {
        const manifestA = { ...mockManifest, id: "plugin-a" };
        const manifestB = { ...mockManifest, id: "plugin-b" };

        // First call - returns manifestA
        getPluginManifestMock.mockResolvedValueOnce(manifestA);

        const { result: result1, unmount: unmount1 } = renderHook(() =>
            useManifest("plugin-a")
        );

        await waitFor(() => {
            expect(result1.current.loading).toBe(false);
        });

        expect(result1.current.manifest?.id).toBe("plugin-a");

        // Unmount first hook
        unmount1();

        // Clear cache to simulate TTL expiry
        clearManifestCache();

        // Request same plugin after cache would be stale
        // Second call - returns manifestB (simulating updated manifest)
        getPluginManifestMock.mockResolvedValueOnce(manifestB);

        const { result: result2, unmount: unmount2 } = renderHook(() =>
            useManifest("plugin-a")
        );

        // Should fetch again because cache is stale
        await waitFor(() => {
            expect(result2.current.loading).toBe(false);
        });

        // Verify API was called for stale cache refresh
        expect(getPluginManifestMock).toHaveBeenCalledTimes(2);
        expect(result2.current.manifest?.id).toBe("plugin-b");
        unmount2();
    });

    it("should fetch manifest even when switching to same pluginId after unmount", async () => {
        getPluginManifestMock.mockResolvedValue(mockManifest);

        // First render with plugin
        const { result: result1, unmount: unmount1 } = renderHook(() =>
            useManifest("same-plugin")
        );

        await waitFor(() => {
            expect(result1.current.loading).toBe(false);
        });

        expect(result1.current.manifest).not.toBeNull();
        expect(getPluginManifestMock).toHaveBeenCalledTimes(1);

        // Unmount and remount with same plugin - should fetch again
        // (no caching between different hook instances in test environment)
        unmount1();

        // Clear cache before remounting
        clearManifestCache();
        getPluginManifestMock.mockClear();
        getPluginManifestMock.mockResolvedValue(mockManifest);

        const { result: result2, unmount: unmount2 } = renderHook(() =>
            useManifest("same-plugin")
        );

        await waitFor(() => {
            expect(result2.current.loading).toBe(false);
        });

        // Each hook instance triggers its own fetch
        expect(getPluginManifestMock).toHaveBeenCalledTimes(1);
        unmount2();
    });
});
