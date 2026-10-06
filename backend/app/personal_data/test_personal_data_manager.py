from __future__ import annotations

from pathlib import Path

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_personal_data_manager.json"
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

    try:

        # ========================================================
        # TEST 1 — EMPTY MANAGER
        # ========================================================

        divider(
            "TEST 1 — EMPTY MANAGER"
        )

        print(
            "COUNTS:",
            manager.counts(),
        )

        # ========================================================
        # TEST 2 — REGISTER READ-ONLY CALENDAR
        # ========================================================

        divider(
            "TEST 2 — REGISTER SOURCE"
        )

        calendar = (
            manager.register_source(
                source_type="calendar",
                name="Personal Calendar",
                access_mode="read_only",
                permissions_required=[
                    "calendar.read",
                ],
            )
        )

        print(
            "SOURCE:",
            calendar.name,
        )

        print(
            "ACCESS:",
            calendar.access_mode,
        )

        print(
            "STATUS:",
            calendar.status,
        )

        # ========================================================
        # TEST 3 — SOURCE DEDUP
        # ========================================================

        divider(
            "TEST 3 — SOURCE DEDUP"
        )

        duplicate = (
            manager.register_source(
                source_type="calendar",
                name="Personal Calendar",
            )
        )

        print(
            "SAME SOURCE:",
            (
                calendar.source_id
                == duplicate.source_id
            ),
        )

        # ========================================================
        # TEST 4 — INGEST INTO READ-ONLY SOURCE
        # ========================================================

        divider(
            "TEST 4 — READ-ONLY INGESTION"
        )

        imported = manager.ingest_record(
            source_id=calendar.source_id,
            record_type="event",
            title="Imported Meeting",
            content=(
                "Imported from external "
                "calendar."
            ),
            external_id="event-001",
        )

        print(
            "INGESTED:",
            imported.title,
        )

        print(
            "RECORDS:",
            len(
                manager.list_records(
                    source_id=(
                        calendar.source_id
                    )
                )
            ),
        )

        # ========================================================
        # TEST 5 — READ-ONLY WRITE BLOCK
        # ========================================================

        divider(
            "TEST 5 — READ-ONLY WRITE BLOCK"
        )

        try:

            manager.create_record(
                source_id=(
                    calendar.source_id
                ),
                record_type="event",
                title=(
                    "AI-Created Meeting"
                ),
            )

            print(
                "WRITE PROTECTION FAILED"
            )

        except PermissionError as exc:

            print(
                "WRITE PROTECTION PASSED:",
                exc,
            )

        # ========================================================
        # TEST 6 — ENABLE WRITE MODE
        # ========================================================

        divider(
            "TEST 6 — ENABLE WRITE MODE"
        )

        calendar = (
            manager.set_access_mode(
                calendar.source_id,
                "read_write",
            )
        )

        print(
            "ACCESS:",
            calendar.access_mode,
        )

        created = (
            manager.create_record(
                source_id=(
                    calendar.source_id
                ),
                record_type="event",
                title=(
                    "AI-Created Meeting"
                ),
                content=(
                    "Created through "
                    "PersonalDataManager."
                ),
            )
        )

        print(
            "CREATED:",
            created.title,
        )

        # ========================================================
        # TEST 7 — USER UPDATE
        # ========================================================

        divider(
            "TEST 7 — UPDATE RECORD"
        )

        updated = manager.update_record(
            created.record_id,
            title=(
                "Updated AI Meeting"
            ),
        )

        print(
            "UPDATED:",
            updated.title,
        )

        # ========================================================
        # TEST 8 — SOURCE DISABLED
        # ========================================================

        divider(
            "TEST 8 — DISABLED SOURCE"
        )

        calendar = (
            manager.set_source_status(
                calendar.source_id,
                "disabled",
            )
        )

        print(
            "STATUS:",
            calendar.status,
        )

        try:

            manager.ingest_record(
                source_id=(
                    calendar.source_id
                ),
                record_type="event",
                title=(
                    "Should Not Import"
                ),
            )

            print(
                "DISABLED PROTECTION FAILED"
            )

        except RuntimeError as exc:

            print(
                "DISABLED PROTECTION PASSED:",
                exc,
            )

        # ========================================================
        # TEST 9 — REACTIVATE + MARK SYNCED
        # ========================================================

        divider(
            "TEST 9 — REACTIVATE AND SYNC"
        )

        calendar = (
            manager.set_source_status(
                calendar.source_id,
                "active",
            )
        )

        synced = (
            manager.mark_source_synced(
                calendar.source_id
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
        # TEST 10 — LOCAL SYNC UPDATE
        # ========================================================

        divider(
            "TEST 10 — INGESTED RECORD UPDATE"
        )

        manager.set_access_mode(
            calendar.source_id,
            "read_only",
        )

        sync_updated = (
            manager.update_ingested_record(
                imported.record_id,
                title=(
                    "Updated External Meeting"
                ),
            )
        )

        print(
            "UPDATED:",
            sync_updated.title,
        )

        # ========================================================
        # TEST 11 — SOURCE SUMMARY
        # ========================================================

        divider(
            "TEST 11 — SOURCE SUMMARY"
        )

        summary = (
            manager.source_summary(
                calendar.source_id
            )
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

        before = manager.counts()

        reloaded_manager = (
            PersonalDataManager(
                PersonalDataStore(
                    TEMP_PATH
                )
            )
        )

        after = (
            reloaded_manager.counts()
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

        reloaded_summary = (
            reloaded_manager
            .source_summary(
                calendar.source_id
            )
        )

        print(
            "SUMMARY RELOADED:",
            (
                reloaded_summary[
                    "records"
                ]
                == 2
            ),
        )

    finally:

        TEMP_PATH.unlink(
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