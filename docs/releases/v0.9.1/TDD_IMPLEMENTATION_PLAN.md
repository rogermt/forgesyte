# 📋 v0.9.1 TDD Implementation Plan

**Created:** 2026-02-18  
**Status:** Ready for Implementation  
**Approach:** Test-Driven Development (TDD)

---

## 📌 Executive Summary

This document outlines the complete TDD implementation plan for v0.9.1, which delivers:

1. **Video Analysis UI** - Complete the UI for v0.9.0 video backend
2. **Multi-Tool Image Analysis** - New `/v1/image/analyze-multi` endpoint + UI

**Key Principle:** Complete the UI. Add multi-tool. Zero backend rewrites.

---

## 🎯 Current Status

### ✅ Completed
- **B1-B3:** Video backend work (pipeline_id optional, ocr_only pipeline, API docs)
- **F1-F6:** Frontend video components (VideoUpload, JobStatus, JobResults, integration test)
- **B4:** YOLO unpickling error fix (beta)

### ⏳ Pending
- **F7:** Update JobResults to display YOLO detections (beta)
- **D1:** Update release notes
- **M1-M8:** Multi-tool image analysis (entire feature)
- **VERIFY:** All CI workflows and verification steps

---

## 📊 Implementation Phases

### **Phase 1: Multi-Tool Image Analysis (Backend)**

#### **B1: Write Failing Test for `/v1/image/analyze-multi`**

**File:** `/server/tests/api/test_multi_tool_image.py`

**Test Scenarios:**
```python
def test_multi_tool_single_ocr():
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
    assert "text" in data["tools"]["ocr"]

def test_multi_tool_ocr_yolo():
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

def test_multi_tool_unknown_tool():
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

def test_multi_tool_response_structure():
    """Response structure matches combined JSON contract."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr"]}
        )
    data = response.json()
    # Validate structure: {"tools": {"ocr": {...}}}
    assert isinstance(data, dict)
    assert "tools" in data
    assert isinstance(data["tools"], dict)
```

