from __future__ import annotations

from typing import Any

from app.personal_data.personal_data_manager import (
    PersonalDataManager,
    personal_data_manager,
)

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
    PersonalDataSource,
)


VALID_DOCUMENT_RECORD_TYPES = {
    "document",
    "file",
}


class DocumentsService:

    def __init__(
        self,
        manager: PersonalDataManager | None = None,
    ) -> None:

        self.manager = (
            manager
            if manager is not None
            else personal_data_manager
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str:

        if value is None:
            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def _clean_list(
        values: list[str] | None,
    ) -> list[str]:

        if values is None:
            return []

        result = []
        seen = set()

        for value in values:

            cleaned = str(
                value
            ).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                cleaned
            )

        return result

    # ============================================================
    # SOURCE VALIDATION
    # ============================================================

    def _require_document_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.manager.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Document source not found: "
                f"{source_id}"
            )

        if source.source_type not in {
            "document",
            "file",
        }:

            raise ValueError(
                "Source is not a document/file source: "
                f"{source.name}"
            )

        return source

    # ============================================================
    # RECORD VALIDATION
    # ============================================================

    def _require_document(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.manager.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Document not found: "
                f"{record_id}"
            )

        if record.record_type not in (
            VALID_DOCUMENT_RECORD_TYPES
        ):

            raise ValueError(
                "Record is not a document/file: "
                f"{record_id}"
            )

        return record

    # ============================================================
    # ATTRIBUTES
    # ============================================================

    def _build_attributes(
        self,
        *,
        path: str | None = None,
        extension: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        modified_at: str | None = None,
        created_at_file: str | None = None,
        checksum: str | None = None,
        folder: str | None = None,
        tags: list[str] | None = None,
        extraction_status: str | None = None,
        extra_attributes:
        dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        attributes = dict(
            extra_attributes
            if extra_attributes is not None
            else {}
        )

        attributes.update(
            {
                "path": self._clean_text(
                    path
                ),
                "extension": self._clean_text(
                    extension
                ).casefold(),
                "mime_type": self._clean_text(
                    mime_type
                ),
                "size_bytes": (
                    int(size_bytes)
                    if size_bytes is not None
                    else None
                ),
                "modified_at": self._clean_text(
                    modified_at
                ),
                "created_at_file": self._clean_text(
                    created_at_file
                ),
                "checksum": self._clean_text(
                    checksum
                ),
                "folder": self._clean_text(
                    folder
                ),
                "tags": self._clean_list(
                    tags
                ),
                "extraction_status": (
                    self._clean_text(
                        extraction_status
                    )
                ),
            }
        )

        return attributes

    # ============================================================
    # REGISTER SOURCE
    # ============================================================

    def register_source(
        self,
        *,
        name: str,
        source_type: str = "file",
        access_mode: str = "read_only",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        if source_type not in {
            "document",
            "file",
        }:

            raise ValueError(
                "source_type must be "
                "'document' or 'file'."
            )

        if permissions_required is None:

            permissions_required = [
                f"{source_type}.read",
            ]

            if access_mode == "read_write":

                permissions_required.append(
                    f"{source_type}.write"
                )

        return self.manager.register_source(
            source_type=source_type,
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
            ),
            attributes=attributes,
        )

    # ============================================================
    # EXTERNAL ID
    # ============================================================

    def get_by_external_id(
        self,
        source_id: str,
        external_id: str,
    ) -> PersonalDataRecord | None:

        self._require_document_source(
            source_id
        )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=False,
        )

        for record in records:

            if (
                record.record_type
                in VALID_DOCUMENT_RECORD_TYPES
                and record.external_id
                == external_id
            ):

                return record

        return None

    # ============================================================
    # INGEST
    # ============================================================

    def ingest_document(
        self,
        *,
        source_id: str,
        external_id: str,
        title: str,
        content: str = "",
        record_type: str = "document",
        path: str | None = None,
        extension: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        modified_at: str | None = None,
        created_at_file: str | None = None,
        checksum: str | None = None,
        folder: str | None = None,
        tags: list[str] | None = None,
        extraction_status: str | None = None,
        extra_attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_document_source(
            source_id
        )

        if (
            record_type
            not in VALID_DOCUMENT_RECORD_TYPES
        ):

            raise ValueError(
                "record_type must be "
                "'document' or 'file'."
            )

        external_id = external_id.strip()

        if not external_id:

            raise ValueError(
                "External document ID "
                "cannot be empty."
            )

        title = title.strip()

        if not title:

            title = "Untitled Document"

        attributes = self._build_attributes(
            path=path,
            extension=extension,
            mime_type=mime_type,
            size_bytes=size_bytes,
            modified_at=modified_at,
            created_at_file=created_at_file,
            checksum=checksum,
            folder=folder,
            tags=tags,
            extraction_status=(
                extraction_status
            ),
            extra_attributes=(
                extra_attributes
            ),
        )

        existing = (
            self.get_by_external_id(
                source_id,
                external_id,
            )
        )

        if existing is not None:

            return (
                self.manager
                .update_ingested_record(
                    record_id=(
                        existing.record_id
                    ),
                    title=title,
                    content=content,
                    attributes=attributes,
                    sensitivity=sensitivity,
                    status="active",
                    external_id=external_id,
                    occurred_at=modified_at,
                )
            )

        return self.manager.ingest_record(
            source_id=source_id,
            record_type=record_type,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=modified_at,
        )

    # ============================================================
    # GET
    # ============================================================

    def get_document(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        return self._require_document(
            record_id
        )

    # ============================================================
    # LIST
    # ============================================================

    def list_documents(
        self,
        *,
        source_id: str | None = None,
        active_only: bool = True,
        record_type: str | None = None,
    ) -> list[PersonalDataRecord]:

        if source_id is not None:

            self._require_document_source(
                source_id
            )

        if (
            record_type is not None
            and record_type
            not in VALID_DOCUMENT_RECORD_TYPES
        ):

            raise ValueError(
                "record_type must be "
                "'document', 'file', or None."
            )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=active_only,
        )

        results = []

        for record in records:

            if (
                record.record_type
                not in VALID_DOCUMENT_RECORD_TYPES
            ):

                continue

            if (
                record_type is not None
                and record.record_type
                != record_type
            ):

                continue

            results.append(
                record
            )

        return results

    # ============================================================
    # SEARCH
    # ============================================================

    def search_documents(
        self,
        query: str,
        *,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        normalized = (
            query.strip()
            .casefold()
        )

        records = self.list_documents(
            source_id=source_id,
            active_only=active_only,
        )

        if not normalized:

            return records

        results = []

        for record in records:

            attributes = (
                record.attributes
            )

            values = [
                record.title,
                record.content,
                attributes.get(
                    "path",
                    "",
                ),
                attributes.get(
                    "extension",
                    "",
                ),
                attributes.get(
                    "mime_type",
                    "",
                ),
                attributes.get(
                    "folder",
                    "",
                ),
            ]

            values.extend(
                attributes.get(
                    "tags",
                    [],
                )
            )

            if any(
                normalized
                in str(value).casefold()
                for value in values
                if value
            ):

                results.append(
                    record
                )

        return results

    # ============================================================
    # MARK DELETED
    # ============================================================

    def mark_ingested_deleted(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self._require_document(
            record_id
        )

        return (
            self.manager
            .update_ingested_record(
                record_id=(
                    record.record_id
                ),
                status="deleted",
            )
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = (
            self._require_document_source(
                source_id
            )
        )

        records = self.list_documents(
            source_id=source_id,
            active_only=False,
        )

        active = [
            record
            for record in records
            if record.status
            == "active"
        ]

        deleted = [
            record
            for record in records
            if record.status
            == "deleted"
        ]

        return {
            "source_id": source.source_id,
            "name": source.name,
            "source_type": (
                source.source_type
            ),
            "access_mode": (
                source.access_mode
            ),
            "status": source.status,
            "records": len(
                records
            ),
            "active_records": len(
                active
            ),
            "deleted_records": len(
                deleted
            ),
            "last_sync_at": (
                source.last_sync_at
            ),
        }


documents_service = (
    DocumentsService()
)