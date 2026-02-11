"""Filter operations."""

from __future__ import annotations

from typing import Any


class FiltersMixin:
    """Mixin providing filter API methods."""

    def list_filters(self) -> dict[str, Any]:
        """GET /users/me/settings/filters — List all filters.

        Returns:
            {"filter": [{"id": "...", "criteria": {...}, "action": {...}}]}
        """
        return self._get("/users/me/settings/filters")

    def get_filter(self, filter_id: str) -> dict[str, Any]:
        """GET /users/me/settings/filters/{id} — Get a specific filter.

        Args:
            filter_id: The filter ID.

        Returns:
            Filter resource.
        """
        return self._get(f"/users/me/settings/filters/{filter_id}")

    def create_filter(
        self,
        criteria: dict[str, Any],
        action: dict[str, Any],
    ) -> dict[str, Any]:
        """POST /users/me/settings/filters — Create a new filter.

        Args:
            criteria: Filter criteria (from, to, subject, query, etc).
            action: Filter action (addLabelIds, removeLabelIds, forward, etc).

        Returns:
            Created filter resource.
        """
        resp = self._post(
            "/users/me/settings/filters",
            json={"criteria": criteria, "action": action},
        )
        return resp.json() if resp.text.strip() else {}

    def delete_filter(self, filter_id: str) -> int:
        """DELETE /users/me/settings/filters/{id} — Delete a filter.

        Args:
            filter_id: The filter ID.

        Returns:
            HTTP status code (204 on success).
        """
        return self._delete(f"/users/me/settings/filters/{filter_id}")
