from __future__ import annotations

import json
import os
import time

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path
from typing import Any

from googleapiclient.errors import (
    HttpError,
)

from app.personal_data.calendar_service import (
    CalendarService,
    calendar_service,
)

from app.personal_data.google_calendar_connector import (
    GoogleCalendarConnector,
    google_calendar_connector,
)

from app.personal_data.google_calendar_sync import (
    GoogleCalendarSync,
    google_calendar_sync,
)


class GoogleCalendarIncrementalSync:

    STATE_VERSION = 1

    PAGE_SIZE = 2500

    FULL_REFRESH_HOURS = 24

    DEFAULT_PAST_DAYS = 90

    DEFAULT_FUTURE_DAYS = 365

    def __init__(
        self,
        connector:
        GoogleCalendarConnector | None = None,
        calendar_service_instance:
        CalendarService | None = None,
        base_sync:
        GoogleCalendarSync | None = None,
        state_path:
        str | Path | None = None,
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

        self.base_sync = (
            base_sync
            if base_sync is not None
            else google_calendar_sync
        )

        self.state_path = Path(
            state_path
            if state_path is not None
            else (
                "data/personal_data/google/"
                "calendar_sync_state.json"
            )
        )

    # ============================================================
    # TIME
    # ============================================================

    @staticmethod
    def _now() -> datetime:

        return datetime.now(
            timezone.utc
        )

    @classmethod
    def _now_text(
        cls,
    ) -> str:

        return (
            cls._now()
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    @staticmethod
    def _parse_time(
        value: str | None,
    ) -> datetime | None:

        if not value:

            return None

        try:

            normalized = value.strip()

            if normalized.endswith(
                "Z"
            ):

                normalized = (
                    normalized[:-1]
                    + "+00:00"
                )

            parsed = datetime.fromisoformat(
                normalized
            )

            if parsed.tzinfo is None:

                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ============================================================
    # STATE
    # ============================================================

    def _empty_state(
        self,
    ) -> dict[str, Any]:

        return {
            "version": (
                self.STATE_VERSION
            ),
            "sync_token": None,
            "calendar_key": None,
            "past_days": None,
            "future_days": None,
            "page_size": (
                self.PAGE_SIZE
            ),
            "single_events": True,
            "show_deleted": True,
            "time_min": None,
            "time_max": None,
            "last_full_sync_at": None,
            "updated_at": None,
        }

    def _load_state(
        self,
    ) -> dict[str, Any]:

        if not self.state_path.exists():

            return self._empty_state()

        try:

            raw = self.state_path.read_text(
                encoding="utf-8"
            ).strip()

            if not raw:

                return self._empty_state()

            data = json.loads(
                raw
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            return self._empty_state()

        if not isinstance(
            data,
            dict,
        ):

            return self._empty_state()

        return data

    def _save_state(
        self,
        *,
        sync_token: str,
        calendar_key: str,
        past_days: int,
        future_days: int,
        time_min: str,
        time_max: str,
        last_full_sync_at: str,
    ) -> None:

        if not sync_token:

            raise ValueError(
                "Calendar sync token "
                "cannot be empty."
            )

        data = {
            "version": (
                self.STATE_VERSION
            ),
            "sync_token": sync_token,
            "calendar_key": calendar_key,
            "past_days": past_days,
            "future_days": future_days,
            "page_size": (
                self.PAGE_SIZE
            ),
            "single_events": True,
            "show_deleted": True,
            "time_min": time_min,
            "time_max": time_max,
            "last_full_sync_at": (
                last_full_sync_at
            ),
            "updated_at": (
                self._now_text()
            ),
        }

        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            self.state_path.with_suffix(
                self.state_path.suffix
                + ".tmp"
            )
        )

        temporary_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        max_attempts = 5

        try:

            for attempt in range(
                1,
                max_attempts + 1,
            ):

                try:

                    os.replace(
                        temporary_path,
                        self.state_path,
                    )

                    break

                except OSError as exc:

                    winerror = getattr(
                        exc,
                        "winerror",
                        None,
                    )

                    retryable = (
                        isinstance(
                            exc,
                            PermissionError,
                        )
                        or winerror in {
                            5,
                            32,
                        }
                    )

                    if (
                        not retryable
                        or attempt
                        == max_attempts
                    ):

                        raise

                    time.sleep(
                        0.10 * attempt
                    )

        except OSError as exc:

            temporary_path.unlink(
                missing_ok=True
            )

            raise RuntimeError(
                "Unable to save Google "
                "Calendar sync state: "
                f"{exc}"
            ) from exc

    def clear_state(
        self,
    ) -> None:

        self.state_path.unlink(
            missing_ok=True
        )

        temporary_path = (
            self.state_path.with_suffix(
                self.state_path.suffix
                + ".tmp"
            )
        )

        temporary_path.unlink(
            missing_ok=True
        )

    def has_sync_token(
        self,
    ) -> bool:

        return bool(
            self._load_state().get(
                "sync_token"
            )
        )

    # ============================================================
    # STATE VALIDATION
    # ============================================================

    def _state_matches(
        self,
        state: dict[str, Any],
        calendar_key: str,
        past_days: int,
        future_days: int,
    ) -> bool:

        return (
            state.get(
                "version"
            )
            == self.STATE_VERSION
            and bool(
                state.get(
                    "sync_token"
                )
            )
            and state.get(
                "calendar_key"
            )
            == calendar_key
            and state.get(
                "past_days"
            )
            == past_days
            and state.get(
                "future_days"
            )
            == future_days
            and state.get(
                "page_size"
            )
            == self.PAGE_SIZE
            and state.get(
                "single_events"
            )
            is True
            and state.get(
                "show_deleted"
            )
            is True
        )

    def _full_refresh_due(
        self,
        state: dict[str, Any],
    ) -> bool:

        last_full = self._parse_time(
            state.get(
                "last_full_sync_at"
            )
        )

        if last_full is None:

            return True

        age = (
            self._now()
            - last_full
        )

        return age >= timedelta(
            hours=(
                self.FULL_REFRESH_HOURS
            )
        )

    # ============================================================
    # GOOGLE ERROR
    # ============================================================

    @staticmethod
    def _is_sync_token_error(
        error: HttpError,
    ) -> bool:

        status = getattr(
            error.resp,
            "status",
            None,
        )

        return status == 410

    # ============================================================
    # CONVERT EVENT
    # ============================================================

    def _convert_event(
        self,
        raw_event: dict[str, Any],
        primary: dict[str, Any],
    ) -> dict[str, Any] | None:

        calendar_id = primary[
            "calendar_id"
        ]

        event = (
            self.connector
            ._convert_event(
                raw_event,
                calendar_id=(
                    calendar_id
                ),
                calendar_name=(
                    primary.get(
                        "name",
                        "",
                    )
                ),
            )
        )

        if event is None:

            return None

        provider_event_id = (
            event[
                "external_id"
            ]
        )

        event[
            "provider_event_id"
        ] = provider_event_id

        event[
            "external_id"
        ] = (
            self.base_sync
            ._local_external_id(
                calendar_id,
                provider_event_id,
            )
        )

        event[
            "calendar_primary"
        ] = True

        event[
            "calendar_timezone"
        ] = primary.get(
            "timezone",
            "",
        )

        event[
            "calendar_access_role"
        ] = primary.get(
            "access_role",
            "",
        )

        return event

    # ============================================================
    # FULL REMOTE FETCH
    # ============================================================

    def _fetch_full(
        self,
        primary: dict[str, Any],
        past_days: int,
        future_days: int,
    ) -> tuple[
        list[dict[str, Any]],
        str,
        str,
        str,
    ]:

        time_min, time_max = (
            self.base_sync
            ._build_window(
                past_days,
                future_days,
            )
        )

        service = (
            self.connector
            ._get_service()
        )

        calendar_id = primary[
            "calendar_id"
        ]

        events = []

        page_token = None

        next_sync_token = None

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
                    maxResults=(
                        self.PAGE_SIZE
                    ),
                    pageToken=page_token,
                )
                .execute()
            )

            for raw_event in response.get(
                "items",
                [],
            ):

                event = self._convert_event(
                    raw_event,
                    primary,
                )

                if event is not None:

                    events.append(
                        event
                    )

            page_token = response.get(
                "nextPageToken"
            )

            if page_token:

                continue

            next_sync_token = (
                response.get(
                    "nextSyncToken"
                )
            )

            break

        if not next_sync_token:

            raise RuntimeError(
                "Google Calendar did not "
                "return nextSyncToken after "
                "the full synchronization."
            )

        return (
            events,
            next_sync_token,
            time_min,
            time_max,
        )

    # ============================================================
    # INCREMENTAL REMOTE FETCH
    # ============================================================

    def _fetch_changes(
        self,
        primary: dict[str, Any],
        sync_token: str,
    ) -> tuple[
        list[dict[str, Any]],
        str,
    ]:

        service = (
            self.connector
            ._get_service()
        )

        calendar_id = primary[
            "calendar_id"
        ]

        changes = []

        page_token = None

        next_sync_token = None

        while True:

            # IMPORTANT:
            #
            # Google does not permit timeMin,
            # timeMax or orderBy together with
            # syncToken.
            response = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    syncToken=sync_token,
                    singleEvents=True,
                    showDeleted=True,
                    maxResults=(
                        self.PAGE_SIZE
                    ),
                    pageToken=page_token,
                )
                .execute()
            )

            for raw_event in response.get(
                "items",
                [],
            ):

                event = self._convert_event(
                    raw_event,
                    primary,
                )

                if event is not None:

                    changes.append(
                        event
                    )

            page_token = response.get(
                "nextPageToken"
            )

            if page_token:

                continue

            next_sync_token = (
                response.get(
                    "nextSyncToken"
                )
            )

            break

        if not next_sync_token:

            raise RuntimeError(
                "Google Calendar did not "
                "return nextSyncToken after "
                "incremental synchronization."
            )

        return (
            changes,
            next_sync_token,
        )

    # ============================================================
    # RECONCILE FULL WINDOW
    # ============================================================

    def _reconcile_missing(
        self,
        source_id: str,
        active_remote_ids: set[str],
    ) -> int:

        local_events = (
            self.calendar_service
            .list_events(
                source_id=source_id,
                active_only=True,
            )
        )

        archived = 0

        for local_event in local_events:

            external_id = (
                local_event.external_id
            )

            if not external_id:

                continue

            if external_id in (
                active_remote_ids
            ):

                continue

            (
                self.calendar_service
                .manager
                .update_ingested_record(
                    record_id=(
                        local_event.record_id
                    ),
                    status="archived",
                )
            )

            archived += 1

        return archived

    # ============================================================
    # FULL SYNC
    # ============================================================

    def full_sync(
        self,
        past_days: int = (
            DEFAULT_PAST_DAYS
        ),
        future_days: int = (
            DEFAULT_FUTURE_DAYS
        ),
        reason: str = "initial",
        primary:
        dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        if primary is None:

            primary = (
                self.base_sync
                ._get_primary_calendar()
            )

        source = (
            self.connector
            .register_local_source()
        )

        (
            events,
            sync_token,
            time_min,
            time_max,
        ) = self._fetch_full(
            primary,
            past_days,
            future_days,
        )

        created = 0

        updated = 0

        deleted = 0

        active_remote_ids: set[str] = (
            set()
        )

        for event in events:

            if event[
                "deleted"
            ]:

                if (
                    self.base_sync
                    ._mark_deleted(
                        source.source_id,
                        event,
                    )
                ):

                    deleted += 1

                continue

            active_remote_ids.add(
                event[
                    "external_id"
                ]
            )

            action = (
                self.base_sync
                ._upsert(
                    source.source_id,
                    event,
                )
            )

            if action == "created":

                created += 1

            else:

                updated += 1

        archived = (
            self._reconcile_missing(
                source.source_id,
                active_remote_ids,
            )
        )

        (
            self.calendar_service
            .manager
            .mark_source_synced(
                source.source_id
            )
        )

        calendar_key = (
            self.base_sync
            ._calendar_key(
                primary[
                    "calendar_id"
                ]
            )
        )

        full_sync_at = (
            self._now_text()
        )

        self._save_state(
            sync_token=sync_token,
            calendar_key=calendar_key,
            past_days=past_days,
            future_days=future_days,
            time_min=time_min,
            time_max=time_max,
            last_full_sync_at=(
                full_sync_at
            ),
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
            "reason": reason,
            "fallback": (
                reason
                == "expired_sync_token"
            ),
            "fetched": len(
                events
            ),
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "archived": archived,
            "active_events": len(
                active_events
            ),
            "sync_token_saved": (
                self.has_sync_token()
            ),
        }

    # ============================================================
    # INCREMENTAL SYNC
    # ============================================================

    def incremental_sync(
        self,
        past_days: int = (
            DEFAULT_PAST_DAYS
        ),
        future_days: int = (
            DEFAULT_FUTURE_DAYS
        ),
        primary:
        dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        state = (
            self._load_state()
        )

        sync_token = state.get(
            "sync_token"
        )

        if not sync_token:

            return self.full_sync(
                past_days=past_days,
                future_days=future_days,
                reason="missing_sync_token",
                primary=primary,
            )

        if primary is None:

            primary = (
                self.base_sync
                ._get_primary_calendar()
            )

        calendar_key = (
            self.base_sync
            ._calendar_key(
                primary[
                    "calendar_id"
                ]
            )
        )

        if not self._state_matches(
            state,
            calendar_key,
            past_days,
            future_days,
        ):

            return self.full_sync(
                past_days=past_days,
                future_days=future_days,
                reason="configuration_changed",
                primary=primary,
            )

        source = (
            self.connector
            .register_local_source()
        )

        try:

            (
                changes,
                next_sync_token,
            ) = self._fetch_changes(
                primary,
                sync_token,
            )

        except HttpError as exc:

            if not (
                self._is_sync_token_error(
                    exc
                )
            ):

                raise

            self.clear_state()

            return self.full_sync(
                past_days=past_days,
                future_days=future_days,
                reason=(
                    "expired_sync_token"
                ),
                primary=primary,
            )

        created = 0

        updated = 0

        deleted = 0

        for event in changes:

            if event[
                "deleted"
            ]:

                if (
                    self.base_sync
                    ._mark_deleted(
                        source.source_id,
                        event,
                    )
                ):

                    deleted += 1

                continue

            action = (
                self.base_sync
                ._upsert(
                    source.source_id,
                    event,
                )
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

        self._save_state(
            sync_token=(
                next_sync_token
            ),
            calendar_key=calendar_key,
            past_days=past_days,
            future_days=future_days,
            time_min=state.get(
                "time_min",
                "",
            ),
            time_max=state.get(
                "time_max",
                "",
            ),
            last_full_sync_at=(
                state.get(
                    "last_full_sync_at"
                )
                or self._now_text()
            ),
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
            "mode": "incremental",
            "reason": "sync_token",
            "fallback": False,
            "fetched": len(
                changes
            ),
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "archived": 0,
            "active_events": len(
                active_events
            ),
            "sync_token_saved": (
                self.has_sync_token()
            ),
        }

    # ============================================================
    # NORMAL ENTRY POINT
    # ============================================================

    def sync(
        self,
        past_days: int = (
            DEFAULT_PAST_DAYS
        ),
        future_days: int = (
            DEFAULT_FUTURE_DAYS
        ),
    ) -> dict[str, Any]:

        primary = (
            self.base_sync
            ._get_primary_calendar()
        )

        calendar_key = (
            self.base_sync
            ._calendar_key(
                primary[
                    "calendar_id"
                ]
            )
        )

        state = (
            self._load_state()
        )

        if not self._state_matches(
            state,
            calendar_key,
            past_days,
            future_days,
        ):

            return self.full_sync(
                past_days=past_days,
                future_days=future_days,
                reason="initial_or_changed",
                primary=primary,
            )

        if self._full_refresh_due(
            state
        ):

            return self.full_sync(
                past_days=past_days,
                future_days=future_days,
                reason=(
                    "scheduled_window_refresh"
                ),
                primary=primary,
            )

        return self.incremental_sync(
            past_days=past_days,
            future_days=future_days,
            primary=primary,
        )


google_calendar_incremental_sync = (
    GoogleCalendarIncrementalSync()
)