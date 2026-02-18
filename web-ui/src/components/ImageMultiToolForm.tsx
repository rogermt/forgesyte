import { useState } from "react";
import { apiClient } from "../api/client";

export function ImageMultiToolForm() {
    const [file, setFile] = useState<File | null>(null);
    const [ocrSelected, setOcrSelected] = useState(false);
    const [yoloSelected, setYoloSelected] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<Record<string, unknown> | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            if (!selectedFile.type.startsWith("image/")) {
                setError("Only image files are supported");
                setFile(null);
                return;
            }
            setError(null);
            setFile(selectedFile);
            setResult(null);
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        const tools: string[] = [];
        if (ocrSelected) tools.push("ocr");
        if (yoloSelected) tools.push("yolo-tracker");

        if (tools.length === 0) return;

        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.analyzeMulti(file, tools);
            setResult(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Analysis failed");
        } finally {
            setLoading(false);
        }
    };

    const canAnalyze = file !== null && (ocrSelected || yoloSelected) && !loading;

    return (
        <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
            <h2 style={{ marginBottom: "20px" }}>Multi-Tool Image Analysis</h2>

            <div style={{ marginBottom: "20px" }}>
                <label htmlFor="image-input" style={{ display: "block", marginBottom: "8px" }}>
                    Image:
                </label>
                <input
                    id="image-input"
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    style={{ width: "100%" }}
                />
            </div>

            <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "flex", alignItems: "center", marginBottom: "8px" }}>
                    <input
                        type="checkbox"
                        checked={ocrSelected}
                        onChange={(e) => {
                            setOcrSelected(e.target.checked);
                            setError(null);
                        }}
                        style={{ marginRight: "8px" }}
                    />
                    OCR
                </label>

                <label style={{ display: "flex", alignItems: "center" }}>
                    <input
                        type="checkbox"
                        checked={yoloSelected}
                        onChange={(e) => {
                            setYoloSelected(e.target.checked);
                            setError(null);
                        }}
                        style={{ marginRight: "8px" }}
                    />
                    YOLO
                </label>
            </div>

            <button
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                style={{
                    padding: "10px 20px",
                    backgroundColor: canAnalyze ? "#007bff" : "#ccc",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: canAnalyze ? "pointer" : "not-allowed",
                }}
            >
                {loading ? "Analyzing..." : "Analyze"}
            </button>

            {error && (
                <div style={{ marginTop: "20px", color: "red" }}>
                    {error}
                </div>
            )}

            {result && (
                <div style={{ marginTop: "20px" }}>
                    <h3>Results:</h3>
                    <pre style={{ backgroundColor: "#f5f5f5", padding: "10px", borderRadius: "4px" }}>
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}