**Expected:** Tests fail (endpoint doesn't exist yet)

---

#### **B2: Implement `/v1/image/analyze-multi` Endpoint**

**File:** `/server/api/routes/image.py`

**Implementation:**
```python
from fastapi import APIRouter, UploadFile, File, Body
from typing import List, Dict, Any
from server.core.plugin_management_service import plugin_manager
import logging

logger = logging.getLogger(__name__)

async def run_tool_on_image(tool_name: str, image_bytes: bytes) -> Any:
    """Run a single tool on image bytes."""
    plugin = plugin_manager.get_plugin(tool_name)
    if not plugin:
        raise ValueError(f"Unknown tool: {tool_name}")
    return await plugin.run(image_bytes=image_bytes)

@router.post("/v1/image/analyze-multi")
async def analyze_image_multi(
    file: UploadFile = File(...),
    tools: List[str] = Body(..., embed=True),
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
    image_bytes = await file.read()
    results: Dict[str, Any] = {"tools": {}}
    
    for tool in tools:
        try:
            result = await run_tool_on_image(tool, image_bytes)
            results["tools"][tool] = result
        except Exception as e:
            results["tools"][tool] = {"error": str(e)}
    
    return results
```

**Expected:** Tests pass

---

#### **B3: Add Logging to Multi-Tool Endpoint**

**File:** `/server/api/routes/image.py`

**Implementation:**
```python
import time

@router.post("/v1/image/analyze-multi")
async def analyze_image_multi(...):
    start_time = time.time()
    logger.info(f"Multi-tool request: tools={tools}, file={file.filename}")
    
    # ... existing code ...
    
    duration = time.time() - start_time
    logger.info(f"Multi-tool completed: tools={tools}, duration={duration:.2f}s")
    return results
```

**Expected:** Logs visible in server output

---

#### **B4: Add Integration Test for Multi-Tool**

**File:** `/server/tests/integration/test_multi_tool_image.py`

**Test Scenarios:**
```python
import pytest
from fastapi.testclient import TestClient

def test_multi_tool_image_analysis_full_flow():
    """Full integration test: upload → analyze → validate response."""
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/v1/image/analyze-multi",
            files={"file": f},
            json={"tools": ["ocr", "yolo-tracker"]}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate structure
    assert "tools" in data
    assert "ocr" in data["tools"]
    assert "yolo-tracker" in data["tools"]
    
    # Validate OCR result
    assert "text" in data["tools"]["ocr"]
    
    # Validate YOLO result
    assert "detections" in data["tools"]["yolo-tracker"]
    assert isinstance(data["tools"]["yolo-tracker"]["detections"], list)
```

**Expected:** Integration test passes

---

### **Phase 2: Multi-Tool Image Analysis (Frontend)**

#### **F1: Write Failing Test for `analyzeMulti` API Helper**

**File:** `/web-ui/src/services/api.test.ts`

**Test Scenarios:**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { analyzeMulti } from './api';

// Mock fetch
global.fetch = vi.fn();

describe('analyzeMulti', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return combined JSON for single tool', async () => {
    const mockResponse = {
      tools: {
        ocr: { text: 'sample text', confidence: 0.95 }
      }
    };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    const result = await analyzeMulti(file, ['ocr']);
    
    expect(result).toEqual(mockResponse);
  });

  it('should return combined JSON for multiple tools', async () => {
    const mockResponse = {
      tools: {
        ocr: { text: 'sample text', confidence: 0.95 },
        'yolo-tracker': { detections: [] }
      }
    };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    const result = await analyzeMulti(file, ['ocr', 'yolo-tracker']);
    
    expect(result).toEqual(mockResponse);
  });
});
```

**Expected:** Tests fail (function doesn't exist)

---

#### **F2: Implement `analyzeMulti` API Helper**

**File:** `/web-ui/src/services/api.ts`

**Implementation:**
```typescript
export async function analyzeMulti(
  file: File,
  tools: string[]
): Promise<{ tools: Record<string, any> }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tools', JSON.stringify(tools));

  const res = await fetch('/v1/image/analyze-multi', {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    throw new Error(`Multi-tool analysis failed: ${res.status}`);
  }

  return res.json();
}
```

**Expected:** Tests pass

---

#### **F3: Write Failing Test for `ImageMultiToolForm` Component**

**File:** `/web-ui/src/components/ImageMultiToolForm.test.tsx`

**Test Scenarios:**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ImageMultiToolForm } from './ImageMultiToolForm';

// Mock API
vi.mock('../services/api', () => ({
  analyzeMulti: vi.fn()
}));

describe('ImageMultiToolForm', () => {
  it('should render component', () => {
    render(<ImageMultiToolForm />);
    expect(screen.getByText('Multi-Tool Image Analyzer')).toBeInTheDocument();
  });

  it('should handle file selection', () => {
    render(<ImageMultiToolForm />);
    const fileInput = screen.getByLabelText(/select image/i);
    
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Verify file was selected (check preview or state)
  });

  it('should handle tool checkbox selection', () => {
    render(<ImageMultiToolForm />);
    const ocrCheckbox = screen.getByLabelText(/ocr/i);
    const yoloCheckbox = screen.getByLabelText(/yolo/i);
    
    fireEvent.click(ocrCheckbox);
    fireEvent.click(yoloCheckbox);
    
    expect(ocrCheckbox).toBeChecked();
    expect(yoloCheckbox).toBeChecked();
  });

  it('should call analyzeMulti on analyze button click', async () => {
    const { analyzeMulti } = await import('../services/api');
    
    render(<ImageMultiToolForm />);
    
    // Select file
    const fileInput = screen.getByLabelText(/select image/i);
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Select tools
    fireEvent.click(screen.getByLabelText(/ocr/i));
    
    // Click analyze
    fireEvent.click(screen.getByText(/analyze/i));
    
    await waitFor(() => {
      expect(analyzeMulti).toHaveBeenCalled();
    });
  });
});
```

