from __future__ import annotations

from datetime import (
    datetime,
    timezone,
    timedelta,
)

from pathlib import Path

from app.personal_data.calendar_query_engine import (
    CalendarQueryEngine,
)

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
    "test_calendar_query_engine.json"
)


def divider(
    title: str,
) -> None:

    print(
        "\n"
        + "=" * 70
    )

    print(title)

    print(
        "=" * 70
    )


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

    local_timezone = timezone(
        timedelta(
            hours=1
        )
    )

    now = datetime(
        2026,
        8,
        24,
        9,
        0,
        tzinfo=local_timezone,
    )

    manager = PersonalDataManager(
        PersonalDataStore(
            TEMP_PATH
        )
    )

    calendar = CalendarService(
        manager
    )

    engine = CalendarQueryEngine(
        calendar
    )

    try:

        source = calendar.register_source(
            name="Test Calendar",
            access_mode="read_only",
        )

        # Monday — today
        calendar.ingest_event(
            source_id=source.source_id,
            external_id="event-today",
            title="Team Standup",
            start_at=(
                "2026-08-24T10:00:00+01:00"
            ),
            end_at=(
                "2026-08-24T11:00:00+01:00"
            ),
        )

        # Tuesday — tomorrow
        calendar.ingest_event(
            source_id=source.source_id,
            external_id="event-tomorrow",
            title="Project Review",
            start_at=(
                "2026-08-25T14:00:00+01:00"
            ),
            end_at=(
                "2026-08-25T15:00:00+01:00"
            ),
        )

        # Friday afternoon
        calendar.ingest_event(
            source_id=source.source_id,
            external_id="event-friday",
            title="Friday Planning",
            start_at=(
                "2026-08-28T13:00:00+01:00"
            ),
            end_at=(
                "2026-08-28T14:00:00+01:00"
            ),
        )

        # ========================================================
        # TEST 1 — CONNECTION
        # ========================================================

        divider(
            "TEST 1 — CONNECTION"
        )

        print(
            "CONNECTED:",
            engine.calendar_connected(),
        )

        # ========================================================
        # TEST 2 — TODAY
        # ========================================================

        divider(
            "TEST 2 — TODAY"
        )

        answer = engine.answer(
            "What do I have today?",
            now=now,
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "TODAY WORKS:",
            (
                answer is not None
                and "Team Standup"
                in answer
            ),
        )

        # ========================================================
        # TEST 3 — TOMORROW
        # ========================================================

        divider(
            "TEST 3 — TOMORROW"
        )

        answer = engine.answer(
            "What do I have tomorrow?",
            now=now,
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "TOMORROW WORKS:",
            (
                answer is not None
                and "Project Review"
                in answer
            ),
        )

        # ========================================================
        # TEST 4 — NEXT EVENT
        # ========================================================

        divider(
            "TEST 4 — NEXT EVENT"
        )

        answer = engine.answer(
            "What is my next meeting?",
            now=now,
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "NEXT EVENT WORKS:",
            (
                answer is not None
                and "Team Standup"
                in answer
            ),
        )

        # ========================================================
        # TEST 5 — BUSY FRIDAY AFTERNOON
        # ========================================================

        divider(
            "TEST 5 — BUSY FRIDAY AFTERNOON"
        )

        answer = engine.answer(
            "Am I free Friday afternoon?",
            now=now,
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "BUSY DETECTED:",
            (
                answer is not None
                and answer.startswith(
                    "No."
                )
                and "Friday Planning"
                in answer
            ),
        )

        # ========================================================
        # TEST 6 — FREE FRIDAY MORNING
        # ========================================================

        divider(
            "TEST 6 — FREE FRIDAY MORNING"
        )

        answer = engine.answer(
            "Am I free Friday morning?",
            now=now,
        )

        print(
            "ANSWER:",
            answer,
        )

        print(
            "FREE DETECTED:",
            (
                answer is not None
                and answer.startswith(
                    "Yes."
                )
            ),
        )

        # ========================================================
        # TEST 7 — DIRECT RANGE
        # ========================================================

        divider(
            "TEST 7 — RANGE QUERY"
        )

        start = datetime(
            2026,
            8,
            25,
            13,
            0,
            tzinfo=local_timezone,
        )

        end = datetime(
            2026,
            8,
            25,
            16,
            0,
            tzinfo=local_timezone,
        )

        events = engine.events_between(
            start,
            end,
        )

        print(
            "RANGE EVENTS:",
            len(events),
        )

        print(
            "RANGE WORKS:",
            (
                len(events) == 1
                and events[0].title
                == "Project Review"
            ),
        )

        # ========================================================
        # TEST 8 — GENERAL QUESTION ISOLATION
        # ========================================================

        divider(
            "TEST 8 — GENERAL ISOLATION"
        )

        question = (
            "What is the capital "
            "of France?"
        )

        print(
            "CAN ANSWER:",
            engine.can_answer(
                question
            ),
        )

        print(
            "ANSWER:",
            engine.answer(
                question,
                now=now,
            ),
        )

        print(
            "GENERAL ISOLATION:",
            (
                not engine.can_answer(
                    question
                )
                and engine.answer(
                    question,
                    now=now,
                )
                is None
            ),
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
        "TEMP FILE DELETED:",
        (
            not TEMP_PATH.exists()
            and not temp_tmp.exists()
        ),
    )


if __name__ == "__main__":

    main()