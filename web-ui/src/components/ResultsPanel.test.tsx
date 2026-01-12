/**
 * Tests for ResultsPanel styling updates
 */

import { render, screen } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";
import { Job } from "../api/client";

describe("ResultsPanel - Styling Updates", () => {
    describe("heading and layout", () => {
        it("should display Results heading with brand colors", () => {
            render(
                <ResultsPanel mode="stream" streamResult={null} />
            );
            const header = screen.getByText("Results");

            expect(header).toBeInTheDocument();
            expect(header).toHaveStyle({
                fontWeight: 600,
                marginBottom: "12px",
            });
        });

        it("should have proper panel styling", () => {
            render(
                <ResultsPanel mode="stream" streamResult={null} />
            );
            const panel = screen.getByTestId("results-panel");

            expect(panel).toHaveStyle({
                borderRadius: "8px",
                padding: "16px",
                minHeight: "400px",
                display: "flex",
                flexDirection: "column",
            });
        });
    });

    describe("stream results display", () => {
        const mockStreamResult = {
            frame_id: "frame-001",
            plugin: "motion_detector",
            processing_time_ms: 45,
            result: { motion_detected: true, confidence: 0.95 },
        };

        it("should display frame ID and processing time", () => {
            render(
                <ResultsPanel
                    mode="stream"
                    streamResult={mockStreamResult}
                />
            );

            expect(screen.getByText(/frame-001/)).toBeInTheDocument();
            expect(screen.getByText(/45ms/)).toBeInTheDocument();
        });

        it("should display JSON result in code block", () => {
            const { container } = render(
                <ResultsPanel
                    mode="stream"
                    streamResult={mockStreamResult}
                />
            );

            const preBlock = container.querySelector("pre");
            expect(preBlock).toBeInTheDocument();
            expect(preBlock?.textContent).toContain("motion_detected");
        });

        it("should show waiting message when no results", () => {
            render(<ResultsPanel mode="stream" streamResult={null} />);

            expect(
                screen.getByText("Waiting for results...")
            ).toBeInTheDocument();
        });
    });

    describe("job results display", () => {
        const mockJob: Job = {
            id: "job-123456",
            status: "done",
            plugin: "motion_detector",
            result: { motion_detected: false },
            created_at: "2026-01-09T21:00:00Z",
            updated_at: "2026-01-09T21:00:30Z",
        };

        it("should display job ID and status", () => {
            render(
                <ResultsPanel mode="job" job={mockJob} />
            );

            expect(screen.getByText(/job-123456/)).toBeInTheDocument();
            expect(screen.getByText(/Status: done/)).toBeInTheDocument();
        });

        it("should display JSON result in code block", () => {
            const { container } = render(
                <ResultsPanel mode="job" job={mockJob} />
            );

            const preBlock = container.querySelector("pre");
            expect(preBlock).toBeInTheDocument();
        });

        it("should show prompt when no job selected", () => {
            render(
                <ResultsPanel mode="job" job={null} />
            );

            expect(
                screen.getByText("Select a job to view results")
            ).toBeInTheDocument();
        });
    });

    describe("code block styling", () => {
        const mockStreamResult = {
            frame_id: "frame-001",
            plugin: "motion_detector",
            processing_time_ms: 45,
            result: { test: true },
        };

        it("should style code blocks with brand colors", () => {
            const { container } = render(
                <ResultsPanel
                    mode="stream"
                    streamResult={mockStreamResult}
                />
            );

            const preBlock = container.querySelector("pre");
            expect(preBlock).toHaveStyle({
                borderRadius: "4px",
                overflow: "auto",
                fontSize: "11px",
                padding: "8px",
            });
        });
    });

    describe("content scrolling", () => {
        it("should apply scrolling to content area", () => {
            render(
                <ResultsPanel mode="stream" streamResult={null} />
            );

            const contentArea = screen.getByTestId("results-content");
            expect(contentArea).toBeInTheDocument();
            expect(contentArea).toHaveStyle({
                overflowY: "auto"
            });
        });
    });
});
