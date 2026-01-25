# Test Failure Analysis: client.test.ts

**Date:** 2026-01-25  
**Branch:** `blackboxai/new-feature-branch`  
**File:** `web-ui/src/api/client.test.ts`  
**Failures:** 13 of 16 tests

---

## Summary

The test mocks are missing the `headers` property that `client.ts` requires.

---

## Root Cause

**client.ts line 73:**
```typescript
const contentType = response.headers.get("content-type");
```

**Test mocks (example from line 31-34):**
```typescript
fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ plugins: mockPlugins }),
});
```

The mock response has no `headers` property. When `response.headers.get()` is called, it throws:
```
TypeError: Cannot read properties of undefined (reading 'get')
```

---

## Why 3 Tests Pass

The `analyzeImage` tests (lines 156-212) pass because `analyzeImage()` uses its own `fetch()` call directly (lines 117-121 in client.ts), bypassing the `this.fetch()` helper that checks content-type.

---

## Affected Tests (13)

| Test | Line |
|------|------|
| should fetch and return plugins list | 19 |
| should handle API errors | 45 |
| should fetch jobs with default parameters | 59 |
| should include pagination parameters | 84 |
| should include status filter when provided | 97 |
| should fetch a specific job | 111 |
| should handle job response without wrapper | 135 |
| should send DELETE request to cancel job | 216 |
| should fetch health status | 235 |
| should poll until job is complete | 258 |
| should timeout if job not completed | 289 |
| should include X-API-Key header when provided | 310 |
| should not include X-API-Key header when not provided | 328 |

---

## Fix Required

All fetch mocks need a `headers` object with a `get` method:

```typescript
fetchMock.mockResolvedValueOnce({
    ok: true,
    headers: {
        get: (name: string) => name === "content-type" ? "application/json" : null,
    },
    json: async () => ({ plugins: mockPlugins }),
});
```

---

## When This Broke

This broke when `client.ts` was updated to check `content-type` header (lines 72-91) to detect HTML error pages. The tests were not updated to match.

---

## Effort Estimate

- **Scope:** Update 13 mock definitions in `client.test.ts`
- **Risk:** Low (test-only change)
- **Time:** ~15 minutes

---

## Recommended Action

Add a helper function at the top of the test file:

```typescript
const mockJsonResponse = (data: unknown, ok = true, status = 200) => ({
    ok,
    status,
    statusText: ok ? "OK" : "Error",
    headers: {
        get: (name: string) => name === "content-type" ? "application/json" : null,
    },
    json: async () => data,
});
```

Then replace all inline mocks with:
```typescript
fetchMock.mockResolvedValueOnce(mockJsonResponse({ plugins: mockPlugins }));
```
