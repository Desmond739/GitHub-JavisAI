from __future__ import annotations

from typing import Any

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
    personal_data_manager,
)

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
    PersonalDataSource,
)


class CalendarService:

    def __init__(
        self,
        manager: PersonalDataManager | None = None,
    ) -> None:

        self.manager = (
            manager
            if manager is not None
            else personal_data_manager
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str:

        if value is None:

            return ""

        return value.strip()

    @staticmethod
    def _clean_list(
        values: list[str] | None,
    ) -> list[str]:

        if values is None:

            return []

        result = []
        seen = set()

        for value in values:

            cleaned = str(
                value
            ).strip()

            if not cleaned:

                continue

            key = cleaned.casefold()

            if key in seen:

                continue

            seen.add(
                key
            )

            result.append(
                cleaned
            )

        return result

    # ============================================================
    # SOURCE VALIDATION
    # ============================================================

    def _require_calendar_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.manager.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Calendar source not found: "
                f"{source_id}"
            )

        if source.source_type != "calendar":

            raise ValueError(
                "Source is not a calendar "
                f"source: {source.name}"
            )

        return source

    # ============================================================
    # EVENT VALIDATION
    # ============================================================

    def _require_event_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.manager.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Calendar event not found: "
                f"{record_id}"
            )

        if record.record_type != "event":

            raise ValueError(
                "Record is not a calendar "
                f"event: {record_id}"
            )

        return record

    # ============================================================
    # ATTRIBUTES
    # ============================================================

    def _build_attributes(
        self,
        start_at: str | None = None,
        end_at: str | None = None,
        timezone: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        organizer: str | None = None,
        event_status: str | None = None,
        all_day: bool = False,
        recurrence: list[str] | None = None,
        meeting_url: str | None = None,
        calendar_name: str | None = None,
        extra_attributes:
        dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        attributes = dict(
            extra_attributes
            if extra_attributes is not None
            else {}
        )

        attributes.update(
            {
                "start_at": (
                    self._clean_text(
                        start_at
                    )
                ),
                "end_at": (
                    self._clean_text(
                        end_at
                    )
                ),
                "timezone": (
                    self._clean_text(
                        timezone
                    )
                ),
                "location": (
                    self._clean_text(
                        location
                    )
                ),
                "attendees": (
                    self._clean_list(
                        attendees
                    )
                ),
                "organizer": (
                    self._clean_text(
                        organizer
                    )
                ),
                "event_status": (
                    self._clean_text(
                        event_status
                    )
                ),
                "all_day": bool(
                    all_day
                ),
                "recurrence": (
                    self._clean_list(
                        recurrence
                    )
                ),
                "meeting_url": (
                    self._clean_text(
                        meeting_url
                    )
                ),
                "calendar_name": (
                    self._clean_text(
                        calendar_name
                    )
                ),
            }
        )

        return attributes

    # ============================================================
    # REGISTER CALENDAR SOURCE
    # ============================================================

    def register_source(
        self,
        name: str = "Personal Calendar",
        access_mode: str = "read_only",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        if permissions_required is None:

            permissions_required = [
                "calendar.read",
            ]

            if access_mode == "read_write":

                permissions_required.append(
                    "calendar.write"
                )

        return self.manager.register_source(
            source_type="calendar",
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
            ),
            attributes=attributes,
        )

    # ============================================================
    # GET EVENT BY EXTERNAL ID
    # ============================================================

    def get_by_external_id(
        self,
        source_id: str,
        external_id: str,
    ) -> PersonalDataRecord | None:

        self._require_calendar_source(
            source_id
        )

        for event in (
            self.manager.list_records(
                source_id=source_id,
                record_type="event",
            )
        ):

            if (
                event.external_id
                == external_id
            ):

                return event

        return None

    # ============================================================
    # INGEST EXTERNAL EVENT
    # ============================================================

    def ingest_event(
        self,
        source_id: str,
        external_id: str,
        title: str,
        description: str = "",
        start_at: str | None = None,
        end_at: str | None = None,
        timezone: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        organizer: str | None = None,
        event_status: str | None = None,
        all_day: bool = False,
        recurrence: list[str] | None = None,
        meeting_url: str | None = None,
        calendar_name: str | None = None,
        extra_attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_calendar_source(
            source_id
        )

        external_id = (
            external_id.strip()
        )

        if not external_id:

            raise ValueError(
                "External calendar event "
                "ID cannot be empty."
            )

        title = title.strip()

        if not title:

            title = "Untitled Event"

        attributes = (
            self._build_attributes(
                start_at=start_at,
                end_at=end_at,
                timezone=timezone,
                location=location,
                attendees=attendees,
                organizer=organizer,
                event_status=event_status,
                all_day=all_day,
                recurrence=recurrence,
                meeting_url=meeting_url,
                calendar_name=calendar_name,
                extra_attributes=(
                    extra_attributes
                ),
            )
        )

        existing = (
            self.get_by_external_id(
                source_id,
                external_id,
            )
        )

        if existing is not None:

            return (
                self.manager
                .update_ingested_record(
                    record_id=(
                        existing.record_id
                    ),
                    title=title,
                    content=description,
                    attributes=attributes,
                    sensitivity=sensitivity,
                    status="active",
                    external_id=external_id,
                    occurred_at=start_at,
                )
            )

        return self.manager.ingest_record(
            source_id=source_id,
            record_type="event",
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=start_at,
        )

    # ============================================================
    # CREATE EVENT
    # ============================================================

    def create_event(
        self,
        source_id: str,
        title: str,
        description: str = "",
        start_at: str | None = None,
        end_at: str | None = None,
        timezone: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        organizer: str | None = None,
        event_status: str = "confirmed",
        all_day: bool = False,
        recurrence: list[str] | None = None,
        meeting_url: str | None = None,
        calendar_name: str | None = None,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_calendar_source(
            source_id
        )

        title = title.strip()

        if not title:

            raise ValueError(
                "Calendar event title "
                "cannot be empty."
            )

        attributes = (
            self._build_attributes(
                start_at=start_at,
                end_at=end_at,
                timezone=timezone,
                location=location,
                attendees=attendees,
                organizer=organizer,
                event_status=event_status,
                all_day=all_day,
                recurrence=recurrence,
                meeting_url=meeting_url,
                calendar_name=calendar_name,
            )
        )

        return self.manager.create_record(
            source_id=source_id,
            record_type="event",
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            occurred_at=start_at,
        )

    # ============================================================
    # GET EVENT
    # ============================================================

    def get_event(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        return self._require_event_record(
            record_id
        )

    # ============================================================
    # UPDATE LOCALLY MANAGED EVENT
    # ============================================================

    def update_event(
        self,
        record_id: str,
        title: str | None = None,
        description: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        timezone: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        organizer: str | None = None,
        event_status: str | None = None,
        all_day: bool | None = None,
        recurrence: list[str] | None = None,
        meeting_url: str | None = None,
        calendar_name: str | None = None,
        sensitivity: str | None = None,
    ) -> PersonalDataRecord:

        event = self._require_event_record(
            record_id
        )

        attributes = dict(
            event.attributes
        )

        if start_at is not None:

            attributes[
                "start_at"
            ] = self._clean_text(
                start_at
            )

        if end_at is not None:

            attributes[
                "end_at"
            ] = self._clean_text(
                end_at
            )

        if timezone is not None:

            attributes[
                "timezone"
            ] = self._clean_text(
                timezone
            )

        if location is not None:

            attributes[
                "location"
            ] = self._clean_text(
                location
            )

        if attendees is not None:

            attributes[
                "attendees"
            ] = self._clean_list(
                attendees
            )

        if organizer is not None:

            attributes[
                "organizer"
            ] = self._clean_text(
                organizer
            )

        if event_status is not None:

            attributes[
                "event_status"
            ] = self._clean_text(
                event_status
            )

        if all_day is not None:

            attributes[
                "all_day"
            ] = bool(
                all_day
            )

        if recurrence is not None:

            attributes[
                "recurrence"
            ] = self._clean_list(
                recurrence
            )

        if meeting_url is not None:

            attributes[
                "meeting_url"
            ] = self._clean_text(
                meeting_url
            )

        if calendar_name is not None:

            attributes[
                "calendar_name"
            ] = self._clean_text(
                calendar_name
            )

        occurred_at = None

        if start_at is not None:

            occurred_at = start_at

        return self.manager.update_record(
            record_id=event.record_id,
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            occurred_at=occurred_at,
        )

    # ============================================================
    # ARCHIVE EVENT
    # ============================================================

    def archive_event(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        event = self._require_event_record(
            record_id
        )

        return self.manager.archive_record(
            event.record_id
        )

    # ============================================================
    # LIST EVENTS
    # ============================================================

    def list_events(
        self,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        if source_id is not None:

            self._require_calendar_source(
                source_id
            )

        return self.manager.list_records(
            source_id=source_id,
            record_type="event",
            active_only=active_only,
        )

    # ============================================================
    # SEARCH EVENTS
    # ============================================================

    def search_events(
        self,
        query: str,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        query = query.strip()

        events = self.list_events(
            source_id=source_id,
            active_only=active_only,
        )

        if not query:

            return events

        normalized = query.casefold()

        results = []

        for event in events:

            attributes = (
                event.attributes
            )

            text_values = [
                event.title,
                event.content,
                attributes.get(
                    "location",
                    "",
                ),
                attributes.get(
                    "organizer",
                    "",
                ),
                attributes.get(
                    "calendar_name",
                    "",
                ),
                attributes.get(
                    "meeting_url",
                    "",
                ),
            ]

            attendee_values = (
                attributes.get(
                    "attendees",
                    [],
                )
            )

            text_match = any(
                normalized
                in str(
                    value
                ).casefold()
                for value in text_values
                if value
            )

            attendee_match = any(
                normalized
                in str(
                    attendee
                ).casefold()
                for attendee
                in attendee_values
            )

            if (
                text_match
                or attendee_match
            ):

                results.append(
                    event
                )

        return sorted(
            results,
            key=lambda event: (
                event.attributes.get(
                    "start_at",
                    "",
                ),
                event.title.casefold(),
            ),
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = (
            self._require_calendar_source(
                source_id
            )
        )

        events = self.list_events(
            source_id=source_id,
            active_only=False,
        )

        active_events = [
            event
            for event in events
            if event.status
            == "active"
        ]

        return {
            "source_id": source.source_id,
            "name": source.name,
            "access_mode": (
                source.access_mode
            ),
            "status": source.status,
            "events": len(
                events
            ),
            "active_events": len(
                active_events
            ),
            "last_sync_at": (
                source.last_sync_at
            ),
        }


calendar_service = CalendarService()