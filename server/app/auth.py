"""Authentication and authorization utilities.

This module provides authentication services using the Service Layer pattern,
with dependency injection and Protocol-based abstractions.

The design separates concerns:
- AuthService: Business logic (hashing, validation, permissions)
- KeyRepository Protocol: Abstraction for key storage
- FastAPI dependencies: HTTP layer with thin wrappers
"""

import hashlib
import logging
import secrets
from typing import Any, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from .protocols import KeyRepository

# Configure logging
logger = logging.getLogger(__name__)

# API key extraction from headers/query parameters
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)


class AuthSettings(BaseSettings):
    """Configuration for authentication via environment variables.

    Uses Pydantic BaseSettings to load authentication configuration
    from environment variables with proper validation and type safety.

    Attributes:
        admin_key: Admin API key (FORGESYTE_ADMIN_KEY env var)
        user_key: User API key (FORGESYTE_USER_KEY env var)
    """

    admin_key: Optional[str] = Field(
        default=None, validation_alias="FORGESYTE_ADMIN_KEY"
    )
    user_key: Optional[str] = Field(default=None, validation_alias="FORGESYTE_USER_KEY")

    model_config = ConfigDict(env_file=".env", extra="ignore")


class InMemoryKeyRepository:
    """In-memory implementation of KeyRepository Protocol.

    Stores API keys in a dictionary, loading them from AuthSettings
    at initialization. This implementation can be replaced with a
    database-backed repository without changing AuthService.

    Attributes:
        keys: Dictionary mapping SHA256 hashes to user dictionaries
    """

    def __init__(self, settings: AuthSettings):
        """Initialize repository from settings.

        Args:
            settings: AuthSettings instance with API keys

        Raises:
            None
        """
        self.keys: dict[str, dict[str, Any]] = {}
        self._load_from_settings(settings)

    def _load_from_settings(self, settings: AuthSettings) -> None:
        """Load keys from AuthSettings.

        Args:
            settings: AuthSettings instance

        Raises:
            None
        """
        if settings.admin_key:
            key_hash = AuthService.hash_key(settings.admin_key)
            self.keys[key_hash] = {
                "name": "admin",
                "permissions": ["admin", "analyze", "stream", "plugins"],
            }
            logger.debug("Loaded admin API key from settings")

        if settings.user_key:
            key_hash = AuthService.hash_key(settings.user_key)
            self.keys[key_hash] = {
                "name": "user",
                "permissions": ["analyze", "stream"],
            }
            logger.debug("Loaded user API key from settings")

    def get_user_by_hash(self, key_hash: str) -> Optional[dict[str, Any]]:
        """Retrieve user information by hashed key.

        Args:
            key_hash: SHA256 hash of API key

        Returns:
            User dictionary with name and permissions if found, None otherwise
                {"name": str, "permissions": list[str]}

        Raises:
            None
        """
        return self.keys.get(key_hash)


class AuthService:
    """Authentication business logic using Service Layer pattern.

    Handles API key hashing, user validation, and permission checking.
    Uses Protocol-based KeyRepository abstraction for flexibility.

    Attributes:
        repository: KeyRepository implementation for key storage access
    """

    def __init__(self, repository: KeyRepository):
        """Initialize AuthService with a key repository.

        Args:
            repository: KeyRepository implementation (in-memory, db, etc.)

        Raises:
            None
        """
        self.repository = repository
        logger.debug("AuthService initialized")

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key using SHA256.

        Args:
            key: Plain text API key

        Returns:
            SHA256 hexadecimal hash of the key

        Raises:
            None
        """
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure new API key.

        Returns:
            URL-safe random token suitable for API key use

        Raises:
            None
        """
        return secrets.token_urlsafe(32)

    def validate_user(self, key: Optional[str]) -> Optional[dict[str, Any]]:
        """Validate API key and return user information.

        Args:
            key: API key from request (or None if missing)

        Returns:
            User dictionary with name and permissions if valid, None otherwise
                {"name": str, "permissions": list[str]}

        Raises:
            None
        """
        if not key:
            # Allow unauthenticated access only if no keys are configured
            # Check by seeing if the repository has any keys at all
            if hasattr(self.repository, "keys") and not self.repository.keys:
                # No keys configured - allow anonymous access
                return {"name": "anonymous", "permissions": ["analyze", "stream"]}
            # Keys are configured - authentication is required
            return None

        key_hash = self.hash_key(key)
        user = self.repository.get_user_by_hash(key_hash)

        if user:
            logger.debug("API key validated successfully", extra={"user": user["name"]})
        else:
            logger.warning("Invalid API key attempted")

        return user

    def check_permissions(
        self, user: dict[str, Any], required_perms: list[str]
    ) -> bool:
        """Check if user has required permissions.

        Args:
            user: User dictionary with permissions
            required_perms: List of required permission strings

        Returns:
            True if user has all required permissions, False otherwise

        Raises:
            None
        """
        user_perms = set(user.get("permissions", []))
        return set(required_perms).issubset(user_perms)


