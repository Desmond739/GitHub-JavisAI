from __future__ import annotations

from pathlib import Path

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
    "test_notes_service.json"
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

    store = PersonalDataStore(
        TEMP_PATH
    )

    manager = PersonalDataManager(
        store
    )

    notes = NotesService(
        manager
    )

    try:

        source = notes.register_source(
            name="Local Notes",
            access_mode="read_write",
        )

        print(
            "SOURCE TYPE:",
            source.source_type
        )

        print(
            "ACCESS:",
            source.access_mode
        )

        note = notes.create_note(
            source_id=source.source_id,
            title="MoneroAI Vision",
            content=(
                "Build a long-term "
                "personal AI assistant."
            ),
            notebook="Projects",
            tags=[
                "MoneroAI",
                "AI",
            ],
            pinned=True,
        )

        print(
            "CREATED:",
            note.title
        )

        print(
            "PINNED:",
            note.attributes[
                "pinned"
            ]
        )

        print(
            "TITLE SEARCH:",
            len(
                notes.search_notes(
                    "MoneroAI"
                )
            )
        )

        print(
            "CONTENT SEARCH:",
            len(
                notes.search_notes(
                    "personal AI"
                )
            )
        )

        print(
            "TAG SEARCH:",
            len(
                notes.search_notes(
                    "AI"
                )
            )
        )

        updated = notes.update_note(
            note.record_id,
            title=(
                "MoneroAI Long-Term Vision"
            ),
            tags=[
                "MoneroAI",
                "Vision",
            ],
        )

        print(
            "TITLE UPDATED:",
            updated.title
            == "MoneroAI Long-Term Vision"
        )

        print(
            "PIN PRESERVED:",
            updated.attributes[
                "pinned"
            ]
            is True
        )

        remote = notes.register_source(
            name="External Notes",
            access_mode="read_only",
        )

        ingested = notes.ingest_note(
            source_id=remote.source_id,
            external_id="note-001",
            title="Imported Note",
            content="Imported content.",
        )

        second = notes.ingest_note(
            source_id=remote.source_id,
            external_id="note-001",
            title="Imported Note Updated",
            content="Updated imported content.",
        )

        print(
            "UPSERT SAME RECORD:",
            ingested.record_id
            == second.record_id
        )

        print(
            "REMOTE COUNT:",
            len(
                notes.list_notes(
                    source_id=(
                        remote.source_id
                    )
                )
            )
        )

        try:

            notes.create_note(
                source_id=remote.source_id,
                title="Forbidden",
                content="Should fail.",
            )

            print(
                "WRITE BLOCK PASSED:",
                False
            )

        except PermissionError:

            print(
                "WRITE BLOCK PASSED:",
                True
            )

        summary = notes.summary(
            source.source_id
        )

        print(
            "SUMMARY RECORDS:",
            summary[
                "records"
            ]
        )

        print(
            "SUMMARY PINNED:",
            summary[
                "pinned"
            ]
        )

        before = store.counts()

        reloaded = NotesService(
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
            "PERSISTED:",
            before == after
        )

    finally:

        TEMP_PATH.unlink(
            missing_ok=True
        )

        temp_tmp.unlink(
            missing_ok=True
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