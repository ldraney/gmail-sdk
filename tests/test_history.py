"""Integration tests for history."""

from __future__ import annotations

import pytest

from gmail_sdk import GmailClient


class TestListHistory:
    def test_list_history_returns_history_id(self, client: GmailClient):
        profile = client.get_profile()
        history_id = profile["historyId"]
        result = client.list_history(start_history_id=history_id)
        assert "historyId" in result or "history" in result

    def test_list_history_with_label_filter(self, client: GmailClient):
        profile = client.get_profile()
        history_id = profile["historyId"]
        result = client.list_history(start_history_id=history_id, label_id="INBOX")
        assert "historyId" in result or "history" in result

    def test_list_history_with_types_filter(self, client: GmailClient):
        profile = client.get_profile()
        history_id = profile["historyId"]
        result = client.list_history(
            start_history_id=history_id,
            history_types=["messageAdded"],
        )
        assert "historyId" in result or "history" in result
