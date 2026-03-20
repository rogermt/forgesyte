/**
 * Tests for ResultsPanel styling and job display
 *
 * Uses mock factories to generate test data matching actual API responses.
 * API References:
 * - Job: GET /v1/jobs/{id} (fixtures/api-responses.json)
 * - FrameResult: WebSocket /v1/stream (fixtures/api-responses.json)
 *
 * Clean Break (Issue #350): No more inline results - use result_url and ArtifactViewer
 */

import { vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ResultsPanel } from "./ResultsPanel";
import { createMockFrameResult, createMockJobDone } from "../test-utils/factories";

// Mock ArtifactViewer component
vi.mock("./ArtifactViewer", () => ({
    ArtifactViewer: ({ url }: { url: string }) => (
        <div data-testid="artifact-viewer" data-url={url}>
            ArtifactViewer: {url}
        </div>
    ),
}));

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

        it("should display summary in code block for completed jobs", () => {
            const { container } = render(
                <ResultsPanel mode="job" job={mockJob} />
            );

            const preBlock = container.querySelector("pre");
            expect(preBlock).toBeInTheDocument();
            // Summary should be displayed
            expect(preBlock?.textContent).toContain("frame_count");
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

    // Issue #350: Clean Break - Artifact Pattern
    describe("Clean Break - Artifact Pattern", () => {
        it("should show summary for job with result_url", () => {
            const mockJob = createMockJobDone({
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100, detection_count: 50, classes: ["player", "ball"] },
            });

            render(<ResultsPanel mode="job" job={mockJob} />);

            // Summary should be displayed
            expect(screen.getByText(/Summary/)).toBeInTheDocument();
            expect(screen.getByText(/frame_count/)).toBeInTheDocument();
            expect(screen.getByText(/100/)).toBeInTheDocument();
        });

        it("should use ArtifactViewer for job with result_url", () => {
            const mockJob = createMockJobDone({
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100 },
            });

            render(<ResultsPanel mode="job" job={mockJob} />);

            // ArtifactViewer should be rendered
            expect(screen.getByTestId("artifact-viewer")).toBeInTheDocument();
            expect(screen.getByTestId("artifact-viewer")).toHaveAttribute(
                "data-url",
                "/v1/jobs/video-123/result"
            );
        });

        it("should show 'No result available' for job without result_url or summary", () => {
            const mockJob = createMockJobDone({
                result_url: undefined,
                summary: undefined,
            });

            render(<ResultsPanel mode="job" job={mockJob} />);

            expect(screen.getByText(/No result available/)).toBeInTheDocument();
        });

        it("should NOT have inline results field", () => {
            const mockJob = createMockJobDone({
                job_type: "video",
                result_url: "/v1/jobs/video-123/result",
                summary: { frame_count: 100 },
            });

            render(<ResultsPanel mode="job" job={mockJob} />);

            // Should not show old "Raw Result" or inline JSON display
            expect(screen.queryByText(/Raw Result/)).not.toBeInTheDocument();
        });
    });
});