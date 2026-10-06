from __future__ import annotations

import re

from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from app.personal_data.calendar_service import (
    CalendarService,
    calendar_service,
)

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
)


class CalendarQueryEngine:

    WEEKDAYS = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    DAYPARTS = {
        "morning": (
            time(6, 0),
            time(12, 0),
        ),
        "afternoon": (
            time(12, 0),
            time(17, 0),
        ),
        "evening": (
            time(17, 0),
            time(21, 0),
        ),
    }

    def __init__(
        self,
        calendar_service_instance:
        CalendarService | None = None,
    ) -> None:

        self.calendar_service = (
            calendar_service_instance
            if calendar_service_instance
            is not None
            else calendar_service
        )

    # ============================================================
    # TIMEZONE
    # ============================================================

    @staticmethod
    def _system_timezone():

        local_timezone = (
            datetime.now()
            .astimezone()
            .tzinfo
        )

        return (
            local_timezone
            if local_timezone is not None
            else timezone.utc
        )

    @staticmethod
    def _timezone_from_name(
        name: str | None,
        fallback,
    ):

        if not name:

            return fallback

        try:

            return ZoneInfo(
                name
            )

        except (
            ZoneInfoNotFoundError,
            ValueError,
        ):

            return fallback

    def _normalize_now(
        self,
        now: datetime | None,
    ) -> datetime:

        if now is None:

            return (
                datetime.now()
                .astimezone()
            )

        if now.tzinfo is None:

            return now.replace(
                tzinfo=(
                    self._system_timezone()
                )
            )

        return now

    # ============================================================
    # CONNECTION STATE
    # ============================================================

    def calendar_connected(
        self,
    ) -> bool:

        sources = (
            self.calendar_service
            .manager
            .list_sources(
                source_type="calendar",
                active_only=True,
            )
        )

        return bool(
            sources
        )

    # ============================================================
    # EVENT TIME PARSING
    # ============================================================

    @staticmethod
    def _is_date_only(
        value: str,
    ) -> bool:

        return bool(
            re.fullmatch(
                r"\d{4}-\d{2}-\d{2}",
                value.strip(),
            )
        )

    def _parse_event_datetime(
        self,
        value: str,
        *,
        timezone_name: str | None,
        reference_timezone,
        date_end: bool = False,
    ) -> datetime | None:

        if not value:

            return None

        value = value.strip()

        event_timezone = (
            self._timezone_from_name(
                timezone_name,
                reference_timezone,
            )
        )

        if self._is_date_only(
            value
        ):

            parsed_date = (
                date.fromisoformat(
                    value
                )
            )

            result = datetime.combine(
                parsed_date,
                time.min,
                tzinfo=event_timezone,
            )

            return result.astimezone(
                reference_timezone
            )

        normalized = value

        if normalized.endswith(
            "Z"
        ):

            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        try:

            parsed = (
                datetime.fromisoformat(
                    normalized
                )
            )

        except ValueError:

            return None

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=event_timezone
            )

        return parsed.astimezone(
            reference_timezone
        )

    def _event_bounds(
        self,
        event: PersonalDataRecord,
        reference_timezone,
    ) -> tuple[
        datetime,
        datetime,
    ] | None:

        attributes = (
            event.attributes
        )

        start_text = str(
            attributes.get(
                "start_at",
                "",
            )
        ).strip()

        end_text = str(
            attributes.get(
                "end_at",
                "",
            )
        ).strip()

        timezone_name = str(
            attributes.get(
                "timezone",
                "",
            )
            or attributes.get(
                "calendar_timezone",
                "",
            )
        ).strip()

        if not start_text:

            return None

        start_at = (
            self._parse_event_datetime(
                start_text,
                timezone_name=(
                    timezone_name
                ),
                reference_timezone=(
                    reference_timezone
                ),
            )
        )

        if start_at is None:

            return None

        all_day = bool(
            attributes.get(
                "all_day",
                False,
            )
        )

        end_at = None

        if end_text:

            end_at = (
                self._parse_event_datetime(
                    end_text,
                    timezone_name=(
                        timezone_name
                    ),
                    reference_timezone=(
                        reference_timezone
                    ),
                    date_end=True,
                )
            )

        if end_at is None:

            if all_day:

                end_at = (
                    start_at
                    + timedelta(
                        days=1
                    )
                )

            else:

                end_at = (
                    start_at
                    + timedelta(
                        minutes=1
                    )
                )

        if end_at <= start_at:

            end_at = (
                start_at
                + timedelta(
                    minutes=1
                )
            )

        return (
            start_at,
            end_at,
        )

    # ============================================================
    # EVENT RANGE QUERY
    # ============================================================

    def events_between(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        PersonalDataRecord
    ]:

        if start_at.tzinfo is None:

            start_at = start_at.replace(
                tzinfo=(
                    self._system_timezone()
                )
            )

        if end_at.tzinfo is None:

            end_at = end_at.replace(
                tzinfo=start_at.tzinfo
            )

        if end_at <= start_at:

            raise ValueError(
                "Calendar query end time "
                "must be after start time."
            )

        reference_timezone = (
            start_at.tzinfo
        )

        matches = []

        for event in (
            self.calendar_service
            .list_events(
                active_only=True
            )
        ):

            bounds = self._event_bounds(
                event,
                reference_timezone,
            )

            if bounds is None:

                continue

            event_start, event_end = (
                bounds
            )

            if (
                event_start < end_at
                and event_end > start_at
            ):

                matches.append(
                    (
                        event_start,
                        event,
                    )
                )

        matches.sort(
            key=lambda item: (
                item[0],
                item[1]
                .title
                .casefold(),
            )
        )

        return [
            event
            for _, event
            in matches
        ]

    # ============================================================
    # DATE QUERY
    # ============================================================

    def events_on_date(
        self,
        target_date: date,
        now: datetime | None = None,
    ) -> list[
        PersonalDataRecord
    ]:

        reference = (
            self._normalize_now(
                now
            )
        )

        timezone_info = (
            reference.tzinfo
        )

        start = datetime.combine(
            target_date,
            time.min,
            tzinfo=timezone_info,
        )

        end = (
            start
            + timedelta(
                days=1
            )
        )

        return self.events_between(
            start,
            end,
        )

    # ============================================================
    # UPCOMING EVENTS
    # ============================================================

    def upcoming(
        self,
        limit: int = 10,
        now: datetime | None = None,
    ) -> list[
        PersonalDataRecord
    ]:

        if limit <= 0:

            return []

        reference = (
            self._normalize_now(
                now
            )
        )

        far_future = (
            reference
            + timedelta(
                days=3660
            )
        )

        events = self.events_between(
            reference,
            far_future,
        )

        return events[
            :limit
        ]

    def next_event(
        self,
        now: datetime | None = None,
    ) -> PersonalDataRecord | None:

        events = self.upcoming(
            limit=1,
            now=now,
        )

        if not events:

            return None

        return events[0]

    # ============================================================
    # FREE / BUSY
    # ============================================================

    def is_free(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[
        bool,
        list[PersonalDataRecord],
    ]:

        conflicts = (
            self.events_between(
                start_at,
                end_at,
            )
        )

        return (
            len(conflicts) == 0,
            conflicts,
        )

    # ============================================================
    # HUMAN DATE RESOLUTION
    # ============================================================

    def _resolve_target_date(
        self,
        query: str,
        now: datetime,
    ) -> date | None:

        normalized = (
            query.casefold()
        )

        if "tomorrow" in normalized:

            return (
                now.date()
                + timedelta(
                    days=1
                )
            )

        if "today" in normalized:

            return now.date()

        iso_match = re.search(
            r"\b"
            r"(\d{4}-\d{2}-\d{2})"
            r"\b",
            normalized,
        )

        if iso_match:

            try:

                return date.fromisoformat(
                    iso_match.group(
                        1
                    )
                )

            except ValueError:

                return None

        for (
            weekday_name,
            weekday_number,
        ) in self.WEEKDAYS.items():

            if weekday_name not in (
                normalized
            ):

                continue

            days_ahead = (
                weekday_number
                - now.weekday()
            ) % 7

            if (
                "next "
                + weekday_name
                in normalized
            ):

                if days_ahead == 0:

                    days_ahead = 7

            return (
                now.date()
                + timedelta(
                    days=days_ahead
                )
            )

        return None

    # ============================================================
    # DAYPART
    # ============================================================

    def _resolve_daypart(
        self,
        query: str,
        target_date: date,
        now: datetime,
    ) -> tuple[
        datetime,
        datetime,
        str,
    ]:

        normalized = (
            query.casefold()
        )

        timezone_info = (
            now.tzinfo
        )

        for (
            name,
            bounds,
        ) in self.DAYPARTS.items():

            if name not in normalized:

                continue

            start_time, end_time = (
                bounds
            )

            start = datetime.combine(
                target_date,
                start_time,
                tzinfo=timezone_info,
            )

            end = datetime.combine(
                target_date,
                end_time,
                tzinfo=timezone_info,
            )

            return (
                start,
                end,
                name,
            )

        start = datetime.combine(
            target_date,
            time.min,
            tzinfo=timezone_info,
        )

        end = (
            start
            + timedelta(
                days=1
            )
        )

        return (
            start,
            end,
            "day",
        )

    # ============================================================
    # DISPLAY
    # ============================================================

    def _event_display(
        self,
        event: PersonalDataRecord,
        reference_timezone,
    ) -> str:

        bounds = self._event_bounds(
            event,
            reference_timezone,
        )

        if bounds is None:

            return event.title

        start_at, end_at = (
            bounds
        )

        if event.attributes.get(
            "all_day",
            False,
        ):

            return (
                f"All day — "
                f"{event.title}"
            )

        return (
            f"{start_at.strftime('%H:%M')}"
            f"–"
            f"{end_at.strftime('%H:%M')}"
            f" — {event.title}"
        )

    def _format_events(
        self,
        events:
        list[PersonalDataRecord],
        reference_timezone,
    ) -> str:

        return "; ".join(
            self._event_display(
                event,
                reference_timezone,
            )
            for event in events
        )

    # ============================================================
    # CAN ANSWER
    # ============================================================

    def can_answer(
        self,
        query: str,
    ) -> bool:

        normalized = (
            " ".join(
                query.casefold()
                .split()
            )
        )

        patterns = (
            "my calendar",
            "my schedule",
            "what do i have",
            "what have i got",
            "do i have anything",
            "am i free",
            "am i busy",
            "next meeting",
            "next event",
            "my next meeting",
            "my next event",
            "today's schedule",
            "tomorrow's schedule",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # ============================================================
    # NATURAL LANGUAGE ANSWER
    # ============================================================

    def answer(
        self,
        query: str,
        now: datetime | None = None,
    ) -> str | None:

        if not self.can_answer(
            query
        ):

            return None

        reference = (
            self._normalize_now(
                now
            )
        )

        normalized = (
            " ".join(
                query.casefold()
                .split()
            )
        )

        if not self.calendar_connected():

            return (
                "Your calendar is not "
                "currently connected."
            )

        # --------------------------------------------------------
        # NEXT EVENT
        # --------------------------------------------------------

        if (
            "next meeting"
            in normalized
            or "next event"
            in normalized
        ):

            event = self.next_event(
                now=reference
            )

            if event is None:

                return (
                    "You have no upcoming "
                    "calendar events."
                )

            bounds = self._event_bounds(
                event,
                reference.tzinfo,
            )

            if bounds is None:

                return (
                    "Your next calendar "
                    f"event is {event.title}."
                )

            start_at, _ = bounds

            return (
                "Your next calendar event "
                f"is {event.title} on "
                f"{start_at.strftime('%A, %d %B')} "
                f"at "
                f"{start_at.strftime('%H:%M')}."
            )

        # --------------------------------------------------------
        # TARGET DATE
        # --------------------------------------------------------

        target_date = (
            self._resolve_target_date(
                normalized,
                reference,
            )
        )

        if target_date is None:

            target_date = (
                reference.date()
            )

        (
            window_start,
            window_end,
            daypart,
        ) = self._resolve_daypart(
            normalized,
            target_date,
            reference,
        )

        # --------------------------------------------------------
        # FREE / BUSY
        # --------------------------------------------------------

        if (
            "am i free"
            in normalized
            or "am i busy"
            in normalized
        ):

            free, conflicts = (
                self.is_free(
                    window_start,
                    window_end,
                )
            )

            date_label = (
                target_date.strftime(
                    "%A, %d %B"
                )
            )

            period_label = (
                date_label
                if daypart == "day"
                else (
                    f"{date_label} "
                    f"{daypart}"
                )
            )

            if free:

                return (
                    "Yes. You are free "
                    f"{period_label}."
                )

            formatted = (
                self._format_events(
                    conflicts,
                    reference.tzinfo,
                )
            )

            return (
                "No. You have "
                f"{len(conflicts)} calendar "
                f"event"
                f"{'' if len(conflicts) == 1 else 's'} "
                f"{period_label}: "
                f"{formatted}."
            )

        # --------------------------------------------------------
        # SCHEDULE QUERY
        # --------------------------------------------------------

        events = self.events_between(
            window_start,
            window_end,
        )

        if "tomorrow" in normalized:

            label = "tomorrow"

        elif "today" in normalized:

            label = "today"

        else:

            label = (
                target_date.strftime(
                    "%A, %d %B"
                )
            )

        if daypart != "day":

            label = (
                f"{label} "
                f"{daypart}"
            )

        if not events:

            return (
                "You have no calendar "
                f"events {label}."
            )

        formatted = (
            self._format_events(
                events,
                reference.tzinfo,
            )
        )

        return (
            f"You have {len(events)} "
            f"calendar event"
            f"{'' if len(events) == 1 else 's'} "
            f"{label}: {formatted}."
        )


calendar_query_engine = (
    CalendarQueryEngine()
)