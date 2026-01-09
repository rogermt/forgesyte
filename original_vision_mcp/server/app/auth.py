"""Authentication and authorization utilities."""

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
import os
import secrets
import hashlib

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)

# In production, load from environment or secrets manager
API_KEYS: dict[str, dict] = {}


def init_api_keys():
    """Initialize API keys from environment."""
    admin_key = os.getenv("VISION_ADMIN_KEY")
    if admin_key:
        API_KEYS[hash_key(admin_key)] = {
            "name": "admin",
            "permissions": ["admin", "analyze", "stream", "plugins"]
        }
    
    user_key = os.getenv("VISION_USER_KEY")
    if user_key:
        API_KEYS[hash_key(user_key)] = {
            "name": "user",
            "permissions": ["analyze", "stream"]
        }


def hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)


async def get_api_key(
    header_key: Optional[str] = Security(API_KEY_HEADER),
    query_key: Optional[str] = Security(API_KEY_QUERY)
) -> Optional[dict]:
    """Extract and validate API key from request."""
    key = header_key or query_key
    
    if not key:
        # Allow unauthenticated access if no keys configured
        if not API_KEYS:
            return {"name": "anonymous", "permissions": ["analyze", "stream"]}
        return None
    
    key_hash = hash_key(key)
    return API_KEYS.get(key_hash)


def require_auth(permissions: list[str] = None):
    """Dependency that requires authentication with specific permissions."""
    async def auth_dependency(
        api_key: Optional[dict] = Depends(get_api_key)
    ) -> dict:
        if api_key is None:
            raise HTTPException(status_code=401, detail="API key required")
        
        if permissions:
            user_perms = set(api_key.get("permissions", []))
            required_perms = set(permissions)
            if not required_perms.issubset(user_perms):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {required_perms - user_perms}"
                )
        
        return api_key
    
    return auth_dependency


# Initialize on import
init_api_keys()