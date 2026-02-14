"""Convenience methods that combine multiple API calls."""

from __future__ import annotations

from typing import Any

from .mime_utils import build_reply_message, build_forward_message


def _get_header(headers: list[dict[str, str]], name: str) -> str:
    """Extract a header value from a Gmail message headers list."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


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
        original = self.get_message(message_id, format_="metadata", metadata_headers=["From", "Subject", "Message-ID", "References"])
        headers = original.get("payload", {}).get("headers", [])

        to = _get_header(headers, "From")
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

    def archive(self, message_id: str) -> dict[str, Any]:
        """Archive a message (remove INBOX label).

        Args:
            message_id: The message ID.

        Returns:
            Modified message resource.
        """
        return self.modify_message(message_id, remove_label_ids=["INBOX"])

    @staticmethod
    def _extract_body(payload: dict[str, Any]) -> str | None:
        """Extract plain text body from a Gmail message payload.

        Recursively traverses nested multipart structures to find the first
        text/plain part. Returns None if no text/plain part is found.
        """
        import base64

        # Simple single-part message
        if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Multipart — recurse into parts
        for part in payload.get("parts", []):
            result = ConvenienceMixin._extract_body(part)
            if result is not None:
                return result

        return None
