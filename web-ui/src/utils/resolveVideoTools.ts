import type { PluginManifest } from "../types/plugin";

/**
 * Resolve logical capabilities (player_detection, ball_detection, etc.)
 * to the correct *video* tool IDs (video_player_tracking, video_ball_detection, etc.)
 *
 * Mapping rules:
 * - input_types includes "video"
 * - AND tool.capabilities.includes(logical_capability)
 */
export function resolveVideoTools(
  logicalTools: string[],
  manifest: PluginManifest | null
): string[] {
  if (!manifest || !manifest.tools) return logicalTools;

  const toolsArray = Array.isArray(manifest.tools)
    ? manifest.tools
    : Object.values(manifest.tools);

  const videoMap: Record<string, string> = {};

  for (const tool of toolsArray as Array<{ id?: string; input_types?: string[]; capabilities?: string[] }>) {
    if (!tool.capabilities) continue;
    if (!tool.input_types || !tool.input_types.includes("video")) continue;

    for (const cap of tool.capabilities) {
      // last one wins, but in your manifest it's 1:1 anyway
      videoMap[cap] = tool.id ?? cap;
    }
  }

  return logicalTools.map((cap) => videoMap[cap] ?? cap);
}
