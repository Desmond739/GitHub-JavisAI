from __future__ import annotations

from threading import Lock
from typing import Any

from app.core.config import GOOGLE_ACCESS_MODE
from app.core.logging_config import log_event
from app.personal_data.google_calendar_connector import (
    google_calendar_connector,
)
from app.personal_data.google_calendar_incremental_sync import (
    google_calendar_incremental_sync,
)
from app.personal_data.google_contacts_connector import (
    google_contacts_connector,
)
from app.personal_data.google_contacts_sync import (
    google_contacts_sync,
)
from app.personal_data.google_tasks_connector import (
    google_tasks_connector,
)
from app.personal_data.google_tasks_sync import (
    google_tasks_sync,
)


class GoogleIntegrationService:
    """Non-interactive, read-only Google synchronization gateway."""

    def __init__(self) -> None:

        self._sync_lock = Lock()

    @staticmethod
    def _service_status(connector) -> dict[str, bool]:

        return {
            "credentials_available": (
                connector.credentials_available()
            ),
            "token_available": connector.token_available(),
        }

    def status(self) -> dict[str, Any]:

        services = {
            "calendar": self._service_status(
                google_calendar_connector
            ),
            "contacts": self._service_status(
                google_contacts_connector
            ),
            "tasks": self._service_status(
                google_tasks_connector
            ),
        }

        ready = all(
            value["credentials_available"]
            and value["token_available"]
            for value in services.values()
        )

        return {
            "access_mode": GOOGLE_ACCESS_MODE,
            "interactive_authorization": False,
            "ready_for_noninteractive_sync": ready,
            "services": services,
        }

    @staticmethod
    def _safe_result(result: Any) -> dict[str, Any]:

        if not isinstance(result, dict):
            return {"completed": True}

        safe_keys = {
            "mode",
            "reason",
            "fallback",
            "fetched",
            "created",
            "updated",
            "deleted",
            "archived",
            "skipped",
            "active_events",
            "active_contacts",
            "active_tasks",
            "sync_token_saved",
        }

        return {
            key: value
            for key, value in result.items()
            if key in safe_keys
        }

    def sync_all(self) -> dict[str, Any]:

        if GOOGLE_ACCESS_MODE != "read_only":

            raise PermissionError(
                "This MoneroAI build supports Google read-only access only."
            )

        status = self.status()

        if not status["ready_for_noninteractive_sync"]:

            log_event(
                "google_sync_blocked",
                component="google",
                status="authorization_required",
            )

            return {
                "status": "authorization_required",
                "message": (
                    "Google read-only credentials and all three "
                    "service tokens are required. No authorization "
                    "window was opened."
                ),
                "google": status,
            }

        if not self._sync_lock.acquire(blocking=False):

            log_event(
                "google_sync_skipped",
                component="google",
                status="sync_in_progress",
            )

            return {
                "status": "sync_in_progress",
                "access_mode": GOOGLE_ACCESS_MODE,
            }

        try:

            operations = {
                "calendar": google_calendar_incremental_sync.sync,
                "contacts": google_contacts_sync.sync,
                "tasks": google_tasks_sync.sync,
            }
            results = {}

            for name, operation in operations.items():

                try:
                    results[name] = {
                        "status": "completed",
                        "result": self._safe_result(operation()),
                    }

                except Exception as error:
                    log_event(
                        "google_service_sync_failed",
                        level=40,
                        component=f"google_{name}",
                        error_type=type(error).__name__,
                    )
                    results[name] = {
                        "status": "failed",
                        "error_type": type(error).__name__,
                    }

            overall = (
                "completed"
                if all(
                    result["status"] == "completed"
                    for result in results.values()
                )
                else "completed_with_errors"
            )

            log_event(
                "google_sync_completed",
                component="google",
                status=overall,
            )

            return {
                "status": overall,
                "access_mode": GOOGLE_ACCESS_MODE,
                "services": results,
            }

        finally:
            self._sync_lock.release()


google_integration_service = GoogleIntegrationService()
