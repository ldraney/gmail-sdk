"""MIME message construction utilities."""

from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def encode_message(mime_msg: MIMEText | MIMEMultipart) -> str:
    """Base64url-encode a MIME message for the Gmail API."""
    raw = mime_msg.as_bytes()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def build_simple_message(
    to: str,
    subject: str,
    body: str,
    from_addr: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    html_body: str | None = None,
) -> str:
    """Build a simple email message and return base64url-encoded string.

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Plain text body.
        from_addr: Sender address (optional, Gmail defaults to authenticated user).
        cc: CC address.
        bcc: BCC address.
        html_body: Optional HTML body. When provided, creates a multipart/alternative
            message with both plain text and HTML parts.

    Returns:
        Base64url-encoded MIME message string.
    """
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
    else:
        msg = MIMEText(body)
    msg["To"] = to
    msg["Subject"] = subject
    if from_addr:
        msg["From"] = from_addr
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    return encode_message(msg)


def build_reply_message(
    to: str,
    subject: str,
    body: str,
    message_id: str,
    references: str | None = None,
    from_addr: str | None = None,
    cc: str | None = None,
    html_body: str | None = None,
) -> str:
    """Build a reply message with proper threading headers.

    Args:
        to: Recipient email address.
        subject: Email subject (should include Re: prefix).
        body: Plain text body.
        message_id: Message-ID of the message being replied to.
        references: References header value for threading.
        from_addr: Sender address.
        cc: CC address.
        html_body: Optional HTML body.

    Returns:
        Base64url-encoded MIME message string.
    """
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
    else:
        msg = MIMEText(body)
    msg["To"] = to
    msg["Subject"] = subject
    msg["In-Reply-To"] = message_id
    msg["References"] = references or message_id
    if from_addr:
        msg["From"] = from_addr
    if cc:
        msg["Cc"] = cc
    return encode_message(msg)


def build_forward_message(
    to: str,
    subject: str,
    original_body: str,
    note: str | None = None,
    from_addr: str | None = None,
    html_body: str | None = None,
) -> str:
    """Build a forward message.

    Args:
        to: Recipient email address.
        subject: Email subject (should include Fwd: prefix).
        original_body: The original message body to forward.
        note: Optional note to prepend.
        from_addr: Sender address.
        html_body: Optional HTML body. When provided, creates a multipart/alternative
            message. The plain text body is still built from original_body and note.

    Returns:
        Base64url-encoded MIME message string.
    """
    parts = []
    if note:
        parts.append(note)
    parts.append(f"\n---------- Forwarded message ----------\n{original_body}")
    full_body = "\n".join(parts)

    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(full_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
    else:
        msg = MIMEText(full_body)
    msg["To"] = to
    msg["Subject"] = subject
    if from_addr:
        msg["From"] = from_addr
    return encode_message(msg)
