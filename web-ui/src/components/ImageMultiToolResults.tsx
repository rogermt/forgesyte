import React from "react";

interface Props {
    results: { tools: Record<string, unknown> };
}

export const ImageMultiToolResults: React.FC<Props> = ({ results }) => {
    return (
        <div style={{ marginTop: "20px" }}>
            <h3>Results</h3>

            {Object.entries(results.tools).map(([toolName, toolResult]) => (
                <div
                    key={toolName}
                    style={{
                        marginBottom: "20px",
                        padding: "15px",
                        backgroundColor: "#f5f5f5",
                        borderRadius: "4px",
                    }}
                >
                    <h4 style={{ marginBottom: "10px" }}>{toolName}</h4>

                    {toolName === "ocr" && typeof toolResult === "object" && toolResult !== null && (
                        <div style={{ marginBottom: "10px" }}>
                            <p>
                                <strong>Text:</strong>{" "}
                                {(toolResult as { text: string }).text}
                            </p>
                            <p>
                                <strong>Confidence:</strong>{" "}
                                {(toolResult as { confidence: number }).confidence?.toFixed(2)}
                            </p>
                        </div>
                    )}

                    {toolName === "yolo-tracker" && typeof toolResult === "object" && toolResult !== null && (
                        <div style={{ marginBottom: "10px" }}>
                            <p>
                                <strong>Detections:</strong>
                            </p>
                        </div>
                    )}

                    <pre
                        style={{
                            backgroundColor: "#fff",
                            padding: "10px",
                            borderRadius: "4px",
                            overflowX: "auto",
                            fontSize: "12px",
                        }}
                    >
                        {JSON.stringify(toolResult, null, 2)}
                    </pre>
                </div>
            ))}
        </div>
    );
};