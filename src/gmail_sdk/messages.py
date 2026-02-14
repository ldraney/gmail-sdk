"""Message operations."""

from __future__ import annotations

from typing import Any

from .mime_utils import build_simple_message


class MessagesMixin:
    """Mixin providing message API methods."""

    def get_profile(self) -> dict[str, Any]:
        """GET /users/me/profile — Get the authenticated user's profile.

        Returns:
            {"emailAddress": "...", "messagesTotal": ..., "threadsTotal": ..., "historyId": "..."}
        """
        return self._get("/users/me/profile")

    def list_messages(
        self,
        query: str | None = None,
        max_results: int = 10,
        label_ids: list[str] | None = None,
        page_token: str | None = None,
        include_spam_trash: bool = False,
    ) -> dict[str, Any]:
        """GET /users/me/messages — List messages.

        Args:
            query: Gmail search query (e.g. "is:unread").
            max_results: Maximum number of messages to return.
            label_ids: Filter by label IDs.
            page_token: Pagination token.
            include_spam_trash: Include spam and trash messages.

        Returns:
            {"messages": [{"id": "...", "threadId": "..."}], "nextPageToken": "...", "resultSizeEstimate": ...}

            Note: The "messages" key is absent when no results match the query.
        """
        params: dict[str, Any] = {"maxResults": max_results}
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids
        if page_token:
            params["pageToken"] = page_token
        if include_spam_trash:
            params["includeSpamTrash"] = True
        return self._get("/users/me/messages", params=params)

    def get_message(
        self,
        message_id: str,
        format_: str = "full",
        metadata_headers: list[str] | None = None,
    ) -> dict[str, Any]:
        """GET /users/me/messages/{id} — Get a specific message.

        Args:
            message_id: The message ID.
            format_: Response format: full, metadata, minimal, or raw.
            metadata_headers: Headers to include when format=metadata.

        Returns:
            Full message resource.
        """
        params: dict[str, Any] = {"format": format_}
        if metadata_headers:
            params["metadataHeaders"] = metadata_headers
        return self._get(f"/users/me/messages/{message_id}", params=params)

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/messages/send — Send an email.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Plain text body.
            from_addr: Sender address (optional, Gmail defaults to authenticated user).
            cc: CC address.
            bcc: BCC address.
            thread_id: Thread ID to send in (for replies).

        Returns:
            Sent message resource.
        """
        raw = build_simple_message(to=to, subject=subject, body=body, from_addr=from_addr, cc=cc, bcc=bcc)
        payload: dict[str, Any] = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return self._post("/users/me/messages/send", json=payload)

    def send_raw_message(
        self,
        raw: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/messages/send — Send a pre-encoded raw message.

        Args:
            raw: Base64url-encoded MIME message.
            thread_id: Thread ID to send in.

        Returns:
            Sent message resource.
        """
        payload: dict[str, Any] = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return self._post("/users/me/messages/send", json=payload)

    def modify_message(
        self,
        message_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/messages/{id}/modify — Modify message labels.

        Args:
            message_id: The message ID.
            add_label_ids: Labels to add.
            remove_label_ids: Labels to remove.

        Returns:
            Modified message resource.
        """
        payload: dict[str, Any] = {}
        if add_label_ids is not None:
            payload["addLabelIds"] = add_label_ids
        if remove_label_ids is not None:
            payload["removeLabelIds"] = remove_label_ids
        return self._post(f"/users/me/messages/{message_id}/modify", json=payload)

    def trash_message(self, message_id: str) -> dict[str, Any]:
        """POST /users/me/messages/{id}/trash — Move message to trash.

        Args:
            message_id: The message ID.

        Returns:
            Trashed message resource.
        """
        return self._post(f"/users/me/messages/{message_id}/trash")

    def untrash_message(self, message_id: str) -> dict[str, Any]:
        """POST /users/me/messages/{id}/untrash — Remove message from trash.

        Args:
            message_id: The message ID.

        Returns:
            Untrashed message resource.
        """
        return self._post(f"/users/me/messages/{message_id}/untrash")

    def delete_message(self, message_id: str) -> int:
        """DELETE /users/me/messages/{id} — Permanently delete a message.

        Args:
            message_id: The message ID.

        Returns:
            HTTP status code (204 on success).
        """
        return self._delete(f"/users/me/messages/{message_id}")

    def batch_modify_messages(
        self,
        message_ids: list[str],
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> None:
        """POST /users/me/messages/batchModify — Modify labels on multiple messages.

        Args:
            message_ids: List of message IDs.
            add_label_ids: Labels to add.
            remove_label_ids: Labels to remove.
        """
        payload: dict[str, Any] = {"ids": message_ids}
        if add_label_ids is not None:
            payload["addLabelIds"] = add_label_ids
        if remove_label_ids is not None:
            payload["removeLabelIds"] = remove_label_ids
        self._post("/users/me/messages/batchModify", json=payload)
