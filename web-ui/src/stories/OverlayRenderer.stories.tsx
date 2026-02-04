import type { Meta, StoryObj } from '@storybook/react';
import { OverlayRenderer } from '../components/OverlayRenderer';

const meta = {
  title: 'Components/OverlayRenderer',
  component: OverlayRenderer,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Canonical overlay renderer for all plugin outputs. Consumes normalised schema and renders SVG overlays.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    showBoxes: {
      control: 'boolean',
      description: 'Toggle bounding box rendering',
    },
    showLabels: {
      control: 'boolean',
      description: 'Toggle label rendering',
    },
  },
} satisfies Meta<typeof OverlayRenderer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: 'Single Detection',
  args: {
    data: {
      frames: [{
        frame_index: 0,
        boxes: [{ x1: 100, y1: 100, x2: 300, y2: 300 }],
        scores: [0.92],
        labels: ['person']
      }]
    },
    width: 640,
    height: 480,
    showBoxes: true,
    showLabels: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows a single person detection with bounding box and confidence label.',
      },
    },
  },
};

export const MultipleDetections: Story = {
  name: 'Multiple Detections',
  args: {
    data: {
      frames: [{
        frame_index: 0,
        boxes: [
          { x1: 50, y1: 50, x2: 150, y2: 150 },
          { x1: 200, y1: 100, x2: 350, y2: 250 },
          { x1: 400, y1: 200, x2: 500, y2: 350 },
        ],
        scores: [0.92, 0.87, 0.78],
        labels: ['person', 'car', 'bicycle']
      }]
    },
    width: 640,
    height: 480,
    showBoxes: true,
    showLabels: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows multiple detections with different labels and confidence scores.',
      },
    },
  },
};

export const NoBoxes: Story = {
  name: 'No Detections',
  args: {
    data: { frames: [] },
    width: 640,
    height: 480,
    showBoxes: true,
    showLabels: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Empty frame with no detections to render.',
      },
    },
  },
};

export const LabelsOnly: Story = {
  name: 'Labels Only',
  args: {
    data: {
      frames: [{
        frame_index: 0,
        boxes: [{ x1: 100, y1: 100, x2: 300, y2: 300 }],
        scores: [0.92],
        labels: ['person']
      }]
    },
    width: 640,
    height: 480,
    showBoxes: false,
    showLabels: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows only labels without bounding boxes.',
      },
    },
  },
};

export const BoxesOnly: Story = {
  name: 'Boxes Only',
  args: {
    data: {
      frames: [{
        frame_index: 0,
        boxes: [{ x1: 100, y1: 100, x2: 300, y2: 300 }],
        scores: [0.92],
        labels: ['person']
      }]
    },
    width: 640,
    height: 480,
    showBoxes: true,
    showLabels: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows only bounding boxes without labels.',
      },
    },
  },
};

export const HighDensityFrame: Story = {
  name: 'High Density Detection',
  args: {
    data: {
      frames: [{
        frame_index: 0,
        boxes: [
          { x1: 20, y1: 20, x2: 80, y2: 80 },
          { x1: 100, y1: 30, x2: 180, y2: 90 },
          { x1: 200, y1: 50, x2: 280, y2: 120 },
          { x1: 320, y1: 80, x2: 400, y2: 180 },
          { x1: 450, y1: 100, x2: 520, y2: 200 },
          { x1: 50, y1: 200, x2: 120, y2: 280 },
          { x1: 150, y1: 250, x2: 220, y2: 350 },
          { x1: 300, y1: 300, x2: 380, y2: 400 },
        ],
        scores: [0.95, 0.91, 0.88, 0.85, 0.82, 0.79, 0.75, 0.72],
        labels: ['person', 'person', 'person', 'car', 'car', 'person', 'person', 'car']
      }]
    },
    width: 640,
    height: 480,
    showBoxes: true,
    showLabels: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'High-density detection frame with 8 objects of various types.',
      },
    },
  },
};

