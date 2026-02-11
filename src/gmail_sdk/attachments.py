"""Attachment operations."""

from __future__ import annotations

from typing import Any


class AttachmentsMixin:
    """Mixin providing attachment API methods."""

    def get_attachment(self, message_id: str, attachment_id: str) -> dict[str, Any]:
        """GET /users/me/messages/{messageId}/attachments/{id} — Get an attachment.

        Args:
            message_id: The message ID.
            attachment_id: The attachment ID.

        Returns:
            {"size": ..., "data": "<base64url-encoded attachment data>"}
        """
        return self._get(
            f"/users/me/messages/{message_id}/attachments/{attachment_id}"
        )
