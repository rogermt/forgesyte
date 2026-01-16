interface ConfigPanelProps {
    pluginName: string;
    options?: Record<string, unknown>;
    onChange?: (opts: Record<string, unknown>) => void;
}

export function ConfigPanel({ pluginName }: ConfigPanelProps) {
    // TODO: Implement UI plugin loading for config components
    // Future: Load ConfigComponent dynamically via UIPluginManager
    
    return (
        <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            No configuration available for plugin: {pluginName}
        </div>
    );
}
