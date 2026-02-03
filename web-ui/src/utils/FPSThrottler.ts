/**
 * FPSThrottler
 *
 * Throttles callback execution to respect a maximum FPS limit.
 * Used for frame-rate capping in overlay rendering.
 *
 * Example:
 *   const throttler = new FPSThrottler(30);
 *   const renderFrame = () => { render code here };
 *   throttler.throttle(renderFrame);
 */
export class FPSThrottler {
  private lastFrameTime = -Infinity;
  private frameInterval: number;
  private getTime: () => number;

  /**
   * Initialize throttler with max FPS limit.
   *
   * @param maxFps - Maximum frames per second (e.g., 30, 60)
   * @param getTime - Optional time provider (for testing). Defaults to performance.now()
   */
  constructor(maxFps: number, getTime: (() => number) | undefined = undefined) {
    this.frameInterval = 1000 / maxFps;
    this.getTime = getTime || (() => performance.now());
  }

  /**
   * Execute callback if enough time has passed since last frame.
   *
   * Skips execution if called too frequently (frames dropped).
   *
   * @param callback - Function to call if interval has elapsed
   */
  throttle(callback: () => void): void {
    const now = this.getTime();

    if (now - this.lastFrameTime >= this.frameInterval) {
      callback();
      this.lastFrameTime = now;
    }
  }
}
