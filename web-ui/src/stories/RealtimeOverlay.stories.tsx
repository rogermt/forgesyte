import type { Meta, StoryObj } from '@storybook/react';
import { RealtimeOverlay } from '@/components/RealtimeOverlay';
import { RealtimeProvider } from '@/realtime/RealtimeContext';

const meta: Meta<typeof RealtimeOverlay> = {
  title: 'Components/RealtimeOverlay',
  component: RealtimeOverlay,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <RealtimeProvider>
        <div style={{ width: '400px' }}>
          <Story />
        </div>
      </RealtimeProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof RealtimeOverlay>;

export const Disconnected: Story = {
  args: {
    showProgressBar: true,
    showPluginInspector: true,
    showWarnings: true,
    showErrors: true,
  },
};

export const WithProgress: Story = {
  args: {
    showProgressBar: true,
    showPluginInspector: true,
  },
};

export const WithWarnings: Story = {
  args: {
    showProgressBar: true,
    showPluginInspector: true,
    showWarnings: true,
  },
};

export const Minimal: Story = {
  args: {
    showProgressBar: false,
    showPluginInspector: false,
    showWarnings: false,
    showErrors: false,
  },
};

