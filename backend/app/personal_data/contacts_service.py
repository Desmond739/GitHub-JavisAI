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


class ContactsService:

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

        return value.strip()

    @staticmethod
    def _normalize_email(
        value: str,
    ) -> str:

        return value.strip().casefold()

    @staticmethod
    def _normalize_phone(
        value: str,
    ) -> str:

        value = value.strip()

        prefix = (
            "+"
            if value.startswith("+")
            else ""
        )

        digits = "".join(
            character
            for character in value
            if character.isdigit()
        )

        return prefix + digits

    @staticmethod
    def _clean_list(
        values: list[str] | None,
    ) -> list[str]:

        if values is None:
            return []

        result = []
        seen = set()

        for value in values:

            cleaned = value.strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    # ============================================================
    # SOURCE VALIDATION
    # ============================================================

    def _require_contact_source(
        self,
        source_id: str,
    ) -> PersonalDataSource:

        source = self.manager.get_source(
            source_id
        )

        if source is None:

            raise KeyError(
                "Contact source not found: "
                f"{source_id}"
            )

        if source.source_type != "contact":

            raise ValueError(
                "Source is not a contact source: "
                f"{source.name}"
            )

        return source

    # ============================================================
    # RECORD VALIDATION
    # ============================================================

    def _require_contact_record(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = self.manager.get_record(
            record_id
        )

        if record is None:

            raise KeyError(
                "Contact record not found: "
                f"{record_id}"
            )

        if record.record_type != "contact":

            raise ValueError(
                "Record is not a contact: "
                f"{record_id}"
            )

        return record

    # ============================================================
    # CONTACT DISPLAY NAME
    # ============================================================

    def _resolve_display_name(
        self,
        display_name: str | None,
        emails: list[str],
        phones: list[str],
    ) -> str:

        name = self._clean_text(
            display_name
        )

        if name:
            return name

        if emails:
            return emails[0]

        if phones:
            return phones[0]

        return "Unnamed Contact"

    # ============================================================
    # CONTACT ATTRIBUTES
    # ============================================================

    def _build_attributes(
        self,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: list[str] | None = None,
        phones: list[str] | None = None,
        company: str | None = None,
        job_title: str | None = None,
        birthday: str | None = None,
        addresses: list[str] | None = None,
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
                "given_name": (
                    self._clean_text(
                        given_name
                    )
                ),
                "family_name": (
                    self._clean_text(
                        family_name
                    )
                ),
                "emails": (
                    self._clean_list(
                        emails
                    )
                ),
                "phones": (
                    self._clean_list(
                        phones
                    )
                ),
                "company": (
                    self._clean_text(
                        company
                    )
                ),
                "job_title": (
                    self._clean_text(
                        job_title
                    )
                ),
                "birthday": (
                    self._clean_text(
                        birthday
                    )
                ),
                "addresses": (
                    self._clean_list(
                        addresses
                    )
                ),
            }
        )

        return attributes

    # ============================================================
    # REGISTER CONTACT SOURCE
    # ============================================================

    def register_source(
        self,
        name: str = "Personal Contacts",
        access_mode: str = "read_only",
        permissions_required:
        list[str] | None = None,
        attributes:
        dict[str, Any] | None = None,
    ) -> PersonalDataSource:

        if permissions_required is None:

            permissions_required = [
                "contacts.read",
            ]

            if access_mode == "read_write":

                permissions_required.append(
                    "contacts.write"
                )

        return self.manager.register_source(
            source_type="contact",
            name=name,
            access_mode=access_mode,
            permissions_required=(
                permissions_required
            ),
            attributes=attributes,
        )

    # ============================================================
    # GET CONTACT BY EXTERNAL ID
    # ============================================================

    def get_by_external_id(
        self,
        source_id: str,
        external_id: str,
    ) -> PersonalDataRecord | None:

        self._require_contact_source(
            source_id
        )

        for record in (
            self.manager.list_records(
                source_id=source_id,
                record_type="contact",
            )
        ):

            if (
                record.external_id
                == external_id
            ):

                return record

        return None

    # ============================================================
    # INGEST / UPSERT EXTERNAL CONTACT
    # ============================================================

    def ingest_contact(
        self,
        source_id: str,
        external_id: str,
        display_name: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: list[str] | None = None,
        phones: list[str] | None = None,
        company: str | None = None,
        job_title: str | None = None,
        birthday: str | None = None,
        addresses: list[str] | None = None,
        notes: str = "",
        extra_attributes:
        dict[str, Any] | None = None,
        sensitivity: str = "sensitive",
    ) -> PersonalDataRecord:

        self._require_contact_source(
            source_id
        )

        external_id = external_id.strip()

        if not external_id:

            raise ValueError(
                "External contact ID "
                "cannot be empty."
            )

        clean_emails = self._clean_list(
            emails
        )

        clean_phones = self._clean_list(
            phones
        )

        title = self._resolve_display_name(
            display_name,
            clean_emails,
            clean_phones,
        )

        attributes = (
            self._build_attributes(
                given_name=given_name,
                family_name=family_name,
                emails=clean_emails,
                phones=clean_phones,
                company=company,
                job_title=job_title,
                birthday=birthday,
                addresses=addresses,
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
                    content=notes,
                    attributes=attributes,
                    sensitivity=sensitivity,
                    status="active",
                    external_id=external_id,
                )
            )

        return self.manager.ingest_record(
            source_id=source_id,
            record_type="contact",
            title=title,
            content=notes,
            attributes=attributes,
            sensitivity=sensitivity,
            external_id=external_id,
        )

    # ============================================================
    # CREATE CONTACT
    # ============================================================

    def create_contact(
        self,
        source_id: str,
        display_name: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: list[str] | None = None,
        phones: list[str] | None = None,
        company: str | None = None,
        job_title: str | None = None,
        birthday: str | None = None,
        addresses: list[str] | None = None,
        notes: str = "",
        sensitivity: str = "sensitive",
    ) -> PersonalDataRecord:

        self._require_contact_source(
            source_id
        )

        clean_emails = self._clean_list(
            emails
        )

        clean_phones = self._clean_list(
            phones
        )

        title = self._resolve_display_name(
            display_name,
            clean_emails,
            clean_phones,
        )

        attributes = (
            self._build_attributes(
                given_name=given_name,
                family_name=family_name,
                emails=clean_emails,
                phones=clean_phones,
                company=company,
                job_title=job_title,
                birthday=birthday,
                addresses=addresses,
            )
        )

        return self.manager.create_record(
            source_id=source_id,
            record_type="contact",
            title=title,
            content=notes,
            attributes=attributes,
            sensitivity=sensitivity,
        )

    # ============================================================
    # GET CONTACT
    # ============================================================

    def get_contact(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        return self._require_contact_record(
            record_id
        )

    # ============================================================
    # UPDATE LOCALLY CREATED CONTACT
    # ============================================================

    def update_contact(
        self,
        record_id: str,
        display_name: str | None = None,
        notes: str | None = None,
        attributes:
        dict[str, Any] | None = None,
        sensitivity: str | None = None,
    ) -> PersonalDataRecord:

        record = (
            self._require_contact_record(
                record_id
            )
        )

        return self.manager.update_record(
            record_id=record.record_id,
            title=display_name,
            content=notes,
            attributes=attributes,
            sensitivity=sensitivity,
        )

    # ============================================================
    # ARCHIVE CONTACT
    # ============================================================

    def archive_contact(
        self,
        record_id: str,
    ) -> PersonalDataRecord:

        record = (
            self._require_contact_record(
                record_id
            )
        )

        return self.manager.archive_record(
            record.record_id
        )

    # ============================================================
    # LIST CONTACTS
    # ============================================================

    def list_contacts(
        self,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        if source_id is not None:

            self._require_contact_source(
                source_id
            )

        return self.manager.list_records(
            source_id=source_id,
            record_type="contact",
            active_only=active_only,
        )

    # ============================================================
    # SEARCH CONTACTS
    # ============================================================

    def search_contacts(
        self,
        query: str,
        source_id: str | None = None,
        active_only: bool = True,
    ) -> list[PersonalDataRecord]:

        query = query.strip()

        contacts = self.list_contacts(
            source_id=source_id,
            active_only=active_only,
        )

        if not query:

            return contacts

        text_query = query.casefold()

        normalized_email = (
            self._normalize_email(
                query
            )
        )

        normalized_phone = (
            self._normalize_phone(
                query
            )
        )

        results = []

        for contact in contacts:

            attributes = (
                contact.attributes
            )

            text_values = [
                contact.title,
                contact.content,
                attributes.get(
                    "given_name",
                    "",
                ),
                attributes.get(
                    "family_name",
                    "",
                ),
                attributes.get(
                    "company",
                    "",
                ),
                attributes.get(
                    "job_title",
                    "",
                ),
            ]

            text_match = any(
                text_query
                in str(value).casefold()
                for value in text_values
                if value
            )

            email_match = any(
                normalized_email
                in self._normalize_email(
                    email
                )
                for email in attributes.get(
                    "emails",
                    [],
                )
            )

            phone_match = (
                bool(
                    normalized_phone
                )
                and any(
                    normalized_phone
                    in self._normalize_phone(
                        phone
                    )
                    for phone
                    in attributes.get(
                        "phones",
                        [],
                    )
                )
            )

            if (
                text_match
                or email_match
                or phone_match
            ):

                results.append(
                    contact
                )

        return sorted(
            results,
            key=lambda contact:
            contact.title.casefold(),
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        source_id: str,
    ) -> dict[str, Any]:

        source = (
            self._require_contact_source(
                source_id
            )
        )

        contacts = self.list_contacts(
            source_id=source_id,
            active_only=False,
        )

        active_contacts = [
            contact
            for contact in contacts
            if contact.status == "active"
        ]

        return {
            "source_id": source.source_id,
            "name": source.name,
            "access_mode": (
                source.access_mode
            ),
            "status": source.status,
            "contacts": len(
                contacts
            ),
            "active_contacts": len(
                active_contacts
            ),
            "last_sync_at": (
                source.last_sync_at
            ),
        }


contacts_service = ContactsService()