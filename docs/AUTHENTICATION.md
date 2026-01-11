# Authentication & Authorization Guide

ForgeSyte uses API key-based authentication for securing endpoints and controlling access to resources. This guide documents the authentication system, authorization patterns, and security best practices.

---

## Overview

ForgeSyte implements:

- **API Key Authentication**: Bearer tokens via header or query parameter
- **Role-Based Access Control (RBAC)**: Permissions assigned to keys
- **Permission-Based Authorization**: Endpoints require specific permissions
- **Graceful Fallback**: Anonymous access when no keys are configured (development mode)

---

## Authentication Methods

### Method 1: Header (Recommended)

Include API key in `X-API-Key` header:

```bash
curl -H "X-API-Key: fgy_live_example_key_abc123" http://localhost:8000/v1/analyze
```

**Advantages**:
- Standard HTTP security practice
- Keeps credentials out of URL logs
- Better for long-lived tokens

### Method 2: Query Parameter

Include API key as `api_key` query parameter:

```bash
curl "http://localhost:8000/v1/analyze?api_key=fgy_live_example_key_abc123"
```

**Advantages**:
- Simpler for browsers (no custom headers)
- Useful for webhooks
- Good for temporary/short-lived tokens

**Disadvantages**:
- Credentials may appear in server logs
- Less secure for sensitive operations

---

## API Key Format

API keys follow this format:

```
fgy_live_<random_base64_characters>
```

- **Prefix**: `fgy_live_` identifies this as a ForgeSyte live key
- **Length**: 32+ characters for security
- **Character set**: URL-safe base64 (alphanumeric, `-`, `_`)

**Example**:
```
fgy_live_mZ8eRfqK9pL7tJ2vN4xM1wQ3sA5dB6cF
```

---

## Permission Model

### Available Permissions

| Permission | Description | Endpoints |
|-----------|-------------|-----------|
| `analyze` | Run image analysis | POST `/v1/analyze`, GET `/v1/jobs/*` |
| `stream` | Use WebSocket streaming | WebSocket `/ws/*` |
| `plugins` | List and manage plugins | GET `/v1/plugins`, GET `/v1/plugins/{name}` |
| `admin` | Administrative access | All endpoints |

### Default Permissions

**Admin Key** (FORGESYTE_ADMIN_KEY):
```
["admin", "analyze", "stream", "plugins"]
```

**User Key** (FORGESYTE_USER_KEY):
```
["analyze", "stream"]
```

**Anonymous** (no keys configured):
```
["analyze", "stream"]
```

---

## Configuration

### Environment Variables

Set these variables to enable authentication:

```bash
# Admin API key (full access)
export FORGESYTE_ADMIN_KEY="fgy_live_your_admin_key_here"

# User API key (limited access)
export FORGESYTE_USER_KEY="fgy_live_your_user_key_here"
```

### Generation

Generate a new API key:

```bash
python -c "import secrets; print('fgy_live_' + secrets.token_urlsafe(32))"
```

### Development Mode

If no environment variables are set, the server runs in **anonymous access mode**:
- All users get default permissions
- No authentication required
- Suitable only for development/testing

Production deployments **must** set API keys.

---

## API Authentication Flow

### Flow Diagram

```
Client Request
  ↓
Extract API Key (header or query)
  ↓
Key not provided?
  ├─ YES: Check if keys configured
  │        ├─ Keys configured → 401 Unauthorized
  │        └─ No keys → Allow (dev mode)
  └─ NO: Continue
  ↓
Hash the key (SHA256)
  ↓
Lookup in API_KEYS registry
  ↓
Key found?
  ├─ YES: Get permissions
  │        ↓
  │        Required permission matches?
  │        ├─ YES: Allow request
  │        └─ NO: 403 Forbidden
  └─ NO: 401 Unauthorized
```

### Implementation Details

**Key Hashing** (`auth.py`):
```python
def hash_key(key: str) -> str:
    """Hash API key with SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()

API_KEYS: dict[str, dict] = {
    "abc123...": {"name": "admin", "permissions": [...]}
}
```

Keys are **never stored in plaintext**. Only SHA256 hashes are stored.

**Permission Checking** (`auth.py`):
```python
def require_auth(permissions: Optional[list[str]] = None):
    """Dependency that enforces permissions."""
    async def auth_dependency(api_key: Optional[dict] = Depends(get_api_key)):
        if api_key is None:
            raise HTTPException(status_code=401)
        
        if permissions:
            user_perms = set(api_key.get("permissions", []))
            required_perms = set(permissions)
            if not required_perms.issubset(user_perms):
                raise HTTPException(status_code=403)
        
        return api_key
    
    return auth_dependency
```

