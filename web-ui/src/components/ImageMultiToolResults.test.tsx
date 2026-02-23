/**
 * Tests for ImageMultiToolResults component (plugin-agnostic for v0.9.4)
 * Now just displays raw JSON - no tool-specific parsing
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageMultiToolResults } from "./ImageMultiToolResults";

describe("ImageMultiToolResults", () => {
    it("should render heading", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/Multi-Tool Results/i)).toBeInTheDocument();
    });

    it("should display tool name label", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText("ocr")).toBeInTheDocument();
    });

    it("should display JSON result for single tool", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
            },
        };

        const { container } = render(<ImageMultiToolResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        expect(preBlock?.textContent).toContain("sample text");
        expect(preBlock?.textContent).toContain("0.95");
    });

    it("should display JSON for yolo-tracker results", () => {
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
        
        // Tool name label should appear
        expect(screen.getByText("yolo-tracker")).toBeInTheDocument();
        
        // JSON should contain the detection
        const { container } = render(<ImageMultiToolResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        expect(preBlock?.textContent).toContain("person");
    });

    it("should display multiple tools", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
                "yolo-tracker": {
                    detections: [
                        { label: "person", confidence: 0.92 },
                    ],
                },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        
        expect(screen.getByText("ocr")).toBeInTheDocument();
        expect(screen.getByText("yolo-tracker")).toBeInTheDocument();
    });

    it("should pretty-print JSON with proper formatting", () => {
        const mockResults = {
            tools: {
                ocr: { 
                    text: "sample text", 
                    confidence: 0.95,
                    metadata: { source: "file.pdf" },
                },
            },
        };

        const { container } = render(<ImageMultiToolResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        // JSON.stringify with 2 spaces should be readable
        expect(preBlock?.textContent).toContain("sample text");
        expect(preBlock?.textContent).toContain("metadata");
    });

    it("should handle empty tool results", () => {
        const mockResults = {
            tools: {
                ocr: {},
                "other-tool": { result: "data" },
            },
        };

        render(<ImageMultiToolResults results={mockResults} />);
        
        expect(screen.getByText("ocr")).toBeInTheDocument();
        expect(screen.getByText("other-tool")).toBeInTheDocument();
    });
});
