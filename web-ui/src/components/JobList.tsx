/**
 * Job list component
 */

import React, { useEffect, useState } from "react";
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

    if (loading) return <p>Loading jobs...</p>;
    if (error) return <p style={{ color: "#dc3545" }}>Error: {error}</p>;
    if (jobs.length === 0) return <p>No jobs yet</p>;

    return (
        <div>
            <h3>Recent Jobs</h3>
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                {jobs.map((job) => (
                    <div
                        key={job.id}
                        onClick={() => onJobSelect(job)}
                        style={{
                            padding: "8px",
                            marginBottom: "8px",
                            backgroundColor: "#2a2a3e",
                            borderRadius: "4px",
                            cursor: "pointer",
                            border: "1px solid #444",
                            transition: "all 0.2s",
                        }}
                        onMouseOver={(e) => {
                            const el = e.currentTarget;
                            el.style.backgroundColor = "#333";
                            el.style.borderColor = "#666";
                        }}
                        onMouseOut={(e) => {
                            const el = e.currentTarget;
                            el.style.backgroundColor = "#2a2a3e";
                            el.style.borderColor = "#444";
                        }}
                    >
                        <div style={{ fontSize: "12px", color: "#aaa" }}>
                            {job.id.slice(0, 8)}...
                        </div>
                        <div style={{ fontSize: "13px", marginTop: "4px" }}>
                            {job.status}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
