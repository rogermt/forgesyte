/**
 * Camera preview component with frame capture
 *
 * Phase 17: Added streaming mode with requestAnimationFrame + FPSThrottler
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRealtimeStreaming } from "../realtime/useRealtime";
import { FPSThrottler } from "../utils/FPSThrottler";

export interface CameraPreviewProps {
    onFrame?: (imageData: string) => void;
    captureInterval?: number;
    enabled?: boolean;
    width?: number;
    height?: number;
    deviceId?: string;
    streaming?: boolean; // Phase 17: Enable streaming mode
}

export function CameraPreview({
    onFrame,
    captureInterval = 100,
    enabled = true,
    width = 640,
    height = 480,
    deviceId,
    streaming = false, // Phase 17: Default to legacy mode
}: CameraPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const intervalRef = useRef<ReturnType<typeof setInterval>>();
    const rafRef = useRef<number>(); // Phase 17: requestAnimationFrame ID
    const throttlerRef = useRef<FPSThrottler | null>(null); // Phase 17: FPS throttler

    // Phase 17: Get realtime hook (always call, but only use in streaming mode)
    const realtimeHook = useRealtimeStreaming();

    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<string>(deviceId || "");

    // Get available camera devices
    useEffect(() => {
        navigator.mediaDevices
            .enumerateDevices()
            .then((deviceList) => {
                const videoDevices = deviceList.filter((d) => d.kind === "videoinput");
                setDevices(videoDevices);
                if (!selectedDevice && videoDevices.length > 0) {
                    setSelectedDevice(videoDevices[0].deviceId);
                }
            })
            .catch((err) => {
                console.error("Failed to enumerate devices:", err);
            });
    }, [selectedDevice]);

    // Start camera stream
    const startCamera = useCallback(async () => {
        try {
            const constraints: MediaStreamConstraints = {
                video: {
                    width: { ideal: width },
                    height: { ideal: height },
                    deviceId: selectedDevice ? { exact: selectedDevice } : undefined,
                },
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
                setIsStreaming(true);
                setError(null);
            }
        } catch (err) {
            console.error("Failed to start camera:", err);
            setError(err instanceof Error ? err.message : "Failed to access camera");
            setIsStreaming(false);
        }
    }, [width, height, selectedDevice]);

    // Stop camera stream
    const stopCamera = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setIsStreaming(false);
    }, []);

    // Phase 17: Capture frame for streaming mode
    const captureStreamingFrame = useCallback(() => {
        if (!videoRef.current || !canvasRef.current || !isStreaming || !enabled || !streaming || !realtimeHook) {
            return;
        }

        const canvas = canvasRef.current;
        const video = videoRef.current;
        const ctx = canvas.getContext("2d");

        if (!ctx) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Convert to JPEG and send binary frame
        canvas.toBlob(async (blob) => {
            if (!blob) return;
            
            const arrayBuffer = await blob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            
            // Send binary frame via realtime hook
            realtimeHook.sendFrame(uint8Array);
        }, "image/jpeg", 0.8);
    }, [isStreaming, enabled, streaming, realtimeHook]);

    // Phase 17: Setup requestAnimationFrame loop for streaming mode
    useEffect(() => {
        if (!streaming || !isStreaming || !enabled) {
            // Clean up streaming resources
            if (rafRef.current) {
                cancelAnimationFrame(rafRef.current);
                rafRef.current = undefined;
            }
            throttlerRef.current = null;
            return;
        }

        // Create FPS throttler (initial 15 FPS)
        if (!throttlerRef.current) {
            throttlerRef.current = new FPSThrottler(15);
        }

        // RequestAnimationFrame loop with FPS throttling
        const loop = () => {
            if (throttlerRef.current) {
                throttlerRef.current.throttle(captureStreamingFrame);
            }
            rafRef.current = requestAnimationFrame(loop);
        };

        rafRef.current = requestAnimationFrame(loop);

        return () => {
            if (rafRef.current) {
                cancelAnimationFrame(rafRef.current);
                rafRef.current = undefined;
            }
        };
    }, [streaming, isStreaming, enabled, captureStreamingFrame]);

    // Phase 17: Reduce FPS when slow_down warnings received
    useEffect(() => {
        if (streaming && realtimeHook && realtimeHook.state.slowDownWarnings > 0 && throttlerRef.current) {
            throttlerRef.current = new FPSThrottler(5);
        }
    }, [streaming, realtimeHook]);
    
    if (realtimeHook && realtimeHook.state.slowDownWarnings > 0 && throttlerRef.current) {
        throttlerRef.current = new FPSThrottler(5);
    }

    // Legacy mode: Capture frame and send to callback
    const captureFrame = useCallback(() => {
        if (!videoRef.current || !canvasRef.current || !isStreaming || !enabled) {
            return;
        }

        const canvas = canvasRef.current;
        const video = videoRef.current;
        const ctx = canvas.getContext("2d");

        if (!ctx) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
        const base64Data = dataUrl.split(",")[1];

        onFrame?.(base64Data);
    }, [isStreaming, enabled, onFrame]);

    // Start/stop camera based on enabled prop
    useEffect(() => {
        if (enabled) {
            startCamera();
        } else {
            stopCamera();
        }

        return () => {
            stopCamera();
        };
    }, [enabled, startCamera, stopCamera]);

    // Legacy mode: Set up frame capture interval
    useEffect(() => {
        if (streaming) return; // Skip in streaming mode

        if (isStreaming && enabled && onFrame) {
            intervalRef.current = setInterval(captureFrame, captureInterval);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [streaming, isStreaming, enabled, captureInterval, captureFrame, onFrame]);

    return (
        <div>
            <h3>Camera Preview</h3>
            {error && (
                <p
                    style={{
                        color: "var(--accent-red)",
                        padding: "8px",
                        backgroundColor: "rgba(220, 53, 69, 0.1)",
                        borderRadius: "4px",
                        border: "1px solid var(--accent-red)",
                    }}
                >
                    {error}
                </p>
            )}
            <video
                ref={videoRef}
                style={{
                    width: "100%",
                    height: "auto",
                    backgroundColor: "var(--bg-primary)",
                    borderRadius: "8px",
                    border: "1px solid var(--border-light)",
                    display: "block",
                    marginBottom: "12px",
                }}
            />
            <canvas
                ref={canvasRef}
                style={{ display: "none" }}
            />
            {devices.length > 1 && (
                <div style={{ marginBottom: "12px" }}>
                    <label
                        style={{
                            display: "block",
                            marginBottom: "4px",
                            fontSize: "12px",
                            fontWeight: 500,
                            color: "var(--text-secondary)",
                        }}
                    >
                        Camera Device
                    </label>
                    <select
                        value={selectedDevice}
                        onChange={(e) => setSelectedDevice(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "8px 12px",
                            borderRadius: "4px",
                            border: "1px solid var(--border-light)",
                            backgroundColor: "var(--bg-tertiary)",
                            color: "var(--text-secondary)",
                            fontSize: "13px",
                        }}
                    >
                        {devices.map((device) => (
                            <option key={device.deviceId} value={device.deviceId}>
                                {device.label ||
                                    `Camera ${device.deviceId.slice(0, 5)}`}
                            </option>
                        ))}
                    </select>
                </div>
            )}
            <p
                style={{
                    fontSize: "12px",
                    color: isStreaming
                        ? "var(--accent-green)"
                        : "var(--text-muted)",
                    margin: 0,
                    fontWeight: 500,
                }}
            >
                {isStreaming ? "● Streaming" : "○ Not streaming"}
                {streaming && " (Phase 17)"}
            </p>
        </div>
    );
}
