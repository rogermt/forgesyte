/**
 * ArtifactViewer - Paginated viewer for large video job results
 *
 * Clean Break (Issue #350): Displays paginated frames from video jobs
 * instead of loading entire JSON into memory.
 */

import React, { useEffect, useState, useCallback } from "react";

interface ArtifactViewerProps {
    url: string;
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

export function ArtifactViewer({ url }: ArtifactViewerProps): React.ReactElement {
    const [page, setPage] = useState(0);
    const [data, setData] = useState<ArtifactPage | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!url) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${url}/page?offset=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const json: ArtifactPage = await response.json();
            setData(json);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load artifact");
        } finally {
            setLoading(false);
        }
    }, [url, page]);

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
        window.open(url, "_blank");
    };

    return (
        <div style={styles.container}>
            <button style={styles.downloadButton} onClick={handleDownload}>
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
