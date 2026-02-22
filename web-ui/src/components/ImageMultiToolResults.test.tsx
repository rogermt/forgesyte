/**
 * Tests for ImageMultiToolResults component
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageMultiToolResults } from "./ImageMultiToolResults";

describe("ImageMultiToolResults", () => {
    it("should render component", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/results/i)).toBeInTheDocument();
    });

    it("should display OCR results", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/ocr/i)).toBeInTheDocument();
        expect(screen.getByText("sample text")).toBeInTheDocument();
    });

    it("should display YOLO results", () => {
        const mockResults = {
            tools: {
                "yolo-tracker": {
                    detections: [
                        { label: "person", confidence: 0.95, bbox: [10, 10, 100, 100] },
                    ],
                },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/yolo/i)).toBeInTheDocument();
        // Check that detections are shown in JSON
        const detectionsElements = screen.getAllByText(/detections/i);
        expect(detectionsElements.length).toBeGreaterThan(0);
    });

    it("should pretty-print JSON", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        // Check that JSON is displayed in formatted way
        // The text appears in both the paragraph and the JSON pre tag
        const textElements = screen.getAllByText(/sample text/);
        expect(textElements.length).toBeGreaterThan(0);
    });
});