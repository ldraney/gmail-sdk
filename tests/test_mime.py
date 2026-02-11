"""Unit tests for MIME utilities."""

from __future__ import annotations

import base64
from email import message_from_bytes

from gmail_sdk.mime_utils import (
    build_simple_message,
    build_reply_message,
    build_forward_message,
    encode_message,
)


class TestBuildSimpleMessage:
    def test_basic_message(self):
        raw = build_simple_message(to="test@example.com", subject="Hello", body="Hi there")
        # Should be valid base64url
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["To"] == "test@example.com"
        assert msg["Subject"] == "Hello"
        assert "Hi there" in msg.get_payload(decode=True).decode()

    def test_with_cc_and_bcc(self):
        raw = build_simple_message(
            to="to@example.com",
            subject="Test",
            body="body",
            cc="cc@example.com",
            bcc="bcc@example.com",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["Cc"] == "cc@example.com"
        assert msg["Bcc"] == "bcc@example.com"

    def test_with_from(self):
        raw = build_simple_message(
            to="to@example.com",
            subject="Test",
            body="body",
            from_addr="sender@example.com",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["From"] == "sender@example.com"


class TestBuildReplyMessage:
    def test_reply_has_threading_headers(self):
        raw = build_reply_message(
            to="original@example.com",
            subject="Re: Hello",
            body="Thanks!",
            message_id="<abc123@example.com>",
            references="<abc123@example.com>",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["In-Reply-To"] == "<abc123@example.com>"
        assert msg["References"] == "<abc123@example.com>"

    def test_reply_defaults_references_to_message_id(self):
        raw = build_reply_message(
            to="original@example.com",
            subject="Re: Hello",
            body="Thanks!",
            message_id="<abc123@example.com>",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["References"] == "<abc123@example.com>"


class TestBuildForwardMessage:
    def test_forward_includes_original(self):
        raw = build_forward_message(
            to="fwd@example.com",
            subject="Fwd: Hello",
            original_body="Original content here",
            note="FYI",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        payload = msg.get_payload(decode=True).decode()
        assert "Original content here" in payload
        assert "FYI" in payload
        assert "Forwarded message" in payload

    def test_forward_without_note(self):
        raw = build_forward_message(
            to="fwd@example.com",
            subject="Fwd: Hello",
            original_body="Original content",
        )
        decoded = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(decoded)
        payload = msg.get_payload(decode=True).decode()
        assert "Original content" in payload


class TestEncodeMessage:
    def test_base64url_encoding(self):
        from email.mime.text import MIMEText
        msg = MIMEText("test body")
        msg["To"] = "test@example.com"
        msg["Subject"] = "Test"
        encoded = encode_message(msg)
        # Should decode without errors
        decoded = base64.urlsafe_b64decode(encoded)
        assert b"test body" in decoded
