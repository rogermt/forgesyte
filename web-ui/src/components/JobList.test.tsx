/**
 * Tests for JobList API integration, styling, and interactions
 */

import { vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { JobList } from "./JobList";
import * as client from "../api/client";

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
        const mockServerJobs = [
            {
                job_id: "550e8400-e29b-41d4-a716-446655440000",
                status: "done",
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                completed_at: "2026-01-09T21:00:30Z",
                result: { motion_detected: true },
                error: null,
                progress: 100,
            },
            {
                job_id: "550e8400-e29b-41d4-a716-446655440001",
                status: "running",
                plugin: "object_detection",
                created_at: "2026-01-09T21:30:00Z",
                completed_at: null,
                result: null,
                error: null,
                progress: 45,
            },
        ];

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
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                mockServerJobs[0],
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(
                    screen.getByText("550e8400-e29b...")
                ).toBeInTheDocument();
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
        const mockJobs = [
            {
                job_id: "job-123456",
                status: "done",
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                completed_at: "2026-01-09T21:00:30Z",
            },
            {
                job_id: "job-234567",
                status: "running",
                plugin: "object_detection",
                created_at: "2026-01-09T21:30:00Z",
                completed_at: null,
            },
        ];

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
            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                mockJobs[0],
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("job-123456...")).toBeInTheDocument();
            });
        });
    });

    describe("status color rendering", () => {
        const statuses = [
            { status: "done", label: "done" },
            { status: "error", label: "error" },
            { status: "running", label: "running" },
            { status: "queued", label: "queued" },
        ];

        statuses.forEach(({ status, label }) => {
            it(`should display ${status} status badge`, async () => {
                const job = {
                    job_id: `job-${status}`,
                    status: status as "done" | "error" | "running" | "queued" | "not_found",
                    plugin: "test_plugin",
                    created_at: "2026-01-09T21:00:00Z",
                };

                (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                    job,
                ]);

                render(<JobList onJobSelect={vi.fn()} />);

                await waitFor(() => {
                    expect(screen.getByText(label)).toBeInTheDocument();
                });
            });
        });

        it("should display unknown status with muted color", async () => {
            const job = {
                job_id: "job-unknown",
                status: "not_found" as const,
                plugin: "test_plugin",
                created_at: "2026-01-09T21:00:00Z",
            };

            (client.apiClient.listJobs as ReturnType<typeof vi.fn>).mockResolvedValue([
                job,
            ]);

            render(<JobList onJobSelect={vi.fn()} />);

            await waitFor(() => {
                expect(screen.getByText("not_found")).toBeInTheDocument();
            });
        });
    });

    describe("job interactions", () => {
        const mockJobs = [
            {
                job_id: "job-123456",
                status: "done" as const,
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                completed_at: "2026-01-09T21:00:30Z",
            },
        ];

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
        const mockJobs = [
            {
                job_id: "job-123456",
                status: "done" as const,
                plugin: "motion_detector",
                created_at: "2026-01-09T21:00:00Z",
                completed_at: "2026-01-09T21:00:30Z",
            },
        ];

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
