import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { FPSThrottler } from './FPSThrottler';

describe('FPSThrottler', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('respects fpsLimit of 15 fps', () => {
    let currentTime = 0;
    const getTime = () => currentTime;

    const throttler = new FPSThrottler(15, getTime); // 15 FPS = ~66.67ms interval
    const renderCount = { value: 0 };

    // Simulate 2 seconds of incoming frames at 60 FPS (16.67ms each)
    for (let i = 0; i < 120; i++) {
      throttler.throttle(() => {
        renderCount.value++;
      });
      currentTime += 16.67; // 60 FPS input
    }

    // After 2 seconds at 60 FPS supply, should have rendered ~30 frames (15 FPS * 2s)
    expect(renderCount.value).toBeGreaterThanOrEqual(25);
    expect(renderCount.value).toBeLessThanOrEqual(35);
  });

  it('calls callback when interval is reached', () => {
    let currentTime = 0;
    const getTime = () => currentTime;

    const throttler = new FPSThrottler(30, getTime);
    const callback = vi.fn();

    // First call should execute
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1);

    // Advance just short of next interval (33ms for 30 FPS)
    currentTime += 32;
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1); // Still 1

    // Advance past interval
    currentTime += 2;
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(2); // Now 2
  });

  it('skips frames when called too frequently', () => {
    let currentTime = 0;
    const getTime = () => currentTime;

    const throttler = new FPSThrottler(10, getTime); // 10 FPS = 100ms per frame
    const callback = vi.fn();

    // Call multiple times in quick succession
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1);

    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1); // Still 1, skipped

    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1); // Still 1, skipped

    // Advance past interval
    currentTime += 100;
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(2); // Now 2
  });

  it('handles zero time start', () => {
    let currentTime = 0;
    const getTime = () => currentTime;

    const throttler = new FPSThrottler(30, getTime);
    const callback = vi.fn();

    // Start at time 0
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1);

    // Still at time 0 (no advancement)
    throttler.throttle(callback);
    expect(callback).toHaveBeenCalledTimes(1); // Skipped
  });
});
