from __future__ import annotations

import json
import os

from datetime import datetime
from pathlib import Path
from typing import Any

from googleapiclient.errors import (
    HttpError,
)

from app.personal_data.contacts_service import (
    ContactsService,
    contacts_service,
)

from app.personal_data.google_contacts_connector import (
    GoogleContactsConnector,
    google_contacts_connector,
)


class GoogleContactsSync:

    PAGE_SIZE = 500

    def __init__(
        self,
        connector:
        GoogleContactsConnector | None = None,
        contacts_service_instance:
        ContactsService | None = None,
        state_path:
        str | Path | None = None,
    ) -> None:

        self.connector = (
            connector
            if connector is not None
            else google_contacts_connector
        )

        self.contacts_service = (
            contacts_service_instance
            if contacts_service_instance
            is not None
            else contacts_service
        )

        self.state_path = Path(
            state_path
            if state_path is not None
            else (
                "data/personal_data/google/"
                "contacts_sync_state.json"
            )
        )

    # ============================================================
    # TIME
    # ============================================================

    @staticmethod
    def _now() -> str:

        return datetime.now().isoformat(
            timespec="seconds"
        )

    # ============================================================
    # STATE
    # ============================================================

    def _empty_state(
        self,
    ) -> dict[str, Any]:

        return {
            "sync_token": None,
            "person_fields": (
                self.connector.PERSON_FIELDS
            ),
            "page_size": self.PAGE_SIZE,
            "updated_at": None,
        }

    def _load_state(
        self,
    ) -> dict[str, Any]:

        if not self.state_path.exists():

            return self._empty_state()

        try:

            raw = self.state_path.read_text(
                encoding="utf-8"
            ).strip()

            if not raw:

                return self._empty_state()

            data = json.loads(
                raw
            )

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return self._empty_state()

        if not isinstance(
            data,
            dict,
        ):

            return self._empty_state()

        # A sync token is valid only when the
        # request parameters still match the
        # original full-sync request.
        if (
            data.get(
                "person_fields"
            )
            != self.connector.PERSON_FIELDS
            or data.get(
                "page_size"
            )
            != self.PAGE_SIZE
        ):

            return self._empty_state()

        return {
            "sync_token": data.get(
                "sync_token"
            ),
            "person_fields": (
                self.connector.PERSON_FIELDS
            ),
            "page_size": self.PAGE_SIZE,
            "updated_at": data.get(
                "updated_at"
            ),
        }

    def _save_state(
        self,
        sync_token: str,
    ) -> None:

        if not sync_token:

            raise ValueError(
                "Google Contacts sync token "
                "cannot be empty."
            )

        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            self.state_path.with_suffix(
                self.state_path.suffix
                + ".tmp"
            )
        )

        data = {
            "sync_token": sync_token,
            "person_fields": (
                self.connector.PERSON_FIELDS
            ),
            "page_size": self.PAGE_SIZE,
            "updated_at": self._now(),
        }

        temporary_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary_path,
            self.state_path,
        )

    def clear_state(
        self,
    ) -> None:

        self.state_path.unlink(
            missing_ok=True
        )

    def has_sync_token(
        self,
    ) -> bool:

        return bool(
            self._load_state().get(
                "sync_token"
            )
        )

    # ============================================================
    # SOURCE
    # ============================================================

    def _get_source(
        self,
    ):

        return (
            self.connector
            .register_local_source()
        )

    # ============================================================
    # GOOGLE ERROR CHECK
    # ============================================================

    @staticmethod
    def _is_expired_sync_error(
        error: HttpError,
    ) -> bool:

        status = getattr(
            error.resp,
            "status",
            None,
        )

        content = getattr(
            error,
            "content",
            b"",
        )

        if isinstance(
            content,
            bytes,
        ):

            content_text = (
                content.decode(
                    "utf-8",
                    errors="ignore",
                )
            )

        else:

            content_text = str(
                content
            )

        return (
            status == 410
            or (
                "EXPIRED_SYNC_TOKEN"
                in content_text
            )
        )

    # ============================================================
    # RAW PERSON CONVERSION
    # ============================================================

    def _convert(
        self,
        person: dict[str, Any],
    ) -> dict[str, Any] | None:

        converted = (
            self.connector
            ._convert_person(
                person
            )
        )

        if converted is None:

            return None

        metadata = person.get(
            "metadata",
            {},
        )

        converted[
            "previous_external_ids"
        ] = list(
            metadata.get(
                "previousResourceNames",
                [],
            )
        )

        return converted

    # ============================================================
    # FULL REMOTE FETCH + TOKEN
    # ============================================================

    def _fetch_full(
        self,
    ) -> tuple[
        list[dict[str, Any]],
        str,
    ]:

        service = (
            self.connector._get_service()
        )

        contacts = []

        page_token = None

        final_sync_token = None

        while True:

            request = (
                service.people()
                .connections()
                .list(
                    resourceName="people/me",
                    pageSize=self.PAGE_SIZE,
                    pageToken=page_token,
                    personFields=(
                        self.connector
                        .PERSON_FIELDS
                    ),
                    requestSyncToken=True,
                )
            )

            response = request.execute()

            for person in response.get(
                "connections",
                [],
            ):

                converted = self._convert(
                    person
                )

                if converted is None:

                    continue

                if converted[
                    "deleted"
                ]:

                    continue

                contacts.append(
                    converted
                )

            page_token = response.get(
                "nextPageToken"
            )

            if page_token:

                continue

            final_sync_token = (
                response.get(
                    "nextSyncToken"
                )
            )

            break

        if not final_sync_token:

            raise RuntimeError(
                "Google did not return "
                "nextSyncToken after the "
                "full Contacts sync."
            )

        return (
            contacts,
            final_sync_token,
        )

    # ============================================================
    # INCREMENTAL REMOTE FETCH
    # ============================================================

    def _fetch_changes(
        self,
        sync_token: str,
    ) -> tuple[
        list[dict[str, Any]],
        str,
    ]:

        service = (
            self.connector._get_service()
        )

        changes = []

        page_token = None

        next_sync_token = None

        while True:

            request = (
                service.people()
                .connections()
                .list(
                    resourceName="people/me",
                    pageSize=self.PAGE_SIZE,
                    pageToken=page_token,
                    personFields=(
                        self.connector
                        .PERSON_FIELDS
                    ),
                    syncToken=sync_token,
                )
            )

            response = request.execute()

            for person in response.get(
                "connections",
                [],
            ):

                converted = self._convert(
                    person
                )

                if converted is None:

                    continue

                changes.append(
                    converted
                )

            page_token = response.get(
                "nextPageToken"
            )

            if page_token:

                continue

            next_sync_token = (
                response.get(
                    "nextSyncToken"
                )
            )

            break

        if not next_sync_token:

            raise RuntimeError(
                "Google did not return "
                "nextSyncToken after "
                "incremental Contacts sync."
            )

        return (
            changes,
            next_sync_token,
        )

    # ============================================================
    # PREVIOUS RESOURCE-NAME MIGRATION
    # ============================================================

    def _resolve_existing_record(
        self,
        source_id: str,
        contact: dict[str, Any],
    ):

        current = (
            self.contacts_service
            .get_by_external_id(
                source_id,
                contact[
                    "external_id"
                ],
            )
        )

        if current is not None:

            return current

        for previous_id in contact.get(
            "previous_external_ids",
            [],
        ):

            previous = (
                self.contacts_service
                .get_by_external_id(
                    source_id,
                    previous_id,
                )
            )

            if previous is None:

                continue

            return (
                self.contacts_service
                .manager
                .update_ingested_record(
                    record_id=(
                        previous.record_id
                    ),
                    external_id=contact[
                        "external_id"
                    ],
                )
            )

        return None

    # ============================================================
    # UPSERT
    # ============================================================

    def _upsert(
        self,
        source_id: str,
        contact: dict[str, Any],
    ) -> str:

        existing = (
            self._resolve_existing_record(
                source_id,
                contact,
            )
        )

        before_id = (
            existing.record_id
            if existing is not None
            else None
        )

        saved = (
            self.contacts_service
            .ingest_contact(
                source_id=source_id,
                external_id=contact[
                    "external_id"
                ],
                display_name=contact[
                    "display_name"
                ],
                given_name=contact[
                    "given_name"
                ],
                family_name=contact[
                    "family_name"
                ],
                emails=contact[
                    "emails"
                ],
                phones=contact[
                    "phones"
                ],
                company=contact[
                    "company"
                ],
                job_title=contact[
                    "job_title"
                ],
                birthday=contact[
                    "birthday"
                ],
                addresses=contact[
                    "addresses"
                ],
                notes=contact[
                    "notes"
                ],
                sensitivity="sensitive",
            )
        )

        if (
            before_id is not None
            and before_id
            == saved.record_id
        ):

            return "updated"

        return "created"

    # ============================================================
    # DELETE LOCAL CACHED CONTACT
    # ============================================================

    def _mark_deleted(
        self,
        source_id: str,
        contact: dict[str, Any],
    ) -> bool:

        existing = (
            self._resolve_existing_record(
                source_id,
                contact,
            )
        )

        if existing is None:

            return False

        self.contacts_service.manager.update_ingested_record(
            record_id=existing.record_id,
            status="deleted",
            external_id=contact[
                "external_id"
            ],
        )

        return True

    # ============================================================
    # FULL-SYNC RECONCILIATION
    # ============================================================

    def _reconcile_missing(
        self,
        source_id: str,
        remote_external_ids: set[str],
    ) -> int:

        local_contacts = (
            self.contacts_service
            .list_contacts(
                source_id=source_id,
                active_only=True,
            )
        )

        deleted_count = 0

        for local_contact in local_contacts:

            external_id = (
                local_contact.external_id
            )

            if not external_id:

                continue

            if (
                external_id
                in remote_external_ids
            ):

                continue

            self.contacts_service.manager.update_ingested_record(
                record_id=(
                    local_contact.record_id
                ),
                status="deleted",
            )

            deleted_count += 1

        return deleted_count

    # ============================================================
    # FULL SYNC
    # ============================================================

    def full_sync(
        self,
    ) -> dict[str, Any]:

        source = self._get_source()

        remote_contacts, sync_token = (
            self._fetch_full()
        )

        created = 0

        updated = 0

        remote_external_ids = set()

        for contact in remote_contacts:

            remote_external_ids.add(
                contact[
                    "external_id"
                ]
            )

            action = self._upsert(
                source.source_id,
                contact,
            )

            if action == "created":

                created += 1

            else:

                updated += 1

        deleted = self._reconcile_missing(
            source.source_id,
            remote_external_ids,
        )

        (
            self.contacts_service
            .manager
            .mark_source_synced(
                source.source_id
            )
        )

        self._save_state(
            sync_token
        )

        active_contacts = (
            self.contacts_service
            .list_contacts(
                source_id=source.source_id,
                active_only=True,
            )
        )

        return {
            "mode": "full",
            "fallback": False,
            "fetched": len(
                remote_contacts
            ),
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "active_contacts": len(
                active_contacts
            ),
            "sync_token_saved": (
                self.has_sync_token()
            ),
        }

    # ============================================================
    # INCREMENTAL SYNC
    # ============================================================

    def incremental_sync(
        self,
    ) -> dict[str, Any]:

        state = self._load_state()

        sync_token = state.get(
            "sync_token"
        )

        if not sync_token:

            return self.full_sync()

        source = self._get_source()

        try:

            changes, next_sync_token = (
                self._fetch_changes(
                    sync_token
                )
            )

        except HttpError as exc:

            if not self._is_expired_sync_error(
                exc
            ):

                raise

            # Google sync tokens expire.
            # Clear it and safely rebuild local
            # state using a new full sync.
            self.clear_state()

            result = self.full_sync()

            result[
                "fallback"
            ] = True

            result[
                "fallback_reason"
            ] = "expired_sync_token"

            return result

        created = 0

        updated = 0

        deleted = 0

        for contact in changes:

            if contact[
                "deleted"
            ]:

                if self._mark_deleted(
                    source.source_id,
                    contact,
                ):

                    deleted += 1

                continue

            action = self._upsert(
                source.source_id,
                contact,
            )

            if action == "created":

                created += 1

            else:

                updated += 1

        (
            self.contacts_service
            .manager
            .mark_source_synced(
                source.source_id
            )
        )

        self._save_state(
            next_sync_token
        )

        active_contacts = (
            self.contacts_service
            .list_contacts(
                source_id=source.source_id,
                active_only=True,
            )
        )

        return {
            "mode": "incremental",
            "fallback": False,
            "fetched": len(
                changes
            ),
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "active_contacts": len(
                active_contacts
            ),
            "sync_token_saved": (
                self.has_sync_token()
            ),
        }

    # ============================================================
    # NORMAL SYNC ENTRY POINT
    # ============================================================

    def sync(
        self,
    ) -> dict[str, Any]:

        if self.has_sync_token():

            return self.incremental_sync()

        return self.full_sync()


google_contacts_sync = (
    GoogleContactsSync()
)