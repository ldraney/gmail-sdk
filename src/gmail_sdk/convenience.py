"""Convenience methods that combine multiple API calls."""

from __future__ import annotations

from email.utils import getaddresses, parseaddr
from typing import Any

from .mime_utils import build_reply_message, build_forward_message


def _get_header(headers: list[dict[str, str]], name: str) -> str:
    """Extract a header value from a Gmail message headers list."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_email(addr: str) -> str:
    """Extract the bare email address from a potentially display-name-wrapped address.

    Handles formats like:
        "alice@example.com" -> "alice@example.com"
        "Alice Smith <alice@example.com>" -> "alice@example.com"
        "<alice@example.com>" -> "alice@example.com"
    """
    _, email = parseaddr(addr)
    return email.lower()


class ConvenienceMixin:
    """Mixin providing high-level convenience methods."""

    def reply(
        self,
        message_id: str,
        body: str,
    ) -> dict[str, Any]:
        """Reply to a message in its thread.

        Fetches the original message headers, builds a properly threaded reply,
        and sends it.

        Args:
            message_id: The message ID to reply to.
            body: Plain text reply body.

        Returns:
            Sent message resource.
        """
        original = self.get_message(message_id, format_="metadata", metadata_headers=["From", "Subject", "Message-ID", "References", "Reply-To"])
        headers = original.get("payload", {}).get("headers", [])

        to = _get_header(headers, "Reply-To") or _get_header(headers, "From")
        subject = _get_header(headers, "Subject")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        orig_message_id = _get_header(headers, "Message-ID")
        references = _get_header(headers, "References")

        raw = build_reply_message(
            to=to,
            subject=subject,
            body=body,
            message_id=orig_message_id,
            references=references,
        )
        return self.send_raw_message(raw=raw, thread_id=original["threadId"])

    def forward(
        self,
        message_id: str,
        to: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Forward a message to another recipient.

        Fetches the original message, extracts the body, and sends a forward.

        Args:
            message_id: The message ID to forward.
            to: Recipient email address.
            note: Optional note to prepend.

        Returns:
            Sent message resource.
        """
        original = self.get_message(message_id, format_="full")
        headers = original.get("payload", {}).get("headers", [])

        subject = _get_header(headers, "Subject")
        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"

        # Extract body from payload
        original_body = self._extract_body(original.get("payload", {})) or "(no text body found)"

        raw = build_forward_message(
            to=to,
            subject=subject,
            original_body=original_body,
            note=note,
        )
        return self.send_raw_message(raw=raw)

    def reply_all(
        self,
        message_id: str,
        body: str,
    ) -> dict[str, Any]:
        """Reply-all to a message in its thread.

        Fetches the original message headers, collects all recipients (To, Cc)
        excluding the authenticated user, builds a properly threaded reply, and sends it.

        Args:
            message_id: The message ID to reply to.
            body: Plain text reply body.

        Returns:
            Sent message resource.
        """
        original = self.get_message(
            message_id,
            format_="metadata",
            metadata_headers=["From", "To", "Cc", "Subject", "Message-ID", "References", "Reply-To"],
        )
        headers = original.get("payload", {}).get("headers", [])

        reply_to = _get_header(headers, "Reply-To") or _get_header(headers, "From")
        orig_from = _get_header(headers, "From")
        orig_to = _get_header(headers, "To")
        orig_cc = _get_header(headers, "Cc")
        subject = _get_header(headers, "Subject")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        orig_message_id = _get_header(headers, "Message-ID")
        references = _get_header(headers, "References")

        # Get own email to exclude from recipients
        my_email = self.get_profile()["emailAddress"].lower()

        # Collect all recipients: reply-to/from goes in To, everyone else in Cc
        # Use _extract_email to handle display names like "Alice <alice@example.com>"
        seen_emails = set()
        to_addr = reply_to
        seen_emails.add(_extract_email(to_addr))

        cc_addrs = []
        all_headers = [h for h in [orig_from, orig_to, orig_cc] if h]
        for display_name, email_addr in getaddresses(all_headers):
            bare = email_addr.lower()
            if bare and bare not in seen_emails and bare != my_email:
                # Preserve display name if present
                full = f"{display_name} <{email_addr}>" if display_name else email_addr
                cc_addrs.append(full)
                seen_emails.add(bare)

        raw = build_reply_message(
            to=to_addr,
            subject=subject,
            body=body,
            message_id=orig_message_id,
            references=references,
            cc=", ".join(cc_addrs) if cc_addrs else None,
        )
        return self.send_raw_message(raw=raw, thread_id=original["threadId"])

    def mark_as_read(self, message_id: str) -> dict[str, Any]:
        """Mark a message as read (remove UNREAD label).

        Args:
            message_id: The message ID.

        Returns:
            Modified message resource.
        """
        return self.modify_message(message_id, remove_label_ids=["UNREAD"])

    def mark_as_unread(self, message_id: str) -> dict[str, Any]:
        """Mark a message as unread (add UNREAD label).

        Args:
            message_id: The message ID.

        Returns:
            Modified message resource.
        """
        return self.modify_message(message_id, add_label_ids=["UNREAD"])

    def archive(self, message_id: str) -> dict[str, Any]:
        """Archive a message (remove INBOX label).

        Args:
            message_id: The message ID.

        Returns:
            Modified message resource.
        """
        return self.modify_message(message_id, remove_label_ids=["INBOX"])

    @staticmethod
    def _extract_body(payload: dict[str, Any], mime_type: str = "text/plain") -> str | None:
        """Extract body from a Gmail message payload by MIME type.

        Recursively traverses nested multipart structures to find the first
        part matching the given MIME type. Returns None if no match is found.

        Args:
            payload: Gmail message payload dict.
            mime_type: MIME type to extract (default: "text/plain"). Use
                "text/html" to get the HTML body.
        """
        import base64

        # Simple single-part message
        if payload.get("mimeType") == mime_type and "data" in payload.get("body", {}):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Multipart — recurse into parts
        for part in payload.get("parts", []):
            result = ConvenienceMixin._extract_body(part, mime_type=mime_type)
            if result is not None:
                return result

        return None
