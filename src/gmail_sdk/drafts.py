"""Draft operations."""

from __future__ import annotations

from typing import Any

from .mime_utils import build_simple_message


class DraftsMixin:
    """Mixin providing draft API methods."""

    def list_drafts(
        self,
        max_results: int = 10,
        page_token: str | None = None,
        query: str | None = None,
        include_spam_trash: bool = False,
    ) -> dict[str, Any]:
        """GET /users/me/drafts — List drafts.

        Args:
            max_results: Maximum number of drafts to return.
            page_token: Pagination token.
            query: Gmail search query.
            include_spam_trash: Include spam and trash drafts.

        Returns:
            {"drafts": [...], "nextPageToken": "...", "resultSizeEstimate": ...}

            Note: The "drafts" key is absent when no results match the query.
        """
        params: dict[str, Any] = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token
        if query:
            params["q"] = query
        if include_spam_trash:
            params["includeSpamTrash"] = True
        return self._get("/users/me/drafts", params=params)

    def get_draft(
        self,
        draft_id: str,
        format_: str = "full",
    ) -> dict[str, Any]:
        """GET /users/me/drafts/{id} — Get a specific draft.

        Args:
            draft_id: The draft ID.
            format_: Response format: full, metadata, minimal, or raw.

        Returns:
            Draft resource with message.
        """
        return self._get(f"/users/me/drafts/{draft_id}", params={"format": format_})

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/drafts — Create a new draft.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Plain text body.
            from_addr: Sender address (optional, Gmail defaults to authenticated user).
            cc: CC address.
            bcc: BCC address.
            thread_id: Thread ID to attach draft to.

        Returns:
            Created draft resource.
        """
        raw = build_simple_message(to=to, subject=subject, body=body, from_addr=from_addr, cc=cc, bcc=bcc)
        message: dict[str, Any] = {"raw": raw}
        if thread_id:
            message["threadId"] = thread_id
        return self._post("/users/me/drafts", json={"message": message})

    def create_raw_draft(
        self,
        raw: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/drafts — Create a draft from a pre-encoded message.

        Args:
            raw: Base64url-encoded MIME message.
            thread_id: Thread ID to attach draft to.

        Returns:
            Created draft resource.
        """
        message: dict[str, Any] = {"raw": raw}
        if thread_id:
            message["threadId"] = thread_id
        return self._post("/users/me/drafts", json={"message": message})

    def send_draft(self, draft_id: str) -> dict[str, Any]:
        """POST /users/me/drafts/send — Send an existing draft.

        Args:
            draft_id: The draft ID.

        Returns:
            Sent message resource.
        """
        return self._post("/users/me/drafts/send", json={"id": draft_id})

    def delete_draft(self, draft_id: str) -> int:
        """DELETE /users/me/drafts/{id} — Permanently delete a draft.

        Args:
            draft_id: The draft ID.

        Returns:
            HTTP status code (204 on success).
        """
        return self._delete(f"/users/me/drafts/{draft_id}")
