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
from .convenience import ConvenienceMixin

GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1"
DEFAULT_SECRETS_DIR = os.path.join(os.path.expanduser("~"), "secrets", "google-oauth")


class GmailClient(
    AuthMixin,
    MessagesMixin,
    ThreadsMixin,
    DraftsMixin,
    LabelsMixin,
    AttachmentsMixin,
    FiltersMixin,
    SettingsMixin,
    ConvenienceMixin,
):
    """Synchronous Python client for the Gmail REST API."""

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

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.json() if resp.text.strip() else {}

    def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        resp = self._http.post(path, json=json or {})
        resp.raise_for_status()
        return resp

    def _delete(self, path: str) -> int:
        resp = self._http.delete(path)
        resp.raise_for_status()
        return resp.status_code

    def _patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.patch(path, json=json or {})
        resp.raise_for_status()
        return resp.json() if resp.text.strip() else {}

    def _put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.put(path, json=json or {})
        resp.raise_for_status()
        return resp.json() if resp.text.strip() else {}

    def close(self) -> None:
        self._http.close()
