from __future__ import annotations

import re

from app.personal_data.contacts_service import (
    ContactsService,
    contacts_service,
)
from app.personal_data.personal_data_model import (
    PersonalDataRecord,
)


class ContactsQueryEngine:

    def __init__(
        self,
        service: ContactsService | None = None,
    ) -> None:

        self.service = (
            service
            if service is not None
            else contacts_service
        )

    def has_active_source(self) -> bool:

        return any(
            source.source_type == "contact"
            and source.status == "active"
            for source in self.service.manager.list_sources()
        )

    def can_answer(self, request: str) -> bool:

        normalized = " ".join(
            str(request).casefold().split()
        )

        if not normalized:
            return False

        write_prefixes = (
            "add a contact",
            "create a contact",
            "delete contact",
            "update contact",
            "change contact",
        )

        if normalized.startswith(write_prefixes):
            return False

        contact_word = bool(
            re.search(
                r"\bcontacts?\b",
                normalized,
            )
        )

        if contact_word and any(
            signal in normalized
            for signal in (
                "my contact",
                "find",
                "search",
                "look up",
                "do i have",
                "show",
                "list",
                "how many",
                "number of contacts",
                "phone",
                "email",
            )
        ):
            return True

        detail_request = (
            "phone number" in normalized
            or "email address" in normalized
        )

        return detail_request and any(
            signal in normalized
            for signal in (
                " for ",
                " of ",
                "'s ",
                "’s ",
            )
        )

    @staticmethod
    def _extract_query(request: str) -> str:

        text = request.strip().strip("?.!,;: ")

        patterns = (
            r"\b(?:phone number|email address)\s+(?:for|of)\s+(.+)$",
            r"\b(?:contact|contacts)\s+(?:for|named)\s+(.+)$",
            r"\b(?:find|search for|look up)\s+(?:my\s+)?contact\s+(.+)$",
            r"\bdo i have\s+(?:a\s+)?contact\s+for\s+(.+)$",
            r"\bwhat is\s+(.+?)(?:'s|’s)\s+(?:phone number|email address)$",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip("?.!,;: \"'")

        return ""

    @staticmethod
    def _format_contact(
        contact: PersonalDataRecord,
        *,
        emails_only: bool,
        phones_only: bool,
    ) -> str:

        attributes = contact.attributes
        emails = attributes.get("emails", [])
        phones = attributes.get("phones", [])
        details = []

        if not phones_only and emails:
            details.append(f"email {emails[0]}")

        if not emails_only and phones:
            details.append(f"phone {phones[0]}")

        if not details:
            details.append("no matching detail is stored")

        return f"{contact.title}: " + ", ".join(details)

    def answer(self, request: str) -> str | None:

        if not self.can_answer(request):
            return None

        if not self.has_active_source():
            return "Your contacts are not currently connected."

        normalized = request.casefold()

        if (
            "how many contacts" in normalized
            or "number of contacts" in normalized
        ):

            count = len(self.service.list_contacts())

            return (
                f"You have {count} active contact"
                f"{'' if count == 1 else 's'}."
            )

        query = self._extract_query(request)

        if not query:
            return (
                "Please name the person whose contact information "
                "you want me to find."
            )

        contacts = self.service.search_contacts(query)[:5]

        if not contacts:
            return f"I could not find a contact matching {query}."

        emails_only = "email" in normalized
        phones_only = (
            "phone" in normalized
            or "number" in normalized
        )

        formatted = [
            self._format_contact(
                contact,
                emails_only=emails_only,
                phones_only=phones_only,
            )
            for contact in contacts
        ]

        return "I found " + "; ".join(formatted) + "."


contacts_query_engine = ContactsQueryEngine()
