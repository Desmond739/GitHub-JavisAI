from app.agents.career_agent import career_agent
from app.agents.finance_agent import finance_agent
from app.agents.trading_agent import trading_agent
from app.agents.technical_agent import technical_agent
from app.agents.personal_agent import personal_agent
from app.agents.cross_agent_coordinator import (
    cross_agent_coordinator,
)
from app.agents.general_agent import general_agent

from app.memory.long_term.memory_context import (
    memory_context,
)

from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
    personal_knowledge_sync,
)

from app.knowledge_graph.graph_reasoner import (
    GraphReasoner,
    graph_reasoner,
)


from app.personal_data.calendar_query_engine import (
    calendar_query_engine,
)

from app.personal_data.task_query_engine import (
    task_query_engine,
)

from app.personal_data.notes_query_engine import (
    notes_query_engine,
)

from app.personal_data.contacts_query_engine import (
    contacts_query_engine,
)

class AgentCoordinator:

    def __init__(
        self,
        knowledge_sync_instance:
        PersonalKnowledgeSynchronizer | None = None,
        graph_reasoner_instance:
        GraphReasoner | None = None,
    ):

        self.agents = [
            career_agent,
            finance_agent,
            trading_agent,
            technical_agent,
            personal_agent,
        ]

        self.cross_agent_coordinator = (
            cross_agent_coordinator
        )

        self.general_agent = (
            general_agent
        )

        self.knowledge_sync = (
            knowledge_sync_instance
            if knowledge_sync_instance is not None
            else personal_knowledge_sync
        )

        self.graph_reasoner = (
            graph_reasoner_instance
            if graph_reasoner_instance is not None
            else graph_reasoner
        )

    # ============================================================
    # AGENT LIST
    # ============================================================

    def list_agents(
        self,
    ) -> list[str]:

        return [
            agent.name
            for agent in self.agents
        ]

    # ============================================================
    # READ-ONLY PERSONAL DATA GUARD
    # ============================================================

    @staticmethod
    def _is_personal_data_write_request(
        request: str,
    ) -> bool:

        normalized = " ".join(
            request.casefold().split()
        )

        polite_prefixes = (
            "please ",
            "naya ",
            "can you ",
            "could you ",
            "would you ",
            "i want you to ",
        )

        prefix_removed = True

        while prefix_removed:

            prefix_removed = False

            for prefix in polite_prefixes:

                if normalized.startswith(prefix):
                    normalized = normalized[len(prefix):]
                    prefix_removed = True
                    break

        write_patterns = (
            "add a contact",
            "add contact",
            "create a contact",
            "create contact",
            "update contact",
            "change contact",
            "delete contact",
            "schedule a meeting",
            "schedule meeting",
            "create an event",
            "create event",
            "add an event",
            "add event",
            "cancel my meeting",
            "delete event",
            "remind me to",
            "create a task",
            "create task",
            "add a task",
            "add task",
            "complete task",
            "delete task",
            "update task",
            "save a note",
            "create a note",
            "add a note",
            "write a note",
        )

        return normalized.startswith(
            write_patterns
        )

    # ============================================================
    # PERSONAL INTENT
    # ============================================================

    def _is_personal_intent(
        self,
        request: str,
    ) -> bool:

        request_lower = (
            request.lower().strip()
        )

        personal_patterns = [

            "how should naya respond",
            "how should naya answer",
            "how should naya talk",
            "how do i want naya",
            "what does naya know about me",

            # Historical name aliases retained for existing memory.
            "how should maya respond",
            "how should maya answer",
            "how should maya talk",
            "how do i want maya",
            "what does maya know about me",

            "what are my current tasks",
            "what are my tasks",
            "what are my current goals",
            "what are my goals",
            "what are my priorities",
            "what is my current task",
            "what is my current goal",
            "what is my current moneroai task",
            "what are my plans",
            "what is my progress",

            "my schedule",
            "my reminders",
            "my notes",
            "my daily tasks",
            "my weekly goals",

        ]

        return any(
            pattern in request_lower
            for pattern in personal_patterns
        )

    # ============================================================
    # FINANCE INTENT
    # ============================================================

    def _is_finance_specific(
        self,
        request: str,
    ) -> bool:

        request_lower = request.lower()

        if (
            "personal savings"
            in request_lower
            and "trading capital"
            in request_lower
        ):

            return True

        if (
            "savings"
            in request_lower
            and "trading capital"
            in request_lower
        ):

            return True

        finance_patterns = [

            "financial objective",
            "financial goal",
            "financial discipline",
            "financial situation",
            "my finances",
            "manage my finances",
            "manage my money",
            "money management",
            "budget",
            "budgeting",
            "saving money",
            "my savings",
            "my expenses",
            "my income",
            "essential living expenses",
            "financial planning",
            "financial plan",

        ]

        return any(
            pattern in request_lower
            for pattern in finance_patterns
        )

    # ============================================================
    # TRADING INTENT
    # ============================================================

    def _is_trading_specific(
        self,
        request: str,
    ) -> bool:

        request_lower = request.lower()

        trading_patterns = [

            "trading strategy",
            "trading concepts",
            "trading risk",
            "trading rules",
            "trading journal",
            "forex",
            "forex trading",
            "market structure",
            "market structure pullback",
            "pullback",
            "support and resistance",
            "prop-firm",
            "prop firm",
            "prop-firm experience",
            "overleveraging",
            "overleveraged",
            "trading psychology",
            "trading timeframes",
            "trade entry",
            "trade entries",
            "trading setup",
            "trading setups",

        ]

        return any(
            pattern in request_lower
            for pattern in trading_patterns
        )

    # ============================================================
    # TECHNICAL INTENT
    # ============================================================

    def _is_technical_specific(
        self,
        request: str,
    ) -> bool:

        request_lower = request.lower()

        technical_patterns = [

            "iot project",
            "iot-based smart home",
            "smart home automation",
            "esp32",
            "blynk",
            "arduino",
            "dht11",
            "dht22",
            "relay module",
            "temperature sensor",
            "humidity sensor",

            "technical components",
            "technical background",
            "technical education",
            "technical skills",

            "what am i learning with c#",
            "what am i currently trying to learn with c#",
            "what am i learning in c#",
            "c# learning",
            "csharp learning",

            "cybersecurity",
            "cyber security",
            "networking",
            "computer network",
            "network security",

            "moneroai",
            "moneroai technical",
            "technical components for moneroai",
            (
                "technical components have i already "
                "built for moneroai"
            ),

        ]

        return any(
            pattern in request_lower
            for pattern in technical_patterns
        )

    # ============================================================
    # CAREER INTENT
    # ============================================================

    def _is_career_specific(
        self,
        request: str,
    ) -> bool:

        request_lower = request.lower()

        career_patterns = [

            "career",
            "career development",
            "professional development",
            "professional growth",

            "internship",
            "intern",
            "permanent staff",
            "become permanent",
            "permanent employment",

            "mtn career",
            "mtn internship",
            "mtn cameroon",

            "job",
            "employment",
            "promotion",
            "workplace",

            "product management",
            "product lifecycle",
            "project management",
            "scrum",
            "pspo",
            "pmp",

            "e-marketing",
            "customer engagement",

        ]

        return any(
            pattern in request_lower
            for pattern in career_patterns
        )

    # ============================================================
    # CROSS-AGENT INTENT
    # ============================================================

    def _is_cross_agent_request(
        self,
        request: str,
    ) -> bool:

        request_lower = request.lower()

        domains = (
            self.cross_agent_coordinator
            .identify_domains(
                request
            )
        )

        if len(domains) < 2:

            return False

        cross_patterns = [

            "considering",
            "what should i prioritize",
            "what should i focus on",
            "how should i balance",
            "how can i balance",
            "overall",
            "across",
            "all of",
            "taking into account",
            "taking everything into account",
            "from all perspectives",
            "combined",
            "combining",
            "multiple areas",

        ]

        return any(
            pattern in request_lower
            for pattern in cross_patterns
        )

    # ============================================================
    # GENERAL REQUEST
    # ============================================================

    def is_general_request(
        self,
        request: str,
    ) -> bool:

        request_lower = (
            request.lower().strip()
        )

        personal_signals = [

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
            "maya",

        ]

        if any(
            signal in request_lower
            for signal in personal_signals
        ):

            return False

        if (
            self._is_personal_intent(request)
            or self._is_finance_specific(request)
            or self._is_trading_specific(request)
            or self._is_technical_specific(request)
            or self._is_career_specific(request)
        ):

            return False

        return True

    # ============================================================
    # FIND AGENT
    # ============================================================

    def find_agent(
        self,
        request: str,
    ):

        if (
            not request
            or not request.strip()
        ):

            return None

        if self._is_cross_agent_request(
            request
        ):

            return (
                self.cross_agent_coordinator
            )

        if self._is_personal_intent(
            request
        ):

            return personal_agent

        if self._is_technical_specific(
            request
        ):

            return technical_agent

        if self._is_finance_specific(
            request
        ):

            return finance_agent

        if self._is_trading_specific(
            request
        ):

            return trading_agent

        if self._is_career_specific(
            request
        ):

            return career_agent

        for agent in self.agents:

            if agent.can_handle(
                request
            ):

                return agent

        return None

    # ============================================================
    # ROUTE
    # ============================================================

    def route(
        self,
        request: str,
    ) -> str:

        if (
            not request
            or not request.strip()
        ):

            return "GENERAL_AGENT"

        if self._is_personal_data_write_request(
            request
        ):

            return "READ_ONLY_PERSONAL_DATA_GUARD"

        # --------------------------------------------------------
        # CONTACTS QUERY ROUTING
        # --------------------------------------------------------

        if contacts_query_engine.can_answer(
            request
        ):

            return "CONTACTS_QUERY_ENGINE"

        # --------------------------------------------------------
        # CALENDAR QUERY ROUTING
        # --------------------------------------------------------

        if calendar_query_engine.can_answer(
            request
        ):

            return "CALENDAR_QUERY_ENGINE"

        # --------------------------------------------------------
        # TASK / REMINDER QUERY ROUTING
        # --------------------------------------------------------

        if task_query_engine.can_answer(
            request
        ):

            return "TASK_QUERY_ENGINE"

        # --------------------------------------------------------
        # NOTES QUERY ROUTING
        # --------------------------------------------------------

        if notes_query_engine.can_answer(
            request
        ):

            return "NOTES_QUERY_ENGINE"

        if self._is_cross_agent_request(
            request
        ):

            return (
                "Cross-Agent Coordinator"
            )

        if self.is_general_request(
            request
        ):

            return "GENERAL_AGENT"

        agent = self.find_agent(
            request
        )

        if agent is None:

            return "GENERAL_AGENT"

        return agent.name

    # ============================================================
    # MEMORY CONTEXT
    # ============================================================

    def _build_enriched_request(
        self,
        request: str,
    ) -> str:

        memory = memory_context.build(
            request
        )

        if not memory:

            return request

        return (
            f"{request}\n\n"
            f"{memory}"
        )

    # ============================================================
    # PERSONAL KNOWLEDGE SYNCHRONIZATION
    # ============================================================

    def _synchronize_personal_knowledge(
        self,
        request: str,
    ):

        try:

            return self.knowledge_sync.process(
                request
            )

        except Exception:

            # Knowledge persistence must never
            # prevent the assistant from answering.
            return None

    # ============================================================
    # PERSONAL KNOWLEDGE GRAPH REASONING
    # ============================================================

    def _reason_from_personal_graph(
        self,
        request: str,
    ) -> str | None:

        try:

            return self.graph_reasoner.reason(
                request
            )

        except Exception:

            # Graph reasoning must never prevent
            # normal agent routing from working.
            return None

    # ============================================================
    # BACKWARD-COMPATIBILITY WRAPPER
    # ============================================================

    def _remember_if_relevant(
        self,
        request: str,
    ):

        return (
            self._synchronize_personal_knowledge(
                request
            )
        )

    # ============================================================
    # HANDLE
    # ============================================================

    def handle(
        self,
        request: str,
    ) -> str:

        if (
            not request
            or not request.strip()
        ):

            return (
                "Please provide a request."
            )

        if self._is_personal_data_write_request(
            request
        ):

            return (
                "Naya's Calendar, Contacts, Tasks, and Notes access "
                "is read-only right now, so I cannot make that change."
            )

        # --------------------------------------------------------
        # CONTACTS QUERY REASONING
        #
        # Contact lookup is read-only and handled before model
        # routing so personal details are never invented.
        # --------------------------------------------------------

        if contacts_query_engine.can_answer(
            request
        ):

            try:
                contacts_answer = contacts_query_engine.answer(
                    request
                )

            except Exception:
                contacts_answer = None

            if contacts_answer is not None:
                return contacts_answer

        # --------------------------------------------------------
        # CALENDAR QUERY REASONING
        #
        # Calendar requests are handled before Memory, Graph,
        # General-Agent and Specialized-Agent routing.
        #
        # This prevents the language model from inventing schedule
        # information when verified Calendar data is available.
        # --------------------------------------------------------

        if calendar_query_engine.can_answer(
            request
        ):

            try:

                calendar_answer = (
                    calendar_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # Calendar failure must never break
                # the remainder of MoneroAI routing.
                calendar_answer = None

            if calendar_answer is not None:

                return calendar_answer

        # --------------------------------------------------------
        # --------------------------------------------------------
        # TASK / REMINDER QUERY REASONING
        #
        # Read-only task and reminder questions are answered
        # before Memory, Graph and normal agent routing.
        #
        # Write commands such as "Remind me to..." are deliberately
        # excluded by TaskQueryEngine and continue through the
        # normal routing path until write permissions are added.
        # --------------------------------------------------------

        if task_query_engine.can_answer(
            request
        ):

            try:

                task_answer = (
                    task_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # A Task subsystem problem must never
                # break the remainder of MoneroAI.
                task_answer = None

            if task_answer is not None:

                return task_answer

        # --------------------------------------------------------
        # NOTES QUERY REASONING
        #
        # Read-only Notes questions are answered before
        # Memory, Graph and normal agent routing.
        #
        # Notes write commands are deliberately excluded by
        # NotesQueryEngine until controlled write permissions
        # are implemented.
        # --------------------------------------------------------

        if notes_query_engine.can_answer(
            request
        ):

            try:

                notes_answer = (
                    notes_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # Notes subsystem problems must not
                # break normal MoneroAI routing.
                notes_answer = None

            if notes_answer is not None:

                return notes_answer

        # PHASE 22 PERSONAL KNOWLEDGE INGESTION
        #
        # One coordinated writer now handles:
        #
        # - Long-Term Memory
        # - Personal Knowledge Graph
        # - reinforcement
        # - duplicate prevention
        # - conflict/supersession
        #
        # This replaces the old direct
        # MemoryExtractor write path.
        # --------------------------------------------------------

        self._synchronize_personal_knowledge(
            request
        )

        # --------------------------------------------------------
        # PERSONAL KNOWLEDGE GRAPH REASONING
        #
        # Explicit personal factual and relationship
        # questions may be answered directly from
        # the verified Personal Knowledge Graph.
        #
        # If the graph cannot answer, normal routing
        # continues unchanged.
        # --------------------------------------------------------

        graph_answer = (
            self._reason_from_personal_graph(
                request
            )
        )

        if graph_answer is not None:

            return graph_answer

        # --------------------------------------------------------
        # CROSS-AGENT INTELLIGENCE
        # --------------------------------------------------------

        if self._is_cross_agent_request(
            request
        ):

            return (
                self.cross_agent_coordinator
                .handle(
                    request
                )
            )

        # --------------------------------------------------------
        # GENERAL KNOWLEDGE
        # --------------------------------------------------------

        if self.is_general_request(
            request
        ):

            return (
                self.general_agent
                .handle(
                    request
                )
            )

        # --------------------------------------------------------
        # SPECIALIZED AGENT
        # --------------------------------------------------------

        agent = self.find_agent(
            request
        )

        if agent is None:

            return (
                self.general_agent
                .handle(
                    request
                )
            )

        # IMPORTANT:
        #
        # The specialized agent receives the
        # ORIGINAL request.
        #
        # Memory/graph context must not contaminate
        # specialized intent detection.
        return agent.handle(
            request
        )


# ================================================================
# GLOBAL COORDINATOR INSTANCE
# ================================================================

agent_coordinator = AgentCoordinator()
