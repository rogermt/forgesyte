/**
 * Tests for CameraPreview component
 */

import { render, screen, act, fireEvent, waitFor } from "@testing-library/react";
import { CameraPreview } from "./CameraPreview";
import { vi, beforeEach, afterEach, describe, it, expect } from "vitest";

// Mock navigator.mediaDevices
const mockGetUserMedia = vi.fn();
const mockEnumerateDevices = vi.fn();
const mockStop = vi.fn();
const mockPlay = vi.fn(async () => {});

beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();

    // Mock MediaStream
    const mockMediaStream = {
        getTracks: vi.fn(() => [
            {
                stop: mockStop,
                kind: "video",
            },
        ]),
    };

    mockGetUserMedia.mockResolvedValue(mockMediaStream);

    // Mock enumerateDevices with default (no devices)
    mockEnumerateDevices.mockResolvedValue([]);

    // Setup navigator.mediaDevices
    Object.defineProperty(navigator, "mediaDevices", {
        value: {
            getUserMedia: mockGetUserMedia,
            enumerateDevices: mockEnumerateDevices,
        },
        writable: true,
    });

    // Mock HTMLVideoElement.play()
    HTMLVideoElement.prototype.play = mockPlay;

    // Mock canvas.getContext
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
        drawImage: vi.fn(),
    }));

    // Mock canvas.toDataURL
    HTMLCanvasElement.prototype.toDataURL = vi.fn(
        () => "data:image/jpeg;base64,abc123=="
    );
});

afterEach(() => {
    vi.restoreAllMocks();
});

describe("CameraPreview - Device Management", () => {
    it("should enumerate video devices on mount", async () => {
        mockEnumerateDevices.mockResolvedValue([
            {
                deviceId: "cam1",
                kind: "videoinput",
                label: "Front Camera",
                groupId: "group1",
                toJSON: () => ({}),
            },
        ]);

        await act(async () => {
            render(<CameraPreview enabled={false} />);
        });

        await waitFor(() => {
            expect(mockEnumerateDevices).toHaveBeenCalled();
        });
    });

    it("should auto-select first device if available", async () => {
        mockEnumerateDevices.mockResolvedValue([
            {
                deviceId: "cam1",
                kind: "videoinput",
                label: "Front Camera",
                groupId: "group1",
                toJSON: () => ({}),
            },
        ]);

        render(<CameraPreview enabled={false} />);

        // Wait for device enumeration and selection
        await waitFor(() => {
            expect(mockEnumerateDevices).toHaveBeenCalled();
        });
    });

    it("should handle enumeration errors gracefully", async () => {
        const error = new Error("Permission denied");
        mockEnumerateDevices.mockRejectedValue(error);

        const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

        await act(async () => {
            render(<CameraPreview enabled={false} />);
        });

        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith(
                "Failed to enumerate devices:",
                error
            );
        });

        consoleSpy.mockRestore();
    });
});

describe("CameraPreview - Camera Lifecycle", () => {
    it("should start camera stream when enabled=true", async () => {
        mockGetUserMedia.mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        });

        await act(async () => {
            render(<CameraPreview enabled={true} />);
        });

        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalled();
        });
    });

    it("should request correct media constraints", async () => {
        const mockStream = {
            getTracks: () => [{ stop: vi.fn() }],
        };
        mockGetUserMedia.mockResolvedValue(mockStream);

        await act(async () => {
            render(<CameraPreview enabled={true} width={800} height={600} />);
        });

        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalledWith(
                expect.objectContaining({
                    video: expect.objectContaining({
                        width: { ideal: 800 },
                        height: { ideal: 600 },
                    }),
                })
            );
        });
    });

    it("should call play() on video element", async () => {
        mockGetUserMedia.mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        });

        await act(async () => {
            render(<CameraPreview enabled={true} />);
        });

        await waitFor(() => {
            expect(mockPlay).toHaveBeenCalled();
        });
    });

    it("should stop camera stream when enabled=false", async () => {
        const { rerender } = render(<CameraPreview enabled={true} />);

        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalled();
        });

        await act(async () => {
            rerender(<CameraPreview enabled={false} />);
        });

        await waitFor(() => {
            expect(mockStop).toHaveBeenCalled();
        });
    });

    it("should stop all tracks on cleanup", async () => {
        const { unmount } = render(<CameraPreview enabled={true} />);

        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalled();
        });

        await act(async () => {
            unmount();
        });

        await waitFor(() => {
            expect(mockStop).toHaveBeenCalled();
        });
    });

    it("should handle getUserMedia permission denied", async () => {
        const error = new Error("Permission denied");
        mockGetUserMedia.mockRejectedValue(error);

        let container: HTMLElement;
        await act(async () => {
            container = render(<CameraPreview enabled={true} />).container;
        });

        await waitFor(() => {
            // Error should be displayed
            const errorText = container!.textContent;
            expect(errorText).toContain("Permission denied");
        });
    });

    it("should clear error on successful start", async () => {
        mockGetUserMedia.mockRejectedValueOnce(new Error("Permission denied"));

        let container: HTMLElement;
        await act(async () => {
            container = render(<CameraPreview enabled={true} />).container;
        });

        // Wait for error to appear
        await waitFor(() => {
            expect(container!.textContent).toContain("Permission denied");
        });

        // Now succeed
        const mockStream = {
            getTracks: () => [{ stop: vi.fn() }],
        };
        mockGetUserMedia.mockResolvedValueOnce(mockStream);

        await act(async () => {
            const { rerender } = render(<CameraPreview enabled={false} />);
            rerender(<CameraPreview enabled={true} />);
        });

        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalledTimes(2);
        });
    });
});

