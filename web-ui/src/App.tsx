/**
 * Main application component for ForgeSyte
 */

import React, { useCallback, useState } from "react";
import { CameraPreview } from "./components/CameraPreview";
import { PluginSelector } from "./components/PluginSelector";
import { JobList } from "./components/JobList";
import { ResultsPanel } from "./components/ResultsPanel";
import { useWebSocket, FrameResult } from "./hooks/useWebSocket";
import { apiClient, Job } from "./api/client";

type ViewMode = "stream" | "upload" | "jobs";

function App() {
    const [viewMode, setViewMode] = useState<ViewMode>("stream");
    const [selectedPlugin, setSelectedPlugin] = useState("motion_detector");
    const [streamEnabled, setStreamEnabled] = useState(false);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [uploadResult, setUploadResult] = useState<Job | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    // WebSocket connection for streaming
    const {
        isConnected,
        isConnecting,
        error: wsError,
        sendFrame,
        switchPlugin,
        latestResult,
        stats,
    } = useWebSocket({
        url: "/v1/stream",
        plugin: selectedPlugin,
        onResult: (result: FrameResult) => {
            console.log("Frame result:", result);
        },
        onError: (error: string) => {
            console.error("WebSocket error:", error);
        },
    });

    // Handle camera frames
    const handleFrame = useCallback(
        (imageData: string) => {
            if (isConnected && streamEnabled) {
                sendFrame(imageData);
            }
        },
        [isConnected, streamEnabled, sendFrame]
    );

    // Handle plugin change
    const handlePluginChange = useCallback(
        (pluginName: string) => {
            setSelectedPlugin(pluginName);
            if (isConnected) {
                switchPlugin(pluginName);
            }
        },
        [isConnected, switchPlugin]
    );

    // Handle file upload
    const handleFileUpload = async (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            const response = await apiClient.analyzeImage(file, selectedPlugin);
            const job = await apiClient.pollJob(response.job_id);
            setUploadResult(job);
            setSelectedJob(job);
        } catch (err) {
            console.error("Upload failed:", err);
        } finally {
            setIsUploading(false);
        }
    };

    const styles: Record<string, React.CSSProperties> = {
        app: {
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            backgroundColor: "var(--bg-primary)",
        },
        header: {
            padding: "16px 24px",
            backgroundColor: "var(--bg-primary)",
            borderBottom: "1px solid var(--border-color)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
        },
        logo: {
            fontSize: "20px",
            fontWeight: 700,
            color: "var(--text-primary)",
        },
        nav: {
            display: "flex",
            gap: "8px",
        },
        navButton: {
            padding: "8px 16px",
            border: "1px solid transparent",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "14px",
            transition: "all 0.2s",
            color: "var(--text-primary)",
            fontWeight: 500,
        },
        status: {
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "13px",
            color: "var(--text-secondary)",
        },
        indicator: {
            width: "8px",
            height: "8px",
            borderRadius: "50%",
        },
        main: {
            flex: 1,
            display: "grid",
            gridTemplateColumns: "300px 1fr 350px",
            gap: "16px",
            padding: "16px",
        },
        sidebar: {
            display: "flex",
            flexDirection: "column",
            gap: "16px",
        },
        panel: {
            backgroundColor: "var(--bg-secondary)",
            borderRadius: "8px",
            padding: "16px",
            border: "1px solid var(--border-light)",
        },
        content: {
            display: "flex",
            flexDirection: "column",
            gap: "16px",
        },
    };

    return (
        <div style={styles.app}>
            {/* Header */}
            <header style={styles.header}>
                <div style={styles.logo}>🔧 ForgeSyte</div>

                <nav style={styles.nav}>
                    {(["stream", "upload", "jobs"] as ViewMode[]).map((mode) => (
                        <button
                            key={mode}
                            style={{
                                ...styles.navButton,
                                backgroundColor:
                                    viewMode === mode
                                        ? "var(--accent-orange)"
                                        : "var(--bg-tertiary)",
                                borderColor:
                                    viewMode === mode
                                        ? "var(--accent-orange)"
                                        : "var(--border-light)",
                            }}
                            onClick={() => setViewMode(mode)}
                        >
                            {mode.charAt(0).toUpperCase() + mode.slice(1)}
                        </button>
                    ))}
                </nav>

                <div style={styles.status}>
                    <div
                        style={{
                            ...styles.indicator,
                            backgroundColor: isConnected
                                ? "#28a745"
                                : isConnecting
                                  ? "#ffc107"
                                  : "#dc3545",
                        }}
                    />
                    <span>
                        {isConnected
                            ? "Connected"
                            : isConnecting
                              ? "Connecting..."
                              : "Disconnected"}
                    </span>
                </div>
            </header>

            {/* Main content */}
            <main style={styles.main}>
                {/* Left sidebar */}
                <aside style={styles.sidebar}>
                    <div style={styles.panel}>
                        <PluginSelector
                            selectedPlugin={selectedPlugin}
                            onPluginChange={handlePluginChange}
                            disabled={streamEnabled}
                        />
                    </div>

                    {viewMode === "jobs" && (
                        <div style={styles.panel}>
                            <JobList onJobSelect={setSelectedJob} />
                        </div>
                    )}
                </aside>

                {/* Main content area */}
                <section style={styles.content}>
                    {viewMode === "stream" && (
                        <>
                            <div style={styles.panel}>
                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                        marginBottom: "12px",
                                    }}
                                >
                                    <h3 style={{ margin: 0 }}>Stream</h3>
                                    <button
                                        onClick={() =>
                                            setStreamEnabled(!streamEnabled)
                                        }
                                        disabled={!isConnected}
                                        style={{
                                            padding: "8px 16px",
                                            backgroundColor: streamEnabled
                                                ? "var(--accent-green)"
                                                : "var(--bg-tertiary)",
                                            color: "var(--text-primary)",
                                            border: "1px solid var(--border-light)",
                                            borderRadius: "4px",
                                            cursor: isConnected
                                                ? "pointer"
                                                : "not-allowed",
                                            fontWeight: 500,
                                            fontSize: "13px",
                                            transition: "all 0.2s",
                                            opacity: isConnected ? 1 : 0.6,
                                        }}
                                        onMouseOver={(e) => {
                                            if (isConnected && !streamEnabled) {
                                                e.currentTarget.style.backgroundColor =
                                                    "var(--accent-green)";
                                                e.currentTarget.style.color =
                                                    "var(--text-primary)";
                                            }
                                        }}
                                        onMouseOut={(e) => {
                                            if (isConnected && !streamEnabled) {
                                                e.currentTarget.style.backgroundColor =
                                                    "var(--bg-tertiary)";
                                                e.currentTarget.style.color =
                                                    "var(--text-primary)";
                                            }
                                        }}
                                    >
                                        {streamEnabled
                                            ? "Stop Streaming"
                                            : "Start Streaming"}
                                    </button>
                                </div>
                                <CameraPreview
                                    onFrame={handleFrame}
                                    enabled={streamEnabled}
                                    captureInterval={200}
                                />
                            </div>
                        </>
                    )}

                    {viewMode === "upload" && (
                        <div style={styles.panel}>
                            <p>Upload image for analysis</p>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileUpload}
                                disabled={isUploading}
                            />
                            {isUploading && <p>Analyzing...</p>}
                        </div>
                    )}

                    {viewMode === "jobs" && (
                        <div style={{ ...styles.panel, flex: 1 }}>
                            <h3>Job Details</h3>
                            {selectedJob ? (
                                <pre>
                                    {JSON.stringify(selectedJob, null, 2)}
                                </pre>
                            ) : (
                                <p>Select a job</p>
                            )}
                        </div>
                    )}

                    {wsError && (
                        <div
                            style={{
                                padding: "12px",
                                backgroundColor: "rgba(220, 53, 69, 0.1)",
                                border: "1px solid var(--accent-red)",
                                borderRadius: "4px",
                                color: "var(--accent-red)",
                            }}
                        >
                            WebSocket Error: {wsError}
                        </div>
                    )}
                </section>

                {/* Right sidebar */}
                <aside>
                    <ResultsPanel
                        mode={viewMode === "stream" ? "stream" : "job"}
                        streamResult={latestResult}
                        job={
                            viewMode === "upload" ? uploadResult : selectedJob
                        }
                    />
                </aside>
            </main>
        </div>
    );
}

export default App;
