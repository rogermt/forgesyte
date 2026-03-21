/**
 * ArtifactViewer - Paginated viewer for large video job results
 *
 * Clean Break (Issue #350): Displays paginated frames from video jobs
 * instead of loading entire JSON into memory.
 *
 * Discussion #352: Uses apiClient.getJobResultPage for pagination
 * instead of building URL from result_url (breaks S3 signed URLs).
 */

import React, { useEffect, useState, useCallback } from "react";
import { apiClient } from "../api/client";

interface ArtifactViewerProps {
    jobId: string;           // Required: Used for API-based pagination
    resultUrl?: string;      // Optional: Used for "Download Full JSON" button
}

interface ArtifactPage {
    offset: number;
    limit: number;
    total: number;
    frames: unknown[];
}

const PAGE_SIZE = 200;

const styles: Record<string, React.CSSProperties> = {
    container: {
        marginTop: 12,
    },
    downloadButton: {
        marginBottom: 8,
        padding: "6px 12px",
        cursor: "pointer",
    },
    loading: {
        color: "var(--text-secondary, #888)",
    },
    error: {
        color: "var(--accent-danger, #ff4444)",
    },
    frameContainer: {
        maxHeight: 300,
        overflow: "auto",
        fontSize: 11,
        backgroundColor: "var(--bg-primary, #1a1a1a)",
        padding: 8,
        borderRadius: 4,
    },
    pagination: {
        marginTop: 8,
        display: "flex",
        gap: 8,
        alignItems: "center",
    },
    button: {
        padding: "4px 12px",
        cursor: "pointer",
    },
    buttonDisabled: {
        padding: "4px 12px",
        cursor: "not-allowed",
        opacity: 0.5,
    },
    pageInfo: {
        fontSize: 12,
        color: "var(--text-secondary, #888)",
    },
};

export function ArtifactViewer({ jobId, resultUrl }: ArtifactViewerProps): React.ReactElement {
    const [page, setPage] = useState(0);
    const [data, setData] = useState<ArtifactPage | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Discussion #353: Reset pagination when jobId changes
    // Prevents showing wrong page when switching between jobs
    useEffect(() => {
        setPage(0);
        setData(null);
        setError(null);
    }, [jobId]);

    const fetchData = useCallback(async () => {
        if (!jobId) return;

        setLoading(true);
        setError(null);

        try {
            // Discussion #352: Use apiClient for pagination (preserves auth headers)
            const json = await apiClient.getJobResultPage(
                jobId,
                page * PAGE_SIZE,
                PAGE_SIZE
            );
            setData(json);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load artifact");
        } finally {
            setLoading(false);
        }
    }, [jobId, page]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const canPrev = page > 0;
    const canNext = data ? (page + 1) * PAGE_SIZE < data.total : false;

    const handlePrev = (): void => {
        if (canPrev) {
            setPage((p) => p - 1);
        }
    };

    const handleNext = (): void => {
        if (canNext) {
            setPage((p) => p + 1);
        }
    };

    const handleDownload = (): void => {
        // Use resultUrl for download (may be S3 signed URL)
        if (resultUrl) {
            // Security: noopener,noreferrer prevents tab-opener attacks
            window.open(resultUrl, "_blank", "noopener,noreferrer");
        }
    };

    return (
        <div style={styles.container}>
            <button
                style={resultUrl ? styles.downloadButton : styles.buttonDisabled}
                onClick={handleDownload}
                disabled={!resultUrl}
            >
                Download Full JSON
            </button>

            {loading && <p style={styles.loading}>Loading artifact…</p>}
            {error && <p style={styles.error}>Error: {error}</p>}

            {data && (
                <>
                    <pre style={styles.frameContainer}>
                        {JSON.stringify(data.frames ?? [], null, 2)}
                    </pre>
                    <div style={styles.pagination}>
                        <button
                            style={canPrev ? styles.button : styles.buttonDisabled}
                            onClick={handlePrev}
                            disabled={!canPrev}
                        >
                            Prev
                        </button>
                        <span style={styles.pageInfo}>
                            Page {page + 1} of {Math.ceil((data.total || 1) / PAGE_SIZE)}{" "}
                            ({data.total} total frames)
                        </span>
                        <button
                            style={canNext ? styles.button : styles.buttonDisabled}
                            onClick={handleNext}
                            disabled={!canNext}
                        >
                            Next
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
