export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  entrypoint: string;
  tools: Record<string, {
    inputs: Record<string, string>;
    outputs: Record<string, string>;
  }>;
}
