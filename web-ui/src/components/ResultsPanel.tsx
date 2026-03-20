/**
 * Results panel component (plugin-agnostic for v0.9.4).
 *
 * Clean Break (Issue #350): No more inline results.
 * All results are viewed via ArtifactViewer component with pagination.
 */

import React, { useMemo } from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";
import { ArtifactViewer } from "./ArtifactViewer";

export interface ResultsPanelProps {
    mode?: "stream" | "job";
    streamResult?: FrameResult | null;
    job?: Job | null;
    pluginName?: string;
    result?: Record<string, unknown> | null;
}

export function ResultsPanel({
    mode = "stream",
    streamResult,
    job,
}: ResultsPanelProps) {
    // PERFORMANCE: Memoize stream result JSON
    const streamResultJson = useMemo(() => {
        if (!streamResult?.result) return "null";
        return JSON.stringify(streamResult.result, null, 2);
    }, [streamResult?.result]);

    const styles: Record<string, React.CSSProperties> = {
        panel: {
            backgroundColor: "var(--bg-secondary)",
            borderRadius: "8px",
            padding: "16px",
            minHeight: "400px",
            display: "flex",
            flexDirection: "column",
            border: "1px solid var(--border-light)",
        },
        header: {
            fontSize: "14px",
            fontWeight: 600,
            marginBottom: "12px",
            color: "var(--text-primary)",
        },
        content: {
            flex: 1,
            overflowY: "auto",
            fontSize: "13px",
            color: "var(--text-secondary)",
            paddingRight: "4px",
        },
        metaInfo: {
            marginBottom: "12px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
        },
        label: {
            fontSize: "12px",
            color: "var(--text-primary)",
            fontWeight: 500,
        },
        subLabel: {
            fontSize: "11px",
            color: "var(--text-muted)",
            marginTop: "4px",
            fontFamily: "monospace",
        },
        codeBlock: {
            backgroundColor: "var(--bg-primary)",
            padding: "8px",
            borderRadius: "4px",
            overflow: "auto",
            fontSize: "11px",
            color: "#a8ff60",
            fontFamily: "monospace",
            border: "1px solid var(--border-light)",
            lineHeight: 1.5,
        },
        emptyState: {
            color: "var(--text-muted)",
            fontSize: "13px",
        },
    };

    return (
        <div
            data-testid="results-panel"
            style={{
                ...styles.panel,
                minHeight: "400px",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <div
                style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    marginBottom: "12px",
                    color: "var(--text-primary)",
                }}
            >
                Results
            </div>

            <div
                data-testid="results-content"
                style={{
                    flex: 1,
                    overflowY: "auto",
                    fontSize: "13px",
                    color: "var(--text-secondary)",
                    paddingRight: "4px",
                }}
            >
                {mode === "stream" && streamResult ? (
                    <div>
                        <div style={styles.metaInfo}>
                            <div>
                                <div style={styles.label}>
                                    Frame ID: {streamResult.frame_id}
                                </div>
                                <div style={styles.subLabel}>
                                    {streamResult.processing_time_ms}ms
                                </div>
                            </div>
                        </div>

                        {/* Raw result JSON only (plugin-agnostic) */}
                         <div>
                             <div style={styles.label}>Raw Result</div>
                             <pre style={styles.codeBlock}>
                                 {streamResultJson}
                             </pre>
                         </div>
                    </div>
                ) : mode === "stream" ? (
                    <p style={styles.emptyState}>Waiting for results...</p>
                ) : null}

                {mode === "job" && job ? (
                    <div>
                        <div style={styles.metaInfo}>
                            <div>
                                <div style={styles.label}>Job ID: {job.job_id}</div>
                                <div style={styles.subLabel}>
                                    Status: {job.status}
                                </div>
                                {job.job_type && (
                                    <div style={styles.subLabel}>
                                        Type: {job.job_type}
                                    </div>
                                )}
                                {job.tool_list && job.tool_list.length > 0 && (
                                    <div style={styles.subLabel}>
                                        Tools: {job.tool_list.join(", ")}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Clean Break: Show summary if available */}
                        {job.summary && (
                            <div style={{ ...styles.codeBlock, marginBottom: "12px" }}>
                                <div style={styles.label}>Summary</div>
                                <pre style={{ margin: 0, fontSize: "11px" }}>
                                    {JSON.stringify(job.summary, null, 2)}
                                </pre>
                            </div>
                        )}

                        {/* Clean Break: Use ArtifactViewer for all jobs */}
                        {job.result_url && (
                            <ArtifactViewer url={job.result_url} />
                        )}

                        {/* No result available */}
                        {!job.summary && !job.result_url && (
                            <p style={styles.emptyState}>No result available.</p>
                        )}
                    </div>
                ) : mode === "job" ? (
                    <p style={styles.emptyState}>
                        Select a job to view results
                    </p>
                ) : null}
            </div>
        </div>
    );
}
