import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import { UIPluginManager } from "../plugin-system/uiPluginManager";

interface ConfigPanelProps {
    pluginName: string;
    options: Record<string, unknown>;
    onChange: (opts: Record<string, unknown>) => void;
}

export function ConfigPanel({
    pluginName,
    options,
    onChange,
}: ConfigPanelProps) {
    const [ConfigComponent, setConfigComponent] = useState<ComponentType<Record<string, unknown>> | null>(null);

    useEffect(() => {
        let mounted = true;

        async function load() {
            const comp = await UIPluginManager.loadConfigComponent(pluginName);
            if (mounted) setConfigComponent(() => comp);
        }

        load();
        return () => {
            mounted = false;
        };
    }, [pluginName]);

    if (!ConfigComponent) {
        return (
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                No configuration available for this plugin.
            </div>
        );
    }

    return (
        <ConfigComponent
            options={options}
            onChange={onChange}
            pluginName={pluginName}
        />
    );
}