---

## Endpoint Authorization

### Protected Endpoints

```python
from app.auth import require_auth

@router.post("/analyze")
async def analyze_image(
    request: Request,
    file: UploadFile = None,
    auth: dict = Depends(require_auth(["analyze"]))
):
    """Requires 'analyze' permission."""
    # auth contains: {"name": "...", "permissions": [...]}
    pass

@router.get("/plugins")
async def list_plugins(
    auth: dict = Depends(require_auth(["plugins"]))
):
    """Requires 'plugins' permission."""
    pass

@router.post("/admin/config")
async def update_config(
    auth: dict = Depends(require_auth(["admin"]))
):
    """Requires 'admin' permission."""
    pass
```

### Optional Authentication

Some endpoints may have optional authentication:

```python
@router.get("/health")
async def health_check(
    auth: Optional[dict] = Depends(get_api_key)  # Optional
):
    """Works with or without authentication."""
    if auth:
        return {"status": "ok", "user": auth["name"]}
    else:
        return {"status": "ok", "user": "anonymous"}
```

---

## Usage Examples

### Python Client

```python
import requests

API_KEY = "fgy_live_example_key_abc123"
BASE_URL = "http://localhost:8000/v1"

# Method 1: Header
headers = {"X-API-Key": API_KEY}
response = requests.post(
    f"{BASE_URL}/analyze",
    files={"file": open("image.png", "rb")},
    headers=headers
)

# Method 2: Query parameter
params = {"api_key": API_KEY}
response = requests.post(
    f"{BASE_URL}/analyze",
    files={"file": open("image.png", "rb")},
    params=params
)

print(response.json())
```

### JavaScript/Fetch API

```javascript
const API_KEY = "fgy_live_example_key_abc123";
const BASE_URL = "http://localhost:8000/v1";

// Method 1: Header
const formData = new FormData();
formData.append("file", imageFile);

const response = await fetch(`${BASE_URL}/analyze`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY
  },
  body: formData
});

// Method 2: Query parameter
const response = await fetch(
  `${BASE_URL}/analyze?api_key=${API_KEY}`,
  {
    method: "POST",
    body: formData
  }
);

const data = await response.json();
console.log(data);
```

### cURL

```bash
# Header authentication
curl -X POST \
  -H "X-API-Key: fgy_live_example_key_abc123" \
  -F "file=@image.png" \
  http://localhost:8000/v1/analyze

# Query parameter authentication
curl -X POST \
  -F "file=@image.png" \
  "http://localhost:8000/v1/analyze?api_key=fgy_live_example_key_abc123"
```

### WebSocket Client

```javascript
const API_KEY = "fgy_live_example_key_abc123";
const CLIENT_ID = "client_" + Date.now();

// Include API key in WebSocket URL
const ws = new WebSocket(
  `ws://localhost:8000/ws/${CLIENT_ID}?api_key=${API_KEY}`
);

ws.onopen = () => {
  console.log("Connected");
  ws.send(JSON.stringify({
    type: "subscribe",
    topic: "all"
  }));
};
```

---

## Error Responses

### 401 Unauthorized

Returned when authentication is required but missing or invalid:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "API key required"
}
```

**Causes**:
- No API key provided
- Invalid/malformed API key
- API key not found in registry

### 403 Forbidden

