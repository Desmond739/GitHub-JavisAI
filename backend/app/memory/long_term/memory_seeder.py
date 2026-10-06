from app.memory.long_term.memory_manager import memory_manager


class PersonalMemorySeeder:

    def __init__(self):

        self.memories = [

            # ====================================================
            # CAREER
            # ====================================================

            {
                "memory_type": "goal",
                "category": "career",
                "content": (
                    "The user wants to become permanent staff at MTN Cameroon "
                    "after completing the internship."
                ),
                "importance": 10
            },

            {
                "memory_type": "fact",
                "category": "career",
                "content": (
                    "The user is currently a Product & Service Intern "
                    "in the Marketing Department at MTN Cameroon."
                ),
                "importance": 9
            },

            {
                "memory_type": "goal",
                "category": "career",
                "content": (
                    "The user wants to develop strong competence in "
                    "Product Management, Project Management, cybersecurity, "
                    "AI, networking, and business leadership."
                ),
                "importance": 9
            },

            {
                "memory_type": "goal",
                "category": "career",
                "content": (
                    "The user wants to create measurable professional value "
                    "during the MTN internship."
                ),
                "importance": 9
            },

            # ====================================================
            # TECHNICAL
            # ====================================================

            {
                "memory_type": "goal",
                "category": "technical",
                "content": (
                    "The user wants to become highly competent in "
                    "cybersecurity and networking."
                ),
                "importance": 9
            },

            {
                "memory_type": "goal",
                "category": "technical",
                "content": (
                    "The user wants to build MoneroAI into a reliable "
                    "personal AI assistant."
                ),
                "importance": 10
            },

            {
                "memory_type": "decision",
                "category": "technical",
                "content": (
                    "The user has decided to prioritize practical technical "
                    "implementation, troubleshooting, system design, and "
                    "building real projects."
                ),
                "importance": 8
            },

            {
                "memory_type": "goal",
                "category": "technical",
                "content": (
                    "The user wants to learn C# from beginner through "
                    "professional level and use it to build practical "
                    "applications such as an IoT dashboard and network "
                    "monitoring tools."
                ),
                "importance": 8
            },

            # ====================================================
            # TRADING
            # ====================================================

            {
                "memory_type": "decision",
                "category": "trading",
                "content": (
                    "The user's active trading strategy is Support and "
                    "Resistance only, without Order Blocks."
                ),
                "importance": 9
            },

            {
                "memory_type": "preference",
                "category": "trading",
                "content": (
                    "The user prefers day trading and swing trading and "
                    "does not want scalping."
                ),
                "importance": 8
            },

            {
                "memory_type": "preference",
                "category": "trading",
                "content": (
                    "The user prefers market analysis using Weekly, Daily, "
                    "4H, 1H, and 30M timeframes, with 1H and 30M preferred "
                    "for entries."
                ),
                "importance": 8
            },

            {
                "memory_type": "lesson",
                "category": "trading",
                "content": (
                    "The user's previous prop-firm experience taught the "
                    "importance of avoiding overleveraging and prioritizing "
                    "capital preservation, patience, and disciplined execution."
                ),
                "importance": 10
            },

            {
                "memory_type": "decision",
                "category": "trading",
                "content": (
                    "The user wants to become calm, patient, disciplined, "
                    "and consistent in trading while avoiding impulsive "
                    "entries, overtrading, revenge trading, and overleveraging."
                ),
                "importance": 9
            },

            # ====================================================
            # FINANCE
            # ====================================================

            {
                "memory_type": "goal",
                "category": "finance",
                "content": (
                    "The user wants to build strong financial discipline "
                    "and consistently save money."
                ),
                "importance": 9
            },

            {
                "memory_type": "decision",
                "category": "finance",
                "content": (
                    "The user has decided that personal savings and trading "
                    "capital must remain separate."
                ),
                "importance": 9
            },

            {
                "memory_type": "decision",
                "category": "finance",
                "content": (
                    "The user has decided that money required for essential "
                    "living expenses should never be exposed to unnecessary "
                    "trading risk."
                ),
                "importance": 10
            },

            # ====================================================
            # PERSONAL
            # ====================================================

            {
                "memory_type": "preference",
                "category": "personal",
                "content": (
                    "The user prefers Naya to respond concisely unless "
                    "the user specifically asks for an explanation."
                ),
                "importance": 9
            },

            {
                "memory_type": "goal",
                "category": "personal",
                "content": (
                    "The user wants to build a personal AI assistant that "
                    "can understand and assist with their personal life, "
                    "work, projects, goals, and long-term development."
                ),
                "importance": 10
            },

            # ====================================================
            # MONEROAI CURRENT STATE
            #
            # IMPORTANT:
            # "current_state" is NOT a supported memory type.
            # We therefore store this as a "fact".
            # ====================================================

            {
                "memory_type": "fact",
                "category": "technical",
                "content": (
                    "MoneroAI already has a Python backend, AI service, "
                    "Naya assistant core, exact Hey Naya wake-phrase "
                    "detection, female voice service, Ollama local AI "
                    "inference, read-only Google integration, automation, "
                    "specialized agents, long-term memory, and a knowledge graph."
                ),
                "importance": 9
            },

            {
                "memory_type": "fact",
                "category": "technical",
                "content": (
                    "The current MoneroAI development focus is production "
                    "hardening and non-voice validation. Voice tuning and "
                    "Google authorization are deliberately deferred until "
                    "the user approves the final validation stage."
                ),
                "importance": 10
            }
        ]

    # ============================================================
    # EXACT DUPLICATE CHECK
    # ============================================================

    def _exists(
        self,
        memory_type: str,
        category: str,
        content: str
    ) -> bool:

        existing_memories = memory_manager.get_all()

        for memory in existing_memories:

            if (
                memory.memory_type == memory_type
                and memory.category == category
                and memory.content == content
            ):
                return True

        return False

    # ============================================================
    # SEED
    # ============================================================

    def seed(self) -> dict:

        added = []
        skipped = []

        for memory in self.memories:

            if self._exists(
                memory["memory_type"],
                memory["category"],
                memory["content"]
            ):

                skipped.append(memory)

                continue

            stored_memory = memory_manager.remember(
                memory_type=memory["memory_type"],
                category=memory["category"],
                content=memory["content"],
                importance=memory["importance"]
            )

            added.append(stored_memory)

        return {
            "added": added,
            "skipped": skipped,
            "added_count": len(added),
            "skipped_count": len(skipped),
            "total_memories": len(
                memory_manager.get_all()
            )
        }


personal_memory_seeder = PersonalMemorySeeder()
