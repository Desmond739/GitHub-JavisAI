import json
import uuid

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class LongTermMemory:

    memory_id: str
    memory_type: str
    category: str
    content: str
    importance: int
    created_at: str
    updated_at: str
    status: str = "active"
    superseded_by: str | None = None

    def to_dict(self) -> dict:

        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "category": self.category,
            "content": self.content,
            "importance": self.importance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "superseded_by": self.superseded_by
        }


class LongTermMemoryStore:

    VALID_MEMORY_TYPES = {
        "fact",
        "event",
        "experience",
        "preference",
        "lesson",
        "decision",
        "goal"
    }

    VALID_CATEGORIES = {
        "personal",
        "career",
        "finance",
        "trading",
        "technical",
        "moneroai"
    }

    VALID_STATUSES = {
        "active",
        "superseded",
        "archived"
    }

    def __init__(self):

        self.storage_path = (
            Path("data")
            / "memory"
            / "long_term"
            / "memories.json"
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.storage_path.exists():

            self.storage_path.write_text(
                "[]",
                encoding="utf-8"
            )

    def _load(self) -> list[dict]:

        try:

            content = self.storage_path.read_text(
                encoding="utf-8"
            )

            if not content.strip():

                return []

            data = json.loads(content)

            if not isinstance(data, list):

                return []

            return data

        except (
            json.JSONDecodeError,
            OSError
        ):

            return []

    def _save(
        self,
        memories: list[dict]
    ) -> None:

        self.storage_path.write_text(
            json.dumps(
                memories,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    def _memory_from_dict(
        self,
        memory: dict
    ) -> LongTermMemory:

        return LongTermMemory(
            memory_id=memory["memory_id"],
            memory_type=memory["memory_type"],
            category=memory["category"],
            content=memory["content"],
            importance=memory["importance"],
            created_at=memory["created_at"],
            updated_at=memory["updated_at"],
            status=memory.get(
                "status",
                "active"
            ),
            superseded_by=memory.get(
                "superseded_by"
            )
        )

    def add_memory(
        self,
        memory_type: str,
        category: str,
        content: str,
        importance: int = 5
    ) -> LongTermMemory:

        memory_type = memory_type.lower().strip()
        category = category.lower().strip()
        content = content.strip()

        if memory_type not in self.VALID_MEMORY_TYPES:

            raise ValueError(
                f"Invalid memory type: {memory_type}"
            )

        if category not in self.VALID_CATEGORIES:

            raise ValueError(
                f"Invalid memory category: {category}"
            )

        if not content:

            raise ValueError(
                "Memory content cannot be empty."
            )

        importance = max(
            1,
            min(
                10,
                int(importance)
            )
        )

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        memory = LongTermMemory(
            memory_id=str(
                uuid.uuid4()
            ),
            memory_type=memory_type,
            category=category,
            content=content,
            importance=importance,
            created_at=now,
            updated_at=now,
            status="active",
            superseded_by=None
        )

        memories = self._load()

        memories.append(
            memory.to_dict()
        )

        self._save(memories)

        return memory

    def get_all(
        self
    ) -> list[LongTermMemory]:

        return [
            self._memory_from_dict(memory)
            for memory in self._load()
        ]

    def get_active(
        self
    ) -> list[LongTermMemory]:

        return [
            memory
            for memory in self.get_all()
            if memory.status == "active"
        ]

    def get_historical(
        self
    ) -> list[LongTermMemory]:

        return [
            memory
            for memory in self.get_all()
            if memory.status in {
                "superseded",
                "archived"
            }
        ]

    def get_superseded(
        self
    ) -> list[LongTermMemory]:

        return [
            memory
            for memory in self.get_all()
            if memory.status == "superseded"
        ]

    def get_archived(
        self
    ) -> list[LongTermMemory]:

        return [
            memory
            for memory in self.get_all()
            if memory.status == "archived"
        ]

    def get_current(
        self,
        category: str | None = None,
        memory_type: str | None = None
    ) -> list[LongTermMemory]:

        memories = self.get_active()

        if category is not None:

            category = category.lower().strip()

            memories = [
                memory
                for memory in memories
                if memory.category == category
            ]

        if memory_type is not None:

            memory_type = memory_type.lower().strip()

            memories = [
                memory
                for memory in memories
                if memory.memory_type == memory_type
            ]

        return sorted(
            memories,
            key=lambda memory: (
                memory.importance,
                memory.updated_at
            ),
            reverse=True
        )

    def get_history(
        self,
        category: str | None = None,
        memory_type: str | None = None
    ) -> list[LongTermMemory]:

        memories = self.get_historical()

        if category is not None:

            category = category.lower().strip()

            memories = [
                memory
                for memory in memories
                if memory.category == category
            ]

        if memory_type is not None:

            memory_type = memory_type.lower().strip()

            memories = [
                memory
                for memory in memories
                if memory.memory_type == memory_type
            ]

        return sorted(
            memories,
            key=lambda memory: memory.updated_at,
            reverse=True
        )

    def get_by_category(
        self,
        category: str
    ) -> list[LongTermMemory]:

        category = category.lower().strip()

        return [
            memory
            for memory in self.get_active()
            if memory.category == category
        ]

    def get_by_type(
        self,
        memory_type: str
    ) -> list[LongTermMemory]:

        memory_type = memory_type.lower().strip()

        return [
            memory
            for memory in self.get_active()
            if memory.memory_type == memory_type
        ]

    def search(
        self,
        query: str
    ) -> list[LongTermMemory]:

        query_lower = query.lower().strip()

        # =========================================================
        # STOP WORDS
        # =========================================================

        stop_words = {
            "the", "a", "an",
            "is", "are", "am", "was", "were",
            "be", "been", "being",
            "to", "of", "and", "or",
            "in", "on", "for", "with",
            "my", "me", "i", "you", "your",
            "what", "whats", "what's",
            "how", "why", "when", "where",
            "should", "can", "could",
            "do", "does", "did",
            "have", "has", "had",
            "about", "regarding",
            "regard", "currently",
            "current"
        }

        query_words = {
            word.lower().strip(".,?!:;()[]{}\"'")
            for word in query.split()
        }

        query_words = {
            word
            for word in query_words
            if len(word) > 2 and word not in stop_words
        }

        if not query_words:
            return []

        # =========================================================
        # INTENT / DOMAIN DETECTION
        # =========================================================

        domain_patterns = {

            "career": [
                "career",
                "internship",
                "intern",
                "mtn",
                "job",
                "employment",
                "professional",
                "staff",
                "promotion",
                "workplace"
            ],

            "finance": [
            "finance",
            "financial",
            "money",
            "saving",
            "savings",
            "budget",
            "budgeting",
            "income",
            "expense",
            "expenses",
            "trading capital"
            ],

            "trading": [
                "trading",
                "trade",
                "forex",
                "market",
                "structure",
                "pullback",
                "support",
                "resistance",
                "support",
                "resistance",
                "prop",
                "overleveraging",
                "overtrading",
                "revenge"
            ],

            "technical": [
                "technical",
                "technology",
                "programming",
                "program",
                "python",
                "c#",
                "csharp",
                "cybersecurity",
                "networking",
                "network",
                "iot",
                "esp32",
                "arduino",
                "software",
                "coding",
                "api",
                "database",
                "moneroai"
            ],

            "personal": [
                "naya",
                "maya",
                "personal",
                "preference",
                "respond",
                "response",
                "task",
                "tasks",
                "goal",
                "goals",
                "priority",
                "priorities",
                "schedule",
                "progress",
                "plans"
            ]
        }
        # =========================================================
        # PERSONAL MEMORY INTENT CHECK
        # =========================================================

        personal_intent_patterns = [
            "my ",
            "i ",
            "i'm ",
            "i am ",
            "i want ",
            "i prefer ",
            "i decided ",
            "my current",
            "my previous",
            "my goal",
            "my goals",
            "my task",
            "my tasks",
            "my career",
            "my finance",
            "my finances",
            "my trading",
            "my strategy",
            "my technical",
            "my project",
            "my development",
            "my progress",
            "my priorities",
            "my preference",
            "naya",
            "maya"
        ]

        has_personal_intent = any(
            pattern in query_lower
            for pattern in personal_intent_patterns
        )

        if not has_personal_intent:
            return []
        
        # =========================================================
        # SCORE DOMAINS
        # =========================================================

        domain_scores = {}

        for domain, keywords in domain_patterns.items():

            score = 0

            for keyword in keywords:

                if keyword in query_lower:

                    # Exact phrase/keyword match.
                    score += 3

            domain_scores[domain] = score

        # =========================================================
        # SPECIALIZED QUESTION PATTERNS
        # =========================================================

        if (
            "naya" in query_lower
            or "maya" in query_lower
            or "respond to me" in query_lower
            or "how should naya" in query_lower
            or "how should maya" in query_lower
        ):

            domain_scores["personal"] += 20

        if (
            "financial priorities" in query_lower
            or "financial priority" in query_lower
            or "savings" in query_lower
            or "saving" in query_lower
        ):

            domain_scores["finance"] += 20

        if (
            "trading strategy" in query_lower
            or "trading system" in query_lower
            or "how do i trade" in query_lower
        ):

            domain_scores["trading"] += 20

        if (
            "career" in query_lower
            or "internship" in query_lower
            or "permanent staff" in query_lower
        ):

            domain_scores["career"] += 20

        if (
            "moneroai" in query_lower
            or "technical development" in query_lower
            or "technical skills" in query_lower
        ):

            domain_scores["technical"] += 20

        # =========================================================
        # DETERMINE PRIMARY DOMAIN
        # =========================================================

        active_domains = [
            domain
            for domain, score in domain_scores.items()
            if score > 0
        ]

        if not active_domains:
            return []

        primary_domain = max(
            active_domains,
            key=lambda domain: domain_scores[domain]
        )

        # =========================================================
        # SCORE MEMORIES
        # =========================================================

        results = []

        for memory in self.get_active():

            # Strict domain isolation.
            if memory.category != primary_domain:
                continue

            content_lower = memory.content.lower()

            content_words = {
                word.lower().strip(".,?!:;()[]{}\"'")
                for word in memory.content.split()
            }

            matching_words = query_words.intersection(
                content_words
            )

            keyword_score = len(
                matching_words
            ) * 3

            # Domain match is mandatory.
            domain_score = 10

            total_score = (
                domain_score
                + keyword_score
                + memory.importance
            )

            results.append(
                (
                    total_score,
                    memory
                )
            )

        # =========================================================
        # SORT
        # =========================================================

        results.sort(
            key=lambda item: (
                item[0],
                item[1].importance
            ),
            reverse=True
        )

        return [
            memory
            for _, memory in results
        ]

    def search_all(
        self,
        query: str
    ) -> list[LongTermMemory]:

        query_words = {
            word.lower()
            for word in query.split()
            if len(word.strip()) > 2
        }

        if not query_words:

            return []

        results = []

        for memory in self.get_all():

            searchable_text = (
                f"{memory.memory_type} "
                f"{memory.category} "
                f"{memory.content}"
            ).lower()

            score = sum(
                1
                for word in query_words
                if word in searchable_text
            )

            if score > 0:

                results.append(
                    (
                        score,
                        memory
                    )
                )

        results.sort(
            key=lambda item: (
                item[0],
                item[1].importance,
                item[1].updated_at
            ),
            reverse=True
        )

        return [
            memory
            for _, memory in results
        ]

    def get_by_id(
        self,
        memory_id: str
    ) -> LongTermMemory | None:

        for memory in self.get_all():

            if memory.memory_id == memory_id:

                return memory

        return None

    def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        importance: int | None = None,
        status: str | None = None,
        superseded_by: str | None = None
    ) -> LongTermMemory | None:

        memories = self._load()

        target = None

        for memory in memories:

            if memory["memory_id"] == memory_id:

                target = memory
                break

        if target is None:

            return None

        if content is not None:

            content = content.strip()

            if not content:

                raise ValueError(
                    "Memory content cannot be empty."
                )

            target["content"] = content

        if importance is not None:

            target["importance"] = max(
                1,
                min(
                    10,
                    int(importance)
                )
            )

        if status is not None:

            status = status.lower().strip()

            if status not in self.VALID_STATUSES:

                raise ValueError(
                    f"Invalid memory status: {status}"
                )

            target["status"] = status

        if superseded_by is not None:

            target["superseded_by"] = superseded_by

        target["updated_at"] = datetime.now().isoformat(
            timespec="seconds"
        )

        self._save(memories)

        return self._memory_from_dict(target)

    def supersede_memory(
        self,
        old_memory_id: str,
        new_memory_id: str
    ) -> LongTermMemory | None:

        if old_memory_id == new_memory_id:

            raise ValueError(
                "A memory cannot supersede itself."
            )

        new_memory = self.get_by_id(
            new_memory_id
        )

        if new_memory is None:

            raise ValueError(
                "The new memory does not exist."
            )

        old_memory = self.get_by_id(
            old_memory_id
        )

        if old_memory is None:

            return None

        if old_memory.status == "superseded":

            return old_memory

        return self.update_memory(
            memory_id=old_memory_id,
            status="superseded",
            superseded_by=new_memory_id
        )

    def archive_memory(
        self,
        memory_id: str
    ) -> LongTermMemory | None:

        return self.update_memory(
            memory_id=memory_id,
            status="archived"
        )

    def delete_memory(
        self,
        memory_id: str
    ) -> bool:

        memories = self._load()

        filtered = [
            memory
            for memory in memories
            if memory["memory_id"] != memory_id
        ]

        if len(filtered) == len(memories):

            return False

        self._save(filtered)

        return True


long_term_memory = LongTermMemoryStore()
