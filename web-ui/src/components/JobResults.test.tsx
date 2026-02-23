/**
 * Tests for JobResults component (plugin-agnostic for v0.9.4)
 * Now just displays raw JSON - no tool-specific logic
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobResults } from "./JobResults";

describe("JobResults", () => {
    it("renders heading", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "Sample text",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText("Job Results")).toBeInTheDocument();
    });

    it("displays JSON when results available", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "Sample OCR text from video",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        const { container } = render(<JobResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        expect(preBlock?.textContent).toContain("Sample OCR text from video");
    });

    it("displays 'No results available' when results are null", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: null,
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/No results available/i)).toBeInTheDocument();
    });

    it("displays JSON with empty text field", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        const { container } = render(<JobResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        expect(preBlock?.textContent).toContain("detections");
    });

    it("displays JSON with detections", () => {
        const mockResults = {
            job_id: "test-job-789",
            results: {
                text: "Sample text",
                detections: [
                    {
                        label: "person",
                        confidence: 0.95,
                        bbox: [100, 100, 50, 100],
                    },
                ],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        const { container } = render(<JobResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        expect(preBlock?.textContent).toContain("person");
        expect(preBlock?.textContent).toContain("0.95");
    });

    it("displays JSON with multiple detections", () => {
        const mockResults = {
            job_id: "test-job-999",
            results: {
                text: "Sample text",
                detections: [
                    {
                        label: "person",
                        confidence: 0.95,
                        bbox: [100, 100, 50, 100],
                    },
                    {
                        label: "ball",
                        confidence: 0.88,
                        bbox: [200, 200, 30, 30],
                    },
                ],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        const { container } = render(<JobResults results={mockResults} />);
        const preBlock = container.querySelector("pre");
        
        expect(preBlock).toBeInTheDocument();
        expect(preBlock?.textContent).toContain("person");
        expect(preBlock?.textContent).toContain("ball");
    });

    it("handles undefined results gracefully", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: undefined,
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults as any} />);
        expect(screen.getByText(/No results available/i)).toBeInTheDocument();
    });
});