**Expected:** Tests fail (component doesn't exist)

---

#### **F4: Create `ImageMultiToolForm` Component**

**Files:** 
- `/web-ui/src/components/ImageMultiToolForm.tsx`
- `/web-ui/src/components/ImageMultiToolForm.module.css`

**Implementation (ImageMultiToolForm.tsx):**
```typescript
import React, { useState } from 'react';
import { analyzeMulti } from '../services/api';
import { ImageMultiToolResults } from './ImageMultiToolResults';
import styles from './ImageMultiToolForm.module.css';

export const ImageMultiToolForm: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [tools, setTools] = useState<string[]>([]);
  const [results, setResults] = useState<any | null>(null);
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
      setTools(tools.filter(t => t !== tool));
    }
  };

  const onAnalyze = async () => {
    if (!file || tools.length === 0) return;
    
    setError(null);
    setAnalyzing(true);

    try {
      const result = await analyzeMulti(file, tools);
      setResults(result);
    } catch (e: any) {
      setError(e.message ?? 'Analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className={styles.container}>
      <h2>Multi-Tool Image Analyzer</h2>

      <input
        type="file"
        accept="image/*"
        onChange={onFileChange}
        className={styles.fileInput}
      />

      <div className={styles.toolSelector}>
        <label>
          <input
            type="checkbox"
            checked={tools.includes('ocr')}
            onChange={(e) => onToolChange('ocr', e.target.checked)}
          />
          OCR
        </label>

        <label>
          <input
            type="checkbox"
            checked={tools.includes('yolo-tracker')}
            onChange={(e) => onToolChange('yolo-tracker', e.target.checked)}
          />
          YOLO
        </label>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {analyzing && <div className={styles.progress}>Analyzing…</div>}

      <button
        onClick={onAnalyze}
        disabled={!file || tools.length === 0 || analyzing}
        className={styles.analyzeButton}
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

**File:** `/web-ui/src/components/ImageMultiToolResults.test.tsx`

**Test Scenarios:**
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ImageMultiToolResults } from './ImageMultiToolResults';

describe('ImageMultiToolResults', () => {
  it('should render component', () => {
    const mockResults = {
      tools: {
        ocr: { text: 'sample text', confidence: 0.95 }
      }
    };
    
    render(<ImageMultiToolResults results={mockResults} />);
    expect(screen.getByText(/results/i)).toBeInTheDocument();
  });

  it('should display OCR results', () => {
    const mockResults = {
      tools: {
        ocr: { text: 'sample text', confidence: 0.95 }
      }
    };
    
    render(<ImageMultiToolResults results={mockResults} />);
    expect(screen.getByText(/ocr/i)).toBeInTheDocument();
    expect(screen.getByText('sample text')).toBeInTheDocument();
  });

  it('should display YOLO results', () => {
    const mockResults = {
      tools: {
        'yolo-tracker': {
          detections: [
            { label: 'person', confidence: 0.95, bbox: [10, 10, 100, 100] }
          ]
        }
      }
    };
    
    render(<ImageMultiToolResults results={mockResults} />);
    expect(screen.getByText(/yolo/i)).toBeInTheDocument();
    expect(screen.getByText('person')).toBeInTheDocument();
  });

  it('should pretty-print JSON', () => {
    const mockResults = {
      tools: {
        ocr: { text: 'sample text', confidence: 0.95 }
      }
    };
    
    render(<ImageMultiToolResults results={mockResults} />);
    // Check that JSON is displayed in formatted way
  });
});
```

**Expected:** Tests fail (component doesn't exist)

---

#### **F6: Create `ImageMultiToolResults` Component**

**Files:**
- `/web-ui/src/components/ImageMultiToolResults.tsx`
- `/web-ui/src/components/ImageMultiToolResults.module.css`

**Implementation (ImageMultiToolResults.tsx):**
```typescript
import React from 'react';
import styles from './ImageMultiToolResults.module.css';

interface Props {
  results: { tools: Record<string, any> };
}

export const ImageMultiToolResults: React.FC<Props> = ({ results }) => {
  return (
    <div className={styles.container}>
      <h3>Results</h3>
      
      {Object.entries(results.tools).map(([toolName, toolResult]) => (
        <div key={toolName} className={styles.toolSection}>
          <h4>{toolName}</h4>
          
          {toolName === 'ocr' && (
            <div className={styles.ocrResult}>
              <p><strong>Text:</strong> {toolResult.text}</p>
              <p><strong>Confidence:</strong> {toolResult.confidence?.toFixed(2)}</p>
            </div>
          )}
          
          {toolName === 'yolo-tracker' && (
            <div className={styles.yoloResult}>
              <p><strong>Detections:</strong></p>
              <pre className={styles.json}>
                {JSON.stringify(toolResult.detections, null, 2)}
              </pre>
            </div>
          )}
          
          <pre className={styles.json}>
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

**File:** `/web-ui/src/App.tsx`

**Implementation:**
```typescript
import { VideoUpload } from './components/VideoUpload';
import { ImageMultiToolForm } from './components/ImageMultiToolForm';

function App() {
  const [mode, setMode] = useState<'video' | 'image-multi'>('video');

  return (
    <div className="app">
      <nav>
        <button onClick={() => setMode('video')}>Video Analyzer</button>
        <button onClick={() => setMode('image-multi')}>Multi-Tool Image</button>
      </nav>
      
      {mode === 'video' && <VideoUpload />}
      {mode === 'image-multi' && <ImageMultiToolForm />}
    </div>
  );
}
```

**Expected:** UI works end-to-end

---

#### **F8: Add Integration Test for Multi-Tool UI**

**File:** `/web-ui/src/integration/test_multi_tool_ui.test.tsx`

**Test Scenarios:**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

// Mock API
vi.mock('../services/api', () => ({
  analyzeMulti: vi.fn(),
  submitVideo: vi.fn(),
  getVideoStatus: vi.fn(),
  getVideoResults: vi.fn()
}));

describe('Multi-Tool UI Integration', () => {
  it('should complete full multi-tool flow', async () => {
    const { analyzeMulti } = await import('../services/api');
    
    render(<App />);
    
    // Switch to multi-tool mode
    fireEvent.click(screen.getByText(/multi-tool image/i));
    
    // Select file
    const fileInput = screen.getByLabelText(/select image/i);
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    // Select tools
    fireEvent.click(screen.getByLabelText(/ocr/i));
    fireEvent.click(screen.getByLabelText(/yolo/i));
    
    // Click analyze
    fireEvent.click(screen.getByText(/analyze/i));
    
    // Verify API was called
    await waitFor(() => {
      expect(analyzeMulti).toHaveBeenCalled();
    });
  });
});
```

**Expected:** Integration test passes

---

### **Phase 3: Final Polish**

#### **F7: Update JobResults to Display YOLO Detections**

**File:** `/web-ui/src/components/JobResults.tsx`

**Implementation:**
```typescript
// Add YOLO detection display
{results.detections && results.detections.length > 0 && (
  <div className={styles.yoloSection}>
    <h3>YOLO Detections</h3>
    {results.detections.map((detection: any, idx: number) => (
      <div key={idx} className={styles.detection}>
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

**File:** `/docs/releases/v0.9.1/RELEASE_NOTES.md`

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
feat(backend): Add logging to multi-tool endpoint
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
- `/docs/releases/v0.9.1/DOCUMENTS_ADDENUM.md` - Additional documentation
- `/docs/releases/v0.9.1/VIDEO_INT_TESTS_RESTORED.md` - Restored video integration tests
- `/AGENTS.md` - Agent commands and conventions
- `/ARCHITECTURE.md` - System architecture

---

**Last Updated:** 2026-02-18  
**Next Step:** Begin Phase 1, B1 - Write failing test for `/v1/image/analyze-multi`