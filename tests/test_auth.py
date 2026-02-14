"""Unit tests for auth module."""

from __future__ import annotations

from gmail_sdk.auth import AuthMixin, REDIRECT_URI, SCOPES


class TestGetAuthUrl:
    def test_builds_url_with_defaults(self):
        url = AuthMixin.get_auth_url(client_id="test-client-id")
        assert "accounts.google.com" in url
        assert "test-client-id" in url
        assert "offline" in url
        assert "consent" in url

    def test_includes_redirect_uri(self):
        url = AuthMixin.get_auth_url(client_id="test-client-id")
        assert "localhost%3A8090" in url or "localhost:8090" in url

    def test_custom_scopes(self):
        url = AuthMixin.get_auth_url(
            client_id="test-client-id",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
        assert "gmail.readonly" in url

    def test_custom_redirect_uri(self):
        url = AuthMixin.get_auth_url(
            client_id="test-client-id",
            redirect_uri="http://localhost:9999",
        )
        assert "9999" in url


class TestTokenPathResolution:
    def test_load_token_returns_none_for_missing(self, tmp_path):
        result = AuthMixin._load_token("nonexistent", str(tmp_path))
        assert result is None

    def test_save_and_load_roundtrip(self, tmp_path):
        token_data = {"access_token": "test123", "expires_at": 9999999999}
        AuthMixin._save_token("testaccount", str(tmp_path), token_data)
        loaded = AuthMixin._load_token("testaccount", str(tmp_path))
        assert loaded is not None
        assert loaded["access_token"] == "test123"

    def test_saved_token_has_restricted_permissions(self, tmp_path):
        import stat
        token_data = {"access_token": "test123"}
        AuthMixin._save_token("testaccount", str(tmp_path), token_data)
        token_path = tmp_path / "gmail-testaccount.json"
        mode = token_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600
