import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { OverlayRenderer } from './OverlayRenderer';

describe('OverlayRenderer', () => {
  const normalised = {
    frames: [
      {
        frame_index: 0,
        boxes: [{ x1: 10, y1: 20, x2: 30, y2: 40 }],
        scores: [0.95],
        labels: ['player'],
      },
    ],
  };

  it('renders SVG container', () => {
    const { container } = render(
      <OverlayRenderer data={normalised} width={640} height={480} />
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();
    expect(svg).toHaveAttribute('width', '640');
    expect(svg).toHaveAttribute('height', '480');
  });

  it('renders bounding box rects', () => {
    const { container } = render(
      <OverlayRenderer data={normalised} width={640} height={480} />
    );

    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBeGreaterThan(0);

    const rect = rects[0];
    expect(rect).toHaveAttribute('x', '10');
    expect(rect).toHaveAttribute('y', '20');
    expect(rect).toHaveAttribute('width', '20'); // 30 - 10
    expect(rect).toHaveAttribute('height', '20'); // 40 - 20
  });

  it('renders multiple boxes', () => {
    const multiBox = {
      frames: [
        {
          frame_index: 0,
          boxes: [
            { x1: 10, y1: 20, x2: 30, y2: 40 },
            { x1: 50, y1: 60, x2: 70, y2: 80 },
          ],
          scores: [0.95, 0.85],
          labels: ['player', 'player'],
        },
      ],
    };

    const { container } = render(
      <OverlayRenderer data={multiBox} width={640} height={480} />
    );

    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(2);
  });

  it('renders with blue stroke styling', () => {
    const { container } = render(
      <OverlayRenderer data={normalised} width={640} height={480} />
    );

    const rect = container.querySelector('rect');
    expect(rect).toHaveAttribute('stroke', 'blue');
    expect(rect).toHaveAttribute('fill', 'none');
  });

  it('handles empty frames gracefully', () => {
    const empty = {
      frames: [
        {
          frame_index: 0,
          boxes: [],
          scores: [],
          labels: [],
        },
      ],
    };

    const { container } = render(
      <OverlayRenderer data={empty} width={640} height={480} />
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();

    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(0);
  });

  it('renders labels with scores', () => {
    const { container } = render(
      <OverlayRenderer data={normalised} width={640} height={480} />
    );

    const texts = container.querySelectorAll('text');
    expect(texts.length).toBeGreaterThan(0);

    const labelText = texts[0].textContent;
    expect(labelText).toContain('player');
    expect(labelText).toContain('95%');
  });

  it('hides boxes when showBoxes is false', () => {
    const { container } = render(
      <OverlayRenderer
        data={normalised}
        width={640}
        height={480}
        showBoxes={false}
      />
    );

    const rects = container.querySelectorAll('rect');
    expect(rects.length).toBe(0);
  });

  it('hides labels when showLabels is false', () => {
    const { container } = render(
      <OverlayRenderer
        data={normalised}
        width={640}
        height={480}
        showLabels={false}
      />
    );

    const texts = container.querySelectorAll('text');
    expect(texts.length).toBe(0);
  });

  it('shows both boxes and labels by default', () => {
    const { container } = render(
      <OverlayRenderer data={normalised} width={640} height={480} />
    );

    const rects = container.querySelectorAll('rect');
    const texts = container.querySelectorAll('text');

    expect(rects.length).toBeGreaterThan(0);
    expect(texts.length).toBeGreaterThan(0);
  });
});
