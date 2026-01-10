# MCP API Reference

Complete API reference for ForgeSyte's MCP (Model Context Protocol) endpoints.

---

## Base URL

```
http://localhost:8000
```

For production deployments, replace with your ForgeSyte server URL.

---

## Endpoints

### 1. Get MCP Manifest

**Endpoint**: `GET /v1/mcp-manifest`

Returns the MCP manifest describing all available tools and server metadata.

#### Request

```bash
curl http://localhost:8000/v1/mcp-manifest
```

#### Response (200 OK)

```json
{
  "tools": [
    {
      "id": "vision.ocr",
      "title": "OCR Plugin",
      "description": "Extracts text from images using optical character recognition",
      "inputs": ["image"],
      "outputs": ["text"],
      "invoke_endpoint": "/v1/analyze?plugin=ocr",
      "permissions": []
    },
    {
      "id": "vision.block_mapper",
      "title": "Block Mapper",
      "description": "Maps image regions to labeled blocks",
      "inputs": ["image"],
      "outputs": ["json"],
      "invoke_endpoint": "/v1/analyze?plugin=block_mapper",
      "permissions": []
    }
  ],
  "server": {
    "name": "forgesyte",
    "version": "0.1.0",
    "mcp_version": "1.0.0"
  },
  "version": "1.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `tools` | `Array<MCPTool>` | Array of available tools |
| `server` | `MCPServerInfo` | Server metadata |
| `version` | `string` | Manifest schema version |

#### MCPTool Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Tool identifier (format: `vision.{plugin_name}`) |
| `title` | `string` | Human-readable tool name |
| `description` | `string` | Tool description |
| `inputs` | `Array<string>` | Input types (e.g., "image", "text") |
| `outputs` | `Array<string>` | Output types (e.g., "json", "text") |
| `invoke_endpoint` | `string` | HTTP endpoint to invoke tool |
| `permissions` | `Array<string>` | Required permissions (optional) |

#### MCPServerInfo Schema

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Server name |
| `version` | `string` | Server semantic version |
| `mcp_version` | `string` | MCP protocol version |

#### Response Codes

| Code | Description |
|------|-------------|
| 200 | Manifest retrieved successfully |
| 500 | Server error generating manifest (check plugin validity) |

#### Example: Extract Tool IDs

```bash
curl http://localhost:8000/v1/mcp-manifest | jq '.tools[].id'
# => "vision.ocr"
# => "vision.block_mapper"
```

---

### 2. Get MCP Version

**Endpoint**: `GET /v1/mcp-version`

Returns the MCP protocol version supported by this server.

#### Request

```bash
curl http://localhost:8000/v1/mcp-version
```

#### Response (200 OK)

```json
{
  "mcp_version": "1.0.0"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `mcp_version` | `string` | MCP protocol semantic version |

#### Response Codes

| Code | Description |
|------|-------------|
| 200 | Version retrieved successfully |

---

### 3. Invoke Tool (via Analyze Endpoint)

**Endpoint**: `POST /v1/analyze?plugin={plugin_name}`

Invokes a plugin tool and creates a job for async processing.

#### Request

```bash
curl -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@image.png"
```

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `plugin` | `string` | Plugin name from tool ID | Yes |

#### Request Body

Multipart form data:

| Field | Type | Description |
|-------|------|-------------|
| `file` | `file` | Image file to analyze |

#### Response (202 Accepted)

```json
{
  "id": "job_abc123def456",
  "status": "queued",
  "plugin": "ocr",
  "created_at": "2024-01-10T12:00:00Z"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Job identifier for polling |
| `status` | `string` | Job status ("queued", "processing", "completed", "failed") |
| `plugin` | `string` | Plugin that will process the job |
| `created_at` | `string` | ISO 8601 timestamp |

#### Response Codes

| Code | Description |
|------|-------------|
| 202 | Job created successfully |
| 400 | Invalid request (missing plugin, invalid file) |
| 404 | Plugin not found |
| 500 | Server error |

#### Example: Create OCR Job

```bash
JOB_ID=$(curl -s -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@image.png" | jq -r '.id')

echo "Job ID: $JOB_ID"
```

---

### 4. Poll Job Status

**Endpoint**: `GET /v1/jobs/{job_id}`

Retrieves the status and results of a submitted job.

#### Request

```bash
curl http://localhost:8000/v1/jobs/job_abc123def456
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `string` | Job identifier from invoke response |

#### Response (200 OK) - Processing

```json
{
  "id": "job_abc123def456",
  "status": "processing",
  "plugin": "ocr",
  "created_at": "2024-01-10T12:00:00Z",
  "progress": 45
}
```

#### Response (200 OK) - Completed

```json
{
  "id": "job_abc123def456",
  "status": "completed",
  "plugin": "ocr",
  "result": {
    "text": "Lorem ipsum dolor sit amet...",
    "confidence": 0.95,
    "language": "en"
  },
  "created_at": "2024-01-10T12:00:00Z",
  "completed_at": "2024-01-10T12:00:05Z"
}
```

#### Response (200 OK) - Failed

```json
{
  "id": "job_abc123def456",
  "status": "failed",
  "plugin": "ocr",
  "error": "Image file is corrupted or not readable",
  "error_code": "INVALID_IMAGE",
  "created_at": "2024-01-10T12:00:00Z",
  "completed_at": "2024-01-10T12:00:02Z"
}
```

#### Job Status Values

| Status | Description |
|--------|-------------|
| `queued` | Job waiting to be processed |
| `processing` | Job currently executing |
| `completed` | Job finished successfully |
| `failed` | Job failed with error |

#### Response Codes

| Code | Description |
|------|-------------|
| 200 | Job status retrieved |
| 404 | Job not found |
| 500 | Server error |

#### Example: Poll Until Completion

```bash
JOB_ID="job_abc123def456"

while true; do
  STATUS=$(curl -s http://localhost:8000/v1/jobs/$JOB_ID)
  STATE=$(echo $STATUS | jq -r '.status')
  
  if [ "$STATE" = "completed" ]; then
    echo "✓ Job completed"
    echo $STATUS | jq '.result'
    break
  elif [ "$STATE" = "failed" ]; then
    echo "✗ Job failed"
    echo $STATUS | jq '.error'
    break
  else
    echo "... Job status: $STATE"
    sleep 1
  fi
done
```

---

## Authentication & Authorization

### Current

ForgeSyte currently does not require authentication. This is suitable for:
- Local development
- Private networks
- Trusted environments

### Production

For production deployments, implement:

```python
# Example: API Key Authentication
@app.get("/v1/mcp-manifest")
async def get_manifest(x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return adapter.get_manifest()
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-10T12:00:00Z"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `PLUGIN_NOT_FOUND` | 404 | Requested plugin doesn't exist |
| `INVALID_IMAGE` | 400 | Image file is invalid or corrupted |
| `JOB_NOT_FOUND` | 404 | Job ID doesn't exist |
| `PLUGIN_ERROR` | 500 | Plugin execution failed |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Rate Limiting

Currently, ForgeSyte does not enforce rate limiting. For production, consider:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/analyze")
@limiter.limit("10/minute")
async def analyze(plugin: str, file: UploadFile):
    ...
```

---

## CORS Configuration

If accessing from a web frontend, CORS must be enabled:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Health Check

**Endpoint**: `GET /health`

Simple health check endpoint.

#### Request

```bash
curl http://localhost:8000/health
```

#### Response (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2024-01-10T12:00:00Z"
}
```

---

## Complete Example Workflow

### 1. Get available tools

```bash
curl http://localhost:8000/v1/mcp-manifest | jq '.tools[] | {id, title}'
```

### 2. Invoke OCR tool

```bash
JOB=$(curl -s -X POST \
  "http://localhost:8000/v1/analyze?plugin=ocr" \
  -F "file=@document.png")

JOB_ID=$(echo $JOB | jq -r '.id')
echo "Created job: $JOB_ID"
```

### 3. Poll for results

```bash
curl http://localhost:8000/v1/jobs/$JOB_ID | jq .
```

### 4. Extract results

```bash
curl -s http://localhost:8000/v1/jobs/$JOB_ID | jq '.result.text'
```

---

## Testing API Endpoints

### Using cURL

```bash
# Get manifest
curl http://localhost:8000/v1/mcp-manifest

# Get version
curl http://localhost:8000/v1/mcp-version

# Invoke tool
curl -X POST http://localhost:8000/v1/analyze?plugin=ocr -F "file=@image.png"

# Check job status
curl http://localhost:8000/v1/jobs/job_id_here
```

### Using Python httpx

```python
import httpx

client = httpx.Client()

# Get manifest
manifest = client.get("http://localhost:8000/v1/mcp-manifest").json()
print(f"Available tools: {len(manifest['tools'])}")

# Invoke plugin
with open("image.png", "rb") as f:
    response = client.post(
        "http://localhost:8000/v1/analyze?plugin=ocr",
        files={"file": f}
    )
    job_id = response.json()["id"]

# Poll status
status = client.get(f"http://localhost:8000/v1/jobs/{job_id}").json()
print(f"Job status: {status['status']}")
```

### Using JavaScript fetch

```javascript
// Get manifest
const manifest = await fetch('http://localhost:8000/v1/mcp-manifest')
  .then(r => r.json());
console.log('Available tools:', manifest.tools);

// Invoke plugin
const formData = new FormData();
formData.append('file', imageFile);
const response = await fetch(
  'http://localhost:8000/v1/analyze?plugin=ocr',
  { method: 'POST', body: formData }
);
const { id } = await response.json();

// Poll status
const status = await fetch(`http://localhost:8000/v1/jobs/${id}`)
  .then(r => r.json());
console.log('Job status:', status.status);
```

---

## Versioning Strategy

### MCP Protocol Version

The server declares its MCP protocol version:

```
GET /v1/mcp-version
=> {"mcp_version": "1.0.0"}
```

### Future Version Negotiation

Clients may optionally specify supported MCP versions:

```
GET /v1/mcp-manifest?client_version=1.0.0
```

The server will:
1. Check compatibility
2. Return compatible manifest
3. Or return HTTP 426 with upgrade instructions

---

## Related Documentation

- **[Configuration Guide](./MCP_CONFIGURATION.md)** - How to configure ForgeSyte
- **[Plugin Implementation Guide](./PLUGIN_IMPLEMENTATION.md)** - How to write plugins
- **[Design Specification](../design/MCP.md)** - Architecture and design

