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


VALID_TASK_STATUSES = {
    "pending",
    "in_progress",
    "completed",
    "cancelled",
}

VALID_PRIORITIES = {
    "low",
    "normal",
    "high",
    "urgent",
}


class TaskService:

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

    @staticmethod
    def _validate_task_status(
        value: str,
    ) -> str:

        normalized = (
            value.strip()
            .casefold()
        )

        if normalized not in VALID_TASK_STATUSES:

            raise ValueError(
                "Invalid task status: "
                f"{value}. Valid values: "
                f"{sorted(VALID_TASK_STATUSES)}"
            )

        return normalized

    @staticmethod
    def _validate_priority(
        value: str,
    ) -> str:

        normalized = (
            value.strip()
            .casefold()
        )

        if normalized not in VALID_PRIORITIES:

            raise ValueError(
                "Invalid task priority: "
                f"{value}. Valid values: "
                f"{sorted(VALID_PRIORITIES)}"
            )

        return normalized

    # ============================================================
    # SOURCE VALIDATION
    # ============================================================

    def _require_task_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.manager.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Task source not found: "
                f"{source_id}"
            )

        if source.source_type not in {
            "task",
            "reminder",
        }:

            raise ValueError(
                "Source is not a task/reminder "
                f"source: {source.name}"
            )

        return source

    # ============================================================
    # RECORD VALIDATION
    # ============================================================

    def _require_task_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.manager.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Task not found: "
                f"{record_id}"
            )

        if record.record_type not in {
            "task",
            "reminder",
        }:

            raise ValueError(
                "Record is not a task/reminder: "
                f"{record_id}"
            )

        return record

    # ============================================================
    # ATTRIBUTES
    # ============================================================

    def _build_attributes(
        self,
        *,
        task_status: str = "pending",
        priority: str = "normal",
        due_at: str | None = None,
        reminder_at: str | None = None,
        completed_at: str | None = None,
        list_name: str | None = None,
        recurrence: list[str] | None = None,
        tags: list[str] | None = None,
        parent_external_id: str | None = None,
        notes: str | None = None,
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
                "task_status": (
                    self._validate_task_status(
                        task_status
                    )
                ),
                "priority": (
                    self._validate_priority(
                        priority
                    )
                ),
                "due_at": (
                    self._clean_text(
                        due_at
                    )
                ),
                "reminder_at": (
                    self._clean_text(
                        reminder_at
                    )
                ),
                "completed_at": (
                    self._clean_text(
                        completed_at
                    )
                ),
                "list_name": (
                    self._clean_text(
                        list_name
                    )
                ),
                "recurrence": (
                    self._clean_list(
                        recurrence
                    )
                ),
                "tags": (
                    self._clean_list(
                        tags
                    )
                ),
                "parent_external_id": (
                    self._clean_text(
                        parent_external_id
                    )
                ),
                "notes": (
                    self._clean_text(
                        notes
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
        name: str = "Personal Tasks",
        source_type: str = "task",
        access_mode: str = "read_write",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        if source_type not in {
            "task",
            "reminder",
        }:

            raise ValueError(
                "Task source_type must be "
                "'task' or 'reminder'."
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
    # GET BY EXTERNAL ID
    # ============================================================

    def get_by_external_id(
        self,
        source_id: str,
        external_id: str,
    ) -> PersonalDataRecord | None:

        self._require_task_source(
            source_id
        )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=False,
        )

        for record in records:

            if (
                record.record_type
                not in {
                    "task",
                    "reminder",
                }
            ):

                continue

            if (
                record.external_id
                == external_id
            ):

                return record

        return None

    # ============================================================
    # INGEST EXTERNAL TASK
    # ============================================================

    def ingest_task(
        self,
        *,
        source_id: str,
        external_id: str,
        title: str,
        description: str = "",
        task_status: str = "pending",
        priority: str = "normal",
        due_at: str | None = None,
        reminder_at: str | None = None,
        completed_at: str | None = None,
        list_name: str | None = None,
        recurrence: list[str] | None = None,
        tags: list[str] | None = None,
        parent_external_id: str | None = None,
        notes: str | None = None,
        record_type: str = "task",
        extra_attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        source = self._require_task_source(
            source_id
        )

        if record_type not in {
            "task",
            "reminder",
        }:

            raise ValueError(
                "record_type must be "
                "'task' or 'reminder'."
            )

        external_id = (
            external_id.strip()
        )

        if not external_id:

            raise ValueError(
                "External task ID "
                "cannot be empty."
            )

        title = title.strip()

        if not title:

            title = "Untitled Task"

        attributes = self._build_attributes(
            task_status=task_status,
            priority=priority,
            due_at=due_at,
            reminder_at=reminder_at,
            completed_at=completed_at,
            list_name=list_name,
            recurrence=recurrence,
            tags=tags,
            parent_external_id=(
                parent_external_id
            ),
            notes=notes,
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
                    content=description,
                    attributes=attributes,
                    sensitivity=sensitivity,
                    status="active",
                    external_id=external_id,
                    occurred_at=(
                        due_at
                        or reminder_at
                    ),
                )
            )

        return self.manager.ingest_record(
            source_id=source.source_id,
            record_type=record_type,
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
            occurred_at=(
                due_at
                or reminder_at
            ),
        )

    # ============================================================
    # CREATE LOCAL TASK
    # ============================================================

    def create_task(
        self,
        *,
        source_id: str,
        title: str,
        description: str = "",
        task_status: str = "pending",
        priority: str = "normal",
        due_at: str | None = None,
        reminder_at: str | None = None,
        list_name: str | None = None,
        recurrence: list[str] | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
        record_type: str = "task",
        sensitivity: str = "private",
    ) -> PersonalDataRecord:

        self._require_task_source(
            source_id
        )

        if record_type not in {
            "task",
            "reminder",
        }:

            raise ValueError(
                "record_type must be "
                "'task' or 'reminder'."
            )

        title = title.strip()

        if not title:

            raise ValueError(
                "Task title cannot "
                "be empty."
            )

        attributes = self._build_attributes(
            task_status=task_status,
            priority=priority,
            due_at=due_at,
            reminder_at=reminder_at,
            list_name=list_name,
            recurrence=recurrence,
            tags=tags,
            notes=notes,
        )

        return self.manager.create_record(
            source_id=source_id,
            record_type=record_type,
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            occurred_at=(
                due_at
                or reminder_at
            ),
        )

    # ============================================================
    # GET
    # ============================================================

    def get_task(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        return self._require_task_record(
            record_id
        )

    # ============================================================
    # UPDATE
    # ============================================================

    def update_task(
        self,
        record_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        task_status: str | None = None,
        priority: str | None = None,
        due_at: str | None = None,
        reminder_at: str | None = None,
        completed_at: str | None = None,
        list_name: str | None = None,
        recurrence: list[str] | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
        sensitivity: str | None = None,
    ) -> PersonalDataRecord:

        task = self._require_task_record(
            record_id
        )

        attributes = dict(
            task.attributes
        )

        if task_status is not None:

            attributes[
                "task_status"
            ] = (
                self._validate_task_status(
                    task_status
                )
            )

        if priority is not None:

            attributes[
                "priority"
            ] = (
                self._validate_priority(
                    priority
                )
            )

        simple_fields = {
            "due_at": due_at,
            "reminder_at": reminder_at,
            "completed_at": completed_at,
            "list_name": list_name,
            "notes": notes,
        }

        for key, value in (
            simple_fields.items()
        ):

            if value is not None:

                attributes[
                    key
                ] = self._clean_text(
                    value
                )

        if recurrence is not None:

            attributes[
                "recurrence"
            ] = self._clean_list(
                recurrence
            )

        if tags is not None:

            attributes[
                "tags"
            ] = self._clean_list(
                tags
            )

        occurred_at = None

        if due_at is not None:

            occurred_at = due_at

        elif reminder_at is not None:

            occurred_at = reminder_at

        return self.manager.update_record(
            record_id=task.record_id,
            title=title,
            content=description,
            attributes=attributes,
            sensitivity=sensitivity,
            occurred_at=occurred_at,
        )

    # ============================================================
    # COMPLETE
    # ============================================================

    def complete_task(
        self,
        record_id: str,
        completed_at: str | None = None,
    ) -> PersonalDataRecord:

        return self.update_task(
            record_id,
            task_status="completed",
            completed_at=completed_at,
        )

    # ============================================================
    # ARCHIVE
    # ============================================================

    def archive_task(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        task = self._require_task_record(
            record_id
        )

        return self.manager.archive_record(
            task.record_id
        )

    # ============================================================
    # LIST
    # ============================================================

    def list_tasks(
        self,
        *,
        source_id: str | None = None,
        record_type: str | None = None,
        active_only: bool = True,
        task_status: str | None = None,
    ) -> list[PersonalDataRecord]:

        if source_id is not None:

            self._require_task_source(
                source_id
            )

        if (
            record_type is not None
            and record_type not in {
                "task",
                "reminder",
            }
        ):

            raise ValueError(
                "record_type must be "
                "'task', 'reminder', or None."
            )

        records = self.manager.list_records(
            source_id=source_id,
            active_only=active_only,
        )

        results = []

        normalized_status = None

        if task_status is not None:

            normalized_status = (
                self._validate_task_status(
                    task_status
                )
            )

        for record in records:

            if (
                record.record_type
                not in {
                    "task",
                    "reminder",
                }
            ):

                continue

            if (
                record_type is not None
                and record.record_type
                != record_type
            ):

                continue

            if normalized_status is not None:

                if (
                    record.attributes.get(
                        "task_status"
                    )
                    != normalized_status
                ):

                    continue

            results.append(
                record
            )

        return results

    # ============================================================
    # SEARCH
    # ============================================================

    def search_tasks(
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

        tasks = self.list_tasks(
            source_id=source_id,
            active_only=active_only,
        )

        if not normalized:

            return tasks

        results = []

        for task in tasks:

            attributes = (
                task.attributes
            )

            values = [
                task.title,
                task.content,
                attributes.get(
                    "list_name",
                    "",
                ),
                attributes.get(
                    "notes",
                    "",
                ),
                attributes.get(
                    "priority",
                    "",
                ),
                attributes.get(
                    "task_status",
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
                    task
                )

        return results

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = self._require_task_source(
            source_id
        )

        records = self.list_tasks(
            source_id=source_id,
            active_only=False,
        )

        active_records = [
            record
            for record in records
            if record.status == "active"
        ]

        pending = [
            record
            for record in active_records
            if (
                record.attributes.get(
                    "task_status"
                )
                in {
                    "pending",
                    "in_progress",
                }
            )
        ]

        completed = [
            record
            for record in active_records
            if (
                record.attributes.get(
                    "task_status"
                )
                == "completed"
            )
        ]

        return {
            "source_id": (
                source.source_id
            ),
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
                active_records
            ),
            "pending": len(
                pending
            ),
            "completed": len(
                completed
            ),
            "last_sync_at": (
                source.last_sync_at
            ),
        }


task_service = TaskService()