# ForgeSyte Web UI

A modern, TypeScript-based React web interface for ForgeSyte plugin management and real-time media processing with WebSocket streaming.

## Features

- 🎥 **Real-time Camera Streaming** - WebSocket-based live video feed processing
- 🔌 **Plugin Management** - Select and switch between analysis plugins
- 📊 **Results Display** - Live results and job history tracking
- 🧪 **Comprehensive Tests** - Full test coverage with Vitest and React Testing Library
- 📱 **Responsive Design** - Dark-themed UI with ForgeSyte brand colors
- ⚡ **Modern Stack** - React 18, TypeScript, Vite, Vitest

## Getting Started

### Prerequisites

- Node.js 18+ (ESM support required)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run preview of production build
npm run preview
```

## Development

### Scripts

```bash
# Development server (hot reload)
npm run dev

# Type checking
npm run type-check

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage

# Linting
npm run lint
```

### Project Structure

```
src/
  ├── api/              # API client and types
  │   ├── client.ts     # ForgeSyteAPIClient implementation
  │   └── client.test.ts
  ├── components/       # React components
  │   ├── App.tsx       # Main application component
  │   ├── CameraPreview.tsx
  │   ├── JobList.tsx
  │   ├── PluginSelector.tsx
  │   ├── ResultsPanel.tsx
  │   └── *.test.tsx    # Component tests
  ├── hooks/            # Custom React hooks
  │   ├── useWebSocket.ts
  │   ├── useWebSocket.test.ts
  │   └── App.integration.test.tsx
  ├── test/            # Test utilities and setup
  │   ├── setup.ts     # Vitest configuration
  │   └── utils.tsx    # Custom render utilities
  ├── App.tsx
  ├── main.tsx
  └── index.css        # Global styles with ForgeSyte color palette

public/
  └── index.html
```

### Environment Variables

Create a `.env.local` file in the web-ui directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000/v1
VITE_API_KEY=your-api-key-here

# WebSocket Configuration
VITE_WS_URL=ws://localhost:8000/v1/stream
```

## Testing

### Test Framework

The project uses **Vitest** (ESM-native test runner optimized for Vite projects) with React Testing Library.

### Running Tests

```bash
# Watch mode (recommended for development)
npm run test

# Interactive UI
npm run test:ui

# Coverage report
npm run test:coverage
```

### Test Files

- `src/components/*.test.tsx` - Component tests
- `src/api/client.test.ts` - API client tests
- `src/hooks/useWebSocket.test.ts` - WebSocket hook tests
- `src/App.integration.test.tsx` - Integration tests

### Test-Driven Development (TDD)

This project follows TDD principles:

1. **Write tests first** - Tests define expected behavior
2. **See tests fail** - Confirm tests describe missing functionality
3. **Implement code** - Write minimal code to make tests pass
4. **Refactor** - Improve code while keeping tests green
5. **Commit** - Only commit when all tests pass

Example:
```bash
# 1. Create test file with failing tests
# 2. npm run test  # See tests fail
# 3. Implement functionality
# 4. npm run test  # Tests pass
# 5. npm run test:coverage  # Check coverage
# 6. git commit -m "feat: Add feature with full test coverage"
```

### Testing Best Practices

#### Component Tests

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import { MyComponent } from "./MyComponent";

describe("MyComponent", () => {
    it("should render content", async () => {
        render(<MyComponent />);
        expect(screen.getByText("Hello")).toBeInTheDocument();
    });

    it("should handle async operations", async () => {
        render(<MyComponent />);
        
        await waitFor(() => {
            expect(screen.getByText("Loaded")).toBeInTheDocument();
        });
    });
});
```

#### API Tests

```typescript
import { ForgeSyteAPIClient } from "./client";

describe("ForgeSyteAPIClient", () => {
    let client: ForgeSyteAPIClient;

    beforeEach(() => {
        global.fetch = vi.fn();
        client = new ForgeSyteAPIClient("http://localhost:3000/v1");
    });

    it("should fetch plugins", async () => {
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ plugins: [] }),
        });

        const plugins = await client.getPlugins();
        expect(plugins).toEqual([]);
    });
});
```

#### Hook Tests

```typescript
import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";

describe("useWebSocket", () => {
    it("should connect and update state", async () => {
        const { result } = renderHook(() =>
            useWebSocket({ url: "ws://localhost:8000/v1/stream" })
        );

        act(() => {
            mockWs.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.isConnected).toBe(true);
        });
    });
});
```

## Branding & Styling

### ForgeSyte Color Palette

The application uses a cohesive color system defined in `src/index.css`:

```css
--primary-charcoal: #111318   /* Dark background */
--secondary-steel: #2b3038    /* Panel background */
--accent-orange: #ff6a00      /* Forge Orange - primary action */
--accent-cyan: #00e5ff        /* Electric Cyan - hover effects */
--accent-green: #4caf50       /* Success states */
--accent-red: #dc3545         /* Error states */
```

All components use CSS variables for consistent theming.

## API Integration

### ForgeSyteAPIClient

The `ForgeSyteAPIClient` provides methods for:

- `getPlugins()` - List available plugins
- `listJobs(limit, skip, status)` - Fetch job history
- `getJob(jobId)` - Get specific job details
- `analyzeImage(file, plugin)` - Upload and analyze image
- `cancelJob(jobId)` - Cancel running job
- `pollJob(jobId, interval, timeout)` - Wait for job completion
- `getHealth()` - Check server status

### WebSocket Integration

The `useWebSocket` hook handles real-time streaming:

```typescript
const { isConnected, sendFrame, switchPlugin, latestResult } = useWebSocket({
    url: "/v1/stream",
    plugin: "motion_detector",
    onResult: (result) => console.log(result),
    onError: (error) => console.error(error),
});
```

## Build & Deployment

### Production Build

```bash
npm run build
npm run preview
```

### Build Output

- `dist/` - Optimized production build
- Source maps included for debugging
- Assets hashed for cache busting

## Performance

- **Vite** - Fast module resolution and HMR
- **React 18** - Concurrent features and automatic batching
- **Code splitting** - Automatic route-based splitting
- **Tree shaking** - Unused code eliminated in production

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines, test patterns, and submission process.

## License

Part of ForgeSyte project.
