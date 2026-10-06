from __future__ import annotations

import hashlib

from typing import Any

from app.personal_data.google_tasks_connector import (
    GoogleTasksConnector,
    google_tasks_connector,
)

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
    PersonalDataSource,
)

from app.personal_data.task_service import (
    TaskService,
    task_service,
)


class GoogleTasksSync:

    SOURCE_NAME = "Google Tasks"

    def __init__(
        self,
        connector:
        GoogleTasksConnector | None = None,
        service:
        TaskService | None = None,
    ) -> None:

        self.connector = (
            connector
            if connector is not None
            else google_tasks_connector
        )

        self.service = (
            service
            if service is not None
            else task_service
        )

    # ============================================================
    # SOURCE
    # ============================================================

    def register_source(
        self,
    ) -> PersonalDataSource:

        return self.service.register_source(
            name=self.SOURCE_NAME,
            source_type="task",
            access_mode="read_only",
            permissions_required=[
                "task.read",
            ],
            attributes={
                "provider": "google",
                "service": "google_tasks",
                "synchronization": "full",
                "read_only": True,
            },
        )

    # ============================================================
    # EXTERNAL ID
    # ============================================================

    @staticmethod
    def _external_id(
        tasklist_id: str,
        task_id: str,
    ) -> str:

        list_key = hashlib.sha256(
            tasklist_id.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

        return (
            "google-tasks:"
            f"{list_key}:"
            f"{task_id}"
        )

    # ============================================================
    # GOOGLE STATUS
    # ============================================================

    @staticmethod
    def _task_status(
        task: dict[str, Any],
    ) -> str:

        status = task.get(
            "status",
            "needsAction",
        )

        if status == "completed":

            return "completed"

        return "pending"

    # ============================================================
    # DUE DATE
    # ============================================================

    @staticmethod
    def _due_date(
        task: dict[str, Any],
    ) -> str:

        due = str(
            task.get(
                "due",
                "",
            )
        ).strip()

        if not due:

            return ""

        # Google Tasks stores due dates without
        # meaningful time-of-day information.
        #
        # Preserve only YYYY-MM-DD so MoneroAI
        # does not invent an exact deadline time.
        if len(due) >= 10:

            return due[:10]

        return due

    # ============================================================
    # ATTRIBUTES
    # ============================================================

    def _attributes(
        self,
        *,
        tasklist_id: str,
        tasklist_title: str,
        task: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "provider": (
                "google"
            ),
            "service": (
                "google_tasks"
            ),
            "google_tasklist_key": (
                hashlib.sha256(
                    tasklist_id.encode(
                        "utf-8"
                    )
                ).hexdigest()[:16]
            ),
            "tasklist_title": (
                tasklist_title
            ),
            "google_updated_at": (
                task.get(
                    "updated",
                    "",
                )
            ),
            "google_status": (
                task.get(
                    "status",
                    "",
                )
            ),
            "hidden": bool(
                task.get(
                    "hidden",
                    False,
                )
            ),
            "deleted": bool(
                task.get(
                    "deleted",
                    False,
                )
            ),
            "position": (
                task.get(
                    "position",
                    "",
                )
            ),
            "parent_task_id": (
                task.get(
                    "parent",
                    "",
                )
            ),
            "due_is_date_only": bool(
                task.get(
                    "due"
                )
            ),
        }

    # ============================================================
    # EXISTING LOCAL RECORDS
    # ============================================================

    def _local_records(
        self,
        source_id: str,
    ) -> list[PersonalDataRecord]:

        return self.service.list_tasks(
            source_id=source_id,
            active_only=False,
        )

    # ============================================================
    # DELETE EXISTING INGESTED RECORD
    # ============================================================

    def _mark_ingested_deleted(
        self,
        record: PersonalDataRecord,
    ) -> PersonalDataRecord:

        attributes = dict(
            record.attributes
        )

        attributes[
            "deleted"
        ] = True

        return (
            self.service.manager
            .update_ingested_record(
                record_id=(
                    record.record_id
                ),
                attributes=attributes,
                status="deleted",
            )
        )

    # ============================================================
    # SYNC ONE REMOTE TASK
    # ============================================================

    def _sync_task(
        self,
        *,
        source_id: str,
        tasklist_id: str,
        tasklist_title: str,
        task: dict[str, Any],
    ) -> tuple[
        str,
        PersonalDataRecord | None,
    ]:

        task_id = str(
            task.get(
                "id",
                "",
            )
        ).strip()

        if not task_id:

            return (
                "skipped",
                None,
            )

        external_id = (
            self._external_id(
                tasklist_id,
                task_id,
            )
        )

        existing = (
            self.service
            .get_by_external_id(
                source_id,
                external_id,
            )
        )

        deleted = bool(
            task.get(
                "deleted",
                False,
            )
        )

        if deleted:

            if existing is None:

                # A remote tombstone that was
                # never imported locally does not
                # need a local record.
                return (
                    "skipped_deleted",
                    None,
                )

            updated = (
                self._mark_ingested_deleted(
                    existing
                )
            )

            return (
                "deleted",
                updated,
            )

        title = str(
            task.get(
                "title",
                "",
            )
        ).strip()

        if not title:

            title = (
                "Untitled Google Task"
            )

        notes = str(
            task.get(
                "notes",
                "",
            )
        ).strip()

        due_at = self._due_date(
            task
        )

        completed_at = str(
            task.get(
                "completed",
                "",
            )
        ).strip()

        attributes = self._attributes(
            tasklist_id=tasklist_id,
            tasklist_title=tasklist_title,
            task=task,
        )

        was_existing = (
            existing is not None
        )

        record = (
            self.service.ingest_task(
                source_id=source_id,
                external_id=external_id,
                title=title,
                description=notes,
                task_status=(
                    self._task_status(
                        task
                    )
                ),
                priority="normal",
                due_at=(
                    due_at
                    or None
                ),
                completed_at=(
                    completed_at
                    or None
                ),
                list_name=(
                    tasklist_title
                ),
                notes=notes,
                record_type="task",
                extra_attributes=(
                    attributes
                ),
                sensitivity="private",
            )
        )

        if was_existing:

            return (
                "updated",
                record,
            )

        return (
            "created",
            record,
        )

    # ============================================================
    # FULL SYNC
    # ============================================================

    def sync(
        self,
    ) -> dict[str, Any]:

        source = self.register_source()

        tasklists = (
            self.connector
            .fetch_tasklists()
        )

        fetched = 0
        created = 0
        updated = 0
        deleted = 0
        skipped = 0

        remote_ids = set()

        for tasklist in tasklists:

            tasklist_id = str(
                tasklist.get(
                    "id",
                    "",
                )
            ).strip()

            if not tasklist_id:

                continue

            tasklist_title = str(
                tasklist.get(
                    "title",
                    "",
                )
            ).strip()

            tasks = (
                self.connector
                .fetch_tasks(
                    tasklist_id,
                    show_completed=True,
                    show_deleted=True,
                    show_hidden=True,
                )
            )

            for task in tasks:

                task_id = str(
                    task.get(
                        "id",
                        "",
                    )
                ).strip()

                if task_id:

                    remote_ids.add(
                        self._external_id(
                            tasklist_id,
                            task_id,
                        )
                    )

                fetched += 1

                action, _ = (
                    self._sync_task(
                        source_id=(
                            source.source_id
                        ),
                        tasklist_id=(
                            tasklist_id
                        ),
                        tasklist_title=(
                            tasklist_title
                        ),
                        task=task,
                    )
                )

                if action == "created":

                    created += 1

                elif action == "updated":

                    updated += 1

                elif action == "deleted":

                    deleted += 1

                else:

                    skipped += 1

        # ========================================================
        # RECONCILIATION
        #
        # Any active local Google Task no longer
        # present in a complete remote snapshot is
        # treated as removed remotely.
        # ========================================================

        local_records = (
            self._local_records(
                source.source_id
            )
        )

        for record in local_records:

            external_id = (
                record.external_id
                or ""
            )

            if not external_id.startswith(
                "google-tasks:"
            ):

                continue

            if record.status != "active":

                continue

            if external_id in remote_ids:

                continue

            self._mark_ingested_deleted(
                record
            )

            deleted += 1

        self.service.manager.mark_source_synced(
            source.source_id
        )

        active_tasks = len(
            self.service.list_tasks(
                source_id=(
                    source.source_id
                ),
                active_only=True,
            )
        )

        return {
            "mode": "full",
            "source_id": (
                source.source_id
            ),
            "source_name": (
                source.name
            ),
            "access_mode": (
                source.access_mode
            ),
            "tasklists": len(
                tasklists
            ),
            "fetched": fetched,
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "skipped": skipped,
            "active_tasks": (
                active_tasks
            ),
        }


google_tasks_sync = (
    GoogleTasksSync()
)