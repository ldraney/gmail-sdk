# gmail-sdk

Python SDK for the Gmail REST API. Uses httpx directly — no google-api-python-client.

## Structure

- `src/gmail_sdk/` — SDK source (mixin-based client)
- `tests/` — unit + integration tests

## Dev Commands

```bash
uv sync
uv run pytest           # run all tests
uv run pytest -v        # verbose
uv run pytest -k unit   # unit tests only
```

## Architecture

`GmailClient` uses mixin composition (same pattern as linkedin-sdk):
- `AuthMixin` — OAuth flow, token load/save/refresh
- `MessagesMixin` — message CRUD
- `ThreadsMixin` — thread operations
- `DraftsMixin` — draft operations
- `LabelsMixin` — label CRUD
- `AttachmentsMixin` — attachment download
- `FiltersMixin` — filter CRUD
- `SettingsMixin` — vacation/forwarding
- `ConvenienceMixin` — reply, forward, archive

## Secrets

Tokens live in `~/secrets/google-oauth/` (configurable via `GMAIL_SECRETS_DIR` env var or constructor param).
- `credentials.json` — Google OAuth client credentials
- `gmail-{account}.json` — per-account token files

## Testing

Integration tests require a valid token at `~/secrets/google-oauth/gmail-draneylucas.json`.
They auto-skip if the token file doesn't exist.
