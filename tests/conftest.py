"""Shared fixtures for Gmail SDK tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gmail_sdk import GmailClient


DEFAULT_SECRETS_DIR = os.path.join(os.path.expanduser("~"), "secrets", "google-oauth")
DEFAULT_ACCOUNT = "draneylucas"


@pytest.fixture(scope="session")
def client() -> GmailClient:
    """Session-scoped Gmail client for integration tests."""
    secrets_dir = os.environ.get("GMAIL_SECRETS_DIR", DEFAULT_SECRETS_DIR)
    account = os.environ.get("GMAIL_TEST_ACCOUNT", DEFAULT_ACCOUNT)

    token_path = Path(secrets_dir) / f"gmail-{account}.json"
    if not token_path.exists():
        pytest.skip(
            f"No token file at {token_path}. "
            f"Run GmailClient.authorize(account='{account}') first."
        )

    return GmailClient(account=account, secrets_dir=secrets_dir)
