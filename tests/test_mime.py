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


def _b64url_decode(data: str) -> bytes:
    """Decode base64url with missing padding."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


class TestBuildSimpleMessage:
    def test_basic_message(self):
        raw = build_simple_message(to="test@example.com", subject="Hello", body="Hi there")
        # Should be valid base64url
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
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
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        payload = msg.get_payload(decode=True).decode()
        assert "Original content" in payload


class TestBuildSimpleMessageHTML:
    def test_html_creates_multipart_alternative(self):
        raw = build_simple_message(
            to="test@example.com",
            subject="HTML Test",
            body="Plain version",
            html_body="<b>HTML version</b>",
        )
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg.get_content_type() == "multipart/alternative"
        parts = msg.get_payload()
        assert len(parts) == 2
        assert parts[0].get_content_type() == "text/plain"
        assert "Plain version" in parts[0].get_payload(decode=True).decode()
        assert parts[1].get_content_type() == "text/html"
        assert "<b>HTML version</b>" in parts[1].get_payload(decode=True).decode()

    def test_plain_only_still_works(self):
        raw = build_simple_message(to="test@example.com", subject="Plain", body="Just plain")
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg.get_content_type() == "text/plain"
        assert "Just plain" in msg.get_payload(decode=True).decode()

    def test_html_message_has_headers(self):
        raw = build_simple_message(
            to="to@example.com",
            subject="HTML",
            body="plain",
            html_body="<p>html</p>",
            cc="cc@example.com",
            from_addr="sender@example.com",
        )
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["To"] == "to@example.com"
        assert msg["Subject"] == "HTML"
        assert msg["Cc"] == "cc@example.com"
        assert msg["From"] == "sender@example.com"


class TestBuildReplyMessageHTML:
    def test_reply_html_has_both_parts_and_threading(self):
        raw = build_reply_message(
            to="original@example.com",
            subject="Re: Hello",
            body="Thanks!",
            message_id="<abc@example.com>",
            html_body="<b>Thanks!</b>",
        )
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg.get_content_type() == "multipart/alternative"
        assert msg["In-Reply-To"] == "<abc@example.com>"
        parts = msg.get_payload()
        assert len(parts) == 2

    def test_reply_with_cc(self):
        raw = build_reply_message(
            to="to@example.com",
            subject="Re: Test",
            body="body",
            message_id="<id@example.com>",
            cc="cc@example.com",
        )
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg["Cc"] == "cc@example.com"


class TestBuildForwardMessageHTML:
    def test_forward_html_has_both_parts(self):
        raw = build_forward_message(
            to="fwd@example.com",
            subject="Fwd: Hello",
            original_body="Original",
            html_body="<p>Forwarded HTML</p>",
        )
        decoded = _b64url_decode(raw)
        msg = message_from_bytes(decoded)
        assert msg.get_content_type() == "multipart/alternative"
        parts = msg.get_payload()
        assert len(parts) == 2
        plain = parts[0].get_payload(decode=True).decode()
        assert "Original" in plain
        html = parts[1].get_payload(decode=True).decode()
        assert "<p>Forwarded HTML</p>" in html


class TestEncodeMessage:
    def test_base64url_encoding(self):
        from email.mime.text import MIMEText
        msg = MIMEText("test body")
        msg["To"] = "test@example.com"
        msg["Subject"] = "Test"
        encoded = encode_message(msg)
        # Should not contain trailing padding
        assert not encoded.endswith("=")
        # Should decode without errors
        decoded = _b64url_decode(encoded)
        assert b"test body" in decoded
