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


class NotesService:

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

        cleaned_values = []
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

            cleaned_values.append(
                cleaned
            )

        return cleaned_values

    # ============================================================
    # SOURCE VALIDATION
    # ============================================================

    def _require_note_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.manager.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Note source not found: "
                f"{source_id}"
            )

        if source.source_type != "note":

            raise ValueError(
                "Source is not a note source: "
                f"{source.name}"
            )

        return source

    # ============================================================
    # RECORD VALIDATION
    # ============================================================

    def _require_note(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.manager.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Note not found: "
                f"{record_id}"
            )

        if record.record_type != "note":

            raise ValueError(
                "Record is not a note: "
                f"{record_id}"
            )

        return record

    # ============================================================
    # ATTRIBUTES
    # ============================================================

    def _build_attributes(
        self,
        *,
        notebook: str | None = None,
        tags: list[str] | None = None,
        pinned: bool = False,
        source_url: str | None = None,
        author: str | None = None,
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
                "notebook": (
                    self._clean_text(
                        notebook
                    )
                ),
                "tags": (
                    self._clean_list(
                        tags
                    )
                ),
                "pinned": bool(
                    pinned
                ),
                "source_url": (
                    self._clean_text(
                        source_url
                    )
                ),
                "author": (
                    self._clean_text(
                        author
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
        name: str = "Personal Notes",
        access_mode: str = "read_write",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        if permissions_required is None:

            permissions_required = [
                "note.read",
            ]

            if access_mode == "read_write":

                permissions_required.append(
                    "note.write"
                )

        return self.manager.register_source(
            source_type="note",
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
            ),
            attributes=attributes,
        )

    # ============================================================
    # EXTERNAL ID LOOKUP
    # ============================================================

    def get_by_external_id(
        self,
        source_id: str,
        external_id: str,
    ) -> PersonalDataRecord | None:

        self._require_note_source(
            source_id
        )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=False,
        )

        for record in records:

            if (
                record.record_type == "note"
                and
                record.external_id
                == external_id
            ):

                return record

        return None

    # ============================================================
    # CREATE LOCAL NOTE
    # ============================================================

    def create_note(
        self,
        *,
        source_id: str,
        title: str,
        content: str,
        notebook: str | None = None,
        tags: list[str] | None = None,
        pinned: bool = False,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_note_source(
            source_id
        )

        title = title.strip()

        if not title:

            raise ValueError(
                "Note title cannot be empty."
            )

        attributes = (
            self._build_attributes(
                notebook=notebook,
                tags=tags,
                pinned=pinned,
            )
        )

        return self.manager.create_record(
            source_id=source_id,
            record_type="note",
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
        )

    # ============================================================
    # INGEST EXTERNAL NOTE
    # ============================================================

    def ingest_note(
        self,
        *,
        source_id: str,
        external_id: str,
        title: str,
        content: str,
        notebook: str | None = None,
        tags: list[str] | None = None,
        pinned: bool = False,
        source_url: str | None = None,
        author: str | None = None,
        extra_attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_note_source(
            source_id
        )

        external_id = (
            external_id.strip()
        )

        if not external_id:

            raise ValueError(
                "External note ID "
                "cannot be empty."
            )

        title = title.strip()

        if not title:

            title = "Untitled Note"

        attributes = (
            self._build_attributes(
                notebook=notebook,
                tags=tags,
                pinned=pinned,
                source_url=source_url,
                author=author,
                extra_attributes=(
                    extra_attributes
                ),
            )
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
                )
            )

        return self.manager.ingest_record(
            source_id=source_id,
            record_type="note",
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
        )

    # ============================================================
    # GET
    # ============================================================

    def get_note(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        return self._require_note(
            record_id
        )

    # ============================================================
    # UPDATE
    # ============================================================

    def update_note(
        self,
        record_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        notebook: str | None = None,
        tags: list[str] | None = None,
        pinned: bool | None = None,
        sensitivity: str | None = None,
    ) -> PersonalDataRecord:

        note = self._require_note(
            record_id
        )

        attributes = dict(
            note.attributes
        )

        if notebook is not None:

            attributes[
                "notebook"
            ] = self._clean_text(
                notebook
            )

        if tags is not None:

            attributes[
                "tags"
            ] = self._clean_list(
                tags
            )

        if pinned is not None:

            attributes[
                "pinned"
            ] = bool(
                pinned
            )

        return self.manager.update_record(
            record_id=note.record_id,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
        )

    # ============================================================
    # ARCHIVE
    # ============================================================

    def archive_note(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        note = self._require_note(
            record_id
        )

        return self.manager.archive_record(
            note.record_id
        )

    # ============================================================
    # LIST
    # ============================================================

    def list_notes(
        self,
        *,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        if source_id is not None:

            self._require_note_source(
                source_id
            )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=active_only,
        )

        return [
            record
            for record in records
            if record.record_type
            == "note"
        ]

    # ============================================================
    # SEARCH
    # ============================================================

    def search_notes(
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

        notes = self.list_notes(
            source_id=source_id,
            active_only=active_only,
        )

        if not normalized:

            return notes

        results = []

        for note in notes:

            attributes = (
                note.attributes
            )

            values = [
                note.title,
                note.content,
                attributes.get(
                    "notebook",
                    "",
                ),
                attributes.get(
                    "author",
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
                    note
                )

        return results

    # ============================================================
    # PINNED NOTES
    # ============================================================

    def pinned_notes(
        self,
        *,
        source_id: str | None = None,
    ) -> list[PersonalDataRecord]:

        return [
            note
            for note in self.list_notes(
                source_id=source_id,
                active_only=True,
            )
            if bool(
                note.attributes.get(
                    "pinned",
                    False,
                )
            )
        ]

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = self._require_note_source(
            source_id
        )

        records = self.list_notes(
            source_id=source_id,
            active_only=False,
        )

        active = [
            record
            for record in records
            if record.status
            == "active"
        ]

        pinned = [
            record
            for record in active
            if bool(
                record.attributes.get(
                    "pinned",
                    False,
                )
            )
        ]

        return {
            "source_id": source.source_id,
            "name": source.name,
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
            "pinned": len(
                pinned
            ),
            "last_sync_at": (
                source.last_sync_at
            ),
        }


notes_service = NotesService()