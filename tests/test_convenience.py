"""Unit tests for convenience methods."""

from __future__ import annotations

import base64

from gmail_sdk.convenience import ConvenienceMixin, _get_header


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
