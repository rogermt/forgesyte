# 📋 v0.9.1 TDD Implementation Plan (ACTUAL CODEBASE)

**Created:** 2026-02-18  
**Status:** Ready for Implementation  
**Approach:** Test-Driven Development (TDD)  
**Based on:** Actual codebase review

---

## 🔍 Codebase Analysis Summary

### Backend Structure
- **Main API file:** `/server/app/api.py` (contains all REST endpoints)
- **Image analyze endpoint:** `POST /v1/analyze` (line 118)
- **Plugin service:** `/server/app/services/plugin_management_service.py`
- **Plugin registry:** `/server/app/plugins/loader/plugin_registry.py`
- **Test fixtures:** `/server/tests/conftest.py`

### Frontend Structure
- **API client:** `/web-ui/src/api/client.ts` (ForgeSyteAPIClient class)
- **Main app:** `/web-ui/src/App.tsx` (view modes: stream, upload, jobs, video-upload)
- **Video component:** `/web-ui/src/components/VideoUpload.tsx` (already implemented)
- **Test patterns:** Vitest with @testing-library/react

### Key Patterns Found

**Backend:**
- Uses `PluginManagementService` with `PluginRegistry` protocol
- Plugin execution via `plugin_service.run_plugin_tool(plugin_id, tool_name, args)`
- Returns typed responses using Pydantic models
- Uses `get_plugin_manifest()` to discover tools

**Frontend:**
- API client uses `ForgeSyteAPIClient` class
- Video upload already uses `apiClient.submitVideo()`
- Components use inline styles (no CSS modules found)
- Tests mock `apiClient` with `vi.mock()`

---

## 📊 Implementation Plan

### **Phase 1: Backend - Multi-Tool Image Analysis**

#### **B1: Write Failing Test for `/v1/image/analyze-multi`**

**File:** `/server/tests/api/test_multi_tool_image.py` (NEW)

**Test Scenarios:**
```python
import pytest
from fastapi.testclient import TestClient

def test_multi_tool_single_ocr(client):
    """Single tool (OCR) returns OCR result."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr"]}
        )
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "ocr" in data["tools"]

def test_multi_tool_ocr_yolo(client):
    """Multiple tools (OCR + YOLO) return both results."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr", "yolo-tracker"]}
        )
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "ocr" in data["tools"]
    assert "yolo-tracker" in data["tools"]

def test_multi_tool_unknown_tool(client):
    """Unknown tool returns error in result."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["unknown_tool"]}
        )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data["tools"]["unknown_tool"]
```

