from __future__ import annotations

import hashlib

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import Any

from app.personal_data.calendar_service import (
    CalendarService,
    calendar_service,
)

from app.personal_data.google_calendar_connector import (
    GoogleCalendarConnector,
    google_calendar_connector,
)


class GoogleCalendarSync:

    PAGE_SIZE = 2500

    def __init__(
        self,
        connector:
        GoogleCalendarConnector | None = None,
        calendar_service_instance:
        CalendarService | None = None,
    ) -> None:

        self.connector = (
            connector
            if connector is not None
            else google_calendar_connector
        )

        self.calendar_service = (
            calendar_service_instance
            if calendar_service_instance
            is not None
            else calendar_service
        )

    # ============================================================
    # TIME
    # ============================================================

    @staticmethod
    def _google_time(
        value: datetime,
    ) -> str:

        return (
            value
            .astimezone(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    def _build_window(
        self,
        past_days: int,
        future_days: int,
    ) -> tuple[str, str]:

        if past_days < 0:

            raise ValueError(
                "past_days cannot "
                "be negative."
            )

        if future_days <= 0:

            raise ValueError(
                "future_days must "
                "be greater than zero."
            )

        now = datetime.now(
            timezone.utc
        )

        time_min = (
            now
            - timedelta(
                days=past_days
            )
        )

        time_max = (
            now
            + timedelta(
                days=future_days
            )
        )

        return (
            self._google_time(
                time_min
            ),
            self._google_time(
                time_max
            ),
        )

    # ============================================================
    # PRIMARY CALENDAR
    # ============================================================

    def _get_primary_calendar(
        self,
    ) -> dict[str, Any]:

        calendars = (
            self.connector
            .fetch_calendars()
        )

        for calendar in calendars:

            if calendar.get(
                "primary"
            ):

                return calendar

        raise RuntimeError(
            "Google primary calendar "
            "was not found."
        )

    # ============================================================
    # STABLE LOCAL EXTERNAL ID
    # ============================================================

    @staticmethod
    def _calendar_key(
        calendar_id: str,
    ) -> str:

        return (
            hashlib.sha256(
                calendar_id.encode(
                    "utf-8"
                )
            )
            .hexdigest()[:16]
        )

    def _local_external_id(
        self,
        calendar_id: str,
        event_id: str,
    ) -> str:

        calendar_key = (
            self._calendar_key(
                calendar_id
            )
        )

        return (
            "google-calendar:"
            f"{calendar_key}:"
            f"{event_id}"
        )

    # ============================================================
    # FETCH PRIMARY CALENDAR WINDOW
    # ============================================================

    def fetch_primary_window(
        self,
        past_days: int = 90,
        future_days: int = 365,
    ) -> dict[str, Any]:

        primary = (
            self._get_primary_calendar()
        )

        calendar_id = primary[
            "calendar_id"
        ]

        calendar_name = primary.get(
            "name",
            "",
        )

        time_min, time_max = (
            self._build_window(
                past_days,
                future_days,
            )
        )

        service = (
            self.connector
            ._get_service()
        )

        events = []

        page_token = None

        while True:

            response = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    showDeleted=True,
                    maxResults=self.PAGE_SIZE,
                    pageToken=page_token,
                )
                .execute()
            )

            for raw_event in response.get(
                "items",
                [],
            ):

                converted = (
                    self.connector
                    ._convert_event(
                        raw_event,
                        calendar_id=(
                            calendar_id
                        ),
                        calendar_name=(
                            calendar_name
                        ),
                    )
                )

                if converted is None:

                    continue

                provider_event_id = (
                    converted[
                        "external_id"
                    ]
                )

                converted[
                    "provider_event_id"
                ] = provider_event_id

                converted[
                    "external_id"
                ] = (
                    self._local_external_id(
                        calendar_id,
                        provider_event_id,
                    )
                )

                converted[
                    "calendar_primary"
                ] = True

                converted[
                    "calendar_timezone"
                ] = primary.get(
                    "timezone",
                    "",
                )

                converted[
                    "calendar_access_role"
                ] = primary.get(
                    "access_role",
                    "",
                )

                events.append(
                    converted
                )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:

                break

        return {
            "calendar": primary,
            "time_min": time_min,
            "time_max": time_max,
            "events": events,
        }

    # ============================================================
    # MARK REMOTE CANCELLATION LOCALLY
    # ============================================================

    def _mark_deleted(
        self,
        source_id: str,
        event: dict[str, Any],
    ) -> bool:

        existing = (
            self.calendar_service
            .get_by_external_id(
                source_id,
                event[
                    "external_id"
                ],
            )
        )

        if existing is None:

            return False

        (
            self.calendar_service
            .manager
            .update_ingested_record(
                record_id=(
                    existing.record_id
                ),
                status="deleted",
                external_id=event[
                    "external_id"
                ],
            )
        )

        return True

    # ============================================================
    # UPSERT EVENT
    # ============================================================

    def _upsert(
        self,
        source_id: str,
        event: dict[str, Any],
    ) -> str:

        existing = (
            self.calendar_service
            .get_by_external_id(
                source_id,
                event[
                    "external_id"
                ],
            )
        )

        extra_attributes = {
            "provider": "google",
            "provider_event_id": (
                event[
                    "provider_event_id"
                ]
            ),
            "provider_calendar_id": (
                event[
                    "calendar_id"
                ]
            ),
            "google_updated": (
                event.get(
                    "updated",
                    "",
                )
            ),
            "html_link": (
                event.get(
                    "html_link",
                    "",
                )
            ),
            "calendar_primary": (
                event.get(
                    "calendar_primary",
                    False,
                )
            ),
            "calendar_timezone": (
                event.get(
                    "calendar_timezone",
                    "",
                )
            ),
            "calendar_access_role": (
                event.get(
                    "calendar_access_role",
                    "",
                )
            ),
        }

        saved = (
            self.calendar_service
            .ingest_event(
                source_id=source_id,
                external_id=event[
                    "external_id"
                ],
                title=event[
                    "title"
                ],
                description=event[
                    "description"
                ],
                start_at=event[
                    "start_at"
                ],
                end_at=event[
                    "end_at"
                ],
                timezone=event[
                    "timezone"
                ],
                location=event[
                    "location"
                ],
                attendees=event[
                    "attendees"
                ],
                organizer=event[
                    "organizer"
                ],
                event_status=event[
                    "event_status"
                ],
                all_day=event[
                    "all_day"
                ],
                recurrence=event[
                    "recurrence"
                ],
                meeting_url=event[
                    "meeting_url"
                ],
                calendar_name=event[
                    "calendar_name"
                ],
                extra_attributes=(
                    extra_attributes
                ),
                sensitivity="private",
            )
        )

        if existing is None:

            return "created"

        if (
            existing.record_id
            == saved.record_id
        ):

            return "updated"

        return "created"

    # ============================================================
    # FULL SAFE SYNC
    # ============================================================

    def full_sync(
        self,
        past_days: int = 90,
        future_days: int = 365,
    ) -> dict[str, Any]:

        source = (
            self.connector
            .register_local_source()
        )

        remote = (
            self.fetch_primary_window(
                past_days=past_days,
                future_days=future_days,
            )
        )

        created = 0
        updated = 0
        deleted = 0

        for event in remote[
            "events"
        ]:

            if event[
                "deleted"
            ]:

                if self._mark_deleted(
                    source.source_id,
                    event,
                ):

                    deleted += 1

                continue

            action = self._upsert(
                source.source_id,
                event,
            )

            if action == "created":

                created += 1

            else:

                updated += 1

        (
            self.calendar_service
            .manager
            .mark_source_synced(
                source.source_id
            )
        )

        active_events = (
            self.calendar_service
            .list_events(
                source_id=(
                    source.source_id
                ),
                active_only=True,
            )
        )

        return {
            "mode": "full",
            "source_id": (
                source.source_id
            ),
            "source_name": (
                source.name
            ),
            "access_mode": (
                source.access_mode
            ),
            "calendar_count": 1,
            "fetched": len(
                remote[
                    "events"
                ]
            ),
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "active_events": len(
                active_events
            ),
            "time_min": (
                remote[
                    "time_min"
                ]
            ),
            "time_max": (
                remote[
                    "time_max"
                ]
            ),
        }


google_calendar_sync = (
    GoogleCalendarSync()
)