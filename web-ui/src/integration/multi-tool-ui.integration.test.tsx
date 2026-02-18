/**
 * Integration tests for Multi-Tool Image Analysis UI
 *
 * Tests the complete user flow from selecting the multi-tool mode
 * to running analysis and viewing results.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        analyzeMulti: vi.fn(),
        getPlugins: vi.fn(),
        getPluginManifest: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

describe("Multi-Tool UI Integration", () => {
    beforeEach(() => {
        vi.clearAllMocks();

        // Mock plugins
        (apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue([
            { name: "ocr", description: "OCR", version: "1.0.0" },
            { name: "yolo-tracker", description: "YOLO", version: "1.0.0" }
        ]);

        // Mock WebSocket hook
        vi.mock("../hooks/useWebSocket", () => ({
            useWebSocket: () => ({
                isConnected: false,
                connectionStatus: "disconnected",
                attempt: 0,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                reconnect: vi.fn(),
                latestResult: null,
            }),
        }));
    });

    it("should complete full multi-tool flow", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue({
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
                "yolo-tracker": { detections: [] }
            }
        });

        render(<App />);

        // Switch to multi-tool mode
        const multiToolButton = screen.getByText(/multi-tool/i);
        fireEvent.click(multiToolButton);

        await waitFor(() => {
            expect(screen.getByText(/multi-tool image analysis/i)).toBeInTheDocument();
        });

        // Select file
        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Select tools - need to find checkboxes within the multi-tool form
        const checkboxes = screen.getAllByRole("checkbox");
        const ocrCheckbox = checkboxes.find(cb => cb.labels?.[0]?.textContent?.toLowerCase().includes("ocr"));
        const yoloCheckbox = checkboxes.find(cb => cb.labels?.[0]?.textContent?.toLowerCase().includes("yolo"));

        if (ocrCheckbox) fireEvent.click(ocrCheckbox);
        if (yoloCheckbox) fireEvent.click(yoloCheckbox);

        // Click analyze
        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        // Verify API was called
        await waitFor(() => {
            expect(apiClient.analyzeMulti).toHaveBeenCalledWith(
                file,
                ["ocr", "yolo-tracker"]
            );
        });
    });

    it("should display results after analysis", async () => {
        const mockResult = {
            tools: {
                ocr: { text: "detected text", confidence: 0.98 },
                "yolo-tracker": {
                    detections: [
                        { label: "person", confidence: 0.92, bbox: [10, 10, 100, 100] }
                    ]
                }
            }
        };

        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue(mockResult);

        render(<App />);

        // Switch to multi-tool mode
        fireEvent.click(screen.getByText(/multi-tool/i));

        await waitFor(() => {
            expect(screen.getByText(/multi-tool image analysis/i)).toBeInTheDocument();
        });

        // Select file and tools
        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        const checkboxes = screen.getAllByRole("checkbox");
        const ocrCheckbox = checkboxes.find(cb => cb.labels?.[0]?.textContent?.toLowerCase().includes("ocr"));
        const yoloCheckbox = checkboxes.find(cb => cb.labels?.[0]?.textContent?.toLowerCase().includes("yolo"));

        if (ocrCheckbox) fireEvent.click(ocrCheckbox);
        if (yoloCheckbox) fireEvent.click(yoloCheckbox);

        // Click analyze
        fireEvent.click(screen.getByText("Analyze"));

        // Wait for results
        await waitFor(() => {
            expect(screen.getByText(/results:/i)).toBeInTheDocument();
        });

        // Verify OCR result
        expect(screen.getByText(/detected text/i)).toBeInTheDocument();

        // Verify YOLO result
        expect(screen.getByText(/person/i)).toBeInTheDocument();
    });

    it("should handle analysis errors", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Network error")
        );

        render(<App />);

        // Switch to multi-tool mode
        fireEvent.click(screen.getByText(/multi-tool/i));

        await waitFor(() => {
            expect(screen.getByText(/multi-tool image analysis/i)).toBeInTheDocument();
        });

        // Select file and tool
        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });

        const checkboxes = screen.getAllByRole("checkbox");
        const ocrCheckbox = checkboxes.find(cb => cb.labels?.[0]?.textContent?.toLowerCase().includes("ocr"));
        if (ocrCheckbox) fireEvent.click(ocrCheckbox);

        // Click analyze
        fireEvent.click(screen.getByText("Analyze"));

        // Verify error message
        await waitFor(() => {
            expect(screen.getByText(/network error/i)).toBeInTheDocument();
        });
    });
});