Returned when authenticated but lacking required permissions:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Missing permissions: {'admin'}"
}
```

**Causes**:
- API key is valid but has insufficient permissions
- Endpoint requires permission user doesn't have

---

## Security Checklist

### For Administrators

- [ ] **Use HTTPS in production**: Never transmit API keys over plain HTTP
- [ ] **Set strong API keys**: Use generated keys with 32+ characters
- [ ] **Rotate keys regularly**: Establish key rotation policy (30-90 days)
- [ ] **Monitor key usage**: Log and audit who uses which keys
- [ ] **Use environment variables**: Never hardcode keys in source code
- [ ] **Revoke compromised keys**: Remove from API_KEYS immediately
- [ ] **Use separate keys per client**: Admin key, user key, integration key
- [ ] **Enable TLS/SSL**: Use certificates signed by trusted CA

### For Developers

- [ ] **Never log API keys**: Redact from logs and error messages
- [ ] **Use header method**: Prefer `X-API-Key` header over query params
- [ ] **Validate permissions**: Check perms on every protected endpoint
- [ ] **Handle auth errors**: Properly handle 401/403 responses
- [ ] **Store keys securely**: Use environment variables or secrets managers
- [ ] **Encrypt at rest**: If storing keys, use encryption
- [ ] **Use timeouts**: Implement request timeouts to prevent hanging
- [ ] **Rate limiting**: Consider rate limiting per API key

### For Operations

- [ ] **Infrastructure security**: Firewall, VPN, network isolation
- [ ] **Server hardening**: Keep OS and dependencies patched
- [ ] **Secrets management**: Use Vault, AWS Secrets Manager, or equivalent
- [ ] **Audit logging**: Log all authentication attempts
- [ ] **Monitoring**: Alert on failed auth attempts, key misuse
- [ ] **Incident response**: Have plan for compromised keys
- [ ] **Disaster recovery**: Backup/restore of configuration
- [ ] **Compliance**: Meet GDPR, HIPAA, or relevant standards

---

## Advanced Patterns

### Per-Client Keys

```bash
export FORGESYTE_ADMIN_KEY="fgy_live_admin_..."
export FORGESYTE_USER_KEY="fgy_live_user_..."
export FORGESYTE_INTEGRATION_KEY="fgy_live_integration_..."
```

Each integration gets its own key with limited permissions.

### Time-Based Expiration

Extend the auth system to support expiring keys:

```python
from datetime import datetime, timedelta

API_KEYS: dict[str, dict] = {
    "abc123...": {
        "name": "temp_user",
        "permissions": ["analyze"],
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
}

def is_key_valid(key_info: dict) -> bool:
    if "expires_at" in key_info:
        return datetime.utcnow() < key_info["expires_at"]
    return True
```

### Rate Limiting Per Key

```python
from collections import defaultdict
from datetime import datetime, timedelta

request_counts = defaultdict(list)

def rate_limit_check(api_key_hash: str, max_requests: int = 1000, window: int = 3600):
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=window)
    
    # Remove old requests
    request_counts[api_key_hash] = [
        t for t in request_counts[api_key_hash] if t > cutoff
    ]
    
    if len(request_counts[api_key_hash]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    request_counts[api_key_hash].append(now)
```

### Key Scopes (OAuth2-like)

```python
# Key with specific resource access
API_KEYS["abc123..."] = {
    "name": "limited_user",
    "permissions": ["analyze"],
    "scopes": {
        "plugins": ["ocr"],  # Only access OCR plugin
        "jobs": ["list", "read"]  # Can't cancel jobs
    }
}
```

---

## Troubleshooting

### "API key required" but key was provided

- [ ] Check API key is not wrapped in quotes
- [ ] Verify X-API-Key header (case-sensitive)
- [ ] Check no extra whitespace in key
- [ ] Try both header and query methods

### "Missing permissions" error

- [ ] Check endpoint documentation for required permissions
- [ ] Verify API key has those permissions
- [ ] Use admin key to test
- [ ] Check permissions are strings in a list

### Key not working after restart

- [ ] Verify environment variables are set
- [ ] Check `init_api_keys()` is called on startup
- [ ] Verify no typos in env var names
- [ ] Check env vars are actually loaded

### Can't connect with WebSocket

- [ ] Include `api_key` in WebSocket URL query params
- [ ] Check API key has `stream` permission
- [ ] Verify WebSocket URL format: `ws://host/ws/client_id?api_key=...`
- [ ] Check CORS and WebSocket proxy configuration

---

## Testing

### Unit Tests

```python
import pytest
from app.auth import hash_key, get_api_key, require_auth

def test_hash_key_consistent():
    """Same key always hashes to same value."""
    key = "fgy_live_test123"
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    assert hash1 == hash2

def test_api_key_extraction():
    """Correctly extracts key from request."""
    # Test with header
    # Test with query param
    # Test with missing key
    pass

def test_permission_check():
    """Enforces permissions correctly."""
    # Test with sufficient permissions
    # Test with missing permissions
    # Test with admin key (should pass all)
    pass
```

### Integration Tests

```bash
# Test with header
curl -H "X-API-Key: $FORGESYTE_ADMIN_KEY" http://localhost:8000/v1/plugins

# Test with query param
curl "http://localhost:8000/v1/plugins?api_key=$FORGESYTE_ADMIN_KEY"

# Test with invalid key
curl -H "X-API-Key: invalid" http://localhost:8000/v1/plugins
# Expected: 401 Unauthorized

# Test with insufficient permissions
curl -H "X-API-Key: $FORGESYTE_USER_KEY" http://localhost:8000/v1/admin/config
# Expected: 403 Forbidden
```

---

## See Also

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [README.md](../README.md) - Project overview
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
