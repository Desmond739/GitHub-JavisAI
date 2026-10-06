from __future__ import annotations

from pathlib import Path

from app.personal_data.notes_query_engine import (
    NotesQueryEngine,
)

from app.personal_data.notes_service import (
    NotesService,
)

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_notes_query_engine.json"
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

    service = NotesService(
        manager
    )

    engine = NotesQueryEngine(
        service
    )

    try:

        source = (
            service.register_source(
                name="Test Notes",
                access_mode="read_write",
            )
        )

        # ========================================================
        # CONTROLLED DATA
        # ========================================================

        service.create_note(
            source_id=source.source_id,
            title="MoneroAI Vision",
            content=(
                "Build a personal AI "
                "assistant with long-term "
                "personal context."
            ),
            notebook="Projects",
            tags=[
                "MoneroAI",
                "AI",
            ],
            pinned=True,
        )

        service.create_note(
            source_id=source.source_id,
            title="Cybersecurity Roadmap",
            content=(
                "Study networking, security, "
                "cloud and defensive security."
            ),
            notebook="Career",
            tags=[
                "Cybersecurity",
                "Career",
            ],
        )

        service.create_note(
            source_id=source.source_id,
            title="SMS Project Ideas",
            content=(
                "Review customer usage, "
                "churn and bundle design."
            ),
            notebook="Work",
            tags=[
                "SMS",
                "Project",
            ],
        )

        before = (
            manager.counts()
        )

        # ========================================================
        # INTENT
        # ========================================================

        divider(
            "INTENT"
        )

        print(
            "NOTES INTENT:",
            engine.can_answer(
                "What notes do I have?"
            )
        )

        print(
            "SEARCH INTENT:",
            engine.can_answer(
                "What notes do I have about MoneroAI?"
            )
        )

        print(
            "WRITE COMMAND ISOLATION:",
            not engine.can_answer(
                "Remember that I need "
                "to finish MoneroAI."
            )
        )

        print(
            "GENERAL ISOLATION:",
            not engine.can_answer(
                "What is the capital of France?"
            )
        )

        # ========================================================
        # ALL NOTES
        # ========================================================

        divider(
            "ALL NOTES"
        )

        answer = engine.answer(
            "What notes do I have?"
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "ALL NOTES WORK:",
            (
                answer is not None
                and "MoneroAI Vision"
                in answer
                and "Cybersecurity Roadmap"
                in answer
                and "SMS Project Ideas"
                in answer
            )
        )

        # ========================================================
        # MONEROAI SEARCH
        # ========================================================

        divider(
            "MONEROAI SEARCH"
        )

        answer = engine.answer(
            "What notes do I have "
            "about MoneroAI?"
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "MONEROAI SEARCH WORK:",
            (
                answer is not None
                and "MoneroAI Vision"
                in answer
                and "Cybersecurity Roadmap"
                not in answer
            )
        )

        # ========================================================
        # CONTENT SEARCH
        # ========================================================

        divider(
            "CONTENT SEARCH"
        )

        answer = engine.answer(
            "What did I write "
            "about networking?"
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "CONTENT SEARCH WORK:",
            (
                answer is not None
                and "Cybersecurity Roadmap"
                in answer
            )
        )

        # ========================================================
        # TAG SEARCH
        # ========================================================

        divider(
            "TAG SEARCH"
        )

        answer = engine.answer(
            "Find my note "
            "about SMS."
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "TAG SEARCH WORK:",
            (
                answer is not None
                and "SMS Project Ideas"
                in answer
            )
        )

        # ========================================================
        # PROJECT SEARCH
        # ========================================================

        divider(
            "PROJECT SEARCH"
        )

        answer = engine.answer(
            "Show my project notes."
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "PROJECT SEARCH WORK:",
            (
                answer is not None
                and (
                    "MoneroAI Vision"
                    in answer
                    or
                    "SMS Project Ideas"
                    in answer
                )
            )
        )

        # ========================================================
        # PINNED
        # ========================================================

        divider(
            "PINNED"
        )

        answer = engine.answer(
            "Show my pinned notes."
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "PINNED WORK:",
            (
                answer is not None
                and "MoneroAI Vision"
                in answer
                and "Cybersecurity Roadmap"
                not in answer
            )
        )

        # ========================================================
        # NO MATCH
        # ========================================================

        divider(
            "NO MATCH"
        )

        answer = engine.answer(
            "Find my note about astronomy."
        )

        print(
            "ANSWER:",
            answer
        )

        print(
            "NO MATCH WORK:",
            (
                answer is not None
                and "no notes matching"
                in answer.casefold()
            )
        )

        # ========================================================
        # READ-ONLY PROTECTION
        # ========================================================

        after = (
            manager.counts()
        )

        divider(
            "READ ONLY"
        )

        print(
            "DATA UNCHANGED:",
            before == after
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
            and
            not temp_tmp.exists()
        )
    )


if __name__ == "__main__":

    main()