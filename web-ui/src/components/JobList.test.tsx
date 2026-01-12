/**
 * Tests for JobList API integration, styling, and interactions
 *
 * Uses mock factories to generate test data matching actual API responses.
 * API Reference: GET /v1/jobs (see fixtures/api-responses.json)
 */

import { vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { JobList } from "./JobList";
import * as client from "../api/client";
import {
    createMockJob,
    createMockJobDone,
    createMockJobRunning,
    createMockJobError,
    createMockJobList,
} from "../test-utils/factories";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        listJobs: vi.fn(),
    },
}));

describe("JobList", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("loading state", () => {
        it("should display loading message initially", () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockImplementation(
                () => new Promise(() => {
                    /* never resolves */
                })
            );

            render(<JobList onJobSelect={vi.fn()} />);
            expect(screen.getByText("Loading jobs...")).toBeInTheDocument();
        });
    });

    describe("error state", () => {
        it("should display error message with brand styling", async () => {
            const errorMsg = "API connection failed";
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockRejectedValue(
                new Error(errorMsg)
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(
                    screen.getByText(new RegExp(errorMsg))
                ).toBeInTheDocument();
            });
        });

        it("should display generic error message for non-Error objects", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockRejectedValue(
                "String error"
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(
                    screen.getByText(new RegExp("Failed to load jobs"))
                ).toBeInTheDocument();
            });
        });
    });

    describe("empty state", () => {
        it("should display message when no jobs", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("No jobs yet")).toBeInTheDocument();
            });
        });
    });

    describe("job list display with server API format (job_id field)", () => {
        // Uses factory-generated test data matching real API responses
        const mockServerJobs = createMockJobList(2);

        it("should render jobs with server API format (job_id instead of id)", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockServerJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("Recent Jobs")).toBeInTheDocument();
                expect(screen.getByText("done")).toBeInTheDocument();
                expect(screen.getByText("running")).toBeInTheDocument();
            });
        });

        it("should display truncated job_id from server format", async () => {
            const job = mockServerJobs[0];
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                job,
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const expectedTruncated = `${job.job_id.slice(0, 12)}...`;
                expect(screen.getByText(expectedTruncated)).toBeInTheDocument();
            });
        });

        it("should call onJobSelect with full job object when server format is used", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                mockServerJobs[0],
            ]);

            const mockSelectJob = vi.fn();
            render(<JobList onJobSelect={mockSelectJob} />);

            await waitFor(() => {
                const jobElement = screen.getByTestId(
                    `job-item-${mockServerJobs[0].job_id}`
                );
                fireEvent.click(jobElement);
                expect(mockSelectJob).toHaveBeenCalledWith(mockServerJobs[0]);
            });
        });
    });

    describe("job list display", () => {
        // Uses factory-generated test data
        const mockJobs = createMockJobList(2);

        it("should display jobs with proper information", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("Recent Jobs")).toBeInTheDocument();
                expect(screen.getByText("done")).toBeInTheDocument();
                expect(screen.getByText("running")).toBeInTheDocument();
            });
        });

        it("should display plugin name for each job", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                mockJobs[0],
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("motion_detector")).toBeInTheDocument();
            });
        });

        it("should display truncated job ID", async () => {
            const job = createMockJobDone();
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                job,
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                // Should display first 12 characters of job_id followed by ellipsis
                const expectedTruncated = `${job.job_id.slice(0, 12)}...`;
                expect(screen.getByText(expectedTruncated)).toBeInTheDocument();
            });
        });
    });

    describe("status color rendering", () => {
        const statuses = [
            { statusValue: "done" as const, factory: createMockJobDone },
            { statusValue: "error" as const, factory: createMockJobError },
            { statusValue: "running" as const, factory: createMockJobRunning },
            { statusValue: "queued" as const, factory: createMockJob },
        ];

        statuses.forEach(({ statusValue, factory }) => {
            it(`should display ${statusValue} status badge`, async () => {
                const job = factory();

                (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                    job,
                ]);

                render(<JobList onJobSelect={vi.fn()} />);

                await waitFor(() => {
                    expect(screen.getByText(statusValue)).toBeInTheDocument();
                });
            });
        });

        it("should display error status with proper styling", async () => {
            const job = createMockJobError();

            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                job,
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("error")).toBeInTheDocument();
            });
        });
    });

    describe("job interactions", () => {
        // Uses factory-generated test data
        const mockJobs = [createMockJobDone()];

        it("should call onJobSelect when job is clicked", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            const mockSelectJob = vi.fn();
            render(<JobList onJobSelect={mockSelectJob} />);

            await waitFor(() => {
                const jobElement = screen.getByTestId(`job-item-${mockJobs[0].job_id}`);
                fireEvent.click(jobElement);
                expect(mockSelectJob).toHaveBeenCalledWith(mockJobs[0]);
            });
        });

        it("should apply hover styles when mouse enters job item", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const jobElement = screen.getByTestId(`job-item-${mockJobs[0].job_id}`);
                fireEvent.mouseOver(jobElement);
                expect(jobElement.style.backgroundColor).toBe("var(--bg-hover)");
                expect(jobElement.style.borderColor).toBe("var(--accent-cyan)");
            });
        });

        it("should remove hover styles when mouse leaves job item", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const jobElement = screen.getByTestId(`job-item-${mockJobs[0].job_id}`);
                fireEvent.mouseOut(jobElement);
                expect(jobElement.style.backgroundColor).toBe("var(--bg-tertiary)");
                expect(jobElement.style.borderColor).toBe("var(--border-light)");
                expect(jobElement.style.boxShadow).toBe("none");
            });
        });
    });

    describe("styling", () => {
        // Uses factory-generated test data
        const mockJobs = [createMockJobDone()];

        it("should use brand colors for job items", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const jobItem = screen.getByTestId(`job-item-${mockJobs[0].job_id}`);
                expect(jobItem).toHaveStyle({
                    cursor: "pointer",
                    borderRadius: "4px",
                    transition: "all 0.2s",
                });
            });
        });

        it("should apply proper scrolling to job list", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const scrollContainer = screen.getByTestId("job-list-container");
                expect(scrollContainer).toHaveStyle({
                    maxHeight: "400px",
                    overflowY: "auto",
                });
            });
        });

        it("should apply consistent spacing to job items", async () => {
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue(
                mockJobs
            );

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                const jobItem = screen.getByTestId(`job-item-${mockJobs[0].job_id}`);
                expect(jobItem).toHaveStyle({
                    padding: "10px",
                    marginBottom: "8px",
                });
            });
        });
    });
});