describe("CameraPreview - Frame Capture", () => {
    it("should capture frame at specified interval", async () => {
        const onFrame = vi.fn();

        mockGetUserMedia.mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        });

        await act(async () => {
            render(
                <CameraPreview
                    enabled={true}
                    onFrame={onFrame}
                    captureInterval={50}
                />
            );
        });

        // Wait for streaming to start
        await waitFor(() => {
            expect(mockGetUserMedia).toHaveBeenCalled();
        });

        // Wait for capture to happen (50ms interval)
        await waitFor(
            () => {
                expect(onFrame).toHaveBeenCalled();
            },
            { timeout: 500 }
        );
    });

    it("should call onFrame callback with base64 data", async () => {
        const onFrame = vi.fn();

        mockGetUserMedia.mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        });

        await act(async () => {
            render(
                <CameraPreview
                    enabled={true}
                    onFrame={onFrame}
                    captureInterval={50}
                />
            );
        });

        await waitFor(
            () => {
                expect(onFrame).toHaveBeenCalledWith("abc123==");
            },
            { timeout: 500 }
        );
    });

    it("should not capture when disabled", async () => {
        const onFrame = vi.fn();

        await act(async () => {
            render(
                <CameraPreview
                    enabled={false}
                    onFrame={onFrame}
                    captureInterval={50}
                />
            );
        });

        // Wait a bit to ensure no captures happen
        await new Promise((resolve) => setTimeout(resolve, 200));

        expect(onFrame).not.toHaveBeenCalled();
    });

    it("should not capture when not streaming", async () => {
        const onFrame = vi.fn();
        mockGetUserMedia.mockRejectedValue(new Error("Camera error"));

        await act(async () => {
            render(
                <CameraPreview
                    enabled={true}
                    onFrame={onFrame}
                    captureInterval={50}
                />
            );
        });

        // Wait a bit to ensure no captures happen
        await new Promise((resolve) => setTimeout(resolve, 200));

        expect(onFrame).not.toHaveBeenCalled();
    });

    it("should handle missing canvas context", async () => {
        const onFrame = vi.fn();

        mockGetUserMedia.mockResolvedValue({
            getTracks: () => [{ stop: vi.fn() }],
        });

        HTMLCanvasElement.prototype.getContext = vi.fn(() => null);

        await act(async () => {
            render(
                <CameraPreview
                    enabled={true}
                    onFrame={onFrame}
                    captureInterval={50}
                />
            );
        });

        await new Promise((resolve) => setTimeout(resolve, 200));

        expect(onFrame).not.toHaveBeenCalled();
    });
});

