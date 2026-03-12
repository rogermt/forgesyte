import type { PluginManifest } from "../types/plugin";

/**
 * Detect tool type from a capability name or tool ID.
 *
 * v0.13.12: Supports both capability names (e.g., "player_detection") and
 * tool IDs (e.g., "video_player_detection"). Finds the tool that matches
 * the given name and checks its input types.
 */
export function detectToolType(
  manifest: PluginManifest,
  toolName: string
): string {
  // First try direct lookup (tool ID)
  const directTool = manifest.tools[toolName];
  if (directTool) {
    return getToolTypeFromInputs(directTool.inputs);
  }

  // If not found, search for capability match
  const toolsArray = Array.isArray(manifest.tools)
    ? manifest.tools
    : Object.values(manifest.tools);

  for (const tool of toolsArray) {
    const toolWithCaps = tool as { capabilities?: string[] };
    if (toolWithCaps.capabilities?.includes(toolName)) {
      // Found a tool with this capability - check its input type
      // Prefer input_types (new) over inputs (legacy)
      const inputTypes = (tool as { input_types?: string[] }).input_types;
      if (inputTypes?.includes("video")) {
        return "frame";  // Video tools are treated as frame-based
      }

      const inputs = (tool as { inputs?: Record<string, unknown> }).inputs;
      if (inputs) {
        return getToolTypeFromInputs(inputs);
      }
    }
  }

  return "unknown";
}

function getToolTypeFromInputs(inputs: Record<string, unknown>): string {
  if ("stream_id" in inputs) return "stream";
  if ("frame_base64" in inputs) return "frame";
  return "image";
}
