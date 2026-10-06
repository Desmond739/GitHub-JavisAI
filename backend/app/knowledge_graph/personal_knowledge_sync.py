from __future__ import annotations

import re

from typing import Any

import app.memory.long_term.memory_manager as memory_manager_module

from app.memory.long_term.memory_extractor import (
    memory_extractor,
)

from app.memory.long_term.memory_manager import (
    memory_manager,
)

from app.knowledge_graph.graph_extractor import (
    GraphExtractor,
    graph_extractor,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)


class PersonalKnowledgeSynchronizer:

    RELATION_MEMORY_CATEGORIES = {
        "works_at": "career",
        "has_role": "career",
        "works_in_department": "career",
        "has_career_goal": "career",

        "learning": "technical",
        "studied": "technical",
        "interested_in": "technical",
        "building": "technical",

        "trades": "trading",
        "uses_strategy": "trading",
    }

    # Relationships which may represent one current state.
    #
    # IMPORTANT:
    # They are superseded only when the user explicitly
    # communicates a change.
    EXCLUSIVE_RELATIONS = {
        "works_at",
        "has_role",
        "works_in_department",
        "uses_strategy",
    }

    CHANGE_PATTERNS = (
        r"\bnow\b",
        r"\bchanged\s+to\b",
        r"\bchanged\s+from\b",
        r"\bswitched\s+to\b",
        r"\bmoved\s+to\b",
        r"\binstead\s+of\b",
    )

    def __init__(
        self,
        graph_manager_instance: GraphManager | None = None,
        graph_extractor_instance: GraphExtractor | None = None,
    ):

        self.memory_extractor = (
            memory_extractor
        )

        self.memory_manager = (
            memory_manager
        )

        self.graph_manager = (
            graph_manager_instance
            if graph_manager_instance is not None
            else graph_manager
        )

        self.graph_extractor = (
            graph_extractor_instance
            if graph_extractor_instance is not None
            else (
                graph_extractor
                if graph_manager_instance is None
                else GraphExtractor(
                    self.graph_manager
                )
            )
        )

    # ============================================================
    # MEMORY OBJECT -> DICT
    # ============================================================

    @staticmethod
    def _memory_to_dict(
        memory,
    ) -> dict[str, Any] | None:

        if memory is None:

            return None

        return {
            "memory_id": getattr(
                memory,
                "memory_id",
                None,
            ),
            "memory_type": getattr(
                memory,
                "memory_type",
                None,
            ),
            "category": getattr(
                memory,
                "category",
                None,
            ),
            "content": getattr(
                memory,
                "content",
                None,
            ),
            "importance": getattr(
                memory,
                "importance",
                None,
            ),
            "status": getattr(
                memory,
                "status",
                None,
            ),
            "superseded_by": getattr(
                memory,
                "superseded_by",
                None,
            ),
        }

    # ============================================================
    # EXPLICIT CHANGE DETECTION
    # ============================================================

    def _has_change_intent(
        self,
        text: str,
    ) -> bool:

        lowered = text.casefold()

        return any(
            re.search(
                pattern,
                lowered,
            )
            is not None
            for pattern
            in self.CHANGE_PATTERNS
        )

    # ============================================================
    # NORMALIZE CHANGE STATEMENTS FOR GRAPH EXTRACTION
    # ============================================================

    @staticmethod
    def _normalize_change_statement(
        text: str,
    ) -> str:

        value = text.strip()

        replacements = (
            (
                r"^\s*i\s+now\s+work\s+at\s+",
                "I work at ",
            ),
            (
                r"^\s*i\s+am\s+now\s+working\s+at\s+",
                "I am working at ",
            ),
            (
                r"^\s*i'm\s+now\s+working\s+at\s+",
                "I'm working at ",
            ),
            (
                r"^\s*i\s+now\s+work\s+as\s+",
                "I work as ",
            ),
            (
                r"^\s*i\s+am\s+now\s+working\s+as\s+",
                "I am working as ",
            ),
            (
                r"^\s*i'm\s+now\s+working\s+as\s+",
                "I'm working as ",
            ),
            (
                r"^\s*my\s+trading\s+strategy\s+is\s+now\s+",
                "My trading strategy is ",
            ),
            (
                r"^\s*i\s+changed\s+my\s+trading\s+strategy\s+to\s+",
                "My trading strategy is ",
            ),
            (
                r"^\s*i\s+have\s+changed\s+my\s+trading\s+strategy\s+to\s+",
                "My trading strategy is ",
            ),
            (
                r"^\s*i\s+switched\s+my\s+trading\s+strategy\s+to\s+",
                "My trading strategy is ",
            ),
        )

        for pattern, replacement in replacements:

            updated = re.sub(
                pattern,
                replacement,
                value,
                count=1,
                flags=re.IGNORECASE,
            )

            if updated != value:

                return updated

        return value

    # ============================================================
    # EXTRACT GRAPH KNOWLEDGE
    # ============================================================

    def _extract_graph_knowledge(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        normalized = (
            self._normalize_change_statement(
                text
            )
        )

        return self.graph_extractor.extract(
            normalized
        )

    # ============================================================
    # GRAPH-ASSISTED MEMORY
    # ============================================================

    def _derive_memory_from_graph(
        self,
        text: str,
        graph_items: list[
            dict[str, Any]
        ] | None = None,
    ) -> dict[str, Any] | None:

        if graph_items is None:

            graph_items = (
                self._extract_graph_knowledge(
                    text
                )
            )

        if not graph_items:

            return None

        for item in graph_items:

            category = (
                self.RELATION_MEMORY_CATEGORIES
                .get(
                    item[
                        "relation_type"
                    ]
                )
            )

            if category is None:

                continue

            return {
                "memory_type": "fact",
                "category": category,
                "content": text.strip(),
                "importance": 6,
                "derived_from_graph": True,
            }

        return None

    # ============================================================
    # EXTRACT MEMORY
    # ============================================================

    def _extract_memory(
        self,
        text: str,
        graph_items: list[
            dict[str, Any]
        ] | None = None,
    ) -> dict[str, Any] | None:

        extracted = (
            self.memory_extractor.extract(
                text
            )
        )

        if extracted is not None:

            result = dict(
                extracted
            )

            result[
                "derived_from_graph"
            ] = False

            return result

        return self._derive_memory_from_graph(
            text=text,
            graph_items=graph_items,
        )

    # ============================================================
    # PLAN GRAPH CHANGES
    # ============================================================

    def _plan_graph_changes(
        self,
        text: str,
    ) -> list[dict[str, Any]]:

        extracted = (
            self._extract_graph_knowledge(
                text
            )
        )

        change_intent = (
            self._has_change_intent(
                text
            )
        )

        plan = []

        for item in extracted:

            source = (
                self.graph_manager.get_entity(
                    name=item[
                        "source_name"
                    ],
                    node_type=item[
                        "source_type"
                    ],
                )
            )

            target = (
                self.graph_manager.get_entity(
                    name=item[
                        "target_name"
                    ],
                    node_type=item[
                        "target_type"
                    ],
                )
            )

            existing_exact = []

            if (
                source is not None
                and target is not None
            ):

                existing_exact = (
                    self.graph_manager.store
                    .find_relationships(
                        source_node_id=(
                            source.node_id
                        ),
                        relation_type=(
                            item[
                                "relation_type"
                            ]
                        ),
                        target_node_id=(
                            target.node_id
                        ),
                        status="active",
                    )
                )

            conflicts = []

            if (
                change_intent
                and item[
                    "relation_type"
                ]
                in self.EXCLUSIVE_RELATIONS
                and source is not None
            ):

                active_same_relation = (
                    self.graph_manager.store
                    .find_relationships(
                        source_node_id=(
                            source.node_id
                        ),
                        relation_type=(
                            item[
                                "relation_type"
                            ]
                        ),
                        status="active",
                    )
                )

                for relationship in (
                    active_same_relation
                ):

                    old_target = (
                        self.graph_manager.store
                        .get_node(
                            relationship
                            .target_node_id
                        )
                    )

                    if old_target is None:

                        continue

                    if (
                        old_target.name
                        .casefold()
                        ==
                        item[
                            "target_name"
                        ]
                        .casefold()
                    ):

                        continue

                    conflicts.append(
                        {
                            "relationship_id": (
                                relationship
                                .relationship_id
                            ),
                            "old_target_name": (
                                old_target.name
                            ),
                            "old_target_type": (
                                old_target
                                .node_type
                            ),
                        }
                    )

            plan.append(
                {
                    "item": item,
                    "existing_exact": bool(
                        existing_exact
                    ),
                    "conflicts": conflicts,
                    "change_intent": (
                        change_intent
                    ),
                }
            )

        return plan

    # ============================================================
    # FIND MEMORIES REPRESENTING OLD GRAPH STATE
    # ============================================================

    def _find_semantic_memory_conflicts(
        self,
        graph_plan: list[
            dict[str, Any]
        ],
        new_memory_id: str,
    ):

        old_semantics = set()

        for entry in graph_plan:

            item = entry[
                "item"
            ]

            for conflict in entry[
                "conflicts"
            ]:

                old_semantics.add(
                    (
                        item[
                            "source_name"
                        ].casefold(),
                        item[
                            "relation_type"
                        ],
                        conflict[
                            "old_target_name"
                        ].casefold(),
                    )
                )

        if not old_semantics:

            return []

        matches = []

        for memory in (
            self.memory_manager
            .get_active()
        ):

            if (
                memory.memory_id
                == new_memory_id
            ):

                continue

            memory_graph_items = (
                self._extract_graph_knowledge(
                    memory.content
                )
            )

            for item in memory_graph_items:

                semantic_key = (
                    item[
                        "source_name"
                    ].casefold(),
                    item[
                        "relation_type"
                    ],
                    item[
                        "target_name"
                    ].casefold(),
                )

                if (
                    semantic_key
                    not in old_semantics
                ):

                    continue

                matches.append(
                    memory
                )

                break

        return matches

    # ============================================================
    # PREVIEW MEMORY
    # ============================================================

    def preview_memory(
        self,
        text: str,
    ) -> dict[str, Any]:

        graph_items = (
            self._extract_graph_knowledge(
                text
            )
        )

        extracted = (
            self._extract_memory(
                text=text,
                graph_items=graph_items,
            )
        )

        if extracted is None:

            return {
                "action": "ignored",
                "extracted": None,
            }

        return {
            "action": "would_process",
            "extracted": extracted,
        }

    # ============================================================
    # PREVIEW GRAPH
    # ============================================================

    def preview_graph(
        self,
        text: str,
    ) -> dict[str, Any]:

        plan = (
            self._plan_graph_changes(
                text
            )
        )

        if not plan:

            return {
                "action": "ignored",
                "extracted": [],
                "relationships": [],
            }

        relationships = []

        for entry in plan:

            item = entry[
                "item"
            ]

            if entry["conflicts"]:

                action = (
                    "would_supersede"
                )

            elif entry[
                "existing_exact"
            ]:

                action = (
                    "would_reuse"
                )

            else:

                action = (
                    "would_create"
                )

            relationships.append(
                {
                    "source_name": (
                        item[
                            "source_name"
                        ]
                    ),
                    "relation_type": (
                        item[
                            "relation_type"
                        ]
                    ),
                    "target_name": (
                        item[
                            "target_name"
                        ]
                    ),
                    "action": action,
                    "conflicts": (
                        entry[
                            "conflicts"
                        ]
                    ),
                }
            )

        return {
            "action": "would_process",
            "extracted": [
                entry["item"]
                for entry in plan
            ],
            "relationships": (
                relationships
            ),
        }

    # ============================================================
    # PREVIEW
    # ============================================================

    def preview(
        self,
        text: str,
    ) -> dict[str, Any]:

        if not text or not text.strip():

            return {
                "memory": {
                    "action": "ignored",
                    "extracted": None,
                },
                "graph": {
                    "action": "ignored",
                    "extracted": [],
                    "relationships": [],
                },
            }

        return {
            "memory": (
                self.preview_memory(
                    text
                )
            ),
            "graph": (
                self.preview_graph(
                    text
                )
            ),
        }

    # ============================================================
    # PROCESS MEMORY
    # ============================================================

    def _process_memory(
        self,
        text: str,
        graph_plan: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        graph_items = [
            entry["item"]
            for entry in graph_plan
        ]

        extracted = (
            self._extract_memory(
                text=text,
                graph_items=graph_items,
            )
        )

        if extracted is None:

            return {
                "action": "ignored",
                "memory": None,
                "superseded_memory": None,
                "superseded_memories": [],
                "extracted": None,
            }

        result = (
            self.memory_manager
            .remember_intelligently(
                memory_type=(
                    extracted[
                        "memory_type"
                    ]
                ),
                category=(
                    extracted[
                        "category"
                    ]
                ),
                content=(
                    extracted[
                        "content"
                    ]
                ),
                importance=(
                    extracted[
                        "importance"
                    ]
                ),
            )
        )

        new_memory = result.get(
            "memory"
        )

        superseded_memories = []

        manager_superseded = (
            result.get(
                "superseded_memory"
            )
        )

        if manager_superseded is not None:

            superseded_memories.append(
                manager_superseded
            )

        # --------------------------------------------------------
        # Semantic fact supersession from graph conflicts.
        # --------------------------------------------------------

        if new_memory is not None:

            semantic_conflicts = (
                self
                ._find_semantic_memory_conflicts(
                    graph_plan=graph_plan,
                    new_memory_id=(
                        new_memory.memory_id
                    ),
                )
            )

            already_superseded_ids = {
                memory.memory_id
                for memory
                in superseded_memories
            }

            for old_memory in (
                semantic_conflicts
            ):

                if (
                    old_memory.memory_id
                    in already_superseded_ids
                ):

                    continue

                superseded = (
                    memory_manager_module
                    .long_term_memory
                    .supersede_memory(
                        old_memory_id=(
                            old_memory
                            .memory_id
                        ),
                        new_memory_id=(
                            new_memory
                            .memory_id
                        ),
                    )
                )

                if superseded is not None:

                    superseded_memories.append(
                        superseded
                    )

                    already_superseded_ids.add(
                        superseded
                        .memory_id
                    )

        final_action = (
            "superseded"
            if superseded_memories
            else result[
                "action"
            ]
        )

        return {
            "action": final_action,
            "base_action": (
                result[
                    "action"
                ]
            ),
            "memory": (
                self._memory_to_dict(
                    new_memory
                )
            ),
            "superseded_memory": (
                self._memory_to_dict(
                    superseded_memories[0]
                )
                if superseded_memories
                else None
            ),
            "superseded_memories": [
                self._memory_to_dict(
                    memory
                )
                for memory
                in superseded_memories
            ],
            "extracted": extracted,
        }

    # ============================================================
    # PROCESS GRAPH
    # ============================================================

    def _process_graph(
        self,
        graph_plan: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        if not graph_plan:

            return {
                "action": "ignored",
                "relationships": [],
                "extracted": [],
            }

        results = []

        any_created = False
        any_superseded = False

        for entry in graph_plan:

            item = entry[
                "item"
            ]

            conflicts = entry[
                "conflicts"
            ]

            if conflicts:

                new_relationship = None

                superseded_records = []

                for conflict in conflicts:

                    result = (
                        self.graph_manager
                        .supersede_connection(
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
                            old_target_name=(
                                conflict[
                                    "old_target_name"
                                ]
                            ),
                            new_target_name=(
                                item[
                                    "target_name"
                                ]
                            ),
                            source_type=(
                                item[
                                    "source_type"
                                ]
                            ),
                            old_target_type=(
                                conflict[
                                    "old_target_type"
                                ]
                            ),
                            new_target_type=(
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

                    new_relationship = (
                        result[
                            "new_relationship"
                        ]
                    )

                    for relationship in (
                        result[
                            "superseded"
                        ]
                    ):

                        if relationship is None:

                            continue

                        superseded_records.append(
                            {
                                "relationship_id": (
                                    relationship
                                    .relationship_id
                                ),
                                "status": (
                                    relationship
                                    .status
                                ),
                                "superseded_by": (
                                    relationship
                                    .superseded_by
                                ),
                            }
                        )

                any_superseded = True

                results.append(
                    {
                        "action": (
                            "superseded"
                        ),
                        "relationship_id": (
                            new_relationship
                            .relationship_id
                            if new_relationship
                            is not None
                            else None
                        ),
                        "source_name": (
                            item[
                                "source_name"
                            ]
                        ),
                        "relation_type": (
                            item[
                                "relation_type"
                            ]
                        ),
                        "target_name": (
                            item[
                                "target_name"
                            ]
                        ),
                        "status": (
                            new_relationship
                            .status
                            if new_relationship
                            is not None
                            else None
                        ),
                        "superseded": (
                            superseded_records
                        ),
                    }
                )

                continue

            relationship = (
                self.graph_manager.connect(
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

            action = (
                "reused"
                if entry[
                    "existing_exact"
                ]
                else "created"
            )

            if action == "created":

                any_created = True

            results.append(
                {
                    "action": action,
                    "relationship_id": (
                        relationship
                        .relationship_id
                    ),
                    "source_name": (
                        item[
                            "source_name"
                        ]
                    ),
                    "relation_type": (
                        relationship
                        .relation_type
                    ),
                    "target_name": (
                        item[
                            "target_name"
                        ]
                    ),
                    "status": (
                        relationship.status
                    ),
                    "superseded": [],
                }
            )

        if any_superseded:

            overall_action = (
                "superseded"
            )

        elif any_created:

            overall_action = (
                "created"
            )

        else:

            overall_action = (
                "reused"
            )

        return {
            "action": overall_action,
            "relationships": results,
            "extracted": [
                entry["item"]
                for entry in graph_plan
            ],
        }

    # ============================================================
    # PROCESS
    # ============================================================

    def process(
        self,
        text: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:

        if not text or not text.strip():

            return {
                "dry_run": dry_run,
                "memory": {
                    "action": "ignored",
                },
                "graph": {
                    "action": "ignored",
                },
            }

        if dry_run:

            preview = self.preview(
                text
            )

            return {
                "dry_run": True,
                "memory": (
                    preview[
                        "memory"
                    ]
                ),
                "graph": (
                    preview[
                        "graph"
                    ]
                ),
            }

        # Read-only plan first.
        graph_plan = (
            self._plan_graph_changes(
                text
            )
        )

        memory_result = (
            self._process_memory(
                text=text,
                graph_plan=graph_plan,
            )
        )

        graph_result = (
            self._process_graph(
                graph_plan
            )
        )

        return {
            "dry_run": False,
            "memory": memory_result,
            "graph": graph_result,
        }


personal_knowledge_sync = (
    PersonalKnowledgeSynchronizer()
)