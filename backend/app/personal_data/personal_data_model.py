from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


# ================================================================
# VALID VALUES
# ================================================================

VALID_SOURCE_TYPES = {
    "calendar",
    "contact",
    "task",
    "reminder",
    "note",
    "document",
    "email",
    "file",
    "manual",
}

VALID_ACCESS_MODES = {
    "read_only",
    "read_write",
}

VALID_SOURCE_STATUSES = {
    "active",
    "disabled",
    "disconnected",
}

VALID_RECORD_STATUSES = {
    "active",
    "archived",
    "deleted",
}

VALID_SENSITIVITY_LEVELS = {
    "normal",
    "private",
    "sensitive",
    "restricted",
}


# ================================================================
# TIME
# ================================================================

def current_timestamp() -> str:

    return datetime.now().isoformat(
        timespec="seconds"
    )


# ================================================================
# PERSONAL DATA SOURCE
# ================================================================

@dataclass
class PersonalDataSource:

    source_id: str

    source_type: str

    name: str

    access_mode: str = "read_only"

    permissions_required: list[str] = field(
        default_factory=list
    )

    status: str = "active"

    last_sync_at: str | None = None

    attributes: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=current_timestamp
    )

    updated_at: str = field(
        default_factory=current_timestamp
    )

    # ============================================================
    # VALIDATION
    # ============================================================

    def __post_init__(
        self,
    ) -> None:

        self.source_type = (
            self.source_type
            .strip()
            .lower()
        )

        self.access_mode = (
            self.access_mode
            .strip()
            .lower()
        )

        self.status = (
            self.status
            .strip()
            .lower()
        )

        self.name = self.name.strip()

        if not self.source_id:

            raise ValueError(
                "source_id cannot be empty."
            )

        if not self.name:

            raise ValueError(
                "Source name cannot be empty."
            )

        if (
            self.source_type
            not in VALID_SOURCE_TYPES
        ):

            raise ValueError(
                "Invalid source type: "
                f"{self.source_type}"
            )

        if (
            self.access_mode
            not in VALID_ACCESS_MODES
        ):

            raise ValueError(
                "Invalid access mode: "
                f"{self.access_mode}"
            )

        if (
            self.status
            not in VALID_SOURCE_STATUSES
        ):

            raise ValueError(
                "Invalid source status: "
                f"{self.status}"
            )

    # ============================================================
    # FACTORY
    # ============================================================

    @classmethod
    def create(
        cls,
        source_type: str,
        name: str,
        access_mode: str = "read_only",
        permissions_required: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> "PersonalDataSource":

        return cls(
            source_id=str(
                uuid4()
            ),
            source_type=source_type,
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
                if permissions_required
                is not None
                else []
            ),
            attributes=(
                attributes
                if attributes
                is not None
                else {}
            ),
        )

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "name": self.name,
            "access_mode": self.access_mode,
            "permissions_required": list(
                self.permissions_required
            ),
            "status": self.status,
            "last_sync_at": self.last_sync_at,
            "attributes": dict(
                self.attributes
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ================================================================
# PERSONAL DATA RECORD
# ================================================================

@dataclass
class PersonalDataRecord:

    record_id: str

    source_id: str

    record_type: str

    title: str

    content: str = ""

    attributes: dict[str, Any] = field(
        default_factory=dict
    )

    sensitivity: str = "private"

    status: str = "active"

    external_id: str | None = None

    occurred_at: str | None = None

    created_at: str = field(
        default_factory=current_timestamp
    )

    updated_at: str = field(
        default_factory=current_timestamp
    )

    # ============================================================
    # VALIDATION
    # ============================================================

    def __post_init__(
        self,
    ) -> None:

        self.record_type = (
            self.record_type
            .strip()
            .lower()
        )

        self.sensitivity = (
            self.sensitivity
            .strip()
            .lower()
        )

        self.status = (
            self.status
            .strip()
            .lower()
        )

        self.title = self.title.strip()

        if not self.record_id:

            raise ValueError(
                "record_id cannot be empty."
            )

        if not self.source_id:

            raise ValueError(
                "source_id cannot be empty."
            )

        if not self.record_type:

            raise ValueError(
                "record_type cannot be empty."
            )

        if not self.title:

            raise ValueError(
                "Record title cannot be empty."
            )

        if (
            self.sensitivity
            not in VALID_SENSITIVITY_LEVELS
        ):

            raise ValueError(
                "Invalid sensitivity level: "
                f"{self.sensitivity}"
            )

        if (
            self.status
            not in VALID_RECORD_STATUSES
        ):

            raise ValueError(
                "Invalid record status: "
                f"{self.status}"
            )

    # ============================================================
    # FACTORY
    # ============================================================

    @classmethod
    def create(
        cls,
        source_id: str,
        record_type: str,
        title: str,
        content: str = "",
        attributes: dict[str, Any] | None = None,
        sensitivity: str = "private",
        external_id: str | None = None,
        occurred_at: str | None = None,
    ) -> "PersonalDataRecord":

        return cls(
            record_id=str(
                uuid4()
            ),
            source_id=source_id,
            record_type=record_type,
            title=title,
            content=content,
            attributes=(
                attributes
                if attributes
                is not None
                else {}
            ),
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=occurred_at,
        )

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "record_id": self.record_id,
            "source_id": self.source_id,
            "record_type": self.record_type,
            "title": self.title,
            "content": self.content,
            "attributes": dict(
                self.attributes
            ),
            "sensitivity": self.sensitivity,
            "status": self.status,
            "external_id": self.external_id,
            "occurred_at": self.occurred_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }