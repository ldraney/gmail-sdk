"""Integration tests for threads."""

from __future__ import annotations

import pytest

from gmail_sdk import GmailClient


class TestListThreads:
    def test_returns_threads(self, client: GmailClient):
        result = client.list_threads(max_results=5)
        assert "threads" in result or "resultSizeEstimate" in result

    def test_get_thread(self, client: GmailClient):
        listing = client.list_threads(max_results=1)
        if not listing.get("threads"):
            pytest.skip("empty inbox")
        thread_id = listing["threads"][0]["id"]
        thread = client.get_thread(thread_id)
        assert "id" in thread
        assert "messages" in thread
