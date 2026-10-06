from __future__ import annotations

import re

from app.personal_data.notes_service import (
    NotesService,
    notes_service,
)

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
)


class NotesQueryEngine:

    def __init__(
        self,
        service: NotesService | None = None,
    ) -> None:

        self.service = (
            service
            if service is not None
            else notes_service
        )

    # ============================================================
    # SOURCE
    # ============================================================

    def has_active_source(
        self,
    ) -> bool:

        sources = (
            self.service.manager
            .list_sources()
        )

        return any(
            source.source_type == "note"
            and source.status == "active"
            for source in sources
        )

    # ============================================================
    # INTENT
    # ============================================================

    def can_answer(
        self,
        request: str,
    ) -> bool:

        if (
            not request
            or not request.strip()
        ):

            return False

        normalized = (
            request.strip()
            .casefold()
        )

        # --------------------------------------------------------
        # WRITE COMMANDS
        #
        # These deliberately bypass the read-only Notes engine.
        # --------------------------------------------------------

        write_prefixes = (
            "remember that ",
            "remember this ",
            "save a note ",
            "save note ",
            "create a note ",
            "create note ",
            "add a note ",
            "add note ",
            "write a note ",
            "write down ",
            "note that ",
        )

        if normalized.startswith(
            write_prefixes
        ):

            return False

        direct_patterns = (
            "what notes do i have",
            "what note do i have",
            "show my notes",
            "show me my notes",
            "list my notes",
            "my notes",
            "find my note",
            "find my notes",
            "search my notes",
            "search my note",
            "what did i write about",
            "what have i written about",
            "what did i note about",
            "pinned notes",
            "pinned note",
        )

        if any(
            pattern in normalized
            for pattern in direct_patterns
        ):

            return True

        if (
            "note" in normalized
            and any(
                word in normalized
                for word in (
                    "show",
                    "find",
                    "search",
                    "about",
                    "pinned",
                    "project",
                    "have",
                )
            )
        ):

            return True

        return False

    # ============================================================
    # SEARCH QUERY EXTRACTION
    # ============================================================

    @staticmethod
    def _clean_query(
        value: str,
    ) -> str:

        return (
            value.strip()
            .strip(
                " \t\r\n"
                "?.!,;:\"'"
            )
        )

    def _extract_search_query(
        self,
        request: str,
    ) -> str:

        text = request.strip()

        # --------------------------------------------------------
        # "... about MoneroAI"
        # --------------------------------------------------------

        about_match = re.search(
            r"\babout\s+(.+?)\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )

        if about_match:

            return self._clean_query(
                about_match.group(1)
            )

        # --------------------------------------------------------
        # "Find my note on cybersecurity"
        # --------------------------------------------------------

        find_match = re.search(
            r"\b(?:find|search)"
            r"\s+(?:for\s+)?"
            r"(?:my\s+)?"
            r"notes?"
            r"(?:\s+(?:about|on|for))?"
            r"\s+(.+?)\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )

        if find_match:

            return self._clean_query(
                find_match.group(1)
            )

        # --------------------------------------------------------
        # "Show my project notes"
        # --------------------------------------------------------

        show_match = re.search(
            r"\bshow\s+"
            r"(?:me\s+)?"
            r"my\s+"
            r"(.+?)\s+"
            r"notes?\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )

        if show_match:

            candidate = (
                self._clean_query(
                    show_match.group(1)
                )
            )

            if candidate.casefold() not in {
                "all",
                "pinned",
            }:

                return candidate

        # --------------------------------------------------------
        # "Notes in Projects"
        # --------------------------------------------------------

        notebook_match = re.search(
            r"\bnotes?\s+in\s+"
            r"(.+?)\s*[?.!]*$",
            text,
            flags=re.IGNORECASE,
        )

        if notebook_match:

            return self._clean_query(
                notebook_match.group(1)
            )

        return ""

    # ============================================================
    # FORMATTING
    # ============================================================

    @staticmethod
    def _content_preview(
        content: str,
        limit: int = 220,
    ) -> str:

        cleaned = " ".join(
            str(
                content
            ).split()
        )

        if len(cleaned) <= limit:

            return cleaned

        return (
            cleaned[
                : limit - 3
            ].rstrip()
            + "..."
        )

    def _format_note(
        self,
        note: PersonalDataRecord,
    ) -> str:

        parts = [
            note.title
        ]

        preview = (
            self._content_preview(
                note.content
            )
        )

        if preview:

            parts.append(
                preview
            )

        notebook = (
            note.attributes.get(
                "notebook",
                "",
            )
        )

        if notebook:

            parts.append(
                f"notebook: {notebook}"
            )

        if bool(
            note.attributes.get(
                "pinned",
                False,
            )
        ):

            parts.append(
                "pinned"
            )

        return " — ".join(
            parts
        )

    def _format_results(
        self,
        records:
        list[PersonalDataRecord],
    ) -> str:

        return "; ".join(
            self._format_note(
                note
            )
            for note in records
        )

    # ============================================================
    # ANSWER
    # ============================================================

    def answer(
        self,
        request: str,
    ) -> str | None:

        if not self.can_answer(
            request
        ):

            return None

        if not self.has_active_source():

            return (
                "You do not have an active "
                "notes source yet."
            )

        normalized = (
            request.strip()
            .casefold()
        )

        # --------------------------------------------------------
        # PINNED NOTES
        # --------------------------------------------------------

        if "pinned" in normalized:

            records = (
                self.service
                .pinned_notes()
            )

            if not records:

                return (
                    "You have no pinned notes."
                )

            return (
                f"You have {len(records)} "
                f"pinned note"
                f"{'' if len(records) == 1 else 's'}: "
                + self._format_results(
                    records
                )
                + "."
            )

        # --------------------------------------------------------
        # SEARCH
        # --------------------------------------------------------

        search_query = (
            self._extract_search_query(
                request
            )
        )

        if search_query:

            records = (
                self.service
                .search_notes(
                    search_query
                )
            )

            if not records:

                return (
                    "I found no notes matching "
                    f"'{search_query}'."
                )

            return (
                f"I found {len(records)} "
                f"note"
                f"{'' if len(records) == 1 else 's'} "
                f"matching '{search_query}': "
                + self._format_results(
                    records
                )
                + "."
            )

        # --------------------------------------------------------
        # ALL NOTES
        # --------------------------------------------------------

        records = (
            self.service
            .list_notes(
                active_only=True
            )
        )

        if not records:

            return (
                "You have no active notes."
            )

        return (
            f"You have {len(records)} "
            f"active note"
            f"{'' if len(records) == 1 else 's'}: "
            + self._format_results(
                records
            )
            + "."
        )


notes_query_engine = (
    NotesQueryEngine()
)