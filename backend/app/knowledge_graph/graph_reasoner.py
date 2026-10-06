from __future__ import annotations

import re

from typing import Any

from app.knowledge_graph.entity_resolver import (
    EntityResolver,
)

from app.knowledge_graph.graph_context import (
    GraphContextBuilder,
    graph_context,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_traversal import (
    GraphTraverser,
)


class GraphReasoner:

    def __init__(
        self,
        manager: GraphManager | None = None,
        context_builder: GraphContextBuilder | None = None,
        traverser: GraphTraverser | None = None,
        resolver: EntityResolver | None = None,
    ):

        self.manager = (
            manager
            if manager is not None
            else graph_manager
        )

        self.store = self.manager.store

        self.resolver = (
            resolver
            if resolver is not None
            else EntityResolver(
                self.store
            )
        )

        self.traverser = (
            traverser
            if traverser is not None
            else GraphTraverser(
                manager=self.manager,
                resolver=self.resolver,
            )
        )

        self.context_builder = (
            context_builder
            if context_builder is not None
            else (
                graph_context
                if manager is None
                else GraphContextBuilder(
                    manager=self.manager,
                    resolver=self.resolver,
                    traverser=self.traverser,
                )
            )
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        text = text.replace(
            "’",
            "'",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # CAN REASON?
    # ============================================================

    def can_reason(
        self,
        query: str,
    ) -> bool:

        if not query or not query.strip():

            return False

        lowered = self._normalize(
            query
        ).casefold()

        explicit_patterns = (
            "connected to me",
            "connected to my",
            "related to me",
            "related to my",
            "how is ",
            "how are ",
            "what projects am i building",
            "what project am i building",
            "what is my trading strategy",
            "what's my trading strategy",
            "what am i learning",
            "where do i work",
            "where am i working",
            "what company do i work",
            "what is my role",
            "what's my role",
            "what are my interests",
            "what am i interested in",
            "what technologies",
            "what does moneroai use",
            "what does naya use",
            "what does jarvis use",
            "what does moneroai include",
            "what does naya include",
            "what does jarvis include",
        )

        if any(
            pattern in lowered
            for pattern in explicit_patterns
        ):

            return True

        # Generic entity-to-entity connection question.
        if (
            "connected" in lowered
            and (
                "how" in lowered
                or "what" in lowered
            )
        ):

            return True

        return False

    # ============================================================
    # FORMAT RELATION
    # ============================================================

    @staticmethod
    def _human_relation(
        relation_type: str,
    ) -> str:

        mapping = {
            "building": "you are building",
            "uses": "uses",
            "includes": "includes",
            "learning": "you are learning",
            "works_at": "you work at",
            "has_role": "your role is",
            "works_in_department": (
                "you work in the department"
            ),
            "has_career_goal": (
                "your career goal is"
            ),
            "studied": "you studied",
            "interested_in": (
                "you are interested in"
            ),
            "trades": "you trade",
            "uses_strategy": (
                "your trading strategy is"
            ),
            "strategy_for": (
                "is a strategy for"
            ),
            "related_to": (
                "is related to"
            ),
            "role_at": "is a role at",
            "department_of": (
                "is a department of"
            ),
        }

        return mapping.get(
            relation_type,
            relation_type.replace(
                "_",
                " ",
            ),
        )

    # ============================================================
    # HUMANIZE PATH
    # ============================================================

    def _humanize_path(
        self,
        path: dict[str, Any],
    ) -> str:

        steps = path.get(
            "steps",
            [],
        )

        if not steps:

            start = path.get(
                "start",
                {},
            )

            return start.get(
                "name",
                "",
            )

        clauses = []

        for index, step in enumerate(
            steps
        ):

            relation = step[
                "relation_type"
            ]

            neighbor = step[
                "neighbor_name"
            ]

            direction = step[
                "traversal_direction"
            ]

            if direction == "outgoing":

                if (
                    index == 0
                    and step[
                        "from_name"
                    ]
                    == "User"
                ):

                    phrase = (
                        self._human_relation(
                            relation
                        )
                    )

                    clauses.append(
                        f"{phrase} {neighbor}"
                    )

                else:

                    source = step[
                        "from_name"
                    ]

                    phrase = (
                        self._human_relation(
                            relation
                        )
                    )

                    clauses.append(
                        f"{source} "
                        f"{phrase} "
                        f"{neighbor}"
                    )

            else:

                source = step[
                    "neighbor_name"
                ]

                target = step[
                    "from_name"
                ]

                phrase = (
                    self._human_relation(
                        relation
                    )
                )

                clauses.append(
                    f"{source} "
                    f"{phrase} "
                    f"{target}"
                )

        if not clauses:

            return ""

        if len(clauses) == 1:

            return clauses[0] + "."

        return (
            "; ".join(
                clauses[:-1]
            )
            + "; and "
            + clauses[-1]
            + "."
        )

    # ============================================================
    # PERSONAL CONNECTION REASONING
    # ============================================================

    def _reason_personal_connection(
        self,
        query: str,
    ) -> str | None:

        entities = (
            self.context_builder
            .find_mentioned_entities(
                query
            )
        )

        targets = [
            entity
            for entity in entities
            if entity[
                "name"
            ] != "User"
        ]

        if not targets:

            return None

        lines = []

        for entity in targets:

            # Use the context builder first because
            # it understands query-specific semantic
            # paths such as education and trading.
            context_lines = (
                self.context_builder
                .build_lines(
                    query=query,
                    max_depth=4,
                    max_lines=3,
                )
            )

            if context_lines:

                for line in context_lines:

                    if line not in lines:

                        lines.append(
                            line
                        )

                break

        if not lines:

            return None

        if len(lines) == 1:

            return (
                "The connection is: "
                + lines[0]
                + "."
            )

        return (
            "The relevant connections are:\n"
            + "\n".join(
                f"- {line}"
                for line in lines
            )
        )

    # ============================================================
    # PROJECTS
    # ============================================================

    def _reason_projects(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
            )
        )

        projects = [
            item["target_name"]
            for item in connections
            if (
                item["relation_type"]
                == "building"
                and item[
                    "target_type"
                ]
                == "project"
            )
        ]

        if not projects:

            return None

        if len(projects) == 1:

            return (
                "You are building "
                + projects[0]
                + "."
            )

        return (
            "You are currently building: "
            + ", ".join(
                projects[:-1]
            )
            + " and "
            + projects[-1]
            + "."
        )

    # ============================================================
    # TRADING STRATEGY
    # ============================================================

    def _reason_trading_strategy(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type=(
                    "uses_strategy"
                ),
            )
        )

        if not connections:

            return None

        strategies = [
            item["target_name"]
            for item in connections
        ]

        if len(strategies) == 1:

            return (
                "Your trading strategy is "
                + strategies[0]
                + "."
            )

        return (
            "Your active trading strategies are "
            + ", ".join(
                strategies
            )
            + "."
        )

    # ============================================================
    # LEARNING
    # ============================================================

    def _reason_learning(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type="learning",
            )
        )

        if not connections:

            return None

        values = [
            item["target_name"]
            for item in connections
        ]

        if len(values) == 1:

            return (
                "You are learning "
                + values[0]
                + "."
            )

        return (
            "You are learning "
            + ", ".join(
                values[:-1]
            )
            + " and "
            + values[-1]
            + "."
        )

    # ============================================================
    # EMPLOYMENT
    # ============================================================

    def _reason_workplace(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type="works_at",
            )
        )

        if not connections:

            return None

        workplaces = [
            item["target_name"]
            for item in connections
        ]

        if len(workplaces) == 1:

            return (
                "You work at "
                + workplaces[0]
                + "."
            )

        return (
            "Your active workplaces are "
            + ", ".join(
                workplaces
            )
            + "."
        )

    # ============================================================
    # ROLE
    # ============================================================

    def _reason_role(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type="has_role",
            )
        )

        if not connections:

            return None

        roles = [
            item["target_name"]
            for item in connections
        ]

        if len(roles) == 1:

            return (
                "Your current role is "
                + roles[0]
                + "."
            )

        return (
            "Your active roles are "
            + ", ".join(
                roles
            )
            + "."
        )

    # ============================================================
    # INTERESTS
    # ============================================================

    def _reason_interests(
        self,
    ) -> str | None:

        connections = (
            self.manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type=(
                    "interested_in"
                ),
            )
        )

        if not connections:

            return None

        interests = [
            item["target_name"]
            for item in connections
        ]

        if len(interests) == 1:

            return (
                "You are interested in "
                + interests[0]
                + "."
            )

        return (
            "Your recorded interests are "
            + ", ".join(
                interests[:-1]
            )
            + " and "
            + interests[-1]
            + "."
        )

    # ============================================================
    # PROJECT DETAILS
    # ============================================================

    def _reason_project_details(
        self,
        project_name: str,
        relation_type: str,
        label: str,
    ) -> str | None:

        node = self.traverser.resolve_node(
            project_name,
            "project",
        )

        if node is None:

            return None

        connections = (
            self.manager.get_connections(
                node.name,
                node.node_type,
                direction="outgoing",
                relation_type=(
                    relation_type
                ),
            )
        )

        if not connections:

            return None

        values = [
            item["target_name"]
            for item in connections
        ]

        return (
            f"{node.name} {label} "
            + ", ".join(
                values
            )
            + "."
        )

    # ============================================================
    # REASON
    # ============================================================

    def reason(
        self,
        query: str,
    ) -> str | None:

        if not self.can_reason(
            query
        ):

            return None

        normalized = self._normalize(
            query
        )

        lowered = normalized.casefold()

        # --------------------------------------------------------
        # PROJECT LIST
        # --------------------------------------------------------

        if (
            "what projects am i building"
            in lowered
            or "what project am i building"
            in lowered
        ):

            return self._reason_projects()

        # --------------------------------------------------------
        # TRADING STRATEGY
        # --------------------------------------------------------

        if (
            "what is my trading strategy"
            in lowered
            or "what's my trading strategy"
            in lowered
        ):

            return (
                self._reason_trading_strategy()
            )

        # --------------------------------------------------------
        # LEARNING
        # --------------------------------------------------------

        if "what am i learning" in lowered:

            return self._reason_learning()

        # --------------------------------------------------------
        # WORKPLACE
        # --------------------------------------------------------

        if (
            "where do i work"
            in lowered
            or "where am i working"
            in lowered
            or "what company do i work"
            in lowered
        ):

            return self._reason_workplace()

        # --------------------------------------------------------
        # ROLE
        # --------------------------------------------------------

        if (
            "what is my role"
            in lowered
            or "what's my role"
            in lowered
        ):

            return self._reason_role()

        # --------------------------------------------------------
        # INTERESTS
        # --------------------------------------------------------

        if (
            "what are my interests"
            in lowered
            or "what am i interested in"
            in lowered
        ):

            return self._reason_interests()

        # --------------------------------------------------------
        # MONEROAI USES
        # --------------------------------------------------------

        if (
            "what does moneroai use"
            in lowered
            or "what does naya use"
            in lowered
            or "what does jarvis use"
            in lowered
            or (
                "what technologies"
                in lowered
                and (
                    "moneroai"
                    in lowered
                    or "naya"
                    in lowered
                    or "jarvis"
                    in lowered
                )
            )
        ):

            return (
                self._reason_project_details(
                    project_name="MoneroAI",
                    relation_type="uses",
                    label="uses",
                )
            )

        # --------------------------------------------------------
        # MONEROAI COMPONENTS
        # --------------------------------------------------------

        if (
            "what does moneroai include"
            in lowered
            or "what does naya include"
            in lowered
            or "what does jarvis include"
            in lowered
        ):

            return (
                self._reason_project_details(
                    project_name="MoneroAI",
                    relation_type="includes",
                    label="includes",
                )
            )

        # --------------------------------------------------------
        # CONNECTION / RELATIONSHIP QUERY
        # --------------------------------------------------------

        if (
            "connected"
            in lowered
            or "related"
            in lowered
            or lowered.startswith(
                "how is "
            )
            or lowered.startswith(
                "how are "
            )
        ):

            return (
                self._reason_personal_connection(
                    normalized
                )
            )

        return None


graph_reasoner = GraphReasoner()
