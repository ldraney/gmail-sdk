"""Integration tests for messages."""

from __future__ import annotations

import pytest

from gmail_sdk import GmailClient


class TestListMessages:
    def test_returns_messages(self, client: GmailClient):
        result = client.list_messages(max_results=5)
        assert "messages" in result or "resultSizeEstimate" in result

    def test_with_query(self, client: GmailClient):
        result = client.list_messages(query="is:unread", max_results=3)
        # Should return without error; may or may not have messages
        assert "resultSizeEstimate" in result

    def test_get_message(self, client: GmailClient):
        listing = client.list_messages(max_results=1)
        if not listing.get("messages"):
            pytest.skip("empty inbox")
        msg_id = listing["messages"][0]["id"]
        msg = client.get_message(msg_id)
        assert "id" in msg
        assert "payload" in msg
