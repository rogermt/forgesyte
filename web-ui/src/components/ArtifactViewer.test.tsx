/**
 * Tests for ArtifactViewer component
 * Clean Break (Issue #350): Paginated artifact viewing
 * Discussion #352: Use API client for pagination (not direct URL fetch)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ArtifactViewer } from "./ArtifactViewer";

// Mock the apiClient module
vi.mock("../api/client", () => ({
    apiClient: {
        getJobResultPage: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

const mockGetJobResultPage = vi.mocked(apiClient.getJobResultPage);

// Mock fetch for download button (opens in new tab)
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("ArtifactViewer", () => {
    beforeEach(() => {
        mockGetJobResultPage.mockReset();
        mockFetch.mockReset();
    });

    // Discussion #352: New tests for jobId prop
    describe("with jobId prop (Discussion #352)", () => {
        it("should accept jobId prop for pagination", () => {
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 100,
                frames: [],
            });

            render(<ArtifactViewer jobId="test-job-123" />);
            expect(screen.getByText(/download/i)).toBeInTheDocument();
        });

        it("should use apiClient.getJobResultPage for pagination (NOT direct fetch)", async () => {
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 500,
                frames: [{ frame: 0 }, { frame: 1 }],
            });

            render(<ArtifactViewer jobId="test-job-456" />);

            await waitFor(() => {
                expect(mockGetJobResultPage).toHaveBeenCalledWith("test-job-456", 0, 200);
            });
        });

        it("should NOT build URL from result_url for pagination", async () => {
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 500,
                frames: [],
            });

            // Pass both jobId and resultUrl - pagination should use jobId only
            render(
                <ArtifactViewer
                    jobId="job-789"
                    resultUrl="http://s3.amazonaws.com/bucket/result?token=abc123"
                />
            );

            await waitFor(() => {
                // Should use apiClient.getJobResultPage with jobId
                expect(mockGetJobResultPage).toHaveBeenCalledWith("job-789", 0, 200);
                // Should NOT call fetch with URL concatenation
                expect(mockFetch).not.toHaveBeenCalled();
            });
        });

        it("should use resultUrl for download button only", async () => {
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 100,
                frames: [],
            });

            render(
                <ArtifactViewer
                    jobId="job-download-test"
                    resultUrl="http://localhost:3000/v1/jobs/job-download-test/result?token=xyz"
                />
            );

            await waitFor(() => {
                expect(screen.getByText(/download/i)).toBeInTheDocument();
            });

            // Click download button - should open resultUrl in new tab
            const downloadButton = screen.getByText(/download/i);
            const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
            fireEvent.click(downloadButton);

            expect(openSpy).toHaveBeenCalledWith(
                "http://localhost:3000/v1/jobs/job-download-test/result?token=xyz",
                "_blank",
                "noopener,noreferrer"
            );
            openSpy.mockRestore();
        });
    });

    // Legacy tests (still need jobId now)
    it("renders download button", () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 100,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job" />);
        expect(screen.getByText(/download/i)).toBeInTheDocument();
    });

    it("fetches paginated data on mount using apiClient", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [{ frame: 0 }, { frame: 1 }],
        });

        render(<ArtifactViewer jobId="test-job-mount" />);

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledWith("test-job-mount", 0, 200);
        });
    });

    it("shows loading state while fetching", () => {
        mockGetJobResultPage.mockImplementation(() => new Promise(() => {})); // Never resolves

        render(<ArtifactViewer jobId="test-job-loading" />);
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it("shows error on fetch failure", async () => {
        mockGetJobResultPage.mockRejectedValueOnce(new Error("Failed to load"));

        render(<ArtifactViewer jobId="test-job-error" />);

        await waitFor(() => {
            expect(screen.getByText(/error/i)).toBeInTheDocument();
        });
    });

    it("shows prev and next buttons after data loads", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-pagination" />);

        await waitFor(() => {
            expect(screen.getByText(/prev/i)).toBeInTheDocument();
            expect(screen.getByText(/next/i)).toBeInTheDocument();
        });
    });

    it("disables prev button on first page", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-first-page" />);

        await waitFor(() => {
            const prevButton = screen.getByText(/prev/i);
            expect(prevButton).toBeDisabled();
        });
    });

    it("enables prev button on second page", async () => {
        // First fetch (page 0)
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-second-page" />);

        await waitFor(() => {
            expect(screen.getByText(/prev/i)).toBeDisabled();
        });

        // Mock fetch for page 1
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 200,
            limit: 200,
            total: 500,
            frames: [],
        });

        // Click next to go to page 1
        const nextButton = screen.getByText(/next/i);
        fireEvent.click(nextButton);

        await waitFor(() => {
            const prevButton = screen.getByText(/prev/i);
            expect(prevButton).not.toBeDisabled();
        });
    });

    it("disables next button on last page", async () => {
        // Start on page 0 with 500 total frames (3 pages)
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-last-page" />);

        await waitFor(() => {
            expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
        });

        // Navigate to page 2 (last page)
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 200,
            limit: 200,
            total: 500,
            frames: [],
        });
        fireEvent.click(screen.getByText(/next/i));

        await waitFor(() => {
            expect(screen.getByText(/Page 2 of 3/)).toBeInTheDocument();
        });

        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 400,
            limit: 200,
            total: 500,
            frames: [],
        });
        fireEvent.click(screen.getByText(/next/i));

        await waitFor(() => {
            expect(screen.getByText(/Page 3 of 3/)).toBeInTheDocument();
            const nextButton = screen.getByText(/next/i);
            expect(nextButton).toBeDisabled();
        });
    });

    it("shows correct page info", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-page-info" />);

        await waitFor(() => {
            expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
            expect(screen.getByText(/500 total frames/)).toBeInTheDocument();
        });
    });

    it("fetches next page when next button clicked", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-next" />);

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledTimes(1);
        });

        // Mock next page fetch
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 200,
            limit: 200,
            total: 500,
            frames: [],
        });

        const nextButton = screen.getByText(/next/i);
        fireEvent.click(nextButton);

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledWith("test-job-next", 200, 200);
        });
    });

    it("fetches previous page when prev button clicked", async () => {
        // Start on page 0
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        render(<ArtifactViewer jobId="test-job-prev" />);

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledTimes(1);
        });

        // Navigate to page 1 first
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 200,
            limit: 200,
            total: 500,
            frames: [],
        });

        fireEvent.click(screen.getByText(/next/i));

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledWith("test-job-prev", 200, 200);
        });

        // Now click prev to go back to page 0
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 500,
            frames: [],
        });

        const prevButton = screen.getByText(/prev/i);
        fireEvent.click(prevButton);

        await waitFor(() => {
            expect(mockGetJobResultPage).toHaveBeenCalledWith("test-job-prev", 0, 200);
        });
    });

    it("displays frames from response", async () => {
        mockGetJobResultPage.mockResolvedValueOnce({
            offset: 0,
            limit: 200,
            total: 2,
            frames: [
                { frame: 0, detections: [{ class: "person" }] },
                { frame: 1, detections: [{ class: "car" }] },
            ],
        });

        const { container } = render(
            <ArtifactViewer jobId="test-job-frames" />
        );

        await waitFor(() => {
            const preBlock = container.querySelector("pre");
            expect(preBlock?.textContent).toContain("person");
            expect(preBlock?.textContent).toContain("car");
        });
    });

    // Discussion #353: Page should reset when jobId changes
    describe("page reset on jobId change (Discussion #353)", () => {
        it("should reset page to 0 when jobId prop changes", async () => {
            // First job - fetch page 0, then navigate to page 2
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 600,
                frames: [],
            });

            const { rerender } = render(<ArtifactViewer jobId="job-A" />);

            await waitFor(() => {
                expect(mockGetJobResultPage).toHaveBeenCalledWith("job-A", 0, 200);
            });

            // Navigate to page 2 (click next twice)
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 200,
                limit: 200,
                total: 600,
                frames: [],
            });
            fireEvent.click(screen.getByText(/next/i));

            await waitFor(() => {
                expect(mockGetJobResultPage).toHaveBeenCalledWith("job-A", 200, 200);
            });

            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 400,
                limit: 200,
                total: 600,
                frames: [],
            });
            fireEvent.click(screen.getByText(/next/i));

            await waitFor(() => {
                expect(mockGetJobResultPage).toHaveBeenCalledWith("job-A", 400, 200);
            });

            // Now switch to a different job - should reset to page 0
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 100,
                frames: [],
            });

            rerender(<ArtifactViewer jobId="job-B" />);

            await waitFor(() => {
                // Should fetch page 0 for the new job, NOT page 2
                expect(mockGetJobResultPage).toHaveBeenCalledWith("job-B", 0, 200);
            });
        });

        it("should clear data when jobId changes", async () => {
            // First job with specific data
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 500,
                frames: [{ frame: 0, data: "job-A-data" }],
            });

            const { rerender, container } = render(<ArtifactViewer jobId="job-A" />);

            await waitFor(() => {
                expect(container.querySelector("pre")?.textContent).toContain("job-A-data");
            });

            // Switch to new job with different data
            mockGetJobResultPage.mockResolvedValueOnce({
                offset: 0,
                limit: 200,
                total: 100,
                frames: [{ frame: 0, data: "job-B-data" }],
            });

            rerender(<ArtifactViewer jobId="job-B" />);

            await waitFor(() => {
                // Should show new job's data, not old job's data
                expect(container.querySelector("pre")?.textContent).toContain("job-B-data");
                expect(container.querySelector("pre")?.textContent).not.toContain("job-A-data");
            });
        });
    });
});
