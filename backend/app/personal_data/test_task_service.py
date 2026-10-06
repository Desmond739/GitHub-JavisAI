from __future__ import annotations

from pathlib import Path

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)

from app.personal_data.task_service import (
    TaskService,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_task_service.json"
)


def divider(
    title: str,
) -> None:

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:

    TEMP_PATH.unlink(
        missing_ok=True
    )

    temp_tmp = Path(
        str(TEMP_PATH)
        + ".tmp"
    )

    temp_tmp.unlink(
        missing_ok=True
    )

    store = PersonalDataStore(
        TEMP_PATH
    )

    manager = PersonalDataManager(
        store
    )

    tasks = TaskService(
        manager
    )

    try:

        # ========================================================
        # TEST 1 — READ-WRITE LOCAL SOURCE
        # ========================================================

        divider(
            "TEST 1 — TASK SOURCE"
        )

        source = tasks.register_source(
            name="Local Tasks",
            source_type="task",
            access_mode="read_write",
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
        # TEST 2 — CREATE
        # ========================================================

        divider(
            "TEST 2 — CREATE TASK"
        )

        task = tasks.create_task(
            source_id=source.source_id,
            title="Complete MoneroAI Task Phase",
            description=(
                "Build and validate "
                "task integration."
            ),
            priority="high",
            due_at=(
                "2026-08-24T18:00:00+01:00"
            ),
            tags=[
                "MoneroAI",
                "Development",
            ],
        )

        print(
            "TITLE:",
            task.title,
        )

        print(
            "TYPE:",
            task.record_type,
        )

        print(
            "STATUS:",
            task.attributes[
                "task_status"
            ],
        )

        print(
            "PRIORITY:",
            task.attributes[
                "priority"
            ],
        )

        # ========================================================
        # TEST 3 — SEARCH
        # ========================================================

        divider(
            "TEST 3 — SEARCH"
        )

        print(
            "TITLE SEARCH:",
            len(
                tasks.search_tasks(
                    "MoneroAI"
                )
            ),
        )

        print(
            "TAG SEARCH:",
            len(
                tasks.search_tasks(
                    "Development"
                )
            ),
        )

        # ========================================================
        # TEST 4 — UPDATE
        # ========================================================

        divider(
            "TEST 4 — UPDATE"
        )

        updated = tasks.update_task(
            task.record_id,
            task_status="in_progress",
            priority="urgent",
        )

        print(
            "STATUS:",
            updated.attributes[
                "task_status"
            ],
        )

        print(
            "PRIORITY:",
            updated.attributes[
                "priority"
            ],
        )

        # ========================================================
        # TEST 5 — COMPLETE
        # ========================================================

        divider(
            "TEST 5 — COMPLETE"
        )

        completed = tasks.complete_task(
            task.record_id,
            completed_at=(
                "2026-08-24T17:30:00+01:00"
            ),
        )

        print(
            "STATUS:",
            completed.attributes[
                "task_status"
            ],
        )

        print(
            "COMPLETED AT EXISTS:",
            bool(
                completed.attributes[
                    "completed_at"
                ]
            ),
        )

        # ========================================================
        # TEST 6 — REMINDER RECORD
        # ========================================================

        divider(
            "TEST 6 — REMINDER"
        )

        reminder = tasks.create_task(
            source_id=source.source_id,
            title="Review MoneroAI",
            reminder_at=(
                "2026-08-25T09:00:00+01:00"
            ),
            record_type="reminder",
        )

        print(
            "TYPE:",
            reminder.record_type,
        )

        print(
            "REMINDER EXISTS:",
            bool(
                reminder.attributes[
                    "reminder_at"
                ]
            ),
        )

        # ========================================================
        # TEST 7 — SUMMARY
        # ========================================================

        divider(
            "TEST 7 — SUMMARY"
        )

        summary = tasks.summary(
            source.source_id
        )

        print(
            "SUMMARY:",
            summary,
        )

        print(
            "TOTAL RECORDS:",
            summary[
                "records"
            ],
        )

        # ========================================================
        # TEST 8 — EXTERNAL READ-ONLY SOURCE
        # ========================================================

        divider(
            "TEST 8 — READ-ONLY SOURCE"
        )

        remote = tasks.register_source(
            name="External Tasks",
            source_type="task",
            access_mode="read_only",
        )

        ingested = tasks.ingest_task(
            source_id=remote.source_id,
            external_id="remote-001",
            title="Imported Task",
            due_at=(
                "2026-08-26T12:00:00+01:00"
            ),
        )

        print(
            "INGESTED:",
            ingested.title,
        )

        try:

            tasks.create_task(
                source_id=remote.source_id,
                title="Forbidden Local Write",
            )

            print(
                "WRITE BLOCK FAILED"
            )

        except PermissionError:

            print(
                "WRITE BLOCK PASSED"
            )

        # ========================================================
        # TEST 9 — EXTERNAL UPSERT
        # ========================================================

        divider(
            "TEST 9 — EXTERNAL UPSERT"
        )

        second = tasks.ingest_task(
            source_id=remote.source_id,
            external_id="remote-001",
            title="Imported Task Updated",
            priority="high",
        )

        print(
            "SAME RECORD:",
            (
                ingested.record_id
                == second.record_id
            ),
        )

        print(
            "REMOTE COUNT:",
            len(
                tasks.list_tasks(
                    source_id=(
                        remote.source_id
                    )
                )
            ),
        )

        # ========================================================
        # TEST 10 — PERSISTENCE
        # ========================================================

        divider(
            "TEST 10 — PERSISTENCE"
        )

        before = store.counts()

        reloaded = TaskService(
            PersonalDataManager(
                PersonalDataStore(
                    TEMP_PATH
                )
            )
        )

        after = (
            reloaded.manager
            .counts()
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

    finally:

        TEMP_PATH.unlink(
            missing_ok=True
        )

        temp_tmp.unlink(
            missing_ok=True
        )

    divider(
        "FINAL"
    )

    print(
        "TEMP DATA DELETED:",
        (
            not TEMP_PATH.exists()
            and not temp_tmp.exists()
        ),
    )


if __name__ == "__main__":

    main()