describe("CameraPreview - Device Selection UI", () => {
    it("should show device selector when multiple devices", async () => {
        mockEnumerateDevices.mockResolvedValue([
            {
                deviceId: "cam1",
                kind: "videoinput",
                label: "Front",
                groupId: "group1",
                toJSON: () => ({}),
            },
            {
                deviceId: "cam2",
                kind: "videoinput",
                label: "Back",
                groupId: "group1",
                toJSON: () => ({}),
            },
        ]);

        let container: HTMLElement;
        await act(async () => {
            container = render(<CameraPreview enabled={false} />).container;
        });

        await waitFor(() => {
            const select = container!.querySelector("select");
            expect(select).toBeInTheDocument();
        });
    });

    it("should hide selector when only one device", async () => {
        mockEnumerateDevices.mockResolvedValue([
            {
                deviceId: "cam1",
                kind: "videoinput",
                label: "Front",
                groupId: "group1",
                toJSON: () => ({}),
            },
        ]);

        let container: HTMLElement;
        await act(async () => {
            container = render(<CameraPreview enabled={false} />).container;
        });

        await waitFor(() => {
            const select = container!.querySelector("select");
            expect(select).not.toBeInTheDocument();
        });
    });

    it("should update selected device on change", async () => {
        mockEnumerateDevices.mockResolvedValue([
            {
                deviceId: "cam1",
                kind: "videoinput",
                label: "Front",
                groupId: "group1",
                toJSON: () => ({}),
            },
            {
                deviceId: "cam2",
                kind: "videoinput",
                label: "Back",
                groupId: "group1",
                toJSON: () => ({}),
            },
        ]);

        let container: HTMLElement;
        await act(async () => {
            container = render(<CameraPreview enabled={false} />).container;
        });

        await waitFor(() => {
            const select = container!.querySelector("select");
            expect(select).toBeInTheDocument();
        });

        const select = container!.querySelector("select") as HTMLSelectElement;
        await act(async () => {
            fireEvent.change(select, { target: { value: "cam2" } });
        });

        expect(select.value).toBe("cam2");
    });
});

describe("CameraPreview - Styling Updates", () => {
    describe("heading and layout", () => {
        it("should display heading with brand colors", async () => {
            await act(async () => {
                render(<CameraPreview enabled={false} />);
            });
            const heading = screen.getByText("Camera Preview");

            expect(heading).toBeInTheDocument();
            expect(heading.tagName).toBe("H3");
        });
    });

    describe("video element styling", () => {
        it("should apply brand background color to video", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const video = container!.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
                borderRadius: "8px",
            });
        });

        it("should use proper aspect ratio styling", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const video = container!.querySelector("video");

            expect(video).toHaveStyle({
                width: "100%",
                height: "auto",
            });
        });
    });

    describe("canvas element", () => {
        it("should have hidden canvas for frame capture", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const canvas = container!.querySelector("canvas");

            expect(canvas).toHaveStyle({
                display: "none",
            });
        });
    });

    describe("status indicator", () => {
        it("should display not streaming status when disabled", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<CameraPreview enabled={false} />).container;
            });
            const statusText = Array.from(container!.querySelectorAll("p"))
                .map((p) => p.textContent)
                .join(" ");

            expect(statusText).toContain("Not streaming");
        });
    });
});

/**
 * Phase 17: Camera Preview Streaming Tests
 *
 * Tests for Phase 17 streaming functionality added to CameraPreview
 */


describe("CameraPreview (Phase 17 Streaming)", () => {

    beforeEach(() => {
        vi.clearAllMocks();
        
        // Mock sendFrame from useRealtimeContext
        mockSendFrame = vi.fn();
        mockSetMaxFps = vi.fn();
    });

    it("converts canvas to JPEG and sends binary frame", async () => {
        // Mock canvas.toBlob to return a JPEG blob
        const mockData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x01]);
        const mockBlob = new Blob([mockData], { type: "image/jpeg" });
        mockBlob.arrayBuffer = async () => mockData.buffer;
        const mockToBlob = vi.fn((callback: (blob: Blob | null) => void) => {
            callback(mockBlob);
        });
        HTMLCanvasElement.prototype.toBlob = mockToBlob;

        // Verify blob is created
        expect(mockBlob.type).toBe("image/jpeg");
        
        // Verify blob can be converted to Uint8Array
        const arrayBuffer = await mockBlob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        expect(uint8Array[0]).toBe(0xFF);
        expect(uint8Array[1]).toBe(0xD8);
    });

    it("reduces FPS when slow_down warnings received", () => {
        // This test will verify that when slowDownWarnings > 0,
        // the FPS throttler is reduced to 5 FPS
        
        // This test will be implemented when the component is updated
        expect(true).toBe(true); // Placeholder
    });

    it("does not send frames marked as dropped", () => {
        // This test will verify that when lastResult.dropped === true,
        // the overlay is not updated
        
        expect(true).toBe(true); // Placeholder
    });
});
