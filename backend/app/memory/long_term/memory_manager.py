from app.memory.long_term.long_term_memory import (
    long_term_memory
)


class MemoryManager:

    CONFLICT_MARKERS = (
        "instead of",
        "no longer",
        "stopped",
        "stop",
        "changed from",
        "changed to",
        "changed my",
        "change from",
        "change to",
        "changed my mind",
        "i have decided to focus on",
        "i decided to focus on",
        "i have decided to",
        "i decided to",
        "i will focus on",
        "i'm focusing on",
        "i am focusing on",
        "i now focus on",
        "i now want to focus on",
        "i no longer want",
        "i don't want to",
        "i do not want to"
    )

    CONFLICT_MEMORY_TYPES = {
        "preference",
        "decision",
        "goal"
    }

    def remember(
        self,
        memory_type: str,
        category: str,
        content: str,
        importance: int = 5
    ):

        return long_term_memory.add_memory(
            memory_type=memory_type,
            category=category,
            content=content,
            importance=importance
        )

    def recall(
        self,
        query: str
    ):

        return long_term_memory.search(
            query
        )

    def get_category(
        self,
        category: str
    ):

        return long_term_memory.get_by_category(
            category
        )

    def get_type(
        self,
        memory_type: str
    ):

        return long_term_memory.get_by_type(
            memory_type
        )

    def get_all(self):

        return long_term_memory.get_all()

    def get_active(self):

        return long_term_memory.get_active()

    def get_by_id(
        self,
        memory_id: str
    ):

        return long_term_memory.get_by_id(
            memory_id
        )

    def update(
        self,
        memory_id: str,
        content: str | None = None,
        importance: int | None = None,
        status: str | None = None,
        superseded_by: str | None = None
    ):

        return long_term_memory.update_memory(
            memory_id=memory_id,
            content=content,
            importance=importance,
            status=status,
            superseded_by=superseded_by
        )

    def supersede(
        self,
        old_memory_id: str,
        new_memory_id: str
    ):

        return long_term_memory.supersede_memory(
            old_memory_id=old_memory_id,
            new_memory_id=new_memory_id
        )

    def archive(
        self,
        memory_id: str
    ):

        return long_term_memory.archive_memory(
            memory_id
        )

    def forget(
        self,
        memory_id: str
    ):

        return long_term_memory.delete_memory(
            memory_id
        )

    def _normalize(
        self,
        text: str
    ) -> str:

        return (
            text
            .lower()
            .strip()
        )

    def _has_conflict_marker(
        self,
        content: str
    ) -> bool:

        normalized = self._normalize(
            content
        )

        return any(
            marker in normalized
            for marker in self.CONFLICT_MARKERS
        )

    def _extract_conflict_targets(
        self,
        content: str
    ) -> list[str]:

        normalized = self._normalize(
            content
        )

        targets = []

        marker_patterns = (
            "instead of",
            "no longer",
            "stopped",
            "stop",
            "changed from",
            "i no longer want"
        )

        for marker in marker_patterns:

            if marker not in normalized:

                continue

            parts = normalized.split(
                marker,
                1
            )

            if len(parts) != 2:

                continue

            target = parts[1].strip()

            if target:

                targets.append(
                    target
                )

        return targets

    def _meaningful_words(
        self,
        text: str
    ) -> set[str]:

        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "of",
            "for",
            "on",
            "in",
            "with",
            "my",
            "i",
            "have",
            "has",
            "had",
            "user",
            "want",
            "wants",
            "decided",
            "decide",
            "focus",
            "focusing",
            "instead",
            "than",
            "this",
            "that",
            "is",
            "am",
            "are",
            "be",
            "will"
        }

        words = set()

        for word in (
            self._normalize(text)
            .replace(",", " ")
            .replace(".", " ")
            .replace("(", " ")
            .replace(")", " ")
            .replace(":", " ")
            .replace(";", " ")
            .replace("-", " ")
            .split()
        ):

            if (
                len(word) >= 3
                and word not in stop_words
            ):

                words.add(word)

        return words

    def _is_conflicting_memory(
        self,
        new_content: str,
        old_content: str
    ) -> bool:

        new_normalized = self._normalize(
            new_content
        )

        old_normalized = self._normalize(
            old_content
        )

        # Explicit target detection.
        targets = self._extract_conflict_targets(
            new_content
        )

        for target in targets:

            target_words = self._meaningful_words(
                target
            )

            old_words = self._meaningful_words(
                old_content
            )

            if (
                target_words
                and target_words.issubset(old_words)
            ):

                return True

            if target in old_normalized:

                return True

        # Explicit "changed to / focus on" detection.
        if (
            "changed to" in new_normalized
            or "change to" in new_normalized
            or "i decided to focus on" in new_normalized
            or "i have decided to focus on" in new_normalized
            or "i will focus on" in new_normalized
            or "i am focusing on" in new_normalized
            or "i'm focusing on" in new_normalized
        ):

            new_words = self._meaningful_words(
                new_content
            )

            old_words = self._meaningful_words(
                old_content
            )

            overlap = (
                new_words
                & old_words
            )

            if len(overlap) >= 1:

                return True

        return False

    def _find_conflicting_memory(
        self,
        memory_type: str,
        category: str,
        content: str
    ):

        if (
            memory_type
            not in self.CONFLICT_MEMORY_TYPES
        ):

            return None

        if not self._has_conflict_marker(
            content
        ):

            return None

        active_memories = (
            long_term_memory.get_active()
        )

        for memory in active_memories:

            if (
                memory.category != category
            ):

                continue

            if (
                memory.memory_type
                not in self.CONFLICT_MEMORY_TYPES
            ):

                continue

            if self._is_conflicting_memory(
                content,
                memory.content
            ):

                return memory

        return None

    def remember_intelligently(
        self,
        memory_type: str,
        category: str,
        content: str,
        importance: int = 5
    ):

        memory_type = (
            memory_type
            .lower()
            .strip()
        )

        category = (
            category
            .lower()
            .strip()
        )

        content = content.strip()

        if not content:

            raise ValueError(
                "Memory content cannot be empty."
            )

        existing_memories = (
            long_term_memory.get_active()
        )

        normalized_content = (
            content
            .lower()
            .strip()
        )

        # =====================================================
        # 1. EXACT DUPLICATE → REINFORCE
        # =====================================================

        for existing in existing_memories:

            if (
                existing.memory_type
                == memory_type
                and existing.category
                == category
                and existing.content
                .lower()
                .strip()
                == normalized_content
            ):

                updated = (
                    long_term_memory.update_memory(
                        memory_id=existing.memory_id,
                        importance=max(
                            existing.importance,
                            int(importance)
                        )
                    )
                )

                return {
                    "action": "reinforced",
                    "memory": updated,
                    "superseded_memory": None
                }

        # =====================================================
        # 2. CREATE NEW MEMORY
        # =====================================================

        created = (
            long_term_memory.add_memory(
                memory_type=memory_type,
                category=category,
                content=content,
                importance=importance
            )
        )

        # =====================================================
        # 3. LOOK FOR EXPLICIT CONFLICT
        # =====================================================

        conflicting_memory = (
            self._find_conflicting_memory(
                memory_type=memory_type,
                category=category,
                content=content
            )
        )

        if conflicting_memory is None:

            return {
                "action": "created",
                "memory": created,
                "superseded_memory": None
            }

        # =====================================================
        # 4. SUPERSEDE OLD MEMORY
        # =====================================================

        superseded = (
            long_term_memory.supersede_memory(
                old_memory_id=(
                    conflicting_memory.memory_id
                ),
                new_memory_id=(
                    created.memory_id
                )
            )
        )

        return {
            "action": "superseded",
            "memory": created,
            "superseded_memory": superseded
        }


memory_manager = MemoryManager()