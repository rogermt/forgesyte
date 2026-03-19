/**
 * Tests for ResultsPanel styling and job display
 *
 * Uses mock factories to generate test data matching actual API responses.
 * API References:
 * - Job: GET /v1/jobs/{id} (fixtures/api-responses.json)
 * - FrameResult: WebSocket /v1/stream (fixtures/api-responses.json)
 */

import { render, screen, waitFor } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";
import { createMockFrameResult, createMockJobDone } from "../test-utils/factories";

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
        // Uses factory-generated test data matching WebSocket API
        const mockStreamResult = createMockFrameResult();

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
        // Uses factory-generated test data matching JobResponse API
        const mockJob = createMockJobDone();

        it("should display job ID and status", () => {
            render(
                <ResultsPanel mode="job" job={mockJob} />
            );

            expect(screen.getByText(new RegExp(mockJob.job_id))).toBeInTheDocument();
            expect(screen.getByText(/Status: completed/)).toBeInTheDocument();
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
        // Uses factory-generated test data
        const mockStreamResult = createMockFrameResult();

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
        it("should apply scrolling to content area", async () => {
            render(
                <ResultsPanel mode="stream" streamResult={null} />
            );

            const contentArea = screen.getByTestId("results-content");
            expect(contentArea).toBeInTheDocument();
            
            await waitFor(() => {
                expect(contentArea).toHaveStyle({
                    overflowY: "auto"
                });
            }, { timeout: 10000 });
        });
    });

    // Issue #350: Artifact Pattern - lazy loading for video jobs
    describe("video job lazy loading", () => {
        it("should show summary for video job with result_url", () => {
            const mockVideoJob = createMockJobDone({
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100, detection_count: 50, classes: ["player", "ball"] },
                results: undefined,
                result: undefined,
            });

            render(<ResultsPanel mode="job" job={mockVideoJob} />);

            expect(screen.getByText(/frame_count/)).toBeInTheDocument();
            expect(screen.getByText(/100/)).toBeInTheDocument();
            expect(screen.getByText(/detection_count/)).toBeInTheDocument();
            expect(screen.getByText(/50/)).toBeInTheDocument();
        });

        it("should show 'Load Results' button for video job with result_url", () => {
            const mockVideoJob = createMockJobDone({
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100, detection_count: 50 },
                results: undefined,
                result: undefined,
            });

            render(<ResultsPanel mode="job" job={mockVideoJob} />);

            expect(screen.getByText(/Load Results/)).toBeInTheDocument();
        });

        it("should NOT show 'Load Results' button for image job without result_url", () => {
            const mockImageJob = createMockJobDone({
                job_type: "image",
                result_url: undefined,
                summary: undefined,
                results: { text: "extracted text" },
            });

            render(<ResultsPanel mode="job" job={mockImageJob} />);

            expect(screen.queryByText(/Load Results/)).not.toBeInTheDocument();
        });

        it("should show 'too large' message for video_multi without result_url", () => {
            const mockVideoMultiJob = createMockJobDone({
                job_type: "video_multi",
                result_url: undefined,
                summary: undefined,
                results: { tools: {} },
            });

            render(<ResultsPanel mode="job" job={mockVideoMultiJob} />);

            expect(screen.getByText(/too large to render/)).toBeInTheDocument();
        });
    });
});
