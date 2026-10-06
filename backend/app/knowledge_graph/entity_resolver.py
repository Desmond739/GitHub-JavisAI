from __future__ import annotations

import re

from typing import Any

from app.knowledge_graph.graph_model import (
    KnowledgeNode,
)

from app.knowledge_graph.graph_store import (
    GraphStore,
    graph_store,
)


class EntityResolver:

    DEFAULT_ENTITIES = [

        {
            "canonical_name": "C#",
            "node_type": "technology",
            "aliases": [
                "C#",
                "C Sharp",
                "CSharp",
            ],
        },

        {
            "canonical_name": "MTN Cameroon",
            "node_type": "organization",
            "aliases": [
                "MTN",
                "MTNC",
                "MTN Cameroon",
            ],
        },

        {
            "canonical_name": "MoneroAI",
            "node_type": "project",
            "aliases": [
                "MoneroAI",
                "Monero AI",
                "Naya",
                "JARVIS",
                "JavisAI",
            ],
        },

        {
            "canonical_name": "Forex",
            "node_type": "market",
            "aliases": [
                "Forex",
                "FX",
                "Foreign Exchange",
            ],
        },

        {
            "canonical_name": "Support and Resistance",
            "node_type": "trading_strategy",
            "aliases": [
                "Support and Resistance",
                "Support & Resistance",
                "S&R",
                "S and R",
            ],
        },

        {
            "canonical_name": "Artificial Intelligence",
            "node_type": "field",
            "aliases": [
                "Artificial Intelligence",
                "AI",
            ],
        },

        {
            "canonical_name": "Cybersecurity",
            "node_type": "field",
            "aliases": [
                "Cybersecurity",
                "Cyber Security",
            ],
        },

        {
            "canonical_name": "Computer Networking",
            "node_type": "field",
            "aliases": [
                "Computer Networking",
                "Computer Networks",
            ],
        },

        {
            "canonical_name": "Python",
            "node_type": "technology",
            "aliases": [
                "Python",
                "Python Programming",
            ],
        },

        {
            "canonical_name": "Ollama",
            "node_type": "technology",
            "aliases": [
                "Ollama",
            ],
        },

        {
            "canonical_name": "Qwen3",
            "node_type": "ai_model",
            "aliases": [
                "Qwen3",
                "Qwen 3",
            ],
        },

        {
            "canonical_name": "ESP32",
            "node_type": "technology",
            "aliases": [
                "ESP32",
                "ESP 32",
            ],
        },

        {
            "canonical_name": "Blynk",
            "node_type": "technology",
            "aliases": [
                "Blynk",
            ],
        },

    ]

    def __init__(
        self,
        store: GraphStore | None = None,
    ):

        self.store = (
            store
            if store is not None
            else graph_store
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize(
        value: str,
    ) -> str:

        value = value.strip()

        value = value.replace(
            "’",
            "'",
        )

        value = value.rstrip(
            " .,!?:;"
        )

        value = re.sub(
            r"[\s_-]+",
            " ",
            value,
        )

        return value.casefold().strip()

    # ============================================================
    # NORMALIZE NODE TYPE
    # ============================================================

    @staticmethod
    def normalize_type(
        node_type: str | None,
    ) -> str | None:

        if node_type is None:

            return None

        value = node_type.strip().lower()

        value = re.sub(
            r"[\s\-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip("_")

    # ============================================================
    # FIND DEFAULT DEFINITIONS
    # ============================================================

    def _find_default_definitions(
        self,
        name: str,
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:

        normalized_name = self.normalize(
            name
        )

        normalized_type = self.normalize_type(
            node_type
        )

        results = []

        for definition in self.DEFAULT_ENTITIES:

            definition_type = (
                self.normalize_type(
                    definition["node_type"]
                )
            )

            if (
                normalized_type is not None
                and definition_type
                != normalized_type
            ):

                continue

            names = [
                definition["canonical_name"],
                *definition["aliases"],
            ]

            normalized_names = {
                self.normalize(item)
                for item in names
            }

            if normalized_name in normalized_names:

                results.append(
                    definition
                )

        return results

    # ============================================================
    # FIND GRAPH MATCHES
    # ============================================================

    def _find_graph_matches(
        self,
        name: str,
        node_type: str | None = None,
    ) -> list[KnowledgeNode]:

        normalized_name = self.normalize(
            name
        )

        normalized_type = self.normalize_type(
            node_type
        )

        matches = []

        for node in self.store.get_active_nodes():

            if (
                normalized_type is not None
                and self.normalize_type(
                    node.node_type
                )
                != normalized_type
            ):

                continue

            candidate_names = {
                self.normalize(
                    node.name
                )
            }

            aliases = node.attributes.get(
                "aliases",
                [],
            )

            if isinstance(
                aliases,
                list,
            ):

                for alias in aliases:

                    if isinstance(
                        alias,
                        str,
                    ):

                        candidate_names.add(
                            self.normalize(
                                alias
                            )
                        )

            if normalized_name in candidate_names:

                matches.append(
                    node
                )

        return matches

    # ============================================================
    # RESOLVE
    # ============================================================

    def resolve(
        self,
        name: str,
        node_type: str | None = None,
    ) -> dict[str, Any]:

        if not name or not name.strip():

            raise ValueError(
                "Entity name cannot be empty."
            )

        cleaned_name = name.strip().rstrip(
            " .,!?:;"
        )

        normalized_type = self.normalize_type(
            node_type
        )

        # --------------------------------------------------------
        # 1. Check persistent graph aliases first
        # --------------------------------------------------------

        graph_matches = (
            self._find_graph_matches(
                cleaned_name,
                normalized_type,
            )
        )

        if len(graph_matches) > 1:

            raise ValueError(
                f"Ambiguous entity reference: "
                f"{name}"
            )

        if len(graph_matches) == 1:

            node = graph_matches[0]

            return {
                "canonical_name": node.name,
                "node_type": node.node_type,
                "node_id": node.node_id,
                "matched_by": "graph",
            }

        # --------------------------------------------------------
        # 2. Check built-in canonical registry
        # --------------------------------------------------------

        definitions = (
            self._find_default_definitions(
                cleaned_name,
                normalized_type,
            )
        )

        if len(definitions) > 1:

            raise ValueError(
                f"Ambiguous canonical entity: "
                f"{name}"
            )

        if len(definitions) == 1:

            definition = definitions[0]

            canonical_name = (
                definition[
                    "canonical_name"
                ]
            )

            canonical_type = (
                definition[
                    "node_type"
                ]
            )

            existing = (
                self._find_graph_matches(
                    canonical_name,
                    canonical_type,
                )
            )

            node_id = None

            if existing:

                node_id = (
                    existing[0].node_id
                )

            return {
                "canonical_name": (
                    canonical_name
                ),
                "node_type": (
                    canonical_type
                ),
                "node_id": node_id,
                "matched_by": "registry",
            }

        # --------------------------------------------------------
        # 3. Unknown entity
        # --------------------------------------------------------

        return {
            "canonical_name": cleaned_name,
            "node_type": normalized_type,
            "node_id": None,
            "matched_by": "unresolved",
        }

    # ============================================================
    # RESOLVE NAME
    # ============================================================

    def resolve_name(
        self,
        name: str,
        node_type: str | None = None,
    ) -> str:

        return self.resolve(
            name=name,
            node_type=node_type,
        )["canonical_name"]

    # ============================================================
    # ENSURE ENTITY
    # ============================================================

    def ensure_entity(
        self,
        name: str,
        node_type: str,
        attributes: dict[str, Any] | None = None,
    ) -> KnowledgeNode:

        result = self.resolve(
            name=name,
            node_type=node_type,
        )

        canonical_name = (
            result["canonical_name"]
        )

        canonical_type = (
            result["node_type"]
            or self.normalize_type(
                node_type
            )
        )

        if not canonical_type:

            raise ValueError(
                "Node type is required."
            )

        if result["node_id"]:

            node = self.store.get_node(
                result["node_id"]
            )

            if node is None:

                raise RuntimeError(
                    "Resolved node could not "
                    "be loaded."
                )

            if attributes:

                return self.store.update_node(
                    node.node_id,
                    attributes=attributes,
                )

            return node

        return self.store.add_node(
            name=canonical_name,
            node_type=canonical_type,
            attributes=attributes,
        )

    # ============================================================
    # REGISTER ALIASES
    # ============================================================

    def register_aliases(
        self,
        canonical_name: str,
        node_type: str,
        aliases: list[str],
        create_if_missing: bool = True,
    ) -> KnowledgeNode | None:

        result = self.resolve(
            canonical_name,
            node_type,
        )

        node = None

        if result["node_id"]:

            node = self.store.get_node(
                result["node_id"]
            )

        elif create_if_missing:

            node = self.ensure_entity(
                canonical_name,
                node_type,
            )

        if node is None:

            return None

        existing_aliases = (
            node.attributes.get(
                "aliases",
                [],
            )
        )

        if not isinstance(
            existing_aliases,
            list,
        ):

            existing_aliases = []

        combined = []

        seen = set()

        for alias in [
            *existing_aliases,
            *aliases,
        ]:

            if (
                not isinstance(alias, str)
                or not alias.strip()
            ):

                continue

            normalized = self.normalize(
                alias
            )

            if normalized in seen:

                continue

            seen.add(
                normalized
            )

            combined.append(
                alias.strip()
            )

        return self.store.update_node(
            node.node_id,
            attributes={
                "aliases": combined
            },
        )

    # ============================================================
    # SEED DEFAULT ALIASES
    # ============================================================

    def seed_default_aliases(
        self,
        create_missing: bool = False,
    ) -> dict[str, int]:

        updated = 0
        created = 0
        skipped = 0

        before_nodes = len(
            self.store.get_all_nodes()
        )

        for definition in self.DEFAULT_ENTITIES:

            node = self.register_aliases(
                canonical_name=(
                    definition[
                        "canonical_name"
                    ]
                ),
                node_type=(
                    definition[
                        "node_type"
                    ]
                ),
                aliases=(
                    definition["aliases"]
                ),
                create_if_missing=(
                    create_missing
                ),
            )

            if node is None:

                skipped += 1
                continue

            updated += 1

        after_nodes = len(
            self.store.get_all_nodes()
        )

        created = (
            after_nodes
            - before_nodes
        )

        return {
            "updated": updated,
            "created": created,
            "skipped": skipped,
        }


entity_resolver = EntityResolver()
