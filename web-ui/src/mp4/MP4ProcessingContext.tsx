import React, { createContext, useContext } from "react";

export interface MP4ProcessingState {
  active: boolean;
  jobId: string | null;
  progress: number; // 0–100
  framesProcessed: number;
}

const MP4ProcessingContext = createContext<MP4ProcessingState | null>(null);

export function MP4ProcessingProvider({
  value,
  children,
}: {
  value: MP4ProcessingState;
  children: React.ReactNode;
}) {
  return (
    <MP4ProcessingContext.Provider value={value}>
      {children}
    </MP4ProcessingContext.Provider>
  );
}

export function useMP4ProcessingContext() {
  return useContext(MP4ProcessingContext);
}