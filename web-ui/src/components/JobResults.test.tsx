/**
 * Tests for JobResults component
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobResults } from "./JobResults";

describe("JobResults", () => {
    it("renders without errors", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "Sample OCR text",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText("Results")).toBeInTheDocument();
    });

    it("displays OCR text when available", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "Sample OCR text from video",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/Sample OCR text from video/i)).toBeInTheDocument();
    });

    it("displays 'No OCR text available' when text is empty", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                text: "",
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/No OCR text available/i)).toBeInTheDocument();
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

    it("displays 'No results available' when results are undefined", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: undefined,
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/No results available/i)).toBeInTheDocument();
    });

    it("handles missing text field gracefully", () => {
        const mockResults = {
            job_id: "test-job-123",
            results: {
                detections: [],
            },
            created_at: "2026-02-18T10:00:00Z",
            updated_at: "2026-02-18T10:01:00Z",
        };

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/No OCR text available/i)).toBeInTheDocument();
    });

    it("displays detections when available (beta feature)", () => {
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

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/person/i)).toBeInTheDocument();
        expect(screen.getByText(/95\.0%/i)).toBeInTheDocument();
    });

    it("displays multiple detections", () => {
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

        render(<JobResults results={mockResults} />);
        expect(screen.getByText(/person/i)).toBeInTheDocument();
        expect(screen.getByText(/ball/i)).toBeInTheDocument();
    });
});