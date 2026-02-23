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

                    {/* Generic JSON display - no tool-specific logic */}
                    <pre style={codeBlockStyle}>
                        {JSON.stringify(toolResult, null, 2)}
                    </pre>
                </div>
            ))}
        </div>
    );
};