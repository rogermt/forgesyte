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
        },
        header: {
            padding: "16px 24px",
            backgroundColor: "#16162a",
            borderBottom: "1px solid #333",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
        },
        logo: {
            fontSize: "20px",
            fontWeight: 700,
            color: "#fff",
        },
        nav: {
            display: "flex",
            gap: "8px",
        },
        navButton: {
            padding: "8px 16px",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "14px",
            transition: "all 0.2s",
        },
        status: {
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "13px",
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
            backgroundColor: "#1e1e2e",
            borderRadius: "8px",
            padding: "16px",
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
                                    viewMode === mode ? "#4CAF50" : "#2a2a3e",
                                color: "#fff",
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
                                border: "1px solid #dc3545",
                                borderRadius: "4px",
                                color: "#dc3545",
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
