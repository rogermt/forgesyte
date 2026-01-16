/**
 * Tests for ResultsPanel plugin mode (when UIPluginManager is implemented)
 */

import { render, screen } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";

describe("ResultsPanel plugin mode", () => {
    it("should render in stream mode with results", () => {
        const result = { motion_detected: true, percentage: 85 };
        render(
            <ResultsPanel
                mode="stream"
                streamResult={{
                    frame_id: "frame-123",
                    processing_time_ms: 45,
                    result: result,
                }}
            />
        );

        expect(screen.getByTestId("results-panel")).toBeInTheDocument();
        expect(screen.getByText("Frame ID: frame-123")).toBeInTheDocument();
    });

    it("should render in job mode with results", () => {
        const job = {
            job_id: "job-123",
            status: "done" as const,
            result: { text: "hello" },
            created_at: "2026-01-16T00:00:00Z",
            completed_at: "2026-01-16T00:00:05Z",
            plugin: "ocr",
        };

        render(
            <ResultsPanel
                mode="job"
                job={job}
            />
        );

        expect(screen.getByText("Job ID: job-123")).toBeInTheDocument();
        expect(screen.getByText(/Status: done/)).toBeInTheDocument();
    });

    // TODO: Add tests for dynamic plugin result rendering when UIPluginManager is implemented
});
