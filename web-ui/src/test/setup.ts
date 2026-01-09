/**
 * Test setup for Vitest
 */

import { expect, afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Cleanup after each test
afterEach(() => {
    cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Mock navigator.mediaDevices
Object.defineProperty(navigator, "mediaDevices", {
    writable: true,
    value: {
        enumerateDevices: vi.fn().mockResolvedValue([]),
        getUserMedia: vi.fn().mockResolvedValue({
            getTracks: () => [],
        }),
    },
});
