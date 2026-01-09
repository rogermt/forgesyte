/**
 * Job list component
 */

import { useEffect, useState } from "react";
import { apiClient, Job } from "../api/client";

export interface JobListProps {
    onJobSelect: (job: Job) => void;
}

export function JobList({ onJobSelect }: JobListProps) {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadJobs = async () => {
            try {
                const data = await apiClient.listJobs();
                setJobs(data);
                setError(null);
            } catch (err) {
                setError(
                    err instanceof Error ? err.message : "Failed to load jobs"
                );
                setJobs([]);
            } finally {
                setLoading(false);
            }
        };

        loadJobs();
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case "done":
                return "var(--accent-green)";
            case "error":
                return "var(--accent-red)";
            case "processing":
                return "var(--accent-yellow)";
            case "pending":
                return "var(--accent-cyan)";
            default:
                return "var(--text-muted)";
        }
    };

    const getStatusBackground = (status: string) => {
        switch (status) {
            case "done":
                return "rgba(76, 175, 80, 0.1)";
            case "error":
                return "rgba(220, 53, 69, 0.1)";
            case "processing":
                return "rgba(255, 193, 7, 0.1)";
            case "pending":
                return "rgba(0, 229, 255, 0.1)";
            default:
                return "transparent";
        }
    };

    if (loading)
        return (
            <p style={{ color: "var(--text-muted)", margin: 0 }}>
                Loading jobs...
            </p>
        );
    if (error)
        return (
            <p
                style={{
                    color: "var(--accent-red)",
                    backgroundColor: "rgba(220, 53, 69, 0.1)",
                    padding: "8px",
                    borderRadius: "4px",
                    border: "1px solid var(--accent-red)",
                    margin: 0,
                }}
            >
                Error: {error}
            </p>
        );
    if (jobs.length === 0)
        return (
            <p style={{ color: "var(--text-muted)", margin: 0 }}>
                No jobs yet
            </p>
        );

    return (
        <div>
            <h3>Recent Jobs</h3>
            <div
                style={{
                    maxHeight: "400px",
                    overflowY: "auto",
                    paddingRight: "4px",
                }}
            >
                {jobs.map((job) => (
                    <div
                        key={job.id}
                        onClick={() => onJobSelect(job)}
                        style={{
                            padding: "10px",
                            marginBottom: "8px",
                            backgroundColor: "var(--bg-tertiary)",
                            borderRadius: "4px",
                            cursor: "pointer",
                            border: "1px solid var(--border-light)",
                            transition: "all 0.2s",
                        }}
                        onMouseOver={(e) => {
                            const el = e.currentTarget;
                            el.style.backgroundColor = "var(--bg-hover)";
                            el.style.borderColor = "var(--accent-cyan)";
                            el.style.boxShadow =
                                "0 2px 8px rgba(0, 229, 255, 0.15)";
                        }}
                        onMouseOut={(e) => {
                            const el = e.currentTarget;
                            el.style.backgroundColor = "var(--bg-tertiary)";
                            el.style.borderColor = "var(--border-light)";
                            el.style.boxShadow = "none";
                        }}
                    >
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                marginBottom: "6px",
                            }}
                        >
                            <div
                                style={{
                                    fontSize: "11px",
                                    color: "var(--text-muted)",
                                    fontFamily: "monospace",
                                }}
                            >
                                {job.id.slice(0, 12)}...
                            </div>
                            <div
                                style={{
                                    fontSize: "10px",
                                    color: "var(--text-muted)",
                                }}
                            >
                                {new Date(job.created_at).toLocaleTimeString()}
                            </div>
                        </div>
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >
                            <div
                                style={{
                                    fontSize: "12px",
                                    color: "var(--text-secondary)",
                                }}
                            >
                                {job.plugin}
                            </div>
                            <div
                                style={{
                                    fontSize: "11px",
                                    fontWeight: 600,
                                    color: getStatusColor(job.status),
                                    backgroundColor: getStatusBackground(
                                        job.status
                                    ),
                                    padding: "3px 8px",
                                    borderRadius: "3px",
                                    textTransform: "uppercase",
                                    letterSpacing: "0.5px",
                                }}
                            >
                                {job.status}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
