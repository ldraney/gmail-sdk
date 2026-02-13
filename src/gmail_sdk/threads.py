"""Thread operations."""

from __future__ import annotations

from typing import Any


class ThreadsMixin:
    """Mixin providing thread API methods."""

    def list_threads(
        self,
        query: str | None = None,
        max_results: int = 10,
        label_ids: list[str] | None = None,
        page_token: str | None = None,
        include_spam_trash: bool = False,
    ) -> dict[str, Any]:
        """GET /users/me/threads — List threads.

        Args:
            query: Gmail search query.
            max_results: Maximum number of threads to return.
            label_ids: Filter by label IDs.
            page_token: Pagination token.
            include_spam_trash: Include spam and trash.

        Returns:
            {"threads": [...], "nextPageToken": "...", "resultSizeEstimate": ...}
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
        return self._get("/users/me/threads", params=params)

    def get_thread(
        self,
        thread_id: str,
        format_: str = "full",
        metadata_headers: list[str] | None = None,
    ) -> dict[str, Any]:
        """GET /users/me/threads/{id} — Get a specific thread.

        Args:
            thread_id: The thread ID.
            format_: Response format: full, metadata, or minimal.
            metadata_headers: Headers to include when format=metadata.

        Returns:
            Full thread resource with messages.
        """
        params: dict[str, Any] = {"format": format_}
        if metadata_headers:
            params["metadataHeaders"] = metadata_headers
        return self._get(f"/users/me/threads/{thread_id}", params=params)

    def modify_thread(
        self,
        thread_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """POST /users/me/threads/{id}/modify — Modify thread labels.

        Args:
            thread_id: The thread ID.
            add_label_ids: Labels to add.
            remove_label_ids: Labels to remove.

        Returns:
            Modified thread resource.
        """
        payload: dict[str, Any] = {}
        if add_label_ids:
            payload["addLabelIds"] = add_label_ids
        if remove_label_ids:
            payload["removeLabelIds"] = remove_label_ids
        resp = self._post(f"/users/me/threads/{thread_id}/modify", json=payload)
        return resp.json() if resp.content else {}

    def trash_thread(self, thread_id: str) -> dict[str, Any]:
        """POST /users/me/threads/{id}/trash — Move thread to trash.

        Args:
            thread_id: The thread ID.

        Returns:
            Trashed thread resource.
        """
        resp = self._post(f"/users/me/threads/{thread_id}/trash")
        return resp.json() if resp.content else {}

    def untrash_thread(self, thread_id: str) -> dict[str, Any]:
        """POST /users/me/threads/{id}/untrash — Remove thread from trash.

        Args:
            thread_id: The thread ID.

        Returns:
            Untrashed thread resource.
        """
        resp = self._post(f"/users/me/threads/{thread_id}/untrash")
        return resp.json() if resp.content else {}

    def delete_thread(self, thread_id: str) -> int:
        """DELETE /users/me/threads/{id} — Permanently delete a thread.

        Args:
            thread_id: The thread ID.

        Returns:
            HTTP status code (204 on success).
        """
        return self._delete(f"/users/me/threads/{thread_id}")
