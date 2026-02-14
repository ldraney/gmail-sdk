"""Unit tests for GmailClient core HTTP helpers."""

from __future__ import annotations

import json

import httpx
import pytest

from gmail_sdk import GmailClient, GmailAPIError


def _make_transport(
    status_code: int = 200,
    body: dict | None = None,
    content: bytes | None = None,
) -> httpx.MockTransport:
    """Build an httpx MockTransport that returns a fixed response."""

    def _handler(request: httpx.Request) -> httpx.Response:
        if content is not None:
            return httpx.Response(status_code, content=content)
        if body is not None:
            return httpx.Response(
                status_code,
                content=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
            )
        return httpx.Response(status_code)

    return httpx.MockTransport(_handler)


def _client_with_transport(transport: httpx.MockTransport, **kwargs) -> GmailClient:
    """Create a GmailClient whose internal httpx.Client uses the given transport."""
    client = GmailClient(**kwargs)
    client._http = httpx.Client(
        base_url="https://gmail.googleapis.com/gmail/v1",
        transport=transport,
        headers=client._http.headers,
    )
    return client


class TestGmailClientAuth:
    """Test that authentication headers are set correctly."""

    def test_access_token_sets_authorization_header(self):
        client = GmailClient(access_token="test-token-xxx")
        assert client._http.headers["Authorization"] == "Bearer test-token-xxx"

    def test_no_args_creates_client_without_auth(self):
        client = GmailClient()
        assert "Authorization" not in client._http.headers


class TestRaiseApiError:
    """Test _raise_api_error raises GmailAPIError with correct status/message."""

    def test_raises_on_4xx(self):
        error_body = {"error": {"message": "Not Found"}}
        resp = httpx.Response(
            404,
            content=json.dumps(error_body).encode(),
            headers={"Content-Type": "application/json"},
            request=httpx.Request("GET", "https://example.com"),
        )
        with pytest.raises(GmailAPIError) as exc_info:
            GmailClient._raise_api_error(resp)
        assert exc_info.value.status_code == 404
        assert exc_info.value.message == "Not Found"

    def test_raises_on_5xx(self):
        resp = httpx.Response(
            500,
            content=b"Internal Server Error",
            request=httpx.Request("GET", "https://example.com"),
        )
        with pytest.raises(GmailAPIError) as exc_info:
            GmailClient._raise_api_error(resp)
        assert exc_info.value.status_code == 500

    def test_no_raise_on_200(self):
        resp = httpx.Response(
            200,
            content=b'{"ok": true}',
            request=httpx.Request("GET", "https://example.com"),
        )
        # Should not raise
        GmailClient._raise_api_error(resp)


class TestGetHelper:
    """Test _get returns parsed JSON."""

    def test_get_returns_parsed_json(self):
        body = {"emailAddress": "test@example.com", "messagesTotal": 42}
        transport = _make_transport(body=body)
        client = _client_with_transport(transport)
        result = client._get("/users/me/profile")
        assert result == body

    def test_get_returns_empty_dict_on_no_content(self):
        transport = _make_transport(status_code=200, content=b"")
        client = _client_with_transport(transport)
        result = client._get("/users/me/profile")
        assert result == {}


class TestPostHelper:
    """Test _post returns parsed JSON (after B1 fix)."""

    def test_post_returns_parsed_json(self):
        body = {"id": "msg-123", "threadId": "thread-456"}
        transport = _make_transport(body=body)
        client = _client_with_transport(transport)
        result = client._post("/users/me/messages/send", json={"raw": "abc"})
        assert result == body

    def test_post_returns_empty_dict_on_no_content(self):
        transport = _make_transport(status_code=204, content=b"")
        client = _client_with_transport(transport)
        result = client._post("/users/me/messages/batchModify", json={"ids": []})
        assert result == {}


class TestDeleteHelper:
    """Test _delete returns status code."""

    def test_delete_returns_status_code(self):
        transport = _make_transport(status_code=204, content=b"")
        client = _client_with_transport(transport)
        result = client._delete("/users/me/messages/msg-123")
        assert result == 204


class TestContextManager:
    """Test context manager calls close."""

    def test_context_manager_closes_http_client(self):
        client = GmailClient()
        assert not client._http.is_closed
        with client:
            pass
        assert client._http.is_closed


class TestRepr:
    """Test __repr__ output."""

    def test_repr_with_account(self):
        client = GmailClient(access_token="xxx")
        client.account = "draneylucas"
        assert repr(client) == "GmailClient(account='draneylucas')"

    def test_repr_without_account(self):
        client = GmailClient()
        assert repr(client) == "GmailClient()"
