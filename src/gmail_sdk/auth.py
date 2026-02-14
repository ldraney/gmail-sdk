"""OAuth authentication for Gmail API."""

from __future__ import annotations

import json
import os
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import urlencode, urlparse, parse_qs

if TYPE_CHECKING:
    from .client import GmailClient

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8090"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://mail.google.com/",
]


class AuthMixin:
    """Mixin providing OAuth authentication methods."""

    @staticmethod
    def get_auth_url(
        client_id: str,
        redirect_uri: str = REDIRECT_URI,
        scopes: list[str] | None = None,
    ) -> str:
        """Build a Google OAuth 2.0 authorization URL.

        Args:
            client_id: Google OAuth client ID.
            redirect_uri: Callback URL.
            scopes: OAuth scopes (defaults to full Gmail access).

        Returns:
            The authorization URL.
        """
        if scopes is None:
            scopes = SCOPES

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    @staticmethod
    def exchange_code(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str = REDIRECT_URI,
    ) -> dict[str, Any]:
        """Exchange an authorization code for tokens.

        Args:
            code: Authorization code from the callback.
            client_id: Google OAuth client ID.
            client_secret: Google OAuth client secret.
            redirect_uri: The same redirect URI used in the auth request.

        Returns:
            Token data dict with access_token, refresh_token, expires_at, etc.
        """
        resp = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()
        token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
        return token_data

    @staticmethod
    def refresh_access_token(
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Refresh an expired access token.

        Args:
            client_id: Google OAuth client ID.
            client_secret: Google OAuth client secret.
            refresh_token: The refresh token.

        Returns:
            Updated token fields (access_token, expires_at, etc).
        """
        resp = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        new_data = resp.json()
        new_data["expires_at"] = time.time() + new_data.get("expires_in", 3600)
        return new_data

    @staticmethod
    def _load_credentials(secrets_dir: str) -> dict[str, str]:
        """Load OAuth client credentials from credentials.json."""
        creds_path = os.path.join(secrets_dir, "credentials.json")
        with open(creds_path) as f:
            data = json.load(f)
        if "installed" in data:
            return data["installed"]
        if "web" in data:
            return data["web"]
        raise ValueError("credentials.json must contain an 'installed' or 'web' application config")

    @staticmethod
    def _load_token(account: str, secrets_dir: str) -> dict[str, Any] | None:
        """Load a saved token file for an account."""
        token_path = Path(secrets_dir) / f"gmail-{account}.json"
        if token_path.exists():
            with open(token_path) as f:
                return json.load(f)
        return None

    @staticmethod
    def _save_token(account: str, secrets_dir: str, token_data: dict[str, Any]) -> None:
        """Save token data to disk with restricted permissions."""
        token_path = Path(secrets_dir) / f"gmail-{account}.json"
        fd = os.open(str(token_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(token_data, f, indent=2)

    @classmethod
    def _load_and_refresh_token(cls, account: str, secrets_dir: str) -> str:
        """Load token for account, refreshing if expired. Returns access_token."""
        token_data = cls._load_token(account, secrets_dir)
        if token_data is None:
            raise FileNotFoundError(
                f"No token file for account '{account}'. "
                f"Run GmailClient.authorize(account='{account}') first."
            )

        if token_data.get("expires_at", 0) < time.time() + 300:
            creds = cls._load_credentials(secrets_dir)
            new_data = cls.refresh_access_token(
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
                refresh_token=token_data["refresh_token"],
            )
            # Preserve refresh_token (not always returned on refresh)
            token_data["access_token"] = new_data["access_token"]
            token_data["expires_at"] = new_data["expires_at"]
            if "refresh_token" in new_data:
                token_data["refresh_token"] = new_data["refresh_token"]
            cls._save_token(account, secrets_dir, token_data)

        return token_data["access_token"]

    @classmethod
    def authorize(
        cls,
        account: str,
        secrets_dir: str | None = None,
    ) -> GmailClient:
        """Run the full OAuth flow: open browser, capture code, save token, return client.

        Args:
            account: Account alias (e.g. "draneylucas").
            secrets_dir: Override secrets directory.

        Returns:
            A configured GmailClient instance.
        """
        from .client import DEFAULT_SECRETS_DIR

        secrets_dir = secrets_dir or os.environ.get("GMAIL_SECRETS_DIR", DEFAULT_SECRETS_DIR)
        creds = cls._load_credentials(secrets_dir)

        auth_url = cls.get_auth_url(client_id=creds["client_id"])

        # Capture the auth code via a local HTTP server
        auth_code = None

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code
                qs = parse_qs(urlparse(self.path).query)
                auth_code = qs.get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Auth successful! You can close this tab.</h1>")

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("localhost", 8090), _Handler)
        webbrowser.open(auth_url)
        server.handle_request()
        server.server_close()

        if not auth_code:
            raise RuntimeError("No auth code received from OAuth callback")

        token_data = cls.exchange_code(
            code=auth_code,
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
        cls._save_token(account, secrets_dir, token_data)

        from .client import GmailClient
        return GmailClient(account=account, secrets_dir=secrets_dir)
