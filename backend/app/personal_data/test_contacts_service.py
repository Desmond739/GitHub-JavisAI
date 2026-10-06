from __future__ import annotations

from pathlib import Path

from app.personal_data.contacts_service import (
    ContactsService,
)

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_contacts_service.json"
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

    store = PersonalDataStore(
        TEMP_PATH
    )

    manager = PersonalDataManager(
        store
    )

    contacts = ContactsService(
        manager
    )

    try:

        # ========================================================
        # TEST 1 — CONTACT SOURCE
        # ========================================================

        divider(
            "TEST 1 — CONTACT SOURCE"
        )

        source = contacts.register_source(
            name="Google Contacts",
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
        # TEST 2 — INGEST CONTACT
        # ========================================================

        divider(
            "TEST 2 — INGEST CONTACT"
        )

        alice = contacts.ingest_contact(
            source_id=source.source_id,
            external_id="people/alice-001",
            display_name="Alice Example",
            given_name="Alice",
            family_name="Example",
            emails=[
                "alice@example.com",
            ],
            phones=[
                "+237 6 70 00 00 01",
            ],
            company="Example Company",
            job_title="AI Engineer",
        )

        print(
            "NAME:",
            alice.title,
        )

        print(
            "TYPE:",
            alice.record_type,
        )

        print(
            "EMAILS:",
            alice.attributes[
                "emails"
            ],
        )

        print(
            "PHONES:",
            alice.attributes[
                "phones"
            ],
        )

        print(
            "SENSITIVITY:",
            alice.sensitivity,
        )

        # ========================================================
        # TEST 3 — EXTERNAL UPSERT
        # ========================================================

        divider(
            "TEST 3 — EXTERNAL UPSERT"
        )

        alice_updated = (
            contacts.ingest_contact(
                source_id=(
                    source.source_id
                ),
                external_id=(
                    "people/alice-001"
                ),
                display_name=(
                    "Alice Example"
                ),
                emails=[
                    "alice.new@example.com",
                ],
                phones=[
                    "+237 6 70 00 00 01",
                ],
                company=(
                    "Updated Company"
                ),
            )
        )

        print(
            "SAME RECORD:",
            (
                alice.record_id
                ==
                alice_updated.record_id
            ),
        )

        print(
            "CONTACT COUNT:",
            len(
                contacts.list_contacts(
                    source.source_id
                )
            ),
        )

        print(
            "UPDATED EMAIL:",
            alice_updated.attributes[
                "emails"
            ],
        )

        print(
            "UPDATED COMPANY:",
            alice_updated.attributes[
                "company"
            ],
        )

        # ========================================================
        # TEST 4 — SEARCH
        # ========================================================

        divider(
            "TEST 4 — SEARCH"
        )

        by_name = (
            contacts.search_contacts(
                "Alice"
            )
        )

        by_email = (
            contacts.search_contacts(
                "alice.new@example.com"
            )
        )

        by_phone = (
            contacts.search_contacts(
                "+237670000001"
            )
        )

        by_company = (
            contacts.search_contacts(
                "Updated Company"
            )
        )

        print(
            "BY NAME:",
            len(by_name),
        )

        print(
            "BY EMAIL:",
            len(by_email),
        )

        print(
            "BY PHONE:",
            len(by_phone),
        )

        print(
            "BY COMPANY:",
            len(by_company),
        )

        # ========================================================
        # TEST 5 — READ-ONLY CREATE BLOCK
        # ========================================================

        divider(
            "TEST 5 — READ-ONLY CREATE BLOCK"
        )

        try:

            contacts.create_contact(
                source_id=(
                    source.source_id
                ),
                display_name=(
                    "Bob Example"
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

        bob = contacts.create_contact(
            source_id=source.source_id,
            display_name="Bob Example",
            emails=[
                "bob@example.com",
            ],
            phones=[
                "+237 6 70 00 00 02",
            ],
            company="MoneroAI",
        )

        print(
            "CREATED:",
            bob.title,
        )

        print(
            "TOTAL CONTACTS:",
            len(
                contacts.list_contacts(
                    source.source_id
                )
            ),
        )

        # ========================================================
        # TEST 7 — UPDATE LOCAL CONTACT
        # ========================================================

        divider(
            "TEST 7 — UPDATE CONTACT"
        )

        bob = contacts.update_contact(
            bob.record_id,
            display_name=(
                "Bob Updated"
            ),
            notes=(
                "Updated locally."
            ),
        )

        print(
            "NAME:",
            bob.title,
        )

        print(
            "NOTES:",
            bob.content,
        )

        # ========================================================
        # TEST 8 — ARCHIVE
        # ========================================================

        divider(
            "TEST 8 — ARCHIVE"
        )

        bob = contacts.archive_contact(
            bob.record_id
        )

        print(
            "STATUS:",
            bob.status,
        )

        print(
            "ACTIVE CONTACTS:",
            len(
                contacts.list_contacts(
                    source.source_id,
                    active_only=True,
                )
            ),
        )

        print(
            "ALL CONTACTS:",
            len(
                contacts.list_contacts(
                    source.source_id,
                    active_only=False,
                )
            ),
        )

        # ========================================================
        # TEST 9 — SOURCE DISABLED
        # ========================================================

        divider(
            "TEST 9 — DISABLED SOURCE"
        )

        manager.set_source_status(
            source.source_id,
            "disabled",
        )

        try:

            contacts.ingest_contact(
                source_id=(
                    source.source_id
                ),
                external_id=(
                    "people/test-003"
                ),
                display_name=(
                    "Blocked Contact"
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
        # TEST 10 — RELOAD
        # ========================================================

        divider(
            "TEST 10 — PERSISTENCE"
        )

        manager.set_source_status(
            source.source_id,
            "active",
        )

        manager.mark_source_synced(
            source.source_id
        )

        before = (
            contacts.summary(
                source.source_id
            )
        )

        reloaded_contacts = (
            ContactsService(
                PersonalDataManager(
                    PersonalDataStore(
                        TEMP_PATH
                    )
                )
            )
        )

        after = (
            reloaded_contacts.summary(
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
            "ALICE RELOADED:",
            len(
                reloaded_contacts
                .search_contacts(
                    "alice.new@example.com"
                )
            )
            == 1,
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