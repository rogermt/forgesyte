import type { PluginManifest } from "../types/plugin";

export function detectToolType(
  manifest: PluginManifest,
  toolName: string
): string {
  const tool = manifest.tools[toolName];
  if (!tool) return "unknown";

  const inputs = tool.inputs;

  if ("stream_id" in inputs) return "stream";
  if ("frame_base64" in inputs) return "frame";
  return "image";
}
