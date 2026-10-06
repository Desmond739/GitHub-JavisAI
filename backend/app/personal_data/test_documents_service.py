from __future__ import annotations

from pathlib import Path

from app.personal_data.documents_service import (
    DocumentsService,
)

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
)


TEMP_PATH = Path(
    "data/personal_data/"
    "test_documents_service.json"
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

    documents = DocumentsService(
        manager
    )

    try:

        source = (
            documents.register_source(
                name="Test Documents",
                source_type="file",
                access_mode="read_only",
            )
        )

        print(
            "SOURCE TYPE:",
            source.source_type
        )

        print(
            "ACCESS:",
            source.access_mode
        )

        first = (
            documents.ingest_document(
                source_id=source.source_id,
                external_id="file-001",
                title="Project Report.pdf",
                content=(
                    "MoneroAI project "
                    "architecture report."
                ),
                record_type="document",
                path=(
                    "C:/Test/"
                    "Project Report.pdf"
                ),
                extension=".pdf",
                mime_type=(
                    "application/pdf"
                ),
                size_bytes=1024,
                checksum="abc123",
                folder="Test",
                tags=[
                    "MoneroAI",
                    "Project",
                ],
                extraction_status=(
                    "complete"
                ),
            )
        )

        print(
            "CREATED:",
            first.title
        )

        print(
            "PATH EXISTS:",
            bool(
                first.attributes.get(
                    "path"
                )
            )
        )

        print(
            "CHECKSUM:",
            first.attributes.get(
                "checksum"
            )
            == "abc123"
        )

        print(
            "TITLE SEARCH:",
            len(
                documents.search_documents(
                    "Project Report"
                )
            )
        )

        print(
            "CONTENT SEARCH:",
            len(
                documents.search_documents(
                    "architecture"
                )
            )
        )

        print(
            "TAG SEARCH:",
            len(
                documents.search_documents(
                    "MoneroAI"
                )
            )
        )

        second = (
            documents.ingest_document(
                source_id=source.source_id,
                external_id="file-001",
                title=(
                    "Project Report Final.pdf"
                ),
                content=(
                    "Updated MoneroAI "
                    "architecture report."
                ),
                record_type="document",
                path=(
                    "C:/Test/"
                    "Project Report Final.pdf"
                ),
                extension=".pdf",
                mime_type=(
                    "application/pdf"
                ),
                size_bytes=2048,
                checksum="def456",
                folder="Test",
                tags=[
                    "MoneroAI",
                    "Final",
                ],
                extraction_status=(
                    "complete"
                ),
            )
        )

        print(
            "UPSERT SAME RECORD:",
            first.record_id
            == second.record_id
        )

        print(
            "UPDATED TITLE:",
            second.title
            == "Project Report Final.pdf"
        )

        print(
            "NO DUPLICATE:",
            len(
                documents.list_documents()
            )
            == 1
        )

        deleted = (
            documents.mark_ingested_deleted(
                second.record_id
            )
        )

        print(
            "DELETED:",
            deleted.status
            == "deleted"
        )

        print(
            "ACTIVE COUNT:",
            len(
                documents.list_documents(
                    active_only=True
                )
            )
        )

        summary = (
            documents.summary(
                source.source_id
            )
        )

        print(
            "SUMMARY RECORDS:",
            summary[
                "records"
            ]
        )

        print(
            "SUMMARY DELETED:",
            summary[
                "deleted_records"
            ]
        )

        before = store.counts()

        reloaded = DocumentsService(
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