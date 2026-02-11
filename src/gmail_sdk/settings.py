"""Settings operations."""

from __future__ import annotations

from typing import Any


class SettingsMixin:
    """Mixin providing settings API methods."""

    def get_vacation_settings(self) -> dict[str, Any]:
        """GET /users/me/settings/vacation — Get vacation responder settings.

        Returns:
            Vacation settings resource.
        """
        return self._get("/users/me/settings/vacation")

    def update_vacation_settings(
        self,
        enable_auto_reply: bool,
        response_subject: str | None = None,
        response_body_plain_text: str | None = None,
        response_body_html: str | None = None,
        restrict_to_contacts: bool = False,
        restrict_to_domain: bool = False,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        """PUT /users/me/settings/vacation — Update vacation responder.

        Args:
            enable_auto_reply: Whether to enable auto-reply.
            response_subject: Auto-reply subject.
            response_body_plain_text: Plain text auto-reply body.
            response_body_html: HTML auto-reply body.
            restrict_to_contacts: Only reply to contacts.
            restrict_to_domain: Only reply to same domain.
            start_time: Start time in milliseconds since epoch.
            end_time: End time in milliseconds since epoch.

        Returns:
            Updated vacation settings resource.
        """
        payload: dict[str, Any] = {
            "enableAutoReply": enable_auto_reply,
            "restrictToContacts": restrict_to_contacts,
            "restrictToDomain": restrict_to_domain,
        }
        if response_subject is not None:
            payload["responseSubject"] = response_subject
        if response_body_plain_text is not None:
            payload["responseBodyPlainText"] = response_body_plain_text
        if response_body_html is not None:
            payload["responseBodyHtml"] = response_body_html
        if start_time is not None:
            payload["startTime"] = start_time
        if end_time is not None:
            payload["endTime"] = end_time
        return self._put("/users/me/settings/vacation", json=payload)
