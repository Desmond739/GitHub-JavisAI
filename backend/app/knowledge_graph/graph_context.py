from __future__ import annotations

import re

from typing import Any

from app.knowledge_graph.entity_resolver import (
    EntityResolver,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_traversal import (
    GraphTraverser,
)


class GraphContextBuilder:

    DOMAIN_RELATIONS = {

        "education": {
            "studied",
            "related_to",
        },

        "study": {
            "studied",
            "related_to",
        },

        "studied": {
            "studied",
            "related_to",
        },

        "career": {
            "works_at",
            "has_role",
            "role_at",
            "works_in_department",
            "department_of",
            "has_career_goal",
            "related_to",
        },

        "work": {
            "works_at",
            "has_role",
            "role_at",
            "works_in_department",
            "department_of",
            "has_career_goal",
            "related_to",
        },

        "job": {
            "works_at",
            "has_role",
            "role_at",
            "works_in_department",
            "department_of",
            "has_career_goal",
            "related_to",
        },

        "project": {
            "building",
            "uses",
            "includes",
            "related_to",
        },

        "projects": {
            "building",
            "uses",
            "includes",
            "related_to",
        },

        "technical": {
            "learning",
            "building",
            "uses",
            "includes",
            "interested_in",
            "studied",
            "related_to",
        },

        "technology": {
            "learning",
            "building",
            "uses",
            "includes",
            "related_to",
        },

        "trading": {
            "trades",
            "uses_strategy",
            "strategy_for",
        },

        "forex": {
            "trades",
            "uses_strategy",
            "strategy_for",
        },
    }

    def __init__(
        self,
        manager: GraphManager | None = None,
        resolver: EntityResolver | None = None,
        traverser: GraphTraverser | None = None,
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

    # ============================================================
    # NORMALIZE QUERY
    # ============================================================

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:

        query = query.replace(
            "’",
            "'",
        )

        query = re.sub(
            r"\s+",
            " ",
            query,
        )

        return query.strip()

    # ============================================================
    # USER REFERENCE DETECTION
    # ============================================================

    @staticmethod
    def _references_user(
        query: str,
    ) -> bool:

        query = query.casefold()

        patterns = [
            r"\bme\b",
            r"\bmy\b",
            r"\bmine\b",
            r"\bmyself\b",
            r"\bi\b",
            r"\bi'm\b",
            r"\bi am\b",
        ]

        return any(
            re.search(
                pattern,
                query,
            )
            is not None
            for pattern in patterns
        )

    # ============================================================
    # QUERY PHRASE MATCHING
    # ============================================================

    @staticmethod
    def _contains_phrase(
        query: str,
        phrase: str,
    ) -> bool:

        query = query.casefold()
        phrase = phrase.casefold().strip()

        if not phrase:

            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(
                phrase
            )
            + r"(?!\w)"
        )

        return (
            re.search(
                pattern,
                query,
            )
            is not None
        )

    # ============================================================
    # ENTITY NAMES + ALIASES
    # ============================================================

    def _candidate_names(
        self,
        node,
    ) -> list[str]:

        candidates = [
            node.name
        ]

        aliases = node.attributes.get(
            "aliases",
            [],
        )

        if isinstance(
            aliases,
            list,
        ):

            candidates.extend(
                alias
                for alias in aliases
                if isinstance(
                    alias,
                    str,
                )
            )

        return candidates

    # ============================================================
    # FIND ENTITIES MENTIONED IN QUERY
    # ============================================================

    def find_mentioned_entities(
        self,
        query: str,
    ) -> list[dict[str, Any]]:

        query = self._normalize_query(
            query
        )

        if not query:

            return []

        matches = []

        seen_ids = set()

        # --------------------------------------------------------
        # Persistent graph names + aliases
        # --------------------------------------------------------

        for node in (
            self.store.get_active_nodes()
        ):

            for candidate in (
                self._candidate_names(
                    node
                )
            ):

                if not self._contains_phrase(
                    query,
                    candidate,
                ):

                    continue

                if node.node_id in seen_ids:

                    break

                seen_ids.add(
                    node.node_id
                )

                matches.append(
                    {
                        "node_id": node.node_id,
                        "name": node.name,
                        "node_type": (
                            node.node_type
                        ),
                        "matched_text": (
                            candidate
                        ),
                    }
                )

                break

        # --------------------------------------------------------
        # Resolver registry aliases
        # --------------------------------------------------------

        for definition in (
            self.resolver.DEFAULT_ENTITIES
        ):

            possible_names = [
                definition[
                    "canonical_name"
                ],
                *definition.get(
                    "aliases",
                    [],
                ),
            ]

            matched_alias = None

            for candidate in possible_names:

                if self._contains_phrase(
                    query,
                    candidate,
                ):

                    matched_alias = candidate
                    break

            if matched_alias is None:

                continue

            resolved = self.resolver.resolve(
                matched_alias,
                definition[
                    "node_type"
                ],
            )

            node_id = resolved.get(
                "node_id"
            )

            if (
                not node_id
                or node_id in seen_ids
            ):

                continue

            node = self.store.get_node(
                node_id
            )

            if node is None:

                continue

            seen_ids.add(
                node_id
            )

            matches.append(
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "node_type": (
                        node.node_type
                    ),
                    "matched_text": (
                        matched_alias
                    ),
                }
            )

        return matches

    # ============================================================
    # GENERAL DOMAIN RELATION FILTER
    # ============================================================

    def _domain_relations(
        self,
        query: str,
    ) -> list[str] | None:

        relations = set()

        for (
            keyword,
            domain_relations,
        ) in self.DOMAIN_RELATIONS.items():

            if self._contains_phrase(
                query,
                keyword,
            ):

                relations.update(
                    domain_relations
                )

        if not relations:

            return None

        return sorted(
            relations
        )

    # ============================================================
    # PREFERRED SEMANTIC PATHS
    # ============================================================

    def _preferred_relation_sets(
        self,
        query: str,
    ) -> list[list[str]]:

        query = query.casefold()

        preferred = []

        # --------------------------------------------------------
        # TRADING STRATEGY
        #
        # Prefer:
        # User -> Support and Resistance -> Forex
        #
        # instead of:
        # User -> Forex
        # --------------------------------------------------------

        if (
            self._contains_phrase(
                query,
                "trading strategy",
            )
            or self._contains_phrase(
                query,
                "strategy",
            )
        ):

            preferred.append(
                [
                    "uses_strategy",
                    "strategy_for",
                ]
            )

        # --------------------------------------------------------
        # EDUCATION
        #
        # Prefer:
        # User -> field of study -> subject
        # --------------------------------------------------------

        if (
            self._contains_phrase(
                query,
                "education",
            )
            or self._contains_phrase(
                query,
                "study",
            )
            or self._contains_phrase(
                query,
                "studied",
            )
        ):

            preferred.append(
                [
                    "studied",
                    "related_to",
                ]
            )

        # --------------------------------------------------------
        # PROJECT / BUILDING RELATIONSHIPS
        # --------------------------------------------------------

        if (
            self._contains_phrase(
                query,
                "project",
            )
            or self._contains_phrase(
                query,
                "projects",
            )
        ):

            preferred.append(
                [
                    "building",
                    "uses",
                    "includes",
                    "related_to",
                ]
            )

        return preferred

    # ============================================================
    # FORMAT PATH
    # ============================================================

    def _format_path(
        self,
        path: dict[str, Any],
    ) -> str:

        return self.traverser.format_path(
            path
        )

    # ============================================================
    # FIND BEST USER → ENTITY PATH
    # ============================================================

    def _find_best_user_paths(
        self,
        query: str,
        entity: dict[str, Any],
        max_depth: int,
    ) -> list[dict[str, Any]]:

        relation_attempts = []

        # --------------------------------------------------------
        # First: query-specific preferred semantic paths
        # --------------------------------------------------------

        for relation_set in (
            self._preferred_relation_sets(
                query
            )
        ):

            relation_attempts.append(
                relation_set
            )

        # --------------------------------------------------------
        # Second: broader domain path
        # --------------------------------------------------------

        domain_relations = (
            self._domain_relations(
                query
            )
        )

        if (
            domain_relations is not None
            and domain_relations
            not in relation_attempts
        ):

            relation_attempts.append(
                domain_relations
            )

        # --------------------------------------------------------
        # Final fallback: unrestricted graph traversal
        # --------------------------------------------------------

        relation_attempts.append(
            None
        )

        for relation_types in (
            relation_attempts
        ):

            candidate_paths = (
                self.traverser.find_paths(
                    start_name="User",
                    target_name=(
                        entity["name"]
                    ),
                    start_type="person",
                    target_type=(
                        entity[
                            "node_type"
                        ]
                    ),
                    max_depth=max_depth,
                    direction="both",
                    relation_types=(
                        relation_types
                    ),
                    max_paths=5,
                )
            )

            if candidate_paths:

                return candidate_paths

        return []

    # ============================================================
    # CONNECTION CONTEXT
    # ============================================================

    def _build_connection_paths(
        self,
        query: str,
        mentioned_entities: list[
            dict[str, Any]
        ],
        max_depth: int,
    ) -> list[str]:

        paths = []

        seen = set()

        references_user = (
            self._references_user(
                query
            )
        )

        for entity in mentioned_entities:

            if entity["name"] == "User":

                continue

            # ----------------------------------------------------
            # PERSONAL QUERY:
            # Build complete User -> Entity relationship.
            # ----------------------------------------------------

            if references_user:

                candidate_paths = (
                    self._find_best_user_paths(
                        query=query,
                        entity=entity,
                        max_depth=max_depth,
                    )
                )

                for path in candidate_paths:

                    formatted = (
                        self._format_path(
                            path
                        )
                    )

                    if (
                        not formatted
                        or formatted in seen
                    ):

                        continue

                    seen.add(
                        formatted
                    )

                    paths.append(
                        formatted
                    )

            # ----------------------------------------------------
            # NON-PERSONAL QUERY:
            # Show local graph context around entity.
            # ----------------------------------------------------

            else:

                connections = (
                    self.manager.get_connections(
                        name=entity["name"],
                        node_type=(
                            entity[
                                "node_type"
                            ]
                        ),
                        direction="both",
                    )
                )

                for connection in connections:

                    if (
                        connection[
                            "direction"
                        ]
                        == "outgoing"
                    ):

                        formatted = (
                            connection[
                                "source_name"
                            ]
                            + " --"
                            + connection[
                                "relation_type"
                            ]
                            + "--> "
                            + connection[
                                "target_name"
                            ]
                        )

                    else:

                        formatted = (
                            connection[
                                "target_name"
                            ]
                            + " <--"
                            + connection[
                                "relation_type"
                            ]
                            + "-- "
                            + connection[
                                "source_name"
                            ]
                        )

                    if formatted in seen:

                        continue

                    seen.add(
                        formatted
                    )

                    paths.append(
                        formatted
                    )

        return paths

    # ============================================================
    # CATEGORY CONTEXT
    # ============================================================

    def _build_category_context(
        self,
        query: str,
    ) -> list[str]:

        target_types = set()

        if (
            self._contains_phrase(
                query,
                "project",
            )
            or self._contains_phrase(
                query,
                "projects",
            )
        ):

            target_types.add(
                "project"
            )

        if (
            self._contains_phrase(
                query,
                "technology",
            )
            or self._contains_phrase(
                query,
                "technologies",
            )
        ):

            target_types.add(
                "technology"
            )

        if self._contains_phrase(
            query,
            "career",
        ):

            target_types.update(
                {
                    "organization",
                    "role",
                    "department",
                    "goal",
                }
            )

        if self._contains_phrase(
            query,
            "trading",
        ):

            target_types.update(
                {
                    "market",
                    "trading_strategy",
                }
            )

        if not target_types:

            return []

        results = []

        seen = set()

        connections = (
            self.manager.get_connections(
                name="User",
                node_type="person",
                direction="outgoing",
            )
        )

        for connection in connections:

            if (
                connection[
                    "target_type"
                ]
                not in target_types
            ):

                continue

            formatted = (
                connection[
                    "source_name"
                ]
                + " --"
                + connection[
                    "relation_type"
                ]
                + "--> "
                + connection[
                    "target_name"
                ]
            )

            if formatted in seen:

                continue

            seen.add(
                formatted
            )

            results.append(
                formatted
            )

        return results

    # ============================================================
    # BUILD RAW CONTEXT LINES
    # ============================================================

    def build_lines(
        self,
        query: str,
        max_depth: int = 4,
        max_lines: int = 8,
    ) -> list[str]:

        if (
            not query
            or not query.strip()
            or max_lines < 1
        ):

            return []

        query = self._normalize_query(
            query
        )

        mentioned_entities = (
            self.find_mentioned_entities(
                query
            )
        )

        lines = (
            self._build_connection_paths(
                query=query,
                mentioned_entities=(
                    mentioned_entities
                ),
                max_depth=max_depth,
            )
        )

        # --------------------------------------------------------
        # No explicit entity path:
        # try category-level personal context.
        # --------------------------------------------------------

        if not lines:

            lines = (
                self._build_category_context(
                    query
                )
            )

        unique = []

        seen = set()

        for line in lines:

            if not line:

                continue

            if line in seen:

                continue

            seen.add(
                line
            )

            unique.append(
                line
            )

            if (
                len(unique)
                >= max_lines
            ):

                break

        return unique

    # ============================================================
    # BUILD PROMPT CONTEXT
    # ============================================================

    def build(
        self,
        query: str,
        max_depth: int = 4,
        max_lines: int = 8,
    ) -> str:

        lines = self.build_lines(
            query=query,
            max_depth=max_depth,
            max_lines=max_lines,
        )

        if not lines:

            return ""

        formatted_lines = "\n".join(
            f"- {line}"
            for line in lines
        )

        return (
            "RELEVANT KNOWLEDGE GRAPH:\n"
            + formatted_lines
        )


graph_context = GraphContextBuilder()
