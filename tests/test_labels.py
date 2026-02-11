"""Integration tests for labels."""

from __future__ import annotations

from gmail_sdk import GmailClient


class TestListLabels:
    def test_returns_labels(self, client: GmailClient):
        result = client.list_labels()
        assert "labels" in result
        assert len(result["labels"]) > 0

    def test_contains_inbox(self, client: GmailClient):
        result = client.list_labels()
        label_names = [l["name"] for l in result["labels"]]
        assert "INBOX" in label_names
