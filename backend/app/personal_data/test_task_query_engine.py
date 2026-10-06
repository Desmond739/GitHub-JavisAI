from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)

from app.personal_data.task_query_engine import (
    TaskQueryEngine,
)

from app.personal_data.task_service import (
    TaskService,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_task_query_engine.json"
)


FIXED_NOW = datetime.fromisoformat(
    "2026-08-24T09:00:00+01:00"
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

    service = TaskService(
        manager
    )

    engine = TaskQueryEngine(
        service=service,
        now_provider=lambda: FIXED_NOW,
    )

    try:

        source = service.register_source(
            name="Test Tasks",
            source_type="task",
            access_mode="read_write",
        )

        # ========================================================
        # CONTROLLED TEST DATA
        # ========================================================

        service.create_task(
            source_id=source.source_id,
            title="Submit Project Report",
            priority="high",
            due_at=(
                "2026-08-24T10:00:00+01:00"
            ),
            tags=[
                "project",
            ],
        )

        service.create_task(
            source_id=source.source_id,
            title="Review Budget",
            task_status="in_progress",
            priority="urgent",
            due_at=(
                "2026-08-25T14:00:00+01:00"
            ),
        )

        service.create_task(
            source_id=source.source_id,
            title="Old Pending Task",
            priority="normal",
            due_at=(
                "2026-08-23T18:00:00+01:00"
            ),
        )

        completed = service.create_task(
            source_id=source.source_id,
            title="Completed Setup",
            due_at=(
                "2026-08-24T08:00:00+01:00"
            ),
        )

        service.complete_task(
            completed.record_id,
            completed_at=(
                "2026-08-24T08:30:00+01:00"
            ),
        )

        service.create_task(
            source_id=source.source_id,
            title="Call Supplier",
            record_type="reminder",
            reminder_at=(
                "2026-08-24T15:00:00+01:00"
            ),
        )

        before = manager.counts()

        # ========================================================
        # CAN ANSWER
        # ========================================================

        divider(
            "INTENT"
        )

        print(
            "TASK INTENT:",
            engine.can_answer(
                "What tasks do I have?"
            ),
        )

        print(
            "REMINDER INTENT:",
            engine.can_answer(
                "What reminders do I have?"
            ),
        )

        print(
            "GENERAL ISOLATION:",
            not engine.can_answer(
                "What is the capital of France?"
            ),
        )

        print(
            "WRITE COMMAND ISOLATION:",
            not engine.can_answer(
                "Remind me to call John tomorrow."
            ),
        )

        # ========================================================
        # OPEN TASKS
        # ========================================================

        divider(
            "OPEN TASKS"
        )

        answer = engine.answer(
            "What tasks do I have?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "OPEN TASKS WORK:",
            (
                answer is not None
                and "Submit Project Report"
                in answer
                and "Review Budget"
                in answer
                and "Old Pending Task"
                in answer
                and "Completed Setup"
                not in answer
            ),
        )

        # ========================================================
        # DUE TODAY
        # ========================================================

        divider(
            "DUE TODAY"
        )

        answer = engine.answer(
            "What tasks are due today?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "TODAY WORKS:",
            (
                answer is not None
                and "Submit Project Report"
                in answer
                and "Review Budget"
                not in answer
            ),
        )

        # ========================================================
        # DUE TOMORROW
        # ========================================================

        divider(
            "DUE TOMORROW"
        )

        answer = engine.answer(
            "What is due tomorrow?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "TOMORROW WORKS:",
            (
                answer is not None
                and "Review Budget"
                in answer
            ),
        )

        # ========================================================
        # URGENT
        # ========================================================

        divider(
            "URGENT"
        )

        answer = engine.answer(
            "What are my urgent tasks?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "URGENT WORKS:",
            (
                answer is not None
                and "Review Budget"
                in answer
                and "Submit Project Report"
                not in answer
            ),
        )

        # ========================================================
        # OVERDUE
        # ========================================================

        divider(
            "OVERDUE"
        )

        answer = engine.answer(
            "What tasks are overdue?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "OVERDUE WORKS:",
            (
                answer is not None
                and "Old Pending Task"
                in answer
            ),
        )

        # ========================================================
        # COMPLETED
        # ========================================================

        divider(
            "COMPLETED"
        )

        answer = engine.answer(
            "What have I completed?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "COMPLETED WORKS:",
            (
                answer is not None
                and "Completed Setup"
                in answer
            ),
        )

        # ========================================================
        # REMINDERS
        # ========================================================

        divider(
            "REMINDERS"
        )

        answer = engine.answer(
            "What reminders do I have?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "REMINDERS WORK:",
            (
                answer is not None
                and "Call Supplier"
                in answer
            ),
        )

        # ========================================================
        # REMINDERS TODAY
        # ========================================================

        divider(
            "REMINDERS TODAY"
        )

        answer = engine.answer(
            "What reminders do I have today?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "REMINDERS TODAY WORK:",
            (
                answer is not None
                and "Call Supplier"
                in answer
            ),
        )

        # ========================================================
        # THIS WEEK
        # ========================================================

        divider(
            "THIS WEEK"
        )

        answer = engine.answer(
            "What is due this week?"
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "THIS WEEK WORKS:",
            (
                answer is not None
                and "Submit Project Report"
                in answer
                and "Review Budget"
                in answer
            ),
        )

        # ========================================================
        # READ-ONLY CHECK
        # ========================================================

        after = manager.counts()

        divider(
            "READ ONLY"
        )

        print(
            "DATA UNCHANGED:",
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