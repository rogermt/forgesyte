import type { PluginManifest, Tool } from "../types/plugin";

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
    return getToolType(directTool);
  }

  // If not found, search for capability match
  const toolsArray = Array.isArray(manifest.tools)
    ? manifest.tools
    : Object.values(manifest.tools);

  for (const tool of toolsArray) {
    if (tool.capabilities?.includes(toolName)) {
      return getToolType(tool);
    }
  }

  return "unknown";
}

/**
 * Get tool type from tool definition.
 * Checks input_types (new format) first, then inputs (legacy format).
 */
function getToolType(tool: Tool): string {
  // v0.13.12: Check input_types first (new manifest format)
  const inputTypes = tool.input_types;
  if (inputTypes) {
    if (inputTypes.includes("video")) return "frame";
    if (inputTypes.includes("stream")) return "stream";
    return "image";
  }

  // Legacy: check inputs object
  const inputs = tool.inputs;
  if (inputs) {
    if ("stream_id" in inputs) return "stream";
    if ("frame_base64" in inputs) return "frame";
  }

  return "image";
}
