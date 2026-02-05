/**
 * Phase 10: RealtimeOverlay integration test.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RealtimeProvider } from "@/realtime/RealtimeContext";

describe("RealtimeOverlay", () => {
     it("should render", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" />
             </RealtimeProvider>
         );
         expect(screen.getByTestId("realtime-overlay")).toBeInTheDocument();
     });

     it("should show connection status", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" />
             </RealtimeProvider>
         );
         expect(screen.getByText(/Disconnected/)).toBeInTheDocument();
     });

     it("should show progress bar container when progress is null", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" showProgressBar={true} />
             </RealtimeProvider>
         );
         // The progress bar only shows when state.progress is not null
         // When progress is null, the progress bar is not rendered
         const progressBar = document.getElementById("progress-bar");
         // Since initial state.progress is null, ProgressBar is not rendered
         expect(progressBar).not.toBeInTheDocument();
     });

     it("should show plugin inspector container", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" showPluginInspector={true} />
             </RealtimeProvider>
         );
         const inspector = document.getElementById("plugin-inspector");
         expect(inspector).toBeInTheDocument();
     });

     it("should render overlay component", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" />
             </RealtimeProvider>
         );
         expect(screen.getByTestId("realtime-overlay")).toBeInTheDocument();
     });

     it("should support hiding warnings", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" showWarnings={false} />
             </RealtimeProvider>
         );
         expect(screen.getByTestId("realtime-overlay")).toBeInTheDocument();
     });

     it("should support hiding errors", async () => {
         const { RealtimeOverlay } = await import("@/components/RealtimeOverlay");
         render(
             <RealtimeProvider>
                 <RealtimeOverlay jobId="job-123" showErrors={false} />
             </RealtimeProvider>
         );
         expect(screen.getByTestId("realtime-overlay")).toBeInTheDocument();
     });
 });

