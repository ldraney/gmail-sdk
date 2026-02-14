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
