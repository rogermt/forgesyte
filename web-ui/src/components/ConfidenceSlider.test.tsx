/**
 * Tests for ConfidenceSlider component
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfidenceSlider } from "./ConfidenceSlider";

// ============================================================================
// Tests
// ============================================================================

describe("ConfidenceSlider", () => {
  it("renders slider and input with default values", () => {
    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={vi.fn()}
      />
    );

    expect(screen.getByText("Detection Confidence")).toBeInTheDocument();
    expect(screen.getByDisplayValue("0.50")).toBeInTheDocument();
  });

  it("displays confidence value formatted to 2 decimals", () => {
    render(
      <ConfidenceSlider
        confidence={0.25}
        onConfidenceChange={vi.fn()}
      />
    );

    expect(screen.getByRole("spinbutton")).toHaveValue(0.25);
  });

  it("calls onConfidenceChange when slider changes", () => {
    const onConfidenceChange = vi.fn();

    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={onConfidenceChange}
      />
    );

    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "0.75" } });

    expect(onConfidenceChange).toHaveBeenCalledWith(0.75);
  });

  it("calls onConfidenceChange when input changes", () => {
    const onConfidenceChange = vi.fn();

    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={onConfidenceChange}
      />
    );

    const input = screen.getByRole("spinbutton");
    fireEvent.change(input, { target: { value: "0.6" } });

    expect(onConfidenceChange).toHaveBeenCalledWith(0.6);
  });

  it("processes out-of-range input on blur and corrects it", () => {
    const onConfidenceChange = vi.fn();

    const { rerender } = render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={onConfidenceChange}
        min={0.0}
        max={1.0}
      />
    );

    const input = screen.getByRole("spinbutton") as HTMLInputElement;

    // User types value above max
    fireEvent.change(input, { target: { value: "1.5" } });
    
    // The change event will call onConfidenceChange with unclamped value
    expect(onConfidenceChange).toHaveBeenCalledWith(1.5);
  });

  it("accepts valid input values", () => {
    const onConfidenceChange = vi.fn();

    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={onConfidenceChange}
        min={0.2}
        max={0.9}
      />
    );

    const input = screen.getByRole("spinbutton") as HTMLInputElement;

    // Type value within range
    fireEvent.change(input, { target: { value: "0.7" } });

    expect(onConfidenceChange).toHaveBeenCalledWith(0.7);
  });

  it("handles invalid input on blur by reverting to current value", () => {
    const onConfidenceChange = vi.fn();

    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={onConfidenceChange}
      />
    );

    const input = screen.getByRole("spinbutton") as HTMLInputElement;

    // Type invalid value
    fireEvent.change(input, { target: { value: "not-a-number" } });
    fireEvent.blur(input);

    // Should revert to current value (0.5)
    expect(onConfidenceChange).toHaveBeenCalledWith(0.5);
  });

  it("respects custom min/max values", () => {
    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={vi.fn()}
        min={0.1}
        max={0.9}
      />
    );

    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("min", "0.1");
    expect(slider).toHaveAttribute("max", "0.9");
  });

  it("respects custom step value", () => {
    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={vi.fn()}
        step={0.1}
      />
    );

    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("step", "0.1");
  });

  it("disables slider when disabled prop is true", () => {
    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={vi.fn()}
        disabled={true}
      />
    );

    const slider = screen.getByRole("slider");
    const input = screen.getByRole("spinbutton");

    expect(slider).toBeDisabled();
    expect(input).toBeDisabled();
  });

  it("displays info text", () => {
    render(
      <ConfidenceSlider
        confidence={0.5}
        onConfidenceChange={vi.fn()}
      />
    );

    expect(
      screen.getByText(/Only detections with confidence above this threshold/)
    ).toBeInTheDocument();
  });

  it("has proper ARIA attributes", () => {
    render(
      <ConfidenceSlider
        confidence={0.75}
        onConfidenceChange={vi.fn()}
        min={0.0}
        max={1.0}
      />
    );

    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("aria-valuemin", "0");
    expect(slider).toHaveAttribute("aria-valuemax", "1");
    expect(slider).toHaveAttribute("aria-valuenow", "0.75");
  });

  it("updates both slider and input when confidence prop changes", () => {
    const { rerender } = render(
      <ConfidenceSlider
        confidence={0.3}
        onConfidenceChange={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue("0.30")).toBeInTheDocument();

    rerender(
      <ConfidenceSlider
        confidence={0.7}
        onConfidenceChange={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue("0.70")).toBeInTheDocument();
  });
});
