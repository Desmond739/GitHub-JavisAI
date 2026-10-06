from __future__ import annotations

from pathlib import Path
from typing import Any

from app.personal_data.personal_data_model import (
    PersonalDataSource,
)

from app.personal_data.contacts_service import (
    ContactsService,
    contacts_service,
)

from google.auth.transport.requests import (
    Request,
)

from google.oauth2.credentials import (
    Credentials,
)

from google_auth_oauthlib.flow import (
    InstalledAppFlow,
)

from googleapiclient.discovery import (
    build,
)

from app.personal_data.secure_file_writer import (
    atomic_write_private_text,
)


class GoogleContactsConnector:

    READONLY_SCOPE = (
        "https://www.googleapis.com/"
        "auth/contacts.readonly"
    )

    SCOPES = [
        READONLY_SCOPE,
    ]

    PERSON_FIELDS = (
        "names,"
        "emailAddresses,"
        "phoneNumbers,"
        "organizations,"
        "birthdays,"
        "addresses,"
        "biographies,"
        "metadata"
    )

    def __init__(
        self,
        contacts_service_instance:
        ContactsService | None = None,
        credentials_path:
        str | Path | None = None,
        token_path:
        str | Path | None = None,
    ) -> None:

        self.contacts_service = (
            contacts_service_instance
            if contacts_service_instance
            is not None
            else contacts_service
        )

        self.credentials_path = Path(
            credentials_path
            if credentials_path is not None
            else (
                "data/personal_data/google/"
                "credentials.json"
            )
        )

        self.token_path = Path(
            token_path
            if token_path is not None
            else (
                "data/personal_data/google/"
                "contacts_token.json"
            )
        )

        self._credentials = None

        self._service = None

    # ============================================================
    # CREDENTIAL FILE
    # ============================================================

    def credentials_available(
        self,
    ) -> bool:

        return self.credentials_path.exists()

    def token_available(
        self,
    ) -> bool:

        return self.token_path.exists()

    def _require_credentials_file(
        self,
    ) -> None:

        if not self.credentials_path.exists():

            raise FileNotFoundError(
                "Google OAuth credentials "
                "file was not found: "
                f"{self.credentials_path}"
            )

    # ============================================================
    # TOKEN STORAGE
    # ============================================================

    def _save_token(
        self,
        credentials: Credentials,
    ) -> None:

        atomic_write_private_text(
            self.token_path,
            credentials.to_json(),
            error_label=(
                "the Google Contacts "
                "OAuth token"
            ),
        )

    # ============================================================
    # AUTHENTICATION
    # ============================================================

    def authenticate(
        self,
        *,
        allow_interactive: bool = False,
    ) -> Credentials:

        self._require_credentials_file()

        credentials = None

        if self.token_path.exists():

            try:

                credentials = (
                    Credentials
                    .from_authorized_user_file(
                        str(
                            self.token_path
                        ),
                        self.SCOPES,
                    )
                )

            except Exception:

                # Invalid/stale local token.
                #
                # The OAuth flow below will
                # obtain a fresh one.
                credentials = None

        if (
            credentials is not None
            and credentials.valid
        ):

            self._credentials = (
                credentials
            )

            return credentials

        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):

            try:

                credentials.refresh(
                    Request()
                )

                self._save_token(
                    credentials
                )

                self._credentials = (
                    credentials
                )

                return credentials

            except Exception:

                # If refresh fails, start a
                # clean interactive login.
                credentials = None

        if not allow_interactive:

            raise PermissionError(
                "Interactive Google Contacts authorization is disabled. "
                "Use the explicit read-only authorization utility after "
                "the user approves."
            )

        flow = (
            InstalledAppFlow
            .from_client_secrets_file(
                str(
                    self.credentials_path
                ),
                self.SCOPES,
            )
        )

        credentials = (
            flow.run_local_server(
                port=0
            )
        )

        self._save_token(
            credentials
        )

        self._credentials = (
            credentials
        )

        return credentials

    # ============================================================
    # GOOGLE PEOPLE SERVICE
    # ============================================================

    def connect(
        self,
    ):

        credentials = (
            self.authenticate()
        )

        self._service = build(
            "people",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        return self._service

    def _get_service(
        self,
    ):

        if self._service is None:

            return self.connect()

        return self._service

    # ============================================================
    # PRIMARY FIELD
    # ============================================================

    @staticmethod
    def _primary_item(
        items: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        if not items:

            return None

        for item in items:

            metadata = item.get(
                "metadata",
                {},
            )

            if metadata.get(
                "primary"
            ) is True:

                return item

        return items[0]

    # ============================================================
    # BIRTHDAY
    # ============================================================

    @staticmethod
    def _birthday_to_text(
        birthdays: list[
            dict[str, Any]
        ],
    ) -> str:

        if not birthdays:

            return ""

        birthday = (
            birthdays[0]
            .get(
                "date",
                {},
            )
        )

        year = birthday.get(
            "year"
        )

        month = birthday.get(
            "month"
        )

        day = birthday.get(
            "day"
        )

        if (
            month is None
            or day is None
        ):

            return ""

        if year is None:

            return (
                f"{month:02d}-"
                f"{day:02d}"
            )

        return (
            f"{year:04d}-"
            f"{month:02d}-"
            f"{day:02d}"
        )

    # ============================================================
    # CONVERT GOOGLE PERSON
    # ============================================================

    def _convert_person(
        self,
        person: dict[str, Any],
    ) -> dict[str, Any] | None:

        external_id = (
            person.get(
                "resourceName"
            )
        )

        if not external_id:

            return None

        metadata = person.get(
            "metadata",
            {},
        )

        deleted = bool(
            metadata.get(
                "deleted",
                False,
            )
        )

        names = person.get(
            "names",
            [],
        )

        primary_name = (
            self._primary_item(
                names
            )
        )

        display_name = ""

        given_name = ""

        family_name = ""

        if primary_name is not None:

            display_name = (
                primary_name.get(
                    "displayName",
                    "",
                )
            )

            given_name = (
                primary_name.get(
                    "givenName",
                    "",
                )
            )

            family_name = (
                primary_name.get(
                    "familyName",
                    "",
                )
            )

        emails = [
            item.get(
                "value",
                "",
            ).strip()
            for item
            in person.get(
                "emailAddresses",
                [],
            )
            if item.get(
                "value"
            )
        ]

        phones = [
            item.get(
                "value",
                "",
            ).strip()
            for item
            in person.get(
                "phoneNumbers",
                [],
            )
            if item.get(
                "value"
            )
        ]

        organization = (
            self._primary_item(
                person.get(
                    "organizations",
                    [],
                )
            )
        )

        company = ""

        job_title = ""

        if organization is not None:

            company = (
                organization.get(
                    "name",
                    "",
                )
            )

            job_title = (
                organization.get(
                    "title",
                    "",
                )
            )

        addresses = [
            (
                item.get(
                    "formattedValue"
                )
                or item.get(
                    "streetAddress"
                )
                or ""
            ).strip()
            for item
            in person.get(
                "addresses",
                [],
            )
            if (
                item.get(
                    "formattedValue"
                )
                or item.get(
                    "streetAddress"
                )
            )
        ]

        biographies = (
            person.get(
                "biographies",
                []
            )
        )

        notes = ""

        if biographies:

            notes = (
                biographies[0]
                .get(
                    "value",
                    "",
                )
            )

        return {
            "external_id": external_id,
            "display_name": display_name,
            "given_name": given_name,
            "family_name": family_name,
            "emails": emails,
            "phones": phones,
            "company": company,
            "job_title": job_title,
            "birthday": (
                self._birthday_to_text(
                    person.get(
                        "birthdays",
                        [],
                    )
                )
            ),
            "addresses": addresses,
            "notes": notes,
            "deleted": deleted,
        }

    # ============================================================
    # FETCH CONTACTS — READ ONLY
    # ============================================================

    def fetch_contacts(
        self,
        max_contacts: int | None = None,
    ) -> list[dict[str, Any]]:

        if (
            max_contacts is not None
            and max_contacts <= 0
        ):

            return []

        service = (
            self._get_service()
        )

        results = []

        page_token = None

        while True:

            remaining = None

            if max_contacts is not None:

                remaining = (
                    max_contacts
                    - len(results)
                )

                if remaining <= 0:

                    break

            page_size = 500

            if remaining is not None:

                page_size = min(
                    page_size,
                    remaining,
                )

            request = (
                service.people()
                .connections()
                .list(
                    resourceName="people/me",
                    pageSize=page_size,
                    pageToken=page_token,
                    personFields=(
                        self.PERSON_FIELDS
                    ),
                )
            )

            response = request.execute()

            for person in response.get(
                "connections",
                [],
            ):

                converted = (
                    self._convert_person(
                        person
                    )
                )

                if converted is None:

                    continue

                if converted[
                    "deleted"
                ]:

                    continue

                results.append(
                    converted
                )

                if (
                    max_contacts is not None
                    and len(results)
                    >= max_contacts
                ):

                    break

            if (
                max_contacts is not None
                and len(results)
                >= max_contacts
            ):

                break

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:

                break

        return results

    # ============================================================
    # REGISTER LOCAL SOURCE
    # ============================================================

    def register_local_source(
        self,
    ) -> PersonalDataSource:

        return (
            self.contacts_service
            .register_source(
                name="Google Contacts",
                access_mode="read_only",
                permissions_required=[
                    "contacts.read",
                ],
                attributes={
                    "provider": "google",
                    "api": "people_v1",
                    "oauth_scope": (
                        self.READONLY_SCOPE
                    ),
                },
            )
        )

    # ============================================================
    # READ-ONLY LOCAL SYNCHRONIZATION
    # ============================================================

    def sync_contacts(
        self,
        max_contacts: int | None = None,
    ) -> dict[str, Any]:

        source = (
            self.register_local_source()
        )

        remote_contacts = (
            self.fetch_contacts(
                max_contacts=max_contacts
            )
        )

        stored = 0

        for contact in remote_contacts:

            self.contacts_service.ingest_contact(
                source_id=source.source_id,
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

            stored += 1

        self.contacts_service.manager.mark_source_synced(
            source.source_id
        )

        return {
            "source_id": source.source_id,
            "source_name": source.name,
            "access_mode": (
                source.access_mode
            ),
            "fetched": len(
                remote_contacts
            ),
            "stored": stored,
            "local_contacts": len(
                self.contacts_service
                .list_contacts(
                    source_id=(
                        source.source_id
                    ),
                    active_only=True,
                )
            ),
        }


google_contacts_connector = (
    GoogleContactsConnector()
)
