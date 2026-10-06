from __future__ import annotations

from pathlib import Path

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_personal_data.json"
)


def separator(
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

    try:

        # ========================================================
        # TEST 1 — EMPTY STORE
        # ========================================================

        separator(
            "TEST 1 — EMPTY STORE"
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 2 — ADD SOURCE
        # ========================================================

        separator(
            "TEST 2 — ADD SOURCE"
        )

        source = store.add_source(
            source_type="calendar",
            name="Personal Calendar",
            access_mode="read_only",
            permissions_required=[
                "calendar.read",
            ],
        )

        print(
            "SOURCE:",
            source.to_dict(),
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 3 — SOURCE DEDUPLICATION
        # ========================================================

        separator(
            "TEST 3 — SOURCE DEDUPLICATION"
        )

        duplicate_source = (
            store.add_source(
                source_type="calendar",
                name="Personal Calendar",
                access_mode="read_only",
            )
        )

        print(
            "SAME SOURCE ID:",
            (
                source.source_id
                == duplicate_source.source_id
            ),
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 4 — ADD RECORD
        # ========================================================

        separator(
            "TEST 4 — ADD RECORD"
        )

        record = store.add_record(
            source_id=source.source_id,
            record_type="event",
            title="MoneroAI Meeting",
            content=(
                "Discuss Phase 23 "
                "development."
            ),
            sensitivity="private",
            external_id="event-001",
            occurred_at=(
                "2026-08-25T10:00:00"
            ),
        )

        print(
            "RECORD:",
            record.to_dict(),
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 5 — EXTERNAL-ID DEDUPLICATION
        # ========================================================

        separator(
            "TEST 5 — RECORD DEDUPLICATION"
        )

        duplicate_record = (
            store.add_record(
                source_id=source.source_id,
                record_type="event",
                title="Duplicate Event",
                external_id="event-001",
            )
        )

        print(
            "SAME RECORD ID:",
            (
                record.record_id
                == duplicate_record.record_id
            ),
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 6 — UPDATE
        # ========================================================

        separator(
            "TEST 6 — UPDATE RECORD"
        )

        updated = store.update_record(
            record_id=record.record_id,
            title=(
                "MoneroAI Phase 23 Meeting"
            ),
            content=(
                "Discuss Personal Data "
                "Integration."
            ),
        )

        print(
            "TITLE:",
            updated.title,
        )

        print(
            "CONTENT:",
            updated.content,
        )

        # ========================================================
        # TEST 7 — ARCHIVE
        # ========================================================

        separator(
            "TEST 7 — ARCHIVE RECORD"
        )

        archived = (
            store.archive_record(
                record.record_id
            )
        )

        print(
            "STATUS:",
            archived.status,
        )

        print(
            "COUNTS:",
            store.counts(),
        )

        # ========================================================
        # TEST 8 — REFERENTIAL INTEGRITY
        # ========================================================

        separator(
            "TEST 8 — INVALID SOURCE"
        )

        try:

            store.add_record(
                source_id=(
                    "source-does-not-exist"
                ),
                record_type="event",
                title="Invalid Event",
            )

            print(
                "VALIDATION FAILED"
            )

        except KeyError as exc:

            print(
                "VALIDATION PASSED:",
                exc,
            )

        # ========================================================
        # TEST 9 — PERSISTENCE RELOAD
        # ========================================================

        separator(
            "TEST 9 — PERSISTENCE"
        )

        before = store.counts()

        reloaded = (
            PersonalDataStore(
                TEMP_PATH
            )
        )

        after = (
            reloaded.counts()
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

        reloaded_source = (
            reloaded.get_source(
                source.source_id
            )
        )

        reloaded_record = (
            reloaded.get_record(
                record.record_id
            )
        )

        print(
            "SOURCE RELOADED:",
            (
                reloaded_source
                is not None
            ),
        )

        print(
            "RECORD RELOADED:",
            (
                reloaded_record
                is not None
            ),
        )

        print(
            "ARCHIVE PERSISTED:",
            (
                reloaded_record
                is not None
                and reloaded_record.status
                == "archived"
            ),
        )

    finally:

        TEMP_PATH.unlink(
            missing_ok=True
        )

    separator(
        "FINAL"
    )

    print(
        "TEMP FILE DELETED:",
        not TEMP_PATH.exists(),
    )


if __name__ == "__main__":

    main()