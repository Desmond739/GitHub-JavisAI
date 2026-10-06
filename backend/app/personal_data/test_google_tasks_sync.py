from __future__ import annotations

from pathlib import Path

from app.personal_data.google_tasks_sync import (
    GoogleTasksSync,
)

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
    "test_google_tasks_sync.json"
)


class FakeGoogleTasksConnector:

    def __init__(
        self,
    ) -> None:

        self.version = 1

    def fetch_tasklists(
        self,
    ):

        return [
            {
                "id": "list-001",
                "title": "My Tasks",
            }
        ]

    def fetch_tasks(
        self,
        tasklist_id,
        **kwargs,
    ):

        if self.version == 1:

            return [
                {
                    "id": "task-001",
                    "title": "Prepare Report",
                    "notes": "Finish draft",
                    "status": "needsAction",
                    "due": (
                        "2026-08-25T00:00:00.000Z"
                    ),
                    "updated": (
                        "2026-08-23T10:00:00Z"
                    ),
                    "deleted": False,
                    "hidden": False,
                },
                {
                    "id": "task-002",
                    "title": "Complete Setup",
                    "status": "completed",
                    "completed": (
                        "2026-08-23T11:00:00Z"
                    ),
                    "updated": (
                        "2026-08-23T11:00:00Z"
                    ),
                    "deleted": False,
                    "hidden": False,
                },
            ]

        return [
            {
                "id": "task-001",
                "title": (
                    "Prepare Final Report"
                ),
                "notes": (
                    "Finish final draft"
                ),
                "status": "completed",
                "completed": (
                    "2026-08-24T09:00:00Z"
                ),
                "due": (
                    "2026-08-25T00:00:00.000Z"
                ),
                "updated": (
                    "2026-08-24T09:00:00Z"
                ),
                "deleted": False,
                "hidden": False,
            }
        ]


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

    connector = (
        FakeGoogleTasksConnector()
    )

    store = PersonalDataStore(
        TEMP_PATH
    )

    manager = PersonalDataManager(
        store
    )

    service = TaskService(
        manager
    )

    sync = GoogleTasksSync(
        connector=connector,
        service=service,
    )

    try:

        print("=" * 70)
        print("FIRST SYNC")
        print("=" * 70)

        first = sync.sync()

        print(
            "MODE:",
            first["mode"]
        )

        print(
            "ACCESS:",
            first[
                "access_mode"
            ]
        )

        print(
            "FETCHED:",
            first[
                "fetched"
            ]
        )

        print(
            "CREATED:",
            first[
                "created"
            ]
        )

        print(
            "ACTIVE:",
            first[
                "active_tasks"
            ]
        )

        records = (
            service.list_tasks(
                active_only=True
            )
        )

        print(
            "LOCAL ACTIVE COUNT:",
            len(records)
        )

        due_records = [
            record
            for record in records
            if record.title
            == "Prepare Report"
        ]

        print(
            "DUE DATE PRESERVED:",
            (
                len(
                    due_records
                )
                == 1
                and
                due_records[0]
                .attributes
                .get(
                    "due_at"
                )
                == "2026-08-25"
            )
        )

        print(
            "DATE ONLY FLAG:",
            (
                len(
                    due_records
                )
                == 1
                and
                due_records[0]
                .attributes
                .get(
                    "due_is_date_only"
                )
                is True
            )
        )

        print()
        print("=" * 70)
        print("SECOND SYNC")
        print("=" * 70)

        connector.version = 2

        second = sync.sync()

        print(
            "FETCHED:",
            second[
                "fetched"
            ]
        )

        print(
            "CREATED:",
            second[
                "created"
            ]
        )

        print(
            "UPDATED:",
            second[
                "updated"
            ]
        )

        print(
            "DELETED:",
            second[
                "deleted"
            ]
        )

        print(
            "ACTIVE:",
            second[
                "active_tasks"
            ]
        )

        all_records = (
            service.list_tasks(
                active_only=False
            )
        )

        active_records = [
            record
            for record
            in all_records
            if record.status
            == "active"
        ]

        deleted_records = [
            record
            for record
            in all_records
            if record.status
            == "deleted"
        ]

        print(
            "NO DUPLICATES:",
            len(
                all_records
            ) == 2
        )

        print(
            "ACTIVE COUNT:",
            len(
                active_records
            )
        )

        print(
            "DELETED COUNT:",
            len(
                deleted_records
            )
        )

        final_task = (
            active_records[0]
            if active_records
            else None
        )

        print(
            "TITLE UPDATED:",
            (
                final_task is not None
                and final_task.title
                == "Prepare Final Report"
            )
        )

        print(
            "COMPLETED:",
            (
                final_task is not None
                and
                final_task.attributes.get(
                    "task_status"
                )
                == "completed"
            )
        )

        print(
            "SOURCE READ ONLY:",
            all(
                source.access_mode
                == "read_only"
                for source
                in manager.list_sources()
            )
        )

    finally:

        TEMP_PATH.unlink(
            missing_ok=True
        )

        temp_tmp.unlink(
            missing_ok=True
        )

    print()
    print("=" * 70)
    print("FINAL")
    print("=" * 70)

    print(
        "TEMP DATA DELETED:",
        (
            not TEMP_PATH.exists()
            and
            not temp_tmp.exists()
        )
    )


if __name__ == "__main__":

    main()