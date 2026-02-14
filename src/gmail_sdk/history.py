"""History operations."""

from __future__ import annotations

from typing import Any


class HistoryMixin:
    """Mixin providing mailbox history API methods."""

    def list_history(
        self,
        start_history_id: str,
        label_id: str | None = None,
        max_results: int = 100,
        page_token: str | None = None,
        history_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """GET /users/me/history — List history of mailbox changes.

        Returns changes since the given history ID. Useful for incremental sync
        and change detection.

        Args:
            start_history_id: History ID to start listing from (e.g. from get_profile()).
            label_id: Only return history for this label.
            max_results: Maximum number of history records to return.
            page_token: Pagination token.
            history_types: Filter by history type(s). Valid values:
                "messageAdded", "messageDeleted", "labelAdded", "labelRemoved".

        Returns:
            {"history": [...], "nextPageToken": "...", "historyId": "..."}

            Note: The "history" key is absent when no changes exist since start_history_id.
        """
        params: dict[str, Any] = {
            "startHistoryId": start_history_id,
            "maxResults": max_results,
        }
        if label_id:
            params["labelId"] = label_id
        if page_token:
            params["pageToken"] = page_token
        if history_types:
            params["historyTypes"] = history_types
        return self._get("/users/me/history", params=params)
