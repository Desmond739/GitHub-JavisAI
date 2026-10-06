from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import (
    Request,
)

from google.oauth2.credentials import (
    Credentials,
)

from google_auth_oauthlib.flow import (
    InstalledAppFlow,
)

from googleapiclient.discovery import (
    build,
)

from app.personal_data.secure_file_writer import (
    atomic_write_private_text,
)


GOOGLE_DIRECTORY = Path(
    "data/personal_data/google"
)

DEFAULT_CREDENTIALS_PATH = (
    GOOGLE_DIRECTORY
    / "credentials.json"
)

DEFAULT_TOKEN_PATH = (
    GOOGLE_DIRECTORY
    / "tasks_token.json"
)

TASKS_READONLY_SCOPE = (
    "https://www.googleapis.com/"
    "auth/tasks.readonly"
)

SCOPES = [
    TASKS_READONLY_SCOPE,
]


class GoogleTasksConnector:

    def __init__(
        self,
        credentials_path:
        str | Path = DEFAULT_CREDENTIALS_PATH,
        token_path:
        str | Path = DEFAULT_TOKEN_PATH,
    ) -> None:

        self.credentials_path = Path(
            credentials_path
        )

        self.token_path = Path(
            token_path
        )

        self._credentials: Credentials | None = None

        self._service = None

    # ============================================================
    # FILE AVAILABILITY
    # ============================================================

    def credentials_available(
        self,
    ) -> bool:

        return self.credentials_path.exists()

    def token_available(
        self,
    ) -> bool:

        return self.token_path.exists()

    # ============================================================
    # TOKEN PERSISTENCE
    # ============================================================

    def _save_token(
        self,
        credentials: Credentials,
    ) -> None:

        atomic_write_private_text(
            self.token_path,
            credentials.to_json(),
            error_label=(
                "the Google Tasks "
                "OAuth token"
            ),
        )

    # ============================================================
    # AUTHENTICATION
    # ============================================================

    def authenticate(
        self,
        *,
        allow_interactive: bool = False,
    ) -> Credentials:

        if not self.credentials_path.exists():

            raise FileNotFoundError(
                "Google OAuth credentials "
                "were not found at: "
                f"{self.credentials_path}"
            )

        credentials = None

        if self.token_path.exists():

            try:

                credentials = (
                    Credentials
                    .from_authorized_user_file(
                        str(
                            self.token_path
                        ),
                        SCOPES,
                    )
                )

            except Exception as exc:

                raise RuntimeError(
                    "The Google Tasks token "
                    "could not be loaded. "
                    "Do not modify the token "
                    "manually."
                ) from exc

        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(
                Request()
            )

            self._save_token(
                credentials
            )

        elif (
            credentials is None
            or not credentials.valid
        ):

            if not allow_interactive:

                raise PermissionError(
                    "Interactive Google Tasks authorization is disabled. "
                    "Use the explicit read-only authorization utility after "
                    "the user approves."
                )

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    str(
                        self.credentials_path
                    ),
                    SCOPES,
                )
            )

            credentials = (
                flow.run_local_server(
                    port=0
                )
            )

            self._save_token(
                credentials
            )

        if not credentials.valid:

            raise RuntimeError(
                "Google Tasks OAuth "
                "credentials are not valid."
            )

        if not credentials.has_scopes(
            SCOPES
        ):

            raise PermissionError(
                "Google Tasks token does not "
                "contain the required "
                "read-only scope."
            )

        self._credentials = (
            credentials
        )

        return credentials

    # ============================================================
    # SERVICE
    # ============================================================

    def service(
        self,
    ):

        if self._service is not None:

            return self._service

        credentials = (
            self.authenticate()
        )

        self._service = build(
            "tasks",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        return self._service

    # ============================================================
    # TASK LISTS
    # ============================================================

    def fetch_tasklists(
        self,
    ) -> list[dict[str, Any]]:

        service = self.service()

        results = []

        page_token = None

        while True:

            response = (
                service.tasklists()
                .list(
                    maxResults=1000,
                    pageToken=page_token,
                )
                .execute()
            )

            items = response.get(
                "items",
                [],
            )

            results.extend(
                items
            )

            page_token = (
                response.get(
                    "nextPageToken"
                )
            )

            if not page_token:

                break

        return results

    # ============================================================
    # TASKS
    # ============================================================

    def fetch_tasks(
        self,
        tasklist_id: str,
        *,
        show_completed: bool = True,
        show_deleted: bool = True,
        show_hidden: bool = True,
    ) -> list[dict[str, Any]]:

        tasklist_id = (
            str(
                tasklist_id
            ).strip()
        )

        if not tasklist_id:

            raise ValueError(
                "Google Task list ID "
                "cannot be empty."
            )

        service = self.service()

        results = []

        page_token = None

        while True:

            response = (
                service.tasks()
                .list(
                    tasklist=tasklist_id,
                    maxResults=100,
                    pageToken=page_token,
                    showCompleted=(
                        show_completed
                    ),
                    showDeleted=(
                        show_deleted
                    ),
                    showHidden=(
                        show_hidden
                    ),
                )
                .execute()
            )

            items = response.get(
                "items",
                [],
            )

            results.extend(
                items
            )

            page_token = (
                response.get(
                    "nextPageToken"
                )
            )

            if not page_token:

                break

        return results

    # ============================================================
    # ALL TASKS
    # ============================================================

    def fetch_all_tasks(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        results = []

        tasklists = (
            self.fetch_tasklists()
        )

        for tasklist in tasklists:

            tasklist_id = (
                tasklist.get(
                    "id"
                )
            )

            if not tasklist_id:

                continue

            tasks = self.fetch_tasks(
                tasklist_id,
            )

            for task in tasks:

                results.append(
                    {
                        "tasklist_id": (
                            tasklist_id
                        ),
                        "tasklist_title": (
                            tasklist.get(
                                "title",
                                "",
                            )
                        ),
                        "task": task,
                    }
                )

        return results

    # ============================================================
    # SAFE SUMMARY
    # ============================================================

    def summary(
        self,
    ) -> dict[str, Any]:

        tasklists = (
            self.fetch_tasklists()
        )

        total_tasks = 0
        open_tasks = 0
        completed_tasks = 0
        deleted_tasks = 0

        for tasklist in tasklists:

            tasklist_id = (
                tasklist.get(
                    "id"
                )
            )

            if not tasklist_id:

                continue

            tasks = self.fetch_tasks(
                tasklist_id
            )

            total_tasks += len(
                tasks
            )

            for task in tasks:

                if task.get(
                    "deleted",
                    False,
                ):

                    deleted_tasks += 1

                    continue

                if (
                    task.get(
                        "status"
                    )
                    == "completed"
                ):

                    completed_tasks += 1

                else:

                    open_tasks += 1

        return {
            "tasklists": len(
                tasklists
            ),
            "tasks": total_tasks,
            "open": open_tasks,
            "completed": (
                completed_tasks
            ),
            "deleted": (
                deleted_tasks
            ),
            "readonly_scope": (
                TASKS_READONLY_SCOPE
            ),
            "token_exists": (
                self.token_path.exists()
            ),
        }


google_tasks_connector = (
    GoogleTasksConnector()
)
