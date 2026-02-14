"""Label operations."""

from __future__ import annotations

from typing import Any


class LabelsMixin:
    """Mixin providing label API methods."""

    def list_labels(self) -> dict[str, Any]:
        """GET /users/me/labels — List all labels.

        Returns:
            {"labels": [{"id": "...", "name": "...", "type": "..."}]}
        """
        return self._get("/users/me/labels")

    def get_label(self, label_id: str) -> dict[str, Any]:
        """GET /users/me/labels/{id} — Get a specific label.

        Args:
            label_id: The label ID.

        Returns:
            Label resource.
        """
        return self._get(f"/users/me/labels/{label_id}")

    def create_label(
        self,
        name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show",
    ) -> dict[str, Any]:
        """POST /users/me/labels — Create a new label.

        Args:
            name: Label name.
            label_list_visibility: labelShow, labelShowIfUnread, or labelHide.
            message_list_visibility: show or hide.

        Returns:
            Created label resource.
        """
        return self._post(
            "/users/me/labels",
            json={
                "name": name,
                "labelListVisibility": label_list_visibility,
                "messageListVisibility": message_list_visibility,
            },
        )

    def update_label(
        self,
        label_id: str,
        name: str | None = None,
        label_list_visibility: str | None = None,
        message_list_visibility: str | None = None,
    ) -> dict[str, Any]:
        """Partial update via PATCH /users/me/labels/{id}.

        Only the fields you provide will be changed; omitted fields remain
        unchanged.

        Args:
            label_id: The label ID.
            name: New label name.
            label_list_visibility: labelShow, labelShowIfUnread, or labelHide.
            message_list_visibility: show or hide.

        Returns:
            Updated label resource.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if label_list_visibility is not None:
            payload["labelListVisibility"] = label_list_visibility
        if message_list_visibility is not None:
            payload["messageListVisibility"] = message_list_visibility
        return self._patch(f"/users/me/labels/{label_id}", json=payload)

    def delete_label(self, label_id: str) -> int:
        """DELETE /users/me/labels/{id} — Delete a label.

        Args:
            label_id: The label ID.

        Returns:
            HTTP status code (204 on success).
        """
        return self._delete(f"/users/me/labels/{label_id}")
