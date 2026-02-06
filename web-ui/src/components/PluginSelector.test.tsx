/**
 * Tests for PluginSelector component
 *
 * @see https://testing-library.com/docs/react-testing-library/api
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PluginSelector } from "./PluginSelector";
import * as client from "../api/client";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("../api/client", () => ({
  apiClient: {
    getPlugins: vi.fn(),
  },
}));

const mockGetPlugins = vi.mocked(client.apiClient.getPlugins);

// ============================================================================
// Test Data
// ============================================================================

const mockPlugins: client.Plugin[] = [
  {
    name: "motion_detector",
    version: "1.0.0",
    description: "Detects motion in video frames",
    inputs: ["image"],
    outputs: ["motion_detected", "motion_percentage"],
  },
  {
    name: "object_detection",
    version: "2.1.0",
    description: "Detects objects in images using YOLO",
    inputs: ["image"],
    outputs: ["objects", "bounding_boxes"],
  },
  {
    name: "ocr",
    version: "1.5.0",
    description: "Optical character recognition",
    inputs: ["image"],
    outputs: ["text", "confidence"],
  },
  {
    name: "face_detection",
    version: "1.2.0",
    description: "Detects faces in images",
    inputs: ["image"],
    outputs: ["faces", "landmarks"],
  },
];

// ============================================================================
// Tests
// ============================================================================

describe("PluginSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Loading State
  // ==========================================================================

  describe("loading state", () => {
    it("should display loading message while fetching plugins", () => {
      mockGetPlugins.mockImplementation(() => new Promise(() => {}));

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      expect(screen.getByText("Loading plugins...")).toBeInTheDocument();
    });

    it("should not show select while loading", () => {
      mockGetPlugins.mockImplementation(() => new Promise(() => {}));

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Error State
  // ==========================================================================

  describe("error state", () => {
    it("should display error message when API fails", async () => {
      mockGetPlugins.mockRejectedValue(new Error("Network error"));

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });

    it("should display generic error for non-Error exceptions", async () => {
      mockGetPlugins.mockRejectedValue("String error");

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load plugins/)).toBeInTheDocument();
      });
    });

    it("should show retry button on error", async () => {
      mockGetPlugins.mockRejectedValue(new Error("API error"));

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Empty State
  // ==========================================================================

  describe("empty state", () => {
    it("should display message when no plugins available", async () => {
      mockGetPlugins.mockResolvedValue([]);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      // Wait for loading to complete AND check for empty state
      await waitFor(() => {
        expect(screen.getByText("No plugins available")).toBeInTheDocument();
      }, { timeout: 10000 });
    });
  });

  // ==========================================================================
  // Plugin Selection
  // ==========================================================================

  describe("plugin selection", () => {
    it("should display all plugins in dropdown", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      // Wait for loading to complete first
      await waitFor(() => {
        expect(screen.queryByText("Loading plugins...")).not.toBeInTheDocument();
      });

      // Then verify the select and all options are present
      await waitFor(() => {
        const select = screen.getByRole("combobox");
        expect(select).toBeInTheDocument();

        mockPlugins.forEach((plugin) => {
          expect(
            screen.getByRole("option", { name: new RegExp(plugin.name) })
          ).toBeInTheDocument();
        });
      });
    });

    it("should show the selected plugin from props", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="object_detection"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        const select = screen.getByRole("combobox") as HTMLSelectElement;
        expect(select.value).toBe("object_detection");
      });
    });

    it("should call onPluginChange when selection changes", async () => {
      const user = userEvent.setup();
      const mockOnChange = vi.fn();
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox");
      await user.selectOptions(select, "ocr");

      expect(mockOnChange).toHaveBeenCalledWith("ocr");
    });

    it("should display plugin version in option text", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("motion_detector (v1.0.0)")).toBeInTheDocument();
        expect(screen.getByText("ocr (v1.5.0)")).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Plugin Info Display
  // ==========================================================================

  describe("plugin info display", () => {
    it("should display selected plugin description", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText("Detects motion in video frames")
        ).toBeInTheDocument();
      });
    });

    // Note: Inputs/outputs are now displayed from manifest (loaded by App),
    // not from the plugins list (which only has health data).
    // PluginSelector only shows basic info: name, version, description.

    it("should update info when selection changes", async () => {
      const user = userEvent.setup();
      const mockOnChange = vi.fn();
      mockGetPlugins.mockResolvedValue(mockPlugins);

      const { rerender } = render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText("Detects motion in video frames")
        ).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox");
      await user.selectOptions(select, "ocr");

      // Re-render with new selectedPlugin (simulates parent updating prop)
      rerender(
        <PluginSelector
          selectedPlugin="ocr"
          onPluginChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText("Optical character recognition")
        ).toBeInTheDocument();
      });
    });

    it("should not show info when compact prop is true", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
          compact
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      });

      expect(screen.queryByText("Detects motion in video frames")).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Disabled State
  // ==========================================================================

  describe("disabled state", () => {
    it("should disable select when disabled prop is true", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
          disabled
        />
      );

      await waitFor(() => {
        const select = screen.getByRole("combobox");
        expect(select).toBeDisabled();
      });
    });

    it("should show message about stopping streaming when disabled", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
          disabled
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText("Stop streaming to change plugin")
        ).toBeInTheDocument();
      });
    });

    it("should apply disabled styling", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
          disabled
        />
      );

      await waitFor(() => {
        const select = screen.getByRole("combobox");
        expect(select).toHaveStyle({ cursor: "not-allowed" });
      });
    });

    it("should not call onPluginChange when disabled and user tries to change", async () => {
      const user = userEvent.setup();
      const mockOnChange = vi.fn();
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={mockOnChange}
          disabled
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox");

      // Try to change selection (should not work when disabled)
      await user.selectOptions(select, "ocr").catch(() => {
        // Expected to fail since select is disabled
      });

      // onPluginChange should not have been called
      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Accessibility
  // ==========================================================================

  describe("accessibility", () => {
    it("should have accessible label for select", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        const select = screen.getByRole("combobox");
        expect(select).toHaveAccessibleName(/analysis plugin/i);
      });
    });

    it("should have aria-describedby pointing to plugin info", async () => {
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        const select = screen.getByRole("combobox");
        expect(select).toHaveAttribute("aria-describedby");
      });
    });
  });

  // ==========================================================================
  // Edge Cases
  // ==========================================================================

  describe("edge cases", () => {
    it("should handle plugins with empty inputs/outputs", async () => {
      const pluginsWithEmpty = [
        {
          name: "simple_plugin",
          version: "1.0.0",
          description: "A simple plugin",
          inputs: [],
          outputs: [],
        },
      ];
      mockGetPlugins.mockResolvedValue(pluginsWithEmpty);

      render(
        <PluginSelector
          selectedPlugin="simple_plugin"
          onPluginChange={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("A simple plugin")).toBeInTheDocument();
        // Should not show Inputs/Outputs sections if empty
        expect(screen.queryByText("Inputs:")).not.toBeInTheDocument();
        expect(screen.queryByText("Outputs:")).not.toBeInTheDocument();
      });
    });

    it("should handle rapid selection changes", async () => {
      const user = userEvent.setup();
      const mockOnChange = vi.fn();
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin="motion_detector"
          onPluginChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox");

      // Rapid changes
      await user.selectOptions(select, "ocr");
      await user.selectOptions(select, "face_detection");
      await user.selectOptions(select, "object_detection");

      expect(mockOnChange).toHaveBeenCalledTimes(3);
      expect(mockOnChange).toHaveBeenLastCalledWith("object_detection");
    });
  });

  describe("Auto-selection when no plugin selected", () => {
    it("should auto-select first plugin when selectedPlugin is empty string", async () => {
      const mockOnChange = vi.fn();
      mockGetPlugins.mockResolvedValue(mockPlugins);

      render(
        <PluginSelector
          selectedPlugin=""
          onPluginChange={mockOnChange}
          disabled={false}
        />
      );

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith("motion_detector");
      });
    });
  });
});