# Module-level service instance (initialized in main.py)
_auth_service: Optional[AuthService] = None


def init_auth_service(repository: Optional[KeyRepository] = None) -> AuthService:
    """Initialize the module-level AuthService instance.

    Called during app startup to set up authentication.
    Can be provided with a custom repository for testing.

    Args:
        repository: KeyRepository implementation (creates InMemoryKeyRepository
                   if not provided)

    Returns:
        AuthService instance

    Raises:
        None
    """
    global _auth_service
    if repository is None:
        settings = AuthSettings()
        repository = InMemoryKeyRepository(settings)
    _auth_service = AuthService(repository)
    logger.info("Authentication service initialized")
    return _auth_service


def get_auth_service() -> AuthService:
    """Dependency injection function for AuthService.

    Used in FastAPI Depends() to inject auth service into endpoints.

    Returns:
        AuthService instance

    Raises:
        RuntimeError: If service not initialized
    """
    if _auth_service is None:
        raise RuntimeError("AuthService not initialized. Call init_auth_service().")
    return _auth_service


async def get_api_key(
    header_key: Optional[str] = Security(API_KEY_HEADER),
    query_key: Optional[str] = Security(API_KEY_QUERY),
    service: AuthService = Depends(get_auth_service),
) -> Optional[dict[str, Any]]:
    """Extract and validate API key from request.

    Checks both header and query parameter for API key, with header
    taking precedence. Returns None if key is missing and no keys
    are configured (allowing anonymous access).

    Args:
        header_key: API key from X-API-Key header
        query_key: API key from api_key query parameter
        service: Injected AuthService instance

    Returns:
        User dictionary if valid, None if no authentication required,
        or raises HTTPException if authentication failed

    Raises:
        None
    """
    key = header_key or query_key
    user = service.validate_user(key)

    if user is None and key:
        logger.warning("Invalid API key provided")
        return None

    return user


def require_auth(permissions: Optional[list[str]] = None):
    """Dependency that requires authentication with specific permissions.

    Higher-order function that returns a dependency for enforcing
    authentication and permission checks on endpoints.

    Args:
        permissions: List of required permission strings (optional)

    Returns:
        FastAPI dependency function

    Raises:
        None
    """

    async def auth_dependency(
        api_key: Optional[dict[str, Any]] = Depends(get_api_key),
        service: AuthService = Depends(get_auth_service),
    ) -> dict[str, Any]:
        """Enforces authentication and permission requirements.

        Args:
            api_key: Result from get_api_key dependency
            service: Injected AuthService instance

        Returns:
            Validated user dictionary

        Raises:
            HTTPException: 401 if authentication required but missing
            HTTPException: 403 if user lacks required permissions
        """
        if api_key is None:
            logger.warning("Unauthorized access attempt")
            raise HTTPException(status_code=401, detail="API key required")

        if permissions:
            if not service.check_permissions(api_key, permissions):
                missing = set(permissions) - set(api_key.get("permissions", []))
                logger.warning(
                    "Insufficient permissions",
                    extra={"user": api_key["name"], "missing": missing},
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {missing}",
                )

        return api_key

    return auth_dependency
