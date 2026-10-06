from __future__ import annotations

from pathlib import Path

from app.personal_data.contacts_query_engine import ContactsQueryEngine
from app.personal_data.contacts_service import ContactsService
from app.personal_data.personal_data_manager import PersonalDataManager
from app.personal_data.personal_data_store import PersonalDataStore


TEMP_PATH = Path(
    "data/personal_data/test_contacts_query_engine.json"
)


def main() -> None:

    TEMP_PATH.unlink(missing_ok=True)
    temporary_write = Path(f"{TEMP_PATH}.tmp")
    temporary_write.unlink(missing_ok=True)

    manager = PersonalDataManager(
        PersonalDataStore(TEMP_PATH)
    )
    contacts = ContactsService(manager)
    engine = ContactsQueryEngine(contacts)

    try:
        source = contacts.register_source(
            name="Test Contacts",
            access_mode="read_only",
        )
        contacts.ingest_contact(
            source_id=source.source_id,
            external_id="people/alice",
            display_name="Alice Example",
            emails=["alice@example.com"],
            phones=["+237 670 000 001"],
        )

        assert engine.can_answer(
            "What is Alice Example's phone number?"
        )
        assert "670 000 001" in (
            engine.answer(
                "What is Alice Example's phone number?"
            )
            or ""
        )
        assert "alice@example.com" in (
            engine.answer(
                "What is the email address for Alice Example?"
            )
            or ""
        )
        assert not engine.can_answer(
            "Add a contact for Bob"
        )

        print("Read-only contacts query checks passed.")

    finally:
        TEMP_PATH.unlink(missing_ok=True)
        temporary_write.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
