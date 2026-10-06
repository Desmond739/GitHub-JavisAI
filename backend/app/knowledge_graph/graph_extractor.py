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

from app.knowledge_graph.graph_model import (
    KnowledgeRelationship,
)


class GraphExtractor:

    QUESTION_STARTERS = (
        "what ",
        "why ",
        "how ",
        "when ",
        "where ",
        "who ",
        "which ",
        "can ",
        "could ",
        "would ",
        "should ",
        "do ",
        "does ",
        "did ",
        "is ",
        "are ",
        "am ",
        "will ",
        "may ",
    )

    NEGATIVE_PATTERNS = (
        "i am not ",
        "i'm not ",
        "i’m not ",
        "i do not ",
        "i don't ",
        "i don’t ",
        "i no longer ",
        "i stopped ",
        "i have stopped ",
        "i used to ",
    )

    KNOWN_TECHNOLOGIES = {
        "c#",
        "c sharp",
        "csharp",
        "python",
        "docker",
        "ollama",
        "qwen3",
        "qwen 3",
        "esp32",
        "esp 32",
        "blynk",
        "arduino",
        ".net",
        "asp.net core",
        "entity framework core",
        "azure",
        "aws",
        "kubernetes",
        "git",
        "github",
        "postgresql",
        "sql",
        "fastapi",
    }

    def __init__(
        self,
        manager: GraphManager | None = None,
        resolver: EntityResolver | None = None,
    ):

        self.manager = (
            manager
            if manager is not None
            else graph_manager
        )

        # IMPORTANT:
        # Use a resolver connected to the SAME graph store
        # as this manager.
        #
        # This keeps temporary graph tests isolated from
        # the real personal knowledge graph.
        self.resolver = (
            resolver
            if resolver is not None
            else EntityResolver(
                self.manager.store
            )
        )

    # ============================================================
    # BASIC NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        text = text.strip()

        text = text.replace(
            "’",
            "'",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # ============================================================
    # CLEAN ENTITY NAME
    # ============================================================

    @staticmethod
    def _clean_entity_name(
        value: str,
    ) -> str:

        value = value.strip()

        value = value.rstrip(
            " .,!?:;"
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        # Remove unnecessary leading articles.
        value = re.sub(
            r"^(?:a|an|the)\s+",
            "",
            value,
            flags=re.IGNORECASE,
        )

        return value.strip()

    # ============================================================
    # QUESTION DETECTION
    # ============================================================

    def _is_question(
        self,
        text: str,
    ) -> bool:

        stripped = (
            text.lower().strip()
        )

        if text.strip().endswith("?"):

            return True

        return stripped.startswith(
            self.QUESTION_STARTERS
        )

    # ============================================================
    # NEGATIVE / HISTORICAL DETECTION
    # ============================================================

    def _is_negative_or_historical(
        self,
        text: str,
    ) -> bool:

        lowered = (
            text.lower().strip()
        )

        return any(
            pattern in lowered
            for pattern in self.NEGATIVE_PATTERNS
        )

    # ============================================================
    # TARGET TYPE INFERENCE
    # ============================================================

    def _infer_target_type(
        self,
        relation_type: str,
        target_name: str,
    ) -> str:

        normalized = (
            target_name.lower().strip()
        )

        if relation_type == "works_at":

            return "organization"

        if relation_type == "has_role":

            return "role"

        if relation_type == "building":

            return "project"

        if relation_type == "studied":

            return "field_of_study"

        if relation_type == "interested_in":

            return "field"

        if relation_type == "trades":

            return "market"

        if relation_type == "uses_strategy":

            return "trading_strategy"

        if relation_type == "learning":

            if (
                normalized
                in self.KNOWN_TECHNOLOGIES
            ):

                return "technology"

            return "skill"

        return "entity"

    # ============================================================
    # RESOLVE TARGET
    # ============================================================

    def _resolve_target(
        self,
        relation_type: str,
        target_name: str,
    ) -> tuple[str, str]:

        cleaned_name = (
            self._clean_entity_name(
                target_name
            )
        )

        if not cleaned_name:

            return "", "entity"

        # --------------------------------------------------------
        # First try full resolver without forcing a type.
        #
        # This lets aliases such as:
        #
        # C Sharp → C#
        # MTNC → MTN Cameroon
        # FX → Forex
        # JARVIS → MoneroAI
        #
        # resolve using their canonical entity definitions.
        # --------------------------------------------------------

        resolved = self.resolver.resolve(
            cleaned_name
        )

        if (
            resolved["matched_by"]
            != "unresolved"
        ):

            canonical_name = (
                resolved["canonical_name"]
            )

            canonical_type = (
                resolved["node_type"]
            )

            if canonical_type:

                return (
                    canonical_name,
                    canonical_type,
                )

        # --------------------------------------------------------
        # Unknown entity:
        # infer its type from the relationship.
        # --------------------------------------------------------

        inferred_type = (
            self._infer_target_type(
                relation_type,
                cleaned_name,
            )
        )

        # --------------------------------------------------------
        # Try once more with the inferred type.
        #
        # This allows persistent graph aliases that may require
        # type disambiguation.
        # --------------------------------------------------------

        resolved = self.resolver.resolve(
            cleaned_name,
            inferred_type,
        )

        return (
            resolved["canonical_name"],
            (
                resolved["node_type"]
                or inferred_type
            ),
        )

    # ============================================================
    # CREATE EXTRACTION RESULT
    # ============================================================

    def _build_result(
        self,
        relation_type: str,
        target_name: str,
        confidence: float = 0.98,
    ) -> dict[str, Any] | None:

        (
            resolved_name,
            resolved_type,
        ) = self._resolve_target(
            relation_type,
            target_name,
        )

        if not resolved_name:

            return None

        return {
            "source_name": "User",
            "source_type": "person",
            "relation_type": relation_type,
            "target_name": resolved_name,
            "target_type": resolved_type,
            "confidence": confidence,
        }

    # ============================================================
    # EXTRACT ONE CLAUSE
    # ============================================================

    def _extract_clause(
        self,
        text: str,
    ) -> dict[str, Any] | None:

        text = self._normalize_text(
            text
        )

        if not text:

            return None

        if self._is_question(
            text
        ):

            return None

        if self._is_negative_or_historical(
            text
        ):

            return None

        patterns = [

            # ----------------------------------------------------
            # WORK
            # ----------------------------------------------------

            (
                r"^(?:i work at|"
                r"i am working at|"
                r"i'm working at)\s+(.+)$",
                "works_at",
            ),

            # ----------------------------------------------------
            # ROLE
            # ----------------------------------------------------

            (
                r"^(?:i work as|"
                r"i am working as|"
                r"i'm working as|"
                r"my role is)\s+(.+)$",
                "has_role",
            ),

            # ----------------------------------------------------
            # LEARNING
            # ----------------------------------------------------

            (
                r"^(?:i am learning|"
                r"i'm learning|"
                r"i learn)\s+(.+)$",
                "learning",
            ),

            # ----------------------------------------------------
            # BUILDING
            # ----------------------------------------------------

            (
                r"^(?:i am building|"
                r"i'm building|"
                r"i am working on|"
                r"i'm working on)\s+(.+)$",
                "building",
            ),

            # ----------------------------------------------------
            # STUDIED
            # ----------------------------------------------------

            (
                r"^(?:i studied|"
                r"i study)\s+(.+)$",
                "studied",
            ),

            # ----------------------------------------------------
            # INTEREST
            # ----------------------------------------------------

            (
                r"^(?:i am interested in|"
                r"i'm interested in|"
                r"i have an interest in)\s+(.+)$",
                "interested_in",
            ),

            # ----------------------------------------------------
            # TRADING
            # ----------------------------------------------------

            (
                r"^(?:i trade|"
                r"i am trading|"
                r"i'm trading)\s+(.+)$",
                "trades",
            ),

            # ----------------------------------------------------
            # TRADING STRATEGY
            # ----------------------------------------------------

            (
                r"^my trading strategy is\s+(.+)$",
                "uses_strategy",
            ),

            (
                r"^(?:i use|"
                r"i am using|"
                r"i'm using)\s+(.+?)"
                r"\s+(?:strategy|trading strategy)$",
                "uses_strategy",
            ),

            (
                r"^(?:i use|"
                r"i am using|"
                r"i'm using)\s+(.+?)"
                r"\s+as my trading strategy$",
                "uses_strategy",
            ),
        ]

        for (
            pattern,
            relation_type,
        ) in patterns:

            match = re.match(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:

                continue

            target = match.group(1)

            return self._build_result(
                relation_type=relation_type,
                target_name=target,
            )

        return None

    # ============================================================
    # EXTRACT
    # ============================================================

    def extract(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        if not text or not text.strip():

            return []

        normalized = (
            self._normalize_text(
                text
            )
        )

        clauses = re.split(
            r"[;\n]+",
            normalized,
        )

        results = []

        seen = set()

        for clause in clauses:

            result = (
                self._extract_clause(
                    clause
                )
            )

            if result is None:

                continue

            key = (
                result[
                    "source_name"
                ].casefold(),
                result[
                    "relation_type"
                ],
                result[
                    "target_name"
                ].casefold(),
                result[
                    "target_type"
                ],
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            results.append(
                result
            )

        return results

    # ============================================================
    # STORE EXTRACTIONS
    # ============================================================

    def _store_extractions(
        self,
        extracted: list[
            dict[str, Any]
        ],
    ) -> list[
        KnowledgeRelationship
    ]:

        stored = []

        for item in extracted:

            relationship = (
                self.manager.connect(
                    source_name=(
                        item[
                            "source_name"
                        ]
                    ),
                    relation_type=(
                        item[
                            "relation_type"
                        ]
                    ),
                    target_name=(
                        item[
                            "target_name"
                        ]
                    ),
                    source_type=(
                        item[
                            "source_type"
                        ]
                    ),
                    target_type=(
                        item[
                            "target_type"
                        ]
                    ),
                    confidence=(
                        item[
                            "confidence"
                        ]
                    ),
                )
            )

            stored.append(
                relationship
            )

        return stored

    # ============================================================
    # STORE
    # ============================================================

    def store(
        self,
        text: str,
    ) -> list[
        KnowledgeRelationship
    ]:

        extracted = self.extract(
            text
        )

        return self._store_extractions(
            extracted
        )

    # ============================================================
    # PROCESS
    # ============================================================

    def process(
        self,
        text: str,
    ) -> dict[str, Any]:

        extracted = self.extract(
            text
        )

        stored = (
            self._store_extractions(
                extracted
            )
        )

        return {
            "extracted": extracted,
            "stored": stored,
        }


graph_extractor = GraphExtractor()