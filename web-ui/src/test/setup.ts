/**
 * Test setup for Vitest
 */

import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";

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

// Mock HTMLMediaElement play
HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
HTMLMediaElement.prototype.pause = vi.fn();
HTMLMediaElement.prototype.load = vi.fn();

// Define CSS custom properties for tests
const getComputedStyle = window.getComputedStyle;
window.getComputedStyle = (element: Element) => {
    const style = getComputedStyle(element);
    // Create a new style object with CSS variables
    const newStyle = Object.create(style);
    // Override getPropertyValue to handle CSS variables
    const originalGetPropertyValue = style.getPropertyValue.bind(style);
    newStyle.getPropertyValue = (prop: string) => {
        if (prop.startsWith("--")) {
            const varName = prop;
            // Return CSS variable values or fallbacks
            const varValues: Record<string, string> = {
                "--text-primary": "#FFFFFF",
                "--text-secondary": "#B0B0B0",
                "--text-muted": "#808080",
                "--bg-primary": "#1A1A1A",
                "--bg-secondary": "#252525",
                "--bg-tertiary": "#333333",
                "--border-light": "#404040",
                "--border-color": "#404040",
                "--accent-primary": "#00BFFF",
                "--accent-secondary": "#FF1493",
                "--accent-orange": "#FF8C00",
                "--accent-green": "#4CAF50",
                "--accent-danger": "#DC3545",
                "--accent-warning": "#FFC107",
                "--accent-success": "#28A745",
            };
            return varValues[varName] || originalGetPropertyValue(varName) || "";
        }
        return originalGetPropertyValue(prop);
    };
    return newStyle;
};
