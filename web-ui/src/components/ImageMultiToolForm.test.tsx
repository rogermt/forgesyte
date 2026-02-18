/**
 * Tests for ImageMultiToolForm component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ImageMultiToolForm } from "./ImageMultiToolForm";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        analyzeMulti: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

describe("ImageMultiToolForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock analyzeMulti to return combined results by default
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue({
            tools: {
                ocr: { text: "Sample text", confidence: 0.95 },
                "yolo-tracker": {
                    detections: [
                        {
                            label: "person",
                            confidence: 0.92,
                            bbox: [100, 100, 50, 100],
                        },
                    ],
                },
            },
        });
    });

    it("renders without errors", () => {
        render(<ImageMultiToolForm />);
        expect(screen.getByText("Multi-Tool Image Analysis")).toBeInTheDocument();
    });

    it("accepts image files", () => {
        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(fileInput.files).toHaveLength(1);
        expect(fileInput.files?.[0]).toBe(file);
    });

    it("rejects non-image files", () => {
        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.txt", { type: "text/plain" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        expect(screen.getByText(/Only image files are supported/i)).toBeInTheDocument();
    });

    it("has OCR checkbox", () => {
        render(<ImageMultiToolForm />);
        expect(screen.getByLabelText(/ocr/i)).toBeInTheDocument();
    });

    it("has YOLO checkbox", () => {
        render(<ImageMultiToolForm />);
        expect(screen.getByLabelText(/yolo/i)).toBeInTheDocument();
    });

    it("disables analyze button when no file selected", () => {
        render(<ImageMultiToolForm />);
        
        const analyzeButton = screen.getByText("Analyze");
        expect(analyzeButton).toBeDisabled();
    });

    it("disables analyze button when no tools selected", async () => {
        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        await waitFor(() => {
            const analyzeButton = screen.getByText("Analyze");
            expect(analyzeButton).toBeDisabled();
        });
    });

    it("enables analyze button when file and tools selected", async () => {
        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        await waitFor(() => {
            const analyzeButton = screen.getByText("Analyze");
            expect(analyzeButton).not.toBeDisabled();
        });
    });

    it("calls analyzeMulti with selected tools", async () => {
        const mockResult = {
            tools: {
                ocr: { text: "Test text" },
            },
        };

        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue(mockResult);

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(apiClient.analyzeMulti).toHaveBeenCalledWith(
                file,
                ["ocr"]
            );
        });
    });

    it("calls analyzeMulti with multiple tools", async () => {
        const mockResult = {
            tools: {
                ocr: { text: "Test text" },
                "yolo-tracker": { detections: [] },
            },
        };

        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue(mockResult);

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const yoloCheckbox = screen.getByLabelText(/yolo/i) as HTMLInputElement;
        fireEvent.click(yoloCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(apiClient.analyzeMulti).toHaveBeenCalledWith(
                file,
                ["ocr", "yolo-tracker"]
            );
        });
    });

    it("displays loading state while analyzing", async () => {
        let resolveAnalysis: ((value: unknown) => void) | null = null;

        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveAnalysis = resolve;
                })
        );

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(screen.getByText("Analyzing...")).toBeInTheDocument();
        });

        // Complete the mock
        if (resolveAnalysis) {
            resolveAnalysis({ tools: {} });
        }
    });

    it("displays error message on failure", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Network error")
        );

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(screen.getByText(/Network error/i)).toBeInTheDocument();
        });
    });

    it("clears error when new file is selected", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Upload failed")
        );

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file1 = new File(["test1"], "test1.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file1] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
        });

        // Select a new file
        const file2 = new File(["test2"], "test2.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file2] } });

        await waitFor(() => {
            expect(screen.queryByText(/Upload failed/i)).not.toBeInTheDocument();
        });
    });

    it("clears error when tools change", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockRejectedValue(
            new Error("Tool execution failed")
        );

        render(<ImageMultiToolForm />);

        const fileInput = screen.getByLabelText(/image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });

        fireEvent.change(fileInput, { target: { files: [file] } });

        const ocrCheckbox = screen.getByLabelText(/ocr/i) as HTMLInputElement;
        fireEvent.click(ocrCheckbox);

        const analyzeButton = screen.getByText("Analyze");
        fireEvent.click(analyzeButton);

        await waitFor(() => {
            expect(screen.getByText(/Tool execution failed/i)).toBeInTheDocument();
        });

        // Toggle OCR off and on
        fireEvent.click(ocrCheckbox);
        fireEvent.click(ocrCheckbox);

        await waitFor(() => {
            expect(screen.queryByText(/Tool execution failed/i)).not.toBeInTheDocument();
        });
    });
});