from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
    PersonalDataSource,
    VALID_ACCESS_MODES,
    VALID_RECORD_STATUSES,
    VALID_SENSITIVITY_LEVELS,
    VALID_SOURCE_STATUSES,
    VALID_SOURCE_TYPES,
    current_timestamp,
)


class PersonalDataStore:

    def __init__(
        self,
        storage_path: str | Path | None = None,
    ) -> None:

        self.storage_path = Path(
            storage_path
            if storage_path is not None
            else (
                "data/personal_data/"
                "personal_data.json"
            )
        )

        self._lock = RLock()

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        return " ".join(
            value.strip().casefold().split()
        )

    # ============================================================
    # EMPTY DATABASE
    # ============================================================

    @staticmethod
    def _empty_database() -> dict[str, Any]:

        return {
            "sources": [],
            "records": [],
        }

    # ============================================================
    # LOAD
    # ============================================================

    def _load(
        self,
    ) -> dict[str, Any]:

        with self._lock:

            if not self.storage_path.exists():

                return self._empty_database()

            try:

                raw = self.storage_path.read_text(
                    encoding="utf-8"
                ).strip()

                if not raw:

                    return self._empty_database()

                data = json.loads(
                    raw
                )

            except (
                json.JSONDecodeError,
                OSError,
            ) as exc:

                raise RuntimeError(
                    "Unable to load personal "
                    f"data store: {exc}"
                ) from exc

            if not isinstance(
                data,
                dict,
            ):

                raise RuntimeError(
                    "Personal data store must "
                    "contain a JSON object."
                )

            sources = data.get(
                "sources",
                [],
            )

            records = data.get(
                "records",
                [],
            )

            if not isinstance(
                sources,
                list,
            ):

                raise RuntimeError(
                    "'sources' must be a list."
                )

            if not isinstance(
                records,
                list,
            ):

                raise RuntimeError(
                    "'records' must be a list."
                )

            return {
                "sources": sources,
                "records": records,
            }

    # ============================================================
    # SAVE
    # ============================================================

    def _save(
        self,
        data: dict[str, Any],
    ) -> None:

        with self._lock:

            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temp_path = (
                self.storage_path.with_suffix(
                    self.storage_path.suffix
                    + ".tmp"
                )
            )

            serialized = json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )

            try:

                temp_path.write_text(
                    serialized,
                    encoding="utf-8",
                )

                os.replace(
                    temp_path,
                    self.storage_path,
                )

            except OSError as exc:

                if temp_path.exists():

                    temp_path.unlink(
                        missing_ok=True
                    )

                raise RuntimeError(
                    "Unable to save personal "
                    f"data store: {exc}"
                ) from exc

    # ============================================================
    # DICT -> SOURCE
    # ============================================================

    @staticmethod
    def _source_from_dict(
        data: dict[str, Any],
    ) -> PersonalDataSource:

        return PersonalDataSource(
            source_id=data[
                "source_id"
            ],
            source_type=data[
                "source_type"
            ],
            name=data[
                "name"
            ],
            access_mode=data.get(
                "access_mode",
                "read_only",
            ),
            permissions_required=list(
                data.get(
                    "permissions_required",
                    [],
                )
            ),
            status=data.get(
                "status",
                "active",
            ),
            last_sync_at=data.get(
                "last_sync_at"
            ),
            attributes=dict(
                data.get(
                    "attributes",
                    {},
                )
            ),
            created_at=data.get(
                "created_at",
                current_timestamp(),
            ),
            updated_at=data.get(
                "updated_at",
                current_timestamp(),
            ),
        )

    # ============================================================
    # DICT -> RECORD
    # ============================================================

    @staticmethod
    def _record_from_dict(
        data: dict[str, Any],
    ) -> PersonalDataRecord:

        return PersonalDataRecord(
            record_id=data[
                "record_id"
            ],
            source_id=data[
                "source_id"
            ],
            record_type=data[
                "record_type"
            ],
            title=data[
                "title"
            ],
            content=data.get(
                "content",
                "",
            ),
            attributes=dict(
                data.get(
                    "attributes",
                    {},
                )
            ),
            sensitivity=data.get(
                "sensitivity",
                "private",
            ),
            status=data.get(
                "status",
                "active",
            ),
            external_id=data.get(
                "external_id"
            ),
            occurred_at=data.get(
                "occurred_at"
            ),
            created_at=data.get(
                "created_at",
                current_timestamp(),
            ),
            updated_at=data.get(
                "updated_at",
                current_timestamp(),
            ),
        )

    # ============================================================
    # SOURCE — GET ALL
    # ============================================================

    def get_all_sources(
        self,
    ) -> list[PersonalDataSource]:

        data = self._load()

        return [
            self._source_from_dict(
                item
            )
            for item in data[
                "sources"
            ]
        ]

    # ============================================================
    # SOURCE — GET BY ID
    # ============================================================

    def get_source(
        self,
        source_id: str,
    ) -> PersonalDataSource | None:

        for source in (
            self.get_all_sources()
        ):

            if (
                source.source_id
                == source_id
            ):

                return source

        return None

    # ============================================================
    # SOURCE — FIND
    # ============================================================

    def find_sources(
        self,
        source_type: str | None = None,
        name: str | None = None,
        status: str | None = None,
    ) -> list[PersonalDataSource]:

        sources = (
            self.get_all_sources()
        )

        if source_type is not None:

            source_type = (
                source_type
                .strip()
                .lower()
            )

            if (
                source_type
                not in VALID_SOURCE_TYPES
            ):

                raise ValueError(
                    "Invalid source type: "
                    f"{source_type}"
                )

            sources = [
                source
                for source in sources
                if (
                    source.source_type
                    == source_type
                )
            ]

        if name is not None:

            normalized_name = (
                self._normalize(
                    name
                )
            )

            sources = [
                source
                for source in sources
                if self._normalize(
                    source.name
                )
                == normalized_name
            ]

        if status is not None:

            status = (
                status.strip().lower()
            )

            if (
                status
                not in VALID_SOURCE_STATUSES
            ):

                raise ValueError(
                    "Invalid source status: "
                    f"{status}"
                )

            sources = [
                source
                for source in sources
                if source.status
                == status
            ]

        return sources

    # ============================================================
    # SOURCE — ADD
    # ============================================================

    def add_source(
        self,
        source_type: str,
        name: str,
        access_mode: str = "read_only",
        permissions_required: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        # Validate before checking duplicates.
        candidate = (
            PersonalDataSource.create(
                source_type=source_type,
                name=name,
                access_mode=access_mode,
                permissions_required=(
                    permissions_required
                ),
                attributes=attributes,
            )
        )

        with self._lock:

            data = self._load()

            for item in data[
                "sources"
            ]:

                existing = (
                    self._source_from_dict(
                        item
                    )
                )

                if (
                    existing.source_type
                    == candidate.source_type
                    and self._normalize(
                        existing.name
                    )
                    == self._normalize(
                        candidate.name
                    )
                ):

                    return existing

            data[
                "sources"
            ].append(
                candidate.to_dict()
            )

            self._save(
                data
            )

            return candidate

    # ============================================================
    # SOURCE — UPDATE
    # ============================================================

    def update_source(
        self,
        source_id: str,
        name: str | None = None,
        access_mode: str | None = None,
        permissions_required:
        list[str] | None = None,
        status: str | None = None,
        last_sync_at: str | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource | None:

        with self._lock:

            data = self._load()

            target = None

            for item in data[
                "sources"
            ]:

                if (
                    item[
                        "source_id"
                    ]
                    == source_id
                ):

                    target = item
                    break

            if target is None:

                return None

            if name is not None:

                name = name.strip()

                if not name:

                    raise ValueError(
                        "Source name cannot "
                        "be empty."
                    )

                target[
                    "name"
                ] = name

            if access_mode is not None:

                access_mode = (
                    access_mode
                    .strip()
                    .lower()
                )

                if (
                    access_mode
                    not in VALID_ACCESS_MODES
                ):

                    raise ValueError(
                        "Invalid access mode: "
                        f"{access_mode}"
                    )

                target[
                    "access_mode"
                ] = access_mode

            if (
                permissions_required
                is not None
            ):

                target[
                    "permissions_required"
                ] = list(
                    permissions_required
                )

            if status is not None:

                status = (
                    status.strip().lower()
                )

                if (
                    status
                    not in VALID_SOURCE_STATUSES
                ):

                    raise ValueError(
                        "Invalid source status: "
                        f"{status}"
                    )

                target[
                    "status"
                ] = status

            if last_sync_at is not None:

                target[
                    "last_sync_at"
                ] = last_sync_at

            if attributes is not None:

                target[
                    "attributes"
                ] = dict(
                    attributes
                )

            target[
                "updated_at"
            ] = current_timestamp()

            # Reconstruct to ensure final
            # persisted state is valid.
            validated = (
                self._source_from_dict(
                    target
                )
            )

            self._save(
                data
            )

            return validated

    # ============================================================
    # RECORD — GET ALL
    # ============================================================

    def get_all_records(
        self,
    ) -> list[PersonalDataRecord]:

        data = self._load()

        return [
            self._record_from_dict(
                item
            )
            for item in data[
                "records"
            ]
        ]

    # ============================================================
    # RECORD — GET BY ID
    # ============================================================

    def get_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord | None:

        for record in (
            self.get_all_records()
        ):

            if (
                record.record_id
                == record_id
            ):

                return record

        return None

    # ============================================================
    # RECORD — FIND
    # ============================================================

    def find_records(
        self,
        source_id: str | None = None,
        record_type: str | None = None,
        status: str | None = None,
        sensitivity: str | None = None,
        external_id: str | None = None,
    ) -> list[PersonalDataRecord]:

        records = (
            self.get_all_records()
        )

        if source_id is not None:

            records = [
                record
                for record in records
                if record.source_id
                == source_id
            ]

        if record_type is not None:

            record_type = (
                record_type
                .strip()
                .lower()
            )

            records = [
                record
                for record in records
                if record.record_type
                == record_type
            ]

        if status is not None:

            status = (
                status.strip().lower()
            )

            if (
                status
                not in VALID_RECORD_STATUSES
            ):

                raise ValueError(
                    "Invalid record status: "
                    f"{status}"
                )

            records = [
                record
                for record in records
                if record.status
                == status
            ]

        if sensitivity is not None:

            sensitivity = (
                sensitivity
                .strip()
                .lower()
            )

            if (
                sensitivity
                not in
                VALID_SENSITIVITY_LEVELS
            ):

                raise ValueError(
                    "Invalid sensitivity "
                    f"level: {sensitivity}"
                )

            records = [
                record
                for record in records
                if record.sensitivity
                == sensitivity
            ]

        if external_id is not None:

            records = [
                record
                for record in records
                if record.external_id
                == external_id
            ]

        return records

    # ============================================================
    # RECORD — ADD
    # ============================================================

    def add_record(
        self,
        source_id: str,
        record_type: str,
        title: str,
        content: str = "",
        attributes: dict[str, Any] | None = None,
        sensitivity: str = "private",
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> PersonalDataRecord:

        source = self.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Personal data source "
                f"not found: {source_id}"
            )

        candidate = (
            PersonalDataRecord.create(
                source_id=source_id,
                record_type=record_type,
                title=title,
                content=content,
                attributes=attributes,
                sensitivity=sensitivity,
                external_id=external_id,
                occurred_at=occurred_at,
            )
        )

        with self._lock:

            data = self._load()

            # External IDs come from systems such
            # as Google Calendar/Gmail.
            #
            # If present, source + external_id is
            # treated as the stable identity.
            if candidate.external_id:

                for item in data[
                    "records"
                ]:

                    if (
                        item[
                            "source_id"
                        ]
                        == candidate.source_id
                        and item.get(
                            "external_id"
                        )
                        == candidate.external_id
                    ):

                        return (
                            self._record_from_dict(
                                item
                            )
                        )

            data[
                "records"
            ].append(
                candidate.to_dict()
            )

            self._save(
                data
            )

            return candidate

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
    ) -> PersonalDataRecord | None:

        with self._lock:

            data = self._load()

            target = None

            for item in data[
                "records"
            ]:

                if (
                    item[
                        "record_id"
                    ]
                    == record_id
                ):

                    target = item
                    break

            if target is None:

                return None

            if title is not None:

                title = title.strip()

                if not title:

                    raise ValueError(
                        "Record title cannot "
                        "be empty."
                    )

                target[
                    "title"
                ] = title

            if content is not None:

                target[
                    "content"
                ] = content

            if attributes is not None:

                target[
                    "attributes"
                ] = dict(
                    attributes
                )

            if sensitivity is not None:

                sensitivity = (
                    sensitivity
                    .strip()
                    .lower()
                )

                if (
                    sensitivity
                    not in
                    VALID_SENSITIVITY_LEVELS
                ):

                    raise ValueError(
                        "Invalid sensitivity "
                        f"level: {sensitivity}"
                    )

                target[
                    "sensitivity"
                ] = sensitivity

            if status is not None:

                status = (
                    status.strip().lower()
                )

                if (
                    status
                    not in VALID_RECORD_STATUSES
                ):

                    raise ValueError(
                        "Invalid record status: "
                        f"{status}"
                    )

                target[
                    "status"
                ] = status

            if external_id is not None:

                target[
                    "external_id"
                ] = external_id

            if occurred_at is not None:

                target[
                    "occurred_at"
                ] = occurred_at

            target[
                "updated_at"
            ] = current_timestamp()

            validated = (
                self._record_from_dict(
                    target
                )
            )

            self._save(
                data
            )

            return validated

    # ============================================================
    # RECORD — ARCHIVE
    # ============================================================

    def archive_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord | None:

        return self.update_record(
            record_id=record_id,
            status="archived",
        )

    # ============================================================
    # RECORD — MARK DELETED
    # ============================================================

    def mark_record_deleted(
        self,
        record_id: str,
    ) -> PersonalDataRecord | None:

        return self.update_record(
            record_id=record_id,
            status="deleted",
        )

    # ============================================================
    # RECORD — HARD DELETE
    # ============================================================

    def delete_record(
        self,
        record_id: str,
    ) -> bool:

        with self._lock:

            data = self._load()

            original_count = len(
                data[
                    "records"
                ]
            )

            data[
                "records"
            ] = [
                item
                for item in data[
                    "records"
                ]
                if (
                    item[
                        "record_id"
                    ]
                    != record_id
                )
            ]

            if (
                len(
                    data[
                        "records"
                    ]
                )
                == original_count
            ):

                return False

            self._save(
                data
            )

            return True

    # ============================================================
    # COUNTS
    # ============================================================

    def counts(
        self,
    ) -> dict[str, int]:

        sources = (
            self.get_all_sources()
        )

        records = (
            self.get_all_records()
        )

        return {
            "sources": len(
                sources
            ),
            "active_sources": len(
                [
                    source
                    for source in sources
                    if source.status
                    == "active"
                ]
            ),
            "records": len(
                records
            ),
            "active_records": len(
                [
                    record
                    for record in records
                    if record.status
                    == "active"
                ]
            ),
        }


personal_data_store = (
    PersonalDataStore()
)