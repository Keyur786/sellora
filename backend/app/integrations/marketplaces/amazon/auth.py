import time
from typing import Any, Dict, Optional
import httpx


class AmazonLWAAuth:
    """Login with Amazon (LWA) OAuth 2.0 client for Selling Partner API."""

    TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    # Amazon India Seller Central authorization URL
    AUTHORIZE_URL = "https://sellercentral.amazon.in/apps/authorize/consent"

    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self._cached_token: Optional[str] = None
        self._expires_at: float = 0.0

    def get_authorization_url(self, app_id: str, state: str, version: str = "beta") -> str:
        """Construct the official Seller Central India consent redirect URL."""
        return f"{self.AUTHORIZE_URL}?application_id={app_id}&state={state}&version={version}"

    async def exchange_code_for_tokens(self, auth_code: str) -> Dict[str, Any]:
        """Exchange the one-time authorization code returned by Seller Central for refresh and access tokens."""
        if (
            not self.client_id
            or not self.client_secret
            or "mock" in self.client_id.lower()
            or "test" in self.client_id.lower()
        ):
            # Mock return for dev testing
            return {
                "access_token": "mock_lwa_access_token_india_sandbox",
                "refresh_token": "mock_lwa_refresh_token_india_sandbox",
                "token_type": "bearer",
                "expires_in": 3600,
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = await client.post(self.TOKEN_URL, data=payload)
            response.raise_for_status()
            data = response.json()
            self._cached_token = data.get("access_token")
            self._expires_at = time.time() + data.get("expires_in", 3600) - 60
            return data

    async def get_access_token(self, refresh_token: str) -> str:
        """Retrieve a valid LWA access token using refresh_token, utilizing cache when valid."""
        now = time.time()
        if self._cached_token and now < self._expires_at:
            return self._cached_token

        if not self.client_id or not self.client_secret or refresh_token.startswith("mock_"):
            self._cached_token = "mock_lwa_access_token_india_sandbox"
            self._expires_at = now + 3600
            return self._cached_token

        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = await client.post(self.TOKEN_URL, data=payload)
            response.raise_for_status()
            data = response.json()
            self._cached_token = data.get("access_token")
            self._expires_at = now + data.get("expires_in", 3600) - 60
            return self._cached_token
