from app.memory.long_term.memory_manager import memory_manager


class MemoryContext:

    def __init__(self):

        self.max_memories = 5
        self.max_historical_memories = 5

    def _format_memory(self, memory) -> str:

        return (
            f"- [{memory.memory_type}] "
            f"[{memory.category}] "
            f"[{memory.status}] "
            f"{memory.content}"
        )

    def build(self, query: str) -> str:

        if not query or not query.strip():

            return ""

        query_lower = query.lower().strip()

        # =========================================================
        # CURRENT / ACTIVE MEMORY
        # =========================================================

        current_results = memory_manager.recall(
            query
        )

        # =========================================================
        # HISTORICAL MEMORY
        # =========================================================

        historical_results = []

        historical_keywords = [
            "previous",
            "previously",
            "before",
            "used to",
            "formerly",
            "past",
            "historical",
            "history",
            "changed",
            "change",
            "what did i",
            "what was i",
            "what were my"
        ]

        wants_history = any(
            keyword in query_lower
            for keyword in historical_keywords
        )

        if wants_history:

            historical_results = (
                memory_manager.search_history(
                    query
                )
            )

        # =========================================================
        # CURRENT-STATE QUESTIONS
        # =========================================================

        current_keywords = [
            "current",
            "currently",
            "now",
            "today",
            "present",
            "what am i",
            "what is my",
            "what are my"
        ]

        wants_current = any(
            keyword in query_lower
            for keyword in current_keywords
        )

        # =========================================================
        # REMOVE DUPLICATES
        # =========================================================

        current_ids = {
            memory.memory_id
            for memory in current_results
        }

        historical_results = [
            memory
            for memory in historical_results
            if memory.memory_id not in current_ids
        ]

        # =========================================================
        # LIMIT RESULTS
        # =========================================================

        current_results = current_results[
            :self.max_memories
        ]

        historical_results = historical_results[
            :self.max_historical_memories
        ]

        # =========================================================
        # BUILD CONTEXT
        # =========================================================

        sections = []

        if current_results:

            sections.append(
                "CURRENT LONG-TERM MEMORY:\n"
                + "\n".join(
                    self._format_memory(memory)
                    for memory in current_results
                )
            )

        if historical_results:

            sections.append(
                "HISTORICAL LONG-TERM MEMORY:\n"
                + "\n".join(
                    self._format_memory(memory)
                    for memory in historical_results
                )
            )

        if not sections:

            return ""

        return "\n\n".join(sections)


memory_context = MemoryContext()