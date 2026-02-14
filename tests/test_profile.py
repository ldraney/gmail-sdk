"""Integration tests for getProfile."""

from __future__ import annotations

from gmail_sdk import GmailClient


class TestGetProfile:
    def test_returns_email_address(self, client: GmailClient):
        profile = client.get_profile()
        assert "emailAddress" in profile
        assert "@" in profile["emailAddress"]

    def test_returns_message_counts(self, client: GmailClient):
        profile = client.get_profile()
        assert "messagesTotal" in profile
        assert "threadsTotal" in profile
        assert isinstance(profile["messagesTotal"], int)
