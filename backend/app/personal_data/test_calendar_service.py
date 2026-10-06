from __future__ import annotations

from pathlib import Path

from app.personal_data.calendar_service import (
    CalendarService,
)

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_calendar_service.json"
)


def divider(
    title: str,
) -> None:

    print(
        "\n"
        + "=" * 70
    )

    print(
        title
    )

    print(
        "=" * 70
    )


def main() -> None:

    TEMP_PATH.unlink(
        missing_ok=True
    )

    store = PersonalDataStore(
        TEMP_PATH
    )

    manager = PersonalDataManager(
        store
    )

    calendar = CalendarService(
        manager
    )

    try:

        # ========================================================
        # TEST 1 — CALENDAR SOURCE
        # ========================================================

        divider(
            "TEST 1 — CALENDAR SOURCE"
        )

        source = calendar.register_source(
            name="Google Calendar",
            access_mode="read_only",
        )

        print(
            "TYPE:",
            source.source_type,
        )

        print(
            "ACCESS:",
            source.access_mode,
        )

        print(
            "PERMISSIONS:",
            source.permissions_required,
        )

        # ========================================================
        # TEST 2 — INGEST EVENT
        # ========================================================

        divider(
            "TEST 2 — INGEST EVENT"
        )

        event = calendar.ingest_event(
            source_id=source.source_id,
            external_id="event-001",
            title="MoneroAI Planning",
            description=(
                "Plan the next "
                "development phase."
            ),
            start_at=(
                "2026-08-25T10:00:00+01:00"
            ),
            end_at=(
                "2026-08-25T11:00:00+01:00"
            ),
            timezone=(
                "Africa/Douala"
            ),
            location=(
                "Meeting Room"
            ),
            attendees=[
                "member@example.com",
            ],
            organizer=(
                "owner@example.com"
            ),
            event_status="confirmed",
            calendar_name=(
                "Primary"
            ),
        )

        print(
            "TITLE:",
            event.title,
        )

        print(
            "TYPE:",
            event.record_type,
        )

        print(
            "START:",
            event.attributes[
                "start_at"
            ],
        )

        print(
            "LOCATION:",
            event.attributes[
                "location"
            ],
        )

        print(
            "SENSITIVITY:",
            event.sensitivity,
        )

        # ========================================================
        # TEST 3 — EXTERNAL UPSERT
        # ========================================================

        divider(
            "TEST 3 — EXTERNAL UPSERT"
        )

        updated_event = (
            calendar.ingest_event(
                source_id=(
                    source.source_id
                ),
                external_id=(
                    "event-001"
                ),
                title=(
                    "MoneroAI Planning Updated"
                ),
                start_at=(
                    "2026-08-25T10:30:00+01:00"
                ),
                end_at=(
                    "2026-08-25T11:30:00+01:00"
                ),
                location=(
                    "Conference Room"
                ),
                attendees=[
                    "member@example.com",
                ],
            )
        )

        print(
            "SAME RECORD:",
            (
                event.record_id
                ==
                updated_event.record_id
            ),
        )

        print(
            "EVENT COUNT:",
            len(
                calendar.list_events(
                    source.source_id
                )
            ),
        )

        print(
            "UPDATED TITLE:",
            updated_event.title,
        )

        print(
            "UPDATED LOCATION:",
            updated_event.attributes[
                "location"
            ],
        )

        # ========================================================
        # TEST 4 — SEARCH
        # ========================================================

        divider(
            "TEST 4 — SEARCH"
        )

        by_title = calendar.search_events(
            "MoneroAI"
        )

        by_location = calendar.search_events(
            "Conference Room"
        )

        by_attendee = calendar.search_events(
            "member@example.com"
        )

        print(
            "BY TITLE:",
            len(
                by_title
            ),
        )

        print(
            "BY LOCATION:",
            len(
                by_location
            ),
        )

        print(
            "BY ATTENDEE:",
            len(
                by_attendee
            ),
        )

        # ========================================================
        # TEST 5 — READ-ONLY CREATE BLOCK
        # ========================================================

        divider(
            "TEST 5 — READ-ONLY CREATE BLOCK"
        )

        try:

            calendar.create_event(
                source_id=(
                    source.source_id
                ),
                title=(
                    "AI Created Event"
                ),
                start_at=(
                    "2026-08-26T12:00:00+01:00"
                ),
            )

            print(
                "WRITE BLOCK FAILED"
            )

        except PermissionError as exc:

            print(
                "WRITE BLOCK PASSED:",
                exc,
            )

        # ========================================================
        # TEST 6 — READ-WRITE CREATE
        # ========================================================

        divider(
            "TEST 6 — READ-WRITE CREATE"
        )

        manager.set_access_mode(
            source.source_id,
            "read_write",
        )

        created = calendar.create_event(
            source_id=source.source_id,
            title="AI Created Event",
            description=(
                "Created locally."
            ),
            start_at=(
                "2026-08-26T12:00:00+01:00"
            ),
            end_at=(
                "2026-08-26T13:00:00+01:00"
            ),
            location="Office",
            attendees=[
                "test@example.com",
            ],
        )

        print(
            "CREATED:",
            created.title,
        )

        print(
            "TOTAL EVENTS:",
            len(
                calendar.list_events(
                    source.source_id
                )
            ),
        )

        # ========================================================
        # TEST 7 — PARTIAL UPDATE
        # ========================================================

        divider(
            "TEST 7 — PARTIAL UPDATE"
        )

        created = calendar.update_event(
            created.record_id,
            title=(
                "Updated AI Event"
            ),
            location=(
                "New Office"
            ),
        )

        print(
            "TITLE:",
            created.title,
        )

        print(
            "LOCATION:",
            created.attributes[
                "location"
            ],
        )

        print(
            "ATTENDEES PRESERVED:",
            created.attributes[
                "attendees"
            ]
            == [
                "test@example.com"
            ],
        )

        # ========================================================
        # TEST 8 — ARCHIVE
        # ========================================================

        divider(
            "TEST 8 — ARCHIVE"
        )

        archived = (
            calendar.archive_event(
                created.record_id
            )
        )

        print(
            "STATUS:",
            archived.status,
        )

        print(
            "ACTIVE EVENTS:",
            len(
                calendar.list_events(
                    source.source_id,
                    active_only=True,
                )
            ),
        )

        print(
            "ALL EVENTS:",
            len(
                calendar.list_events(
                    source.source_id,
                    active_only=False,
                )
            ),
        )

        # ========================================================
        # TEST 9 — DISABLED SOURCE
        # ========================================================

        divider(
            "TEST 9 — DISABLED SOURCE"
        )

        manager.set_source_status(
            source.source_id,
            "disabled",
        )

        try:

            calendar.ingest_event(
                source_id=(
                    source.source_id
                ),
                external_id=(
                    "event-blocked"
                ),
                title=(
                    "Blocked Event"
                ),
            )

            print(
                "DISABLED BLOCK FAILED"
            )

        except RuntimeError as exc:

            print(
                "DISABLED BLOCK PASSED:",
                exc,
            )

        # ========================================================
        # TEST 10 — REACTIVATE / SYNC
        # ========================================================

        divider(
            "TEST 10 — REACTIVATE AND SYNC"
        )

        manager.set_source_status(
            source.source_id,
            "active",
        )

        synced = (
            manager.mark_source_synced(
                source.source_id
            )
        )

        print(
            "STATUS:",
            synced.status,
        )

        print(
            "LAST SYNC SET:",
            bool(
                synced.last_sync_at
            ),
        )

        # ========================================================
        # TEST 11 — SUMMARY
        # ========================================================

        divider(
            "TEST 11 — SUMMARY"
        )

        summary = calendar.summary(
            source.source_id
        )

        print(
            "SUMMARY:",
            summary,
        )

        # ========================================================
        # TEST 12 — PERSISTENCE
        # ========================================================

        divider(
            "TEST 12 — PERSISTENCE"
        )

        before = calendar.summary(
            source.source_id
        )

        reloaded_calendar = (
            CalendarService(
                PersonalDataManager(
                    PersonalDataStore(
                        TEMP_PATH
                    )
                )
            )
        )

        after = (
            reloaded_calendar.summary(
                source.source_id
            )
        )

        print(
            "BEFORE:",
            before,
        )

        print(
            "AFTER:",
            after,
        )

        print(
            "PERSISTED:",
            before == after,
        )

        print(
            "EVENT RELOADED:",
            (
                reloaded_calendar
                .get_by_external_id(
                    source.source_id,
                    "event-001",
                )
                is not None
            ),
        )

    finally:

        TEMP_PATH.unlink(
            missing_ok=True
        )

        temp_file = Path(
            str(
                TEMP_PATH
            )
            + ".tmp"
        )

        temp_file.unlink(
            missing_ok=True
        )

    divider(
        "FINAL"
    )

    print(
        "TEMP FILE DELETED:",
        not TEMP_PATH.exists(),
    )


if __name__ == "__main__":

    main()