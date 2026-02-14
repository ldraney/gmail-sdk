"""Unit tests for convenience methods."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch, call

from gmail_sdk.convenience import ConvenienceMixin, _get_header, _extract_email


class TestGetHeader:
    def test_finds_header_case_insensitive(self):
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "Subject", "value": "Hello"},
        ]
        assert _get_header(headers, "from") == "alice@example.com"
        assert _get_header(headers, "FROM") == "alice@example.com"
        assert _get_header(headers, "Subject") == "Hello"

    def test_returns_empty_string_for_missing(self):
        headers = [{"name": "From", "value": "alice@example.com"}]
        assert _get_header(headers, "To") == ""

    def test_empty_headers_list(self):
        assert _get_header([], "From") == ""

    def test_returns_first_match(self):
        headers = [
            {"name": "X-Custom", "value": "first"},
            {"name": "X-Custom", "value": "second"},
        ]
        assert _get_header(headers, "X-Custom") == "first"


class TestExtractBody:
    def _encode(self, text: str) -> str:
        return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")

    def test_simple_text_plain(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": self._encode("Hello world")},
        }
        assert ConvenienceMixin._extract_body(payload) == "Hello world"

    def test_single_level_multipart(self):
        payload = {
            "mimeType": "multipart/alternative",
            "body": {},
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": self._encode("Plain text body")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": self._encode("<p>HTML body</p>")},
                },
            ],
        }
        assert ConvenienceMixin._extract_body(payload) == "Plain text body"

    def test_nested_multipart(self):
        payload = {
            "mimeType": "multipart/mixed",
            "body": {},
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "body": {},
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": self._encode("Nested plain text")},
                        },
                        {
                            "mimeType": "text/html",
                            "body": {"data": self._encode("<p>Nested HTML</p>")},
                        },
                    ],
                },
                {
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "abc123"},
                },
            ],
        }
        assert ConvenienceMixin._extract_body(payload) == "Nested plain text"

    def test_deeply_nested_multipart(self):
        payload = {
            "mimeType": "multipart/mixed",
            "body": {},
            "parts": [
                {
                    "mimeType": "multipart/related",
                    "body": {},
                    "parts": [
                        {
                            "mimeType": "multipart/alternative",
                            "body": {},
                            "parts": [
                                {
                                    "mimeType": "text/plain",
                                    "body": {"data": self._encode("Deep text")},
                                },
                            ],
                        },
                    ],
                },
            ],
        }
        assert ConvenienceMixin._extract_body(payload) == "Deep text"

    def test_no_text_body(self):
        payload = {
            "mimeType": "multipart/mixed",
            "body": {},
            "parts": [
                {
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "abc123"},
                },
            ],
        }
        assert ConvenienceMixin._extract_body(payload) is None

    def test_empty_payload(self):
        assert ConvenienceMixin._extract_body({}) is None

    def test_extract_html_body(self):
        payload = {
            "mimeType": "multipart/alternative",
            "body": {},
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": self._encode("Plain text")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": self._encode("<p>HTML body</p>")},
                },
            ],
        }
        assert ConvenienceMixin._extract_body(payload, mime_type="text/html") == "<p>HTML body</p>"

    def test_extract_html_returns_none_when_missing(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": self._encode("Only plain")},
        }
        assert ConvenienceMixin._extract_body(payload, mime_type="text/html") is None


class TestExtractEmail:
    def test_bare_email(self):
        assert _extract_email("alice@example.com") == "alice@example.com"

    def test_display_name_with_angle_brackets(self):
        assert _extract_email("Alice Smith <alice@example.com>") == "alice@example.com"

    def test_angle_brackets_only(self):
        assert _extract_email("<alice@example.com>") == "alice@example.com"

    def test_case_insensitive(self):
        assert _extract_email("Alice@Example.COM") == "alice@example.com"

    def test_empty_string(self):
        assert _extract_email("") == ""


class TestMarkAsReadUnread:
    def test_mark_as_read_calls_modify(self):
        mixin = ConvenienceMixin()
        mixin.modify_message = MagicMock(return_value={"id": "msg1"})
        result = mixin.mark_as_read("msg1")
        mixin.modify_message.assert_called_once_with("msg1", remove_label_ids=["UNREAD"])
        assert result == {"id": "msg1"}

    def test_mark_as_unread_calls_modify(self):
        mixin = ConvenienceMixin()
        mixin.modify_message = MagicMock(return_value={"id": "msg1"})
        result = mixin.mark_as_unread("msg1")
        mixin.modify_message.assert_called_once_with("msg1", add_label_ids=["UNREAD"])
        assert result == {"id": "msg1"}


class TestReplyAll:
    def _make_mixin(self, headers, my_email="me@example.com"):
        """Create a ConvenienceMixin with mocked dependencies."""
        mixin = ConvenienceMixin()
        mixin.get_message = MagicMock(return_value={
            "threadId": "thread1",
            "payload": {"headers": headers},
        })
        mixin.get_profile = MagicMock(return_value={"emailAddress": my_email})
        mixin.send_raw_message = MagicMock(return_value={"id": "sent1"})
        return mixin

    def test_excludes_self_with_display_name(self):
        """The key bug fix: self-exclusion must work with display names."""
        headers = [
            {"name": "From", "value": "Alice <alice@example.com>"},
            {"name": "To", "value": "Me <me@example.com>, Bob <bob@example.com>"},
            {"name": "Subject", "value": "Team thread"},
            {"name": "Message-ID", "value": "<id@example.com>"},
        ]
        mixin = self._make_mixin(headers, my_email="me@example.com")
        mixin.reply_all("msg1", body="Thanks!")

        # Verify send_raw_message was called
        mixin.send_raw_message.assert_called_once()
        raw = mixin.send_raw_message.call_args.kwargs["raw"]

        # Decode and check recipients
        from email import message_from_bytes
        padding = 4 - len(raw) % 4
        if padding != 4:
            raw += "=" * padding
        import base64
        msg = message_from_bytes(base64.urlsafe_b64decode(raw))

        # To should be From (alice), Cc should be Bob only (me excluded)
        assert msg["To"] == "Alice <alice@example.com>"
        assert "bob@example.com" in msg["Cc"].lower()
        assert "me@example.com" not in msg["Cc"].lower()

    def test_deduplicates_addresses_with_different_formats(self):
        """Same email with and without display name should not appear twice."""
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "To", "value": "me@example.com, Alice <alice@example.com>"},
            {"name": "Subject", "value": "Test"},
            {"name": "Message-ID", "value": "<id@example.com>"},
        ]
        mixin = self._make_mixin(headers, my_email="me@example.com")
        mixin.reply_all("msg1", body="Reply")

        raw = mixin.send_raw_message.call_args.kwargs["raw"]
        from email import message_from_bytes
        padding = 4 - len(raw) % 4
        if padding != 4:
            raw += "=" * padding
        import base64
        msg = message_from_bytes(base64.urlsafe_b64decode(raw))

        # Alice is already in To, should not also be in Cc
        assert msg["Cc"] is None

    def test_includes_cc_recipients(self):
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "To", "value": "me@example.com"},
            {"name": "Cc", "value": "charlie@example.com, dave@example.com"},
            {"name": "Subject", "value": "Test"},
            {"name": "Message-ID", "value": "<id@example.com>"},
        ]
        mixin = self._make_mixin(headers, my_email="me@example.com")
        mixin.reply_all("msg1", body="Reply")

        raw = mixin.send_raw_message.call_args.kwargs["raw"]
        from email import message_from_bytes
        padding = 4 - len(raw) % 4
        if padding != 4:
            raw += "=" * padding
        import base64
        msg = message_from_bytes(base64.urlsafe_b64decode(raw))

        assert "charlie@example.com" in msg["Cc"]
        assert "dave@example.com" in msg["Cc"]

    def test_handles_comma_in_display_name(self):
        """Commas inside quoted display names must not split the address."""
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "To", "value": '"Doe, John" <john@example.com>, me@example.com'},
            {"name": "Subject", "value": "Test"},
            {"name": "Message-ID", "value": "<id@example.com>"},
        ]
        mixin = self._make_mixin(headers, my_email="me@example.com")
        mixin.reply_all("msg1", body="Reply")

        raw = mixin.send_raw_message.call_args.kwargs["raw"]
        from email import message_from_bytes
        padding = 4 - len(raw) % 4
        if padding != 4:
            raw += "=" * padding
        import base64
        msg = message_from_bytes(base64.urlsafe_b64decode(raw))

        # John should be in Cc with display name preserved, me excluded
        assert "john@example.com" in msg["Cc"].lower()
        assert "Doe" in msg["Cc"]
        assert "me@example.com" not in (msg["Cc"] or "").lower()

    def test_uses_reply_to_when_present(self):
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "Reply-To", "value": "reply@example.com"},
            {"name": "To", "value": "me@example.com"},
            {"name": "Subject", "value": "Test"},
            {"name": "Message-ID", "value": "<id@example.com>"},
        ]
        mixin = self._make_mixin(headers, my_email="me@example.com")
        mixin.reply_all("msg1", body="Reply")

        raw = mixin.send_raw_message.call_args.kwargs["raw"]
        from email import message_from_bytes
        padding = 4 - len(raw) % 4
        if padding != 4:
            raw += "=" * padding
        import base64
        msg = message_from_bytes(base64.urlsafe_b64decode(raw))

        assert msg["To"] == "reply@example.com"
        # alice (From) should be in Cc since Reply-To is different
        assert "alice@example.com" in msg["Cc"]


class TestBatchDeleteMessages:
    def test_calls_correct_endpoint(self):
        mixin = ConvenienceMixin()
        # batch_delete_messages is on MessagesMixin, but we can test via duck typing
        from gmail_sdk.messages import MessagesMixin
        m = MessagesMixin()
        m._post = MagicMock(return_value={})
        m.batch_delete_messages(["msg1", "msg2"])
        m._post.assert_called_once_with(
            "/users/me/messages/batchDelete",
            json={"ids": ["msg1", "msg2"]},
        )
