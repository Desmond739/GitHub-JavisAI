from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

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

from app.personal_data.calendar_service import (
    CalendarService,
    calendar_service,
)

from app.personal_data.personal_data_model import (
    PersonalDataSource,
)

from app.personal_data.secure_file_writer import (
    atomic_write_private_text,
)


class GoogleCalendarConnector:

    READONLY_SCOPE = (
        "https://www.googleapis.com/"
        "auth/calendar.readonly"
    )

    SCOPES = [
        READONLY_SCOPE,
    ]

    def __init__(
        self,
        calendar_service_instance:
        CalendarService | None = None,
        credentials_path:
        str | Path | None = None,
        token_path:
        str | Path | None = None,
    ) -> None:

        self.calendar_service = (
            calendar_service_instance
            if calendar_service_instance
            is not None
            else calendar_service
        )

        self.credentials_path = Path(
            credentials_path
            if credentials_path is not None
            else (
                "data/personal_data/google/"
                "credentials.json"
            )
        )

        self.token_path = Path(
            token_path
            if token_path is not None
            else (
                "data/personal_data/google/"
                "calendar_token.json"
            )
        )

        self._credentials = None

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

    def _require_credentials_file(
        self,
    ) -> None:

        if not self.credentials_path.exists():

            raise FileNotFoundError(
                "Google OAuth credentials "
                "file was not found: "
                f"{self.credentials_path}"
            )

    # ============================================================
    # TOKEN
    # ============================================================

    def _save_token(
        self,
        credentials: Credentials,
    ) -> None:

        atomic_write_private_text(
            self.token_path,
            credentials.to_json(),
            error_label=(
                "the Google Calendar "
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

        self._require_credentials_file()

        credentials = None

        if self.token_path.exists():

            try:

                credentials = (
                    Credentials
                    .from_authorized_user_file(
                        str(
                            self.token_path
                        ),
                        self.SCOPES,
                    )
                )

            except Exception:

                credentials = None

        if (
            credentials is not None
            and credentials.valid
        ):

            self._credentials = (
                credentials
            )

            return credentials

        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):

            try:

                credentials.refresh(
                    Request()
                )

                self._save_token(
                    credentials
                )

                self._credentials = (
                    credentials
                )

                return credentials

            except Exception:

                credentials = None

        if not allow_interactive:

            raise PermissionError(
                "Interactive Google Calendar authorization is disabled. "
                "Use the explicit read-only authorization utility after "
                "the user approves."
            )

        flow = (
            InstalledAppFlow
            .from_client_secrets_file(
                str(
                    self.credentials_path
                ),
                self.SCOPES,
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

        self._credentials = (
            credentials
        )

        return credentials

    # ============================================================
    # SERVICE
    # ============================================================

    def connect(
        self,
    ):

        credentials = (
            self.authenticate()
        )

        self._service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

        return self._service

    def _get_service(
        self,
    ):

        if self._service is None:

            return self.connect()

        return self._service

    # ============================================================
    # CURRENT UTC TIME
    # ============================================================

    @staticmethod
    def _utc_now() -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    # ============================================================
    # CALENDAR LIST
    # ============================================================

    def fetch_calendars(
        self,
    ) -> list[dict[str, Any]]:

        service = (
            self._get_service()
        )

        calendars = []

        page_token = None

        while True:

            response = (
                service
                .calendarList()
                .list(
                    pageToken=page_token,
                )
                .execute()
            )

            for item in response.get(
                "items",
                [],
            ):

                calendar_id = item.get(
                    "id"
                )

                if not calendar_id:

                    continue

                calendars.append(
                    {
                        "calendar_id": (
                            calendar_id
                        ),
                        "name": (
                            item.get(
                                "summary",
                                "",
                            )
                        ),
                        "primary": bool(
                            item.get(
                                "primary",
                                False,
                            )
                        ),
                        "access_role": (
                            item.get(
                                "accessRole",
                                "",
                            )
                        ),
                        "timezone": (
                            item.get(
                                "timeZone",
                                "",
                            )
                        ),
                        "selected": bool(
                            item.get(
                                "selected",
                                False,
                            )
                        ),
                    }
                )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:

                break

        return calendars

    # ============================================================
    # GOOGLE EVENT CONVERSION
    # ============================================================

    @staticmethod
    def _convert_event(
        event: dict[str, Any],
        calendar_id: str,
        calendar_name: str = "",
    ) -> dict[str, Any] | None:

        external_id = event.get(
            "id"
        )

        if not external_id:

            return None

        start_data = event.get(
            "start",
            {},
        )

        end_data = event.get(
            "end",
            {},
        )

        start_at = (
            start_data.get(
                "dateTime"
            )
            or start_data.get(
                "date",
                "",
            )
        )

        end_at = (
            end_data.get(
                "dateTime"
            )
            or end_data.get(
                "date",
                "",
            )
        )

        all_day = (
            "date" in start_data
            and "dateTime"
            not in start_data
        )

        timezone_name = (
            start_data.get(
                "timeZone"
            )
            or end_data.get(
                "timeZone"
            )
            or ""
        )

        organizer_data = (
            event.get(
                "organizer",
                {},
            )
        )

        organizer = (
            organizer_data.get(
                "email"
            )
            or organizer_data.get(
                "displayName"
            )
            or ""
        )

        attendees = []

        for attendee in event.get(
            "attendees",
            [],
        ):

            value = (
                attendee.get(
                    "email"
                )
                or attendee.get(
                    "displayName"
                )
            )

            if value:

                attendees.append(
                    value
                )

        meeting_url = (
            event.get(
                "hangoutLink"
            )
            or ""
        )

        if not meeting_url:

            conference_data = (
                event.get(
                    "conferenceData",
                    {},
                )
            )

            for entry in conference_data.get(
                "entryPoints",
                [],
            ):

                uri = entry.get(
                    "uri"
                )

                if uri:

                    meeting_url = uri
                    break

        return {
            "external_id": external_id,
            "title": (
                event.get(
                    "summary"
                )
                or "Untitled Event"
            ),
            "description": (
                event.get(
                    "description",
                    "",
                )
            ),
            "start_at": start_at,
            "end_at": end_at,
            "timezone": timezone_name,
            "location": (
                event.get(
                    "location",
                    "",
                )
            ),
            "attendees": attendees,
            "organizer": organizer,
            "event_status": (
                event.get(
                    "status",
                    "",
                )
            ),
            "all_day": all_day,
            "recurrence": list(
                event.get(
                    "recurrence",
                    [],
                )
            ),
            "meeting_url": meeting_url,
            "calendar_name": (
                calendar_name
            ),
            "calendar_id": (
                calendar_id
            ),
            "updated": (
                event.get(
                    "updated",
                    "",
                )
            ),
            "html_link": (
                event.get(
                    "htmlLink",
                    "",
                )
            ),
            "deleted": (
                event.get(
                    "status"
                )
                == "cancelled"
            ),
        }

    # ============================================================
    # FETCH UPCOMING EVENTS
    # ============================================================

    def fetch_events(
        self,
        calendar_id: str = "primary",
        max_events: int = 10,
        time_min: str | None = None,
        calendar_name: str = "",
    ) -> list[dict[str, Any]]:

        if max_events <= 0:

            return []

        service = (
            self._get_service()
        )

        if time_min is None:

            time_min = (
                self._utc_now()
            )

        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                maxResults=max_events,
                singleEvents=True,
                orderBy="startTime",
                showDeleted=False,
            )
            .execute()
        )

        events = []

        for raw_event in response.get(
            "items",
            [],
        ):

            event = self._convert_event(
                raw_event,
                calendar_id=calendar_id,
                calendar_name=(
                    calendar_name
                ),
            )

            if event is None:

                continue

            if event[
                "deleted"
            ]:

                continue

            events.append(
                event
            )

        return events

    # ============================================================
    # PRIMARY CALENDAR EVENTS
    # ============================================================

    def fetch_primary_events(
        self,
        max_events: int = 10,
    ) -> list[dict[str, Any]]:

        return self.fetch_events(
            calendar_id="primary",
            max_events=max_events,
        )

    # ============================================================
    # REGISTER LOCAL SOURCE
    # ============================================================

    def register_local_source(
        self,
    ) -> PersonalDataSource:

        return (
            self.calendar_service
            .register_source(
                name="Google Calendar",
                access_mode="read_only",
                permissions_required=[
                    "calendar.read",
                ],
                attributes={
                    "provider": "google",
                    "api": "calendar_v3",
                    "oauth_scope": (
                        self.READONLY_SCOPE
                    ),
                },
            )
        )


google_calendar_connector = (
    GoogleCalendarConnector()
)
