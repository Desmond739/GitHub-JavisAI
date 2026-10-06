from __future__ import annotations

from typing import Any

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
    PersonalDataSource,
    current_timestamp,
)

from app.personal_data.personal_data_store import (
    PersonalDataStore,
    personal_data_store,
)


class PersonalDataManager:

    def __init__(
        self,
        store: PersonalDataStore | None = None,
    ) -> None:

        self.store = (
            store
            if store is not None
            else personal_data_store
        )

    # ============================================================
    # INTERNAL SOURCE VALIDATION
    # ============================================================

    def _require_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.store.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Personal data source "
                f"not found: {source_id}"
            )

        return source

    def _require_active_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self._require_source(
            source_id
        )

        if source.status != "active":

            raise RuntimeError(
                f"Personal data source "
                f"'{source.name}' is not active. "
                f"Current status: {source.status}"
            )

        return source

    def _require_write_access(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self._require_active_source(
            source_id
        )

        if source.access_mode != "read_write":

            raise PermissionError(
                f"Personal data source "
                f"'{source.name}' is read-only."
            )

        return source

    # ============================================================
    # SOURCE — REGISTER
    # ============================================================

    def register_source(
        self,
        source_type: str,
        name: str,
        access_mode: str = "read_only",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        return self.store.add_source(
            source_type=source_type,
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
            ),
            attributes=attributes,
        )

    # ============================================================
    # SOURCE — GET
    # ============================================================

    def get_source(
        self,
        source_id: str,
    ) -> PersonalDataSource | None:

        return self.store.get_source(
            source_id
        )

    # ============================================================
    # SOURCE — LIST
    # ============================================================

    def list_sources(
        self,
        source_type: str | None = None,
        active_only: bool = False,
    ) -> list[PersonalDataSource]:

        if active_only:

            return self.store.find_sources(
                source_type=source_type,
                status="active",
            )

        return self.store.find_sources(
            source_type=source_type,
        )

    # ============================================================
    # SOURCE — STATUS
    # ============================================================

    def set_source_status(
        self,
        source_id: str,
        status: str,
    ) -> PersonalDataSource:

        self._require_source(
            source_id
        )

        updated = self.store.update_source(
            source_id=source_id,
            status=status,
        )

        if updated is None:

            raise KeyError(
                "Personal data source "
                f"not found: {source_id}"
            )

        return updated

    # ============================================================
    # SOURCE — ACCESS MODE
    # ============================================================

    def set_access_mode(
        self,
        source_id: str,
        access_mode: str,
    ) -> PersonalDataSource:

        self._require_source(
            source_id
        )

        updated = self.store.update_source(
            source_id=source_id,
            access_mode=access_mode,
        )

        if updated is None:

            raise KeyError(
                "Personal data source "
                f"not found: {source_id}"
            )

        return updated

    # ============================================================
    # SOURCE — MARK SYNCED
    # ============================================================

    def mark_source_synced(
        self,
        source_id: str,
        sync_time: str | None = None,
    ) -> PersonalDataSource:

        self._require_active_source(
            source_id
        )

        timestamp = (
            sync_time
            if sync_time is not None
            else current_timestamp()
        )

        updated = self.store.update_source(
            source_id=source_id,
            last_sync_at=timestamp,
        )

        if updated is None:

            raise KeyError(
                "Personal data source "
                f"not found: {source_id}"
            )

        return updated

    # ============================================================
    # RECORD — INGEST EXTERNAL DATA
    # ============================================================

    def ingest_record(
        self,
        source_id: str,
        record_type: str,
        title: str,
        content: str = "",
        attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> PersonalDataRecord:

        # Ingestion means MoneroAI received data
        # FROM the external source.
        #
        # A read-only source may therefore still
        # be ingested locally.
        self._require_active_source(
            source_id
        )

        return self.store.add_record(
            source_id=source_id,
            record_type=record_type,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=occurred_at,
        )

    # ============================================================
    # RECORD — CREATE USER/AI DATA
    # ============================================================

    def create_record(
        self,
        source_id: str,
        record_type: str,
        title: str,
        content: str = "",
        attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> PersonalDataRecord:

        # Creating data intended for a source is
        # different from importing data from it.
        #
        # For example:
        #
        # Reading Calendar → read_only is enough.
        # Creating Calendar event → read_write.
        self._require_write_access(
            source_id
        )

        return self.store.add_record(
            source_id=source_id,
            record_type=record_type,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=occurred_at,
        )

    # ============================================================
    # RECORD — GET
    # ============================================================

    def get_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord | None:

        return self.store.get_record(
            record_id
        )

    # ============================================================
    # RECORD — LIST
    # ============================================================

    def list_records(
        self,
        source_id: str | None = None,
        record_type: str | None = None,
        active_only: bool = False,
        sensitivity: str | None = None,
    ) -> list[PersonalDataRecord]:

        status = (
            "active"
            if active_only
            else None
        )

        return self.store.find_records(
            source_id=source_id,
            record_type=record_type,
            status=status,
            sensitivity=sensitivity,
        )

    # ============================================================
    # RECORD — UPDATE
    # ============================================================

    def update_record(
        self,
        record_id: str,
        title: str | None = None,
        content: str | None = None,
        attributes:
        dict[str, Any] | None = None,
        sensitivity: str | None = None,
        status: str | None = None,
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> PersonalDataRecord:

        record = self.store.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        self._require_write_access(
            record.source_id
        )

        updated = self.store.update_record(
            record_id=record_id,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            status=status,
            external_id=external_id,
            occurred_at=occurred_at,
        )

        if updated is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        return updated

    # ============================================================
    # RECORD — SYNC UPDATE
    # ============================================================

    def update_ingested_record(
        self,
        record_id: str,
        title: str | None = None,
        content: str | None = None,
        attributes:
        dict[str, Any] | None = None,
        sensitivity: str | None = None,
        status: str | None = None,
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> PersonalDataRecord:

        record = self.store.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        # Synchronization updates the LOCAL cached
        # representation of external data.
        #
        # It does not write back to the external
        # service, so read_only remains acceptable.
        self._require_active_source(
            record.source_id
        )

        updated = self.store.update_record(
            record_id=record_id,
            title=title,
            content=content,
            attributes=attributes,
            sensitivity=sensitivity,
            status=status,
            external_id=external_id,
            occurred_at=occurred_at,
        )

        if updated is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        return updated

    # ============================================================
    # RECORD — ARCHIVE
    # ============================================================

    def archive_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.store.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        self._require_write_access(
            record.source_id
        )

        archived = (
            self.store.archive_record(
                record_id
            )
        )

        if archived is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        return archived

    # ============================================================
    # RECORD — MARK DELETED
    # ============================================================

    def mark_record_deleted(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.store.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        self._require_write_access(
            record.source_id
        )

        deleted = (
            self.store.mark_record_deleted(
                record_id
            )
        )

        if deleted is None:

            raise KeyError(
                "Personal data record "
                f"not found: {record_id}"
            )

        return deleted

    # ============================================================
    # RECORD — HARD DELETE
    # ============================================================

    def delete_record(
        self,
        record_id: str,
    ) -> bool:

        record = self.store.get_record(
            record_id
        )

        if record is None:

            return False

        self._require_write_access(
            record.source_id
        )

        return self.store.delete_record(
            record_id
        )

    # ============================================================
    # SOURCE SUMMARY
    # ============================================================

    def source_summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = self._require_source(
            source_id
        )

        records = (
            self.store.find_records(
                source_id=source_id
            )
        )

        active_records = [
            record
            for record in records
            if record.status
            == "active"
        ]

        return {
            "source_id": (
                source.source_id
            ),
            "source_type": (
                source.source_type
            ),
            "name": source.name,
            "access_mode": (
                source.access_mode
            ),
            "status": source.status,
            "last_sync_at": (
                source.last_sync_at
            ),
            "records": len(
                records
            ),
            "active_records": len(
                active_records
            ),
        }

    # ============================================================
    # COUNTS
    # ============================================================

    def counts(
        self,
    ) -> dict[str, int]:

        return self.store.counts()


personal_data_manager = (
    PersonalDataManager()
)