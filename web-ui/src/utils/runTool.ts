/**
 * Unified Tool Runner with Logging and Retry
 * 
 * Centralized utility for executing plugin tools with:
 * - Structured logging for debugging
 * - Exponential backoff retry for reliability
 * - Error handling that never throws (returns result object)
 */

export interface RunToolOptions {
  pluginId: string;
  toolName: string;
  args: Record<string, unknown>;
}

export interface RunToolResult {
  result: Record<string, unknown> | null;
  success: boolean;
  error?: string;
}

export interface LoggingContext {
  pluginId: string;
  toolName: string;
  endpoint: string;
  attempt?: number;
  maxRetries?: number;
}

export interface RetryOptions {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
}

/**
 * Wrapper that adds structured logging to async functions
 * Logs start, success, and error events with timing information
 */
export function withLogging<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  context: LoggingContext
): T {
  return (async (...args: unknown[]) => {
    const start = performance.now();
    console.debug("🔧 runTool:start", context);

    try {
      const result = await fn(...args);
      const durationMs = performance.now() - start;
      console.debug("🔧 runTool:success", { ...context, durationMs });
      return result;
    } catch (error) {
      const durationMs = performance.now() - start;
      console.error("🔧 runTool:error", { ...context, durationMs, error });
      throw error;
    }
  }) as T;
}

/**
 * Wrapper that adds exponential backoff retry logic
 * Retries on failure with increasing delays
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelayMs = 200,
    maxDelayMs = 2000,
    backoffMultiplier = 2,
  } = options;

  let attempt = 0;
  let delay = baseDelayMs;

  for (; attempt < maxRetries + 1; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt >= maxRetries) {
        throw err;
      }
      await new Promise((r) => setTimeout(r, delay));
      delay = Math.min(delay * backoffMultiplier, maxDelayMs);
    }
  }
  
  throw new Error("Unexpected state in retry loop");
}

/**
 * Unified tool execution with logging and retry
 * 
 * @param pluginId - Plugin identifier (e.g., "forgesyte-yolo-tracker")
 * @param toolName - Tool name (e.g., "player_detection")
 * @param args - Tool arguments matching manifest input schema
 * @returns { result, success, error? } - Never throws, always returns result object
 */
export async function runTool({
  pluginId,
  toolName,
  args,
}: RunToolOptions): Promise<RunToolResult> {
  const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;

  const start = performance.now();
  console.debug("🔧 runTool:start", { pluginId, toolName, endpoint });

  try {
    // Log the request payload for debugging
    console.log("runTool:request", { pluginId, toolName, payload: { args } });

    // Execute with retry for network/JSON errors only
    const { resp, json } = await withRetry(
      async (): Promise<{ resp: Response; json: Record<string, unknown> }> => {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ args }),
        });

        // Get response data
        const data = await res.json().catch(async (): Promise<Record<string, unknown>> => {
          // If JSON parsing fails, get the raw text for debugging
          const text = await res.text().catch(() => "unknown");
          console.log("runTool:error-response", { pluginId, toolName, status: res.status, text });
          throw new Error(`Invalid JSON from tool: ${text}`);
        });

        // Log successful response for debugging
        console.log("runTool:response", { pluginId, toolName, status: res.status, success: !!data?.result });

        return { resp: res, json: data };
      },
      { maxRetries: 3, baseDelayMs: 200, maxDelayMs: 2000, backoffMultiplier: 2 }
    );

    // HTTP errors don't retry (business logic errors)
    if (!resp.ok || (json.success as boolean) === false) {
      const error = (json.detail as string) || (json.error as string) || `HTTP ${resp.status}`;
      const durationMs = performance.now() - start;
      console.debug("🔧 runTool:success", { pluginId, toolName, durationMs });
      return { result: null, success: false, error };
    }

    const durationMs = performance.now() - start;
    console.debug("🔧 runTool:success", { pluginId, toolName, durationMs });
    return { result: (json.result as Record<string, unknown>) || json, success: true };
  } catch (error) {
    const durationMs = performance.now() - start;
    console.error("🔧 runTool:error", { pluginId, toolName, durationMs, error });
    return {
      result: null,
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

