import React from "react";

interface Props {
    results: { tools: Record<string, unknown> };
}

export const ImageMultiToolResults: React.FC<Props> = ({ results }) => {
    const codeBlockStyle: React.CSSProperties = {
        backgroundColor: "var(--bg-primary)",
        padding: "8px",
        borderRadius: "4px",
        overflow: "auto",
        fontSize: "11px",
        color: "#a8ff60",
        fontFamily: "monospace",
        border: "1px solid var(--border-light)",
        lineHeight: 1.5,
    };

    const toolLabelStyle: React.CSSProperties = {
        fontSize: "12px",
        color: "var(--text-primary)",
        fontWeight: 500,
        marginBottom: "8px",
    };

    return (
        <div style={{ marginTop: "20px" }}>
            <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "12px" }}>
                Multi-Tool Results
            </div>

            {Object.entries(results.tools).map(([toolName, toolResult]) => (
                <div
                    key={toolName}
                    style={{
                        marginBottom: "16px",
                    }}
                >
                    <div style={toolLabelStyle}>{toolName}</div>

                    {toolName === "ocr" && typeof toolResult === "object" && toolResult !== null && (
                        <div style={{ marginBottom: "8px", fontSize: "13px" }}>
                            <p style={{ margin: "0 0 4px 0" }}>
                                <strong>Text:</strong>{" "}
                                {(toolResult as { text: string }).text}
                            </p>
                            <p style={{ margin: "0" }}>
                                <strong>Confidence:</strong>{" "}
                                {(toolResult as { confidence: number }).confidence?.toFixed(2)}
                            </p>
                        </div>
                    )}

                    <pre style={codeBlockStyle}>
                        {JSON.stringify(toolResult, null, 2)}
                    </pre>
                </div>
            ))}
        </div>
    );
};