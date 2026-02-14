"""Main Gmail API client."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .auth import AuthMixin
from .messages import MessagesMixin
from .threads import ThreadsMixin
from .drafts import DraftsMixin
from .labels import LabelsMixin
from .attachments import AttachmentsMixin
from .filters import FiltersMixin
from .settings import SettingsMixin
from .history import HistoryMixin
from .convenience import ConvenienceMixin

GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1"
DEFAULT_SECRETS_DIR = os.path.join(os.path.expanduser("~"), "secrets", "google-oauth")


class GmailAPIError(Exception):
    """Exception wrapping Gmail API HTTP errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Gmail API error {status_code}: {message}")


class GmailClient(
    AuthMixin,
    MessagesMixin,
    ThreadsMixin,
    DraftsMixin,
    LabelsMixin,
    AttachmentsMixin,
    FiltersMixin,
    SettingsMixin,
    HistoryMixin,
    ConvenienceMixin,
):
    """Synchronous Python client for the Gmail REST API.

    Either ``account`` or ``access_token`` must be provided. If neither is
    given, the client will be created without authentication and API calls
    will fail.
    """

    def __init__(
        self,
        account: str | None = None,
        access_token: str | None = None,
        secrets_dir: str | None = None,
    ):
        self.account = account
        self.secrets_dir = secrets_dir or os.environ.get("GMAIL_SECRETS_DIR", DEFAULT_SECRETS_DIR)

        if access_token is None and account is not None:
            access_token = self._load_and_refresh_token(account, self.secrets_dir)

        self.access_token = access_token

        headers: dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        self._http = httpx.Client(
            base_url=GMAIL_BASE,
            headers=headers,
            timeout=60.0,
        )

    # ---- low-level helpers ------------------------------------------------

    @staticmethod
    def _raise_api_error(resp: httpx.Response) -> None:
        """Raise GmailAPIError from an httpx response."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                detail = resp.text
            raise GmailAPIError(resp.status_code, detail) from exc

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.get(path, params=params)
        self._raise_api_error(resp)
        return resp.json() if resp.content else {}

    def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = self._http.post(path, json=json)
        self._raise_api_error(resp)
        return resp.json() if resp.content else {}

    def _delete(self, path: str) -> int:
        resp = self._http.delete(path)
        self._raise_api_error(resp)
        return resp.status_code

    def _patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.patch(path, json=json)
        self._raise_api_error(resp)
        return resp.json() if resp.content else {}

    def _put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.put(path, json=json)
        self._raise_api_error(resp)
        return resp.json() if resp.content else {}

    def __repr__(self) -> str:
        if self.account:
            return f"GmailClient(account={self.account!r})"
        return "GmailClient()"

    def __enter__(self) -> GmailClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()
