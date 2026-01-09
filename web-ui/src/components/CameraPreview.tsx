/**
 * Camera preview component with frame capture
 */

import React, { useCallback, useEffect, useRef, useState } from "react";

export interface CameraPreviewProps {
    onFrame?: (imageData: string) => void;
    captureInterval?: number;
    enabled?: boolean;
    width?: number;
    height?: number;
    deviceId?: string;
}

export function CameraPreview({
    onFrame,
    captureInterval = 100,
    enabled = true,
    width = 640,
    height = 480,
    deviceId,
}: CameraPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const intervalRef = useRef<NodeJS.Timeout>();

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

    // Capture frame and send to callback
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

    // Set up frame capture interval
    useEffect(() => {
        if (isStreaming && enabled && onFrame) {
            intervalRef.current = setInterval(captureFrame, captureInterval);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [isStreaming, enabled, captureInterval, captureFrame, onFrame]);

    return (
        <div>
            <h3>Camera Preview</h3>
            {error && <p style={{ color: "#dc3545" }}>{error}</p>}
            <video
                ref={videoRef}
                style={{
                    width: "100%",
                    height: "auto",
                    backgroundColor: "#000",
                    borderRadius: "8px",
                }}
            />
            <canvas
                ref={canvasRef}
                style={{ display: "none" }}
            />
            {devices.length > 1 && (
                <select
                    value={selectedDevice}
                    onChange={(e) => setSelectedDevice(e.target.value)}
                    style={{
                        marginTop: "10px",
                        padding: "8px",
                        borderRadius: "4px",
                    }}
                >
                    {devices.map((device) => (
                        <option key={device.deviceId} value={device.deviceId}>
                            {device.label || `Camera ${device.deviceId.slice(0, 5)}`}
                        </option>
                    ))}
                </select>
            )}
            <p style={{ fontSize: "13px", color: "#888" }}>
                {isStreaming ? "● Streaming" : "○ Not streaming"}
            </p>
        </div>
    );
}
