import { useEffect, useState } from "react";
import { UIPluginManager } from "./uiPluginManager";

interface PluginHostProps {
    plugin: string;
    props?: Record<string, unknown>;
}

export function PluginHost({ plugin, props = {} }: PluginHostProps) {
    const [Component, setComponent] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;

        async function load() {
            try {
                const comp = await UIPluginManager.loadUIComponent(plugin);
                if (mounted) setComponent(() => comp);
            } catch (err: any) {
                if (mounted) {
                    setError(err.message || "Failed to load plugin UI");
                }
            }
        }

        load();
        return () => {
            mounted = false;
        };
    }, [plugin]);

    if (error) {
        return (
            <div style={{ color: "var(--accent-red)" }}>
                Failed to load plugin "{plugin}": {error}
            </div>
        );
    }

    if (!Component) {
        return <div>Loading plugin UI…</div>;
    }

    return <Component {...props} />;
}
