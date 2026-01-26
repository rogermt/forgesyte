# Task 6.2 — Device Selector Implementation

## Plan
- [x] Fix device state type: `useState("cpu")` → `useState<"cpu" | "cuda">("cpu")`
- [x] Fix device option value: `<option value="gpu">` → `<option value="cuda">`
- [x] Add aria-label="Device" to select element
- [x] Add type assertion in onChange handler
- [x] Add device selector integration tests to VideoTracker.test.tsx

## Status: COMPLETED

