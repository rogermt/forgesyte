/* RED Tests for UI Controls.

These tests define the expected behavior for Phase 9 UI controls:
- Device selector with persistence
- Overlay toggles (boxes, labels, pitch, radar)
- FPS slider

Tests will FAIL until the components are implemented.
*/

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    clear: vi.fn(),
    removeItem: vi.fn(),
};
Object.defineProperty(globalThis, "localStorage", {
    value: localStorageMock,
    writable: true,
});

describe("UI Controls - Device Selector", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorageMock.getItem.mockReturnValue(null);
    });

    it("should render device selector with id #device-selector", async () => {
        // This test will FAIL until DeviceSelector component is implemented
        const { DeviceSelector } = await import("@/components/DeviceSelector");
        
        render(<DeviceSelector />);
        
        const selector = document.getElementById("device-selector");
        expect(selector).toBeInTheDocument();
    });

    it("should persist device preference to localStorage", async () => {
        const { DeviceSelector } = await import("@/components/DeviceSelector");
        
        render(<DeviceSelector />);
        
        // Select a device
        const select = document.getElementById("device-selector") as HTMLSelectElement;
        fireEvent.change(select, { target: { value: "nvidia" } });
        
        // Verify localStorage was called
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
            "forgesyte_device_preference",
            "nvidia"
        );
    });

    it("should restore device preference from localStorage on mount", async () => {
        localStorageMock.getItem.mockReturnValue("gpu");
        
        const { DeviceSelector } = await import("@/components/DeviceSelector");
        
        render(<DeviceSelector />);
        
        const select = document.getElementById("device-selector") as HTMLSelectElement;
        expect(select.value).toBe("gpu");
    });
});

describe("UI Controls - Overlay Toggles", () => {
    it("should render toggle-boxes with id #toggle-boxes", async () => {
        const { OverlayToggles } = await import("@/components/OverlayToggles");
        
        render(<OverlayToggles visibleLayers={{ boxes: true, labels: false, pitch: true, radar: false }} onChange={() => {}} />);
        
        const toggle = document.getElementById("toggle-boxes");
        expect(toggle).toBeInTheDocument();
    });

    it("should render toggle-labels with id #toggle-labels", async () => {
        const { OverlayToggles } = await import("@/components/OverlayToggles");
        
        render(<OverlayToggles visibleLayers={{ boxes: true, labels: false, pitch: true, radar: false }} onChange={() => {}} />);
        
        const toggle = document.getElementById("toggle-labels");
        expect(toggle).toBeInTheDocument();
    });

    it("should render toggle-pitch with id #toggle-pitch", async () => {
        const { OverlayToggles } = await import("@/components/OverlayToggles");
        
        render(<OverlayToggles visibleLayers={{ boxes: true, labels: false, pitch: true, radar: false }} onChange={() => {}} />);
        
        const toggle = document.getElementById("toggle-pitch");
        expect(toggle).toBeInTheDocument();
    });

    it("should render toggle-radar with id #toggle-radar", async () => {
        const { OverlayToggles } = await import("@/components/OverlayToggles");
        
        render(<OverlayToggles visibleLayers={{ boxes: true, labels: false, pitch: true, radar: false }} onChange={() => {}} />);
        
        const toggle = document.getElementById("toggle-radar");
        expect(toggle).toBeInTheDocument();
    });

    it("should be checkable (toggle functionality)", async () => {
        const { OverlayToggles } = await import("@/components/OverlayToggles");
        
        render(<OverlayToggles visibleLayers={{ boxes: true, labels: false, pitch: true, radar: false }} onChange={() => {}} />);
        
        const toggle = document.getElementById("toggle-boxes") as HTMLInputElement;
        
        // Initial state should be unchecked or checked (implementation dependent)
        // Just verify it's a toggle/checkbox
        expect(toggle.type).toBe("checkbox");
    });
});

describe("UI Controls - FPS Slider", () => {
    it("should render fps-slider with id #fps-slider", async () => {
        const { FPSSlider } = await import("@/components/FPSSlider");
        
        render(<FPSSlider />);
        
        const slider = document.getElementById("fps-slider");
        expect(slider).toBeInTheDocument();
    });

    it("should be a range input type", async () => {
        const { FPSSlider } = await import("@/components/FPSSlider");
        
        render(<FPSSlider />);
        
        const slider = document.getElementById("fps-slider") as HTMLInputElement;
        expect(slider.type).toBe("range");
    });

it("should have fps slider functionality", async () => {
        const { FPSSlider } = await import("@/components/FPSSlider");
        
        render(<FPSSlider />);
        
        const slider = document.getElementById("fps-slider") as HTMLInputElement;
        
        // Verify it's a range input with correct attributes
        expect(slider.type).toBe("range");
        expect(slider.min).toBe("1");
        expect(slider.max).toBe("120");
        
        // Verify it has a value (default 30)
        expect(slider.value).toBeTruthy();
    });

    it("should restore fps target from localStorage on mount", async () => {
        localStorageMock.getItem.mockReturnValue("60");
        
        const { FPSSlider } = await import("@/components/FPSSlider");
        
        render(<FPSSlider />);
        
        const slider = document.getElementById("fps-slider") as HTMLInputElement;
        expect(slider.value).toBe("60");
    });
});

describe("UI Controls - Loading State", () => {
    it("should render LoadingSpinner component", async () => {
        const { LoadingSpinner } = await import("@/components/LoadingSpinner");
        
        render(<LoadingSpinner />);
        
        expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("should show loading indicator", async () => {
        const { LoadingSpinner } = await import("@/components/LoadingSpinner");
        
        render(<LoadingSpinner />);
        
        // Should have some loading text or spinner role
        const spinner = screen.getByRole("status");
        expect(spinner).toBeInTheDocument();
    });
});

describe("UI Controls - Error State", () => {
    it("should render ErrorBanner component", async () => {
        const { ErrorBanner } = await import("@/components/ErrorBanner");
        
        render(<ErrorBanner message="Test error" />);
        
        expect(screen.getByText("Test error")).toBeInTheDocument();
    });

    it("should display error message", async () => {
        const { ErrorBanner } = await import("@/components/ErrorBanner");
        
        render(<ErrorBanner message="Connection failed" />);
        
        expect(screen.getByText("Connection failed")).toBeInTheDocument();
    });
});

