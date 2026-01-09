/**
 * Test utilities for rendering components with providers
 */

import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";

/**
 * Custom render function that wraps components with any necessary providers
 */
function customRender(
    ui: ReactElement,
    options?: Omit<RenderOptions, "wrapper">
) {
    function Wrapper({ children }: { children: React.ReactNode }) {
        return <>{children}</>;
    }

    return render(ui, { wrapper: Wrapper, ...options });
}

export * from "@testing-library/react";
export { customRender as render };
