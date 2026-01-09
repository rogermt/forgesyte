/**
 * Results panel component
 */

import React from "react";
import { FrameResult } from "../hooks/useWebSocket";
import { Job } from "../api/client";

export interface ResultsPanelProps {
    mode: "stream" | "job";
    streamResult?: FrameResult | null;
    job?: Job | null;
}

export function ResultsPanel({
    mode,
    streamResult,
    job,
}: ResultsPanelProps) {
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
        <div style={styles.panel}>
            <div style={styles.header}>Results</div>

            <div style={styles.content}>
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
                        <pre style={styles.codeBlock}>
                            {JSON.stringify(streamResult.result, null, 2)}
                        </pre>
                    </div>
                ) : mode === "stream" ? (
                    <p style={styles.emptyState}>Waiting for results...</p>
                ) : null}

                {mode === "job" && job ? (
                    <div>
                        <div style={styles.metaInfo}>
                            <div>
                                <div style={styles.label}>Job ID: {job.id}</div>
                                <div style={styles.subLabel}>
                                    Status: {job.status}
                                </div>
                            </div>
                        </div>
                        <pre style={styles.codeBlock}>
                            {JSON.stringify(job.result, null, 2)}
                        </pre>
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
