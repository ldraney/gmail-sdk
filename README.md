[![PyPI](https://img.shields.io/pypi/v/gmail-sdk-ldraney)](https://pypi.org/project/gmail-sdk-ldraney/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

# gmail-sdk

Python SDK for the Gmail REST API. Uses `httpx` directly — no `google-api-python-client`.

## Install

```bash
pip install ldraney-gmail-sdk
```

## Quick Start

```python
from gmail_sdk import GmailClient

# Load token from ~/secrets/google-oauth/gmail-draneylucas.json
client = GmailClient(account="draneylucas")
print(client.get_profile())

# List unread messages
messages = client.list_messages(query="is:unread", max_results=5)

# Send an email
client.send_message(to="someone@example.com", subject="Hello", body="Hi there!")

# Reply to a message
client.reply(message_id="abc123", body="Thanks!")

# Send an HTML email
client.send_message(
    to="someone@example.com",
    subject="Hello",
    body="Plain text fallback",
    html_body="<h1>Hello!</h1><p>This is <b>HTML</b>.</p>",
)

# Reply-all, mark as read/unread
client.reply_all(message_id="abc123", body="Thanks everyone!")
client.mark_as_read(message_id="abc123")
client.mark_as_unread(message_id="abc123")

# List mailbox changes since a history ID (for incremental sync)
profile = client.get_profile()
changes = client.list_history(start_history_id=profile["historyId"])
```

## First-Time Setup

Run the OAuth flow to authorize an account:

```python
from gmail_sdk import GmailClient

client = GmailClient.authorize(account="draneylucas")
print(client.get_profile())
```

This opens a browser for Google sign-in and saves the token for future use.

## Multi-Account

```python
personal = GmailClient(account="draneylucas")
work = GmailClient(account="lucastoddraney")
dev = GmailClient(account="devopsphilosopher")
```

## Configuration

- Secrets directory: `~/secrets/google-oauth/` (override with `secrets_dir=` or `GMAIL_SECRETS_DIR` env var)
- Credentials file: `{secrets_dir}/credentials.json`
- Token files: `{secrets_dir}/gmail-{account}.json`