**Expected:** Tests fail (endpoint doesn't exist yet)

---

#### **B2: Implement `/v1/image/analyze-multi` Endpoint**

**File:** `/server/app/api.py` (ADD to existing file)

**Implementation:**
```python
@router.post("/image/analyze-multi")
async def analyze_image_multi(
    request: Request,
    file: UploadFile = File(...),
    tools: List[str] = Body(..., embed=True),
    auth: Dict[str, Any] = Depends(require_auth(["analyze"])),
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """
    Run multiple tools on a single image.
    
    Returns combined JSON:
    {
      "tools": {
        "ocr": { ... },
        "yolo-tracker": { ... }
      }
    }
    """
    import time
    start_time = time.time()
    
    logger.info(f"Multi-tool request: tools={tools}, file={file.filename}")
    
    # Read image bytes
    image_bytes = await file.read()
    
    # Validate image
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image data provided"
        )
    
    results: Dict[str, Any] = {"tools": {}}
    
    # Execute each tool
    for tool in tools:
        try:
            # Determine plugin_id from tool name
            # For now, assume tool name is in format: "plugin_id:tool_name" or just "tool_name"
            # OCR and YOLO are special cases
            if tool == "ocr":
                plugin_id = "ocr"
                tool_name = "analyze"
            elif tool == "yolo-tracker":
                plugin_id = "yolo-tracker"
                tool_name = "player_detection"
            else:
                # Try to parse as "plugin_id:tool_name"
                if ":" in tool:
                    plugin_id, tool_name = tool.split(":", 1)
                else:
                    plugin_id = tool
                    tool_name = "analyze"
            
            # Execute tool via plugin service
            result = plugin_service.run_plugin_tool(
                plugin_id=plugin_id,
                tool_name=tool_name,
                args={"image_bytes": image_bytes}
            )
            
            results["tools"][tool] = result
            
        except Exception as e:
            logger.error(f"Tool '{tool}' execution failed: {e}")
            results["tools"][tool] = {"error": str(e)}
    
    duration = time.time() - start_time
    logger.info(f"Multi-tool completed: tools={tools}, duration={duration:.2f}s")
    
    return results
```

**Expected:** Tests pass

---

#### **B3: Add Integration Test for Multi-Tool**

**File:** `/server/tests/integration/test_multi_tool_image.py` (NEW)

**Test Scenarios:**
```python
import pytest
from fastapi.testclient import TestClient

def test_multi_tool_image_analysis_full_flow(client):
    """Full integration test: upload → analyze → validate response."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr"]}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate structure
    assert "tools" in data
    assert "ocr" in data["tools"]
```

**Expected:** Integration test passes

---

### **Phase 2: Frontend - Multi-Tool Image Analysis**

#### **F1: Write Failing Test for `analyzeMulti` API Helper**

**File:** `/web-ui/src/api/client.test.ts` (ADD to existing file)

**Test Scenarios:**
```typescript
describe("analyzeMulti", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should return combined JSON for single tool", async () => {
        const mockResponse = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 }
            }
        };
        
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const file = new File([""], "test.jpg", { type: "image/jpeg" });
        const result = await apiClient.analyzeMulti(file, ["ocr"]);
        
        expect(result).toEqual(mockResponse);
    });

    it("should return combined JSON for multiple tools", async () => {
        const mockResponse = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
                "yolo-tracker": { detections: [] }
            }
        };
        
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const file = new File([""], "test.jpg", { type: "image/jpeg" });
        const result = await apiClient.analyzeMulti(file, ["ocr", "yolo-tracker"]);
        
        expect(result).toEqual(mockResponse);
    });
});
```

**Expected:** Tests fail (method doesn't exist)

---

#### **F2: Implement `analyzeMulti` API Helper**

**File:** `/web-ui/src/api/client.ts` (ADD to ForgeSyteAPIClient class)

**Implementation:**
```typescript
async analyzeMulti(
    file: File,
    tools: string[]
): Promise<{ tools: Record<string, unknown> }> {
    const formData = new FormData();
    formData.append("file", file);
    
    const headers: HeadersInit = {};
    
    if (this.apiKey) {
        headers["X-API-Key"] = this.apiKey;
    }

    const response = await fetch(`${this.baseUrl}/image/analyze-multi`, {
        method: "POST",
        headers,
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    return response.json() as Promise<{ tools: Record<string, unknown> }>;
}
```

**Expected:** Tests pass

---

#### **F3: Write Failing Test for `ImageMultiToolForm` Component**

**File:** `/web-ui/src/components/ImageMultiToolForm.test.tsx` (NEW)

**Test Scenarios:**
```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ImageMultiToolForm } from "./ImageMultiToolForm";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        analyzeMulti: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

describe("ImageMultiToolForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders without errors", () => {
        render(<ImageMultiToolForm />);
        expect(screen.getByText(/Multi-Tool Image Analyzer/i)).toBeInTheDocument();
    });

    it("handles file selection", () => {
        render(<ImageMultiToolForm />);
        
        const fileInput = screen.getByLabelText(/select image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        
        fireEvent.change(fileInput, { target: { files: [file] } });
        
        expect(fileInput.files).toHaveLength(1);
    });

    it("handles tool checkbox selection", () => {
        render(<ImageMultiToolForm />);
        
        const ocrCheckbox = screen.getByLabelText(/ocr/i);
        const yoloCheckbox = screen.getByLabelText(/yolo/i);
        
        fireEvent.click(ocrCheckbox);
        fireEvent.click(yoloCheckbox);
        
        expect(ocrCheckbox).toBeChecked();
        expect(yoloCheckbox).toBeChecked();
    });

    it("calls analyzeMulti on analyze button click", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue({
            tools: {
                ocr: { text: "sample text" }
            }
        });
        
        render(<ImageMultiToolForm />);
        
        // Select file
        const fileInput = screen.getByLabelText(/select image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });
        
        // Select tools
        fireEvent.click(screen.getByLabelText(/ocr/i));
        
        // Click analyze
        fireEvent.click(screen.getByText(/analyze/i));
        
        await waitFor(() => {
            expect(apiClient.analyzeMulti).toHaveBeenCalled();
        });
    });
});
```

**Expected:** Tests fail (component doesn't exist)

---

#### **F4: Create `ImageMultiToolForm` Component**

**File:** `/web-ui/src/components/ImageMultiToolForm.tsx` (NEW)

**Implementation:**
```typescript
import React, { useState } from "react";
import { apiClient } from "../api/client";
import { ImageMultiToolResults } from "./ImageMultiToolResults";

export const ImageMultiToolForm: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [tools, setTools] = useState<string[]>([]);
    const [results, setResults] = useState<{ tools: Record<string, unknown> } | null>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0] ?? null;
        setError(null);
        setResults(null);
        setFile(selectedFile);
    };

    const onToolChange = (tool: string, checked: boolean) => {
        if (checked) {
            setTools([...tools, tool]);
        } else {
            setTools(tools.filter((t) => t !== tool));
        }
    };

    const onAnalyze = async () => {
        if (!file || tools.length === 0) return;
        
        setError(null);
        setAnalyzing(true);

        try {
            const result = await apiClient.analyzeMulti(file, tools);
            setResults(result);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Analysis failed.");
        } finally {
            setAnalyzing(false);
        }
    };

    return (
        <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
            <h2>Multi-Tool Image Analyzer</h2>

            <label htmlFor="image-upload">Select image:</label>
            <input
                id="image-upload"
                type="file"
                accept="image/*"
                onChange={onFileChange}
            />

            <div style={{ marginTop: "20px" }}>
                <label style={{ marginRight: "20px" }}>
                    <input
                        type="checkbox"
                        checked={tools.includes("ocr")}
                        onChange={(e) => onToolChange("ocr", e.target.checked)}
                    />
                    OCR
                </label>

                <label>
                    <input
                        type="checkbox"
                        checked={tools.includes("yolo-tracker")}
                        onChange={(e) => onToolChange("yolo-tracker", e.target.checked)}
                    />
                    YOLO
                </label>
            </div>

            {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}

            {analyzing && <div style={{ marginTop: "10px" }}>Analyzing…</div>}

            <button
                onClick={onAnalyze}
                disabled={!file || tools.length === 0 || analyzing}
                style={{
                    marginTop: "10px",
                    padding: "10px 20px",
                    cursor: file && tools.length > 0 && !analyzing ? "pointer" : "not-allowed",
                }}
            >
                Analyze
            </button>

            {results && <ImageMultiToolResults results={results} />}
        </div>
    );
};
```

**Expected:** Tests pass

---

#### **F5: Write Failing Test for `ImageMultiToolResults` Component**

**File:** `/web-ui/src/components/ImageMultiToolResults.test.tsx` (NEW)

**Test Scenarios:**
```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageMultiToolResults } from "./ImageMultiToolResults";

describe("ImageMultiToolResults", () => {
    it("renders component", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 }
            }
        };
        
        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/results/i)).toBeInTheDocument();
    });

    it("displays OCR results", () => {
        const mockResults = {
            tools: {
                ocr: { text: "sample text", confidence: 0.95 }
            }
        };
        
        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/ocr/i)).toBeInTheDocument();
        expect(screen.getByText("sample text")).toBeInTheDocument();
    });

    it("displays YOLO results", () => {
        const mockResults = {
            tools: {
                "yolo-tracker": {
                    detections: [
                        { label: "person", confidence: 0.95, bbox: [10, 10, 100, 100] }
                    ]
                }
            }
        };
        
        render(<ImageMultiToolResults results={mockResults} />);
        expect(screen.getByText(/yolo/i)).toBeInTheDocument();
        expect(screen.getByText("person")).toBeInTheDocument();
    });
});
```

**Expected:** Tests fail (component doesn't exist)

---

#### **F6: Create `ImageMultiToolResults` Component**

**File:** `/web-ui/src/components/ImageMultiToolResults.tsx` (NEW)

**Implementation:**
```typescript
import React from "react";

interface Props {
    results: { tools: Record<string, unknown> };
}

export const ImageMultiToolResults: React.FC<Props> = ({ results }) => {
    return (
        <div style={{ marginTop: "20px" }}>
            <h3>Results</h3>
            
            {Object.entries(results.tools).map(([toolName, toolResult]) => (
                <div key={toolName} style={{ marginBottom: "20px" }}>
                    <h4>{toolName}</h4>
                    
                    {toolName === "ocr" && typeof toolResult === "object" && toolResult && (
                        <div>
                            <p><strong>Text:</strong> {(toolResult as any).text}</p>
                            <p><strong>Confidence:</strong> {(toolResult as any).confidence?.toFixed(2)}</p>
                        </div>
                    )}
                    
                    {toolName === "yolo-tracker" && typeof toolResult === "object" && toolResult && (
                        <div>
                            <p><strong>Detections:</strong></p>
                            <pre style={{ backgroundColor: "#f5f5f5", padding: "10px" }}>
                                {JSON.stringify((toolResult as any).detections, null, 2)}
                            </pre>
                        </div>
                    )}
                    
                    <pre style={{ backgroundColor: "#f5f5f5", padding: "10px" }}>
                        {JSON.stringify(toolResult, null, 2)}
                    </pre>
                </div>
            ))}
        </div>
    );
};
```

**Expected:** Tests pass

---

#### **F7: Wire Multi-Tool UI to Main Page**

**File:** `/web-ui/src/App.tsx` (MODIFY existing file)

**Implementation:**
```typescript
// Add import
import { ImageMultiToolForm } from "./components/ImageMultiToolForm";

// Add to ViewMode type
type ViewMode = "stream" | "upload" | "jobs" | "video-upload" | "multi-tool-image";

// Add to nav buttons
{(["stream", "upload", "jobs", "video-upload", "multi-tool-image"] as ViewMode[]).map((mode) => (
    <button
        key={mode}
        onClick={() => setViewMode(mode)}
        // ... existing button styles
    >
        {mode === "multi-tool-image" ? "Multi-Tool" : mode.charAt(0).toUpperCase() + mode.slice(1)}
    </button>
))}

// Add to content section
{viewMode === "multi-tool-image" && (
    <div style={{ ...styles.panel, flex: 1 }}>
        <ImageMultiToolForm />
    </div>
)}
```

**Expected:** UI works end-to-end

---

#### **F8: Add Integration Test for Multi-Tool UI**

**File:** `/web-ui/src/integration/test_multi_tool_ui.test.tsx` (NEW)

**Test Scenarios:**
```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";

// Mock the API client
vi.mock("../api/client", () => ({
    apiClient: {
        analyzeMulti: vi.fn(),
        getPlugins: vi.fn(),
        getPluginManifest: vi.fn(),
    },
}));

import { apiClient } from "../api/client";

describe("Multi-Tool UI Integration", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        
        // Mock plugins
        (apiClient.getPlugins as ReturnType<typeof vi.fn>).mockResolvedValue([
            { name: "ocr", description: "OCR", version: "1.0.0" },
            { name: "yolo-tracker", description: "YOLO", version: "1.0.0" }
        ]);
    });

    it("should complete full multi-tool flow", async () => {
        (apiClient.analyzeMulti as ReturnType<typeof vi.fn>).mockResolvedValue({
            tools: {
                ocr: { text: "sample text", confidence: 0.95 },
                "yolo-tracker": { detections: [] }
            }
        });
        
        render(<App />);
        
        // Switch to multi-tool mode
        fireEvent.click(screen.getByText(/multi-tool/i));
        
        // Select file
        const fileInput = screen.getByLabelText(/select image/i) as HTMLInputElement;
        const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
        fireEvent.change(fileInput, { target: { files: [file] } });
        
        // Select tools
        fireEvent.click(screen.getByLabelText(/ocr/i));
        fireEvent.click(screen.getByLabelText(/yolo/i));
        
        // Click analyze
        fireEvent.click(screen.getByText(/analyze/i));
        
        // Verify API was called
        await waitFor(() => {
            expect(apiClient.analyzeMulti).toHaveBeenCalled();
        });
    });
});
```

**Expected:** Integration test passes

---

### **Phase 3: Final Polish**

#### **F9: Update JobResults to Display YOLO Detections**

**File:** `/web-ui/src/components/JobStatus.tsx` or `/web-ui/src/components/ResultsPanel.tsx` (MODIFY)

**Implementation:**
```typescript
// Add YOLO detection display to existing results panel
{result && typeof result === "object" && "detections" in result && (
    <div style={{ marginTop: "20px" }}>
        <h4>YOLO Detections</h4>
        {(result as any).detections.map((detection: any, idx: number) => (
            <div key={idx} style={{ marginBottom: "10px" }}>
                <p><strong>Label:</strong> {detection.label}</p>
                <p><strong>Confidence:</strong> {detection.confidence?.toFixed(2)}</p>
                <p><strong>BBox:</strong> {JSON.stringify(detection.bbox)}</p>
            </div>
        ))}
    </div>
)}
```

**Expected:** YOLO results visible in UI

---

#### **D1: Update Release Notes**

**File:** `/docs/releases/v0.9.1/RELEASE_NOTES.md` (NEW)

**Implementation:**
```markdown
# v0.9.1 Release Notes

## New Features

### Video Analysis UI
- Video upload form with file selection
- HTML5 video preview player
- Upload progress indicator
- Real-time job status polling
- Results display (OCR + YOLO)

### Multi-Tool Image Analysis
- New endpoint: `/v1/image/analyze-multi`
- Run multiple tools (OCR + YOLO) in one request
- Combined JSON response format
- UI for selecting tools and viewing combined results

## Bug Fixes
- Fixed YOLO unpickling error (beta)

## Breaking Changes
- None

## Known Issues
- YOLO support is in beta (GPU required)
```

**Expected:** Release notes complete

---

### **Phase 4: Verification (MANDATORY Before Commit)**

#### **VERIFY-1: Run All CI Workflows Locally**

```bash
# Vocabulary validation
python scripts/validate_vocabulary.py

# Video batch validation
bash scripts/smoke_test_video_batch.sh

# Governance CI
python scripts/scan_execution_violations.py

# Execution CI
cd server && uv run pytest tests/execution -v

# Main CI
cd server && uv run pytest tests/ -v
cd web-ui && npm run lint && npm run type-check && npm run test -- --run
```

**Expected:** All workflows pass

---

#### **VERIFY-2: Run Full Test Suite**

```bash
cd server && uv run pytest tests/ -v
cd web-ui && npm run test -- --run
```

**Expected:** All tests pass

---

#### **VERIFY-3: Run Type-Check on Web-UI**

```bash
cd web-ui && npm run type-check
```

**Expected:** No type errors

---

#### **VERIFY-4: Run Execution Governance Scanner**

```bash
python scripts/scan_execution_violations.py
```

**Expected:** No violations

---

## 📝 Commit Strategy

Each phase should be committed separately with clear commit messages:

```
feat(backend): Add /v1/image/analyze-multi endpoint
test(backend): Add integration test for multi-tool image analysis
feat(frontend): Add analyzeMulti API helper
feat(frontend): Create ImageMultiToolForm component
feat(frontend): Create ImageMultiToolResults component
feat(frontend): Wire multi-tool UI to main page
test(frontend): Add integration test for multi-tool UI
fix(frontend): Update JobResults to display YOLO detections
docs(release): Update v0.9.1 release notes
```

---

## ✅ Success Criteria

- ✅ All tests pass (backend + frontend)
- ✅ All CI workflows pass locally
- ✅ No type errors (TypeScript)
- ✅ No linting errors
- ✅ No execution governance violations
- ✅ Video upload → status → results flow works
- ✅ Multi-tool image analysis flow works
- ✅ YOLO detections display correctly

---

## 📚 References

- `/docs/releases/v0.9.1/DOCUMENTS.md` - Complete v0.9.1 documentation
- `/docs/releases/v0.9.1/VIDEO_TESTS_STATUS.md` - Video tests status
- `/AGENTS.md` - Agent commands and conventions
- `/server/app/api.py` - Main API endpoints
- `/web-ui/src/api/client.ts` - API client patterns
- `/web-ui/src/components/VideoUpload.tsx` - Component patterns

---

**Last Updated:** 2026-02-18  
**Next Step:** Begin Phase 1, B1 - Write failing test for `/v1/image/analyze-multi`