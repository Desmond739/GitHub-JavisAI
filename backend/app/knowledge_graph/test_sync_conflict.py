from __future__ import annotations

from pathlib import Path

import app.memory.long_term.memory_manager as memory_manager_module

from app.memory.long_term.memory_manager import (
    memory_manager,
)

from app.knowledge_graph.graph_extractor import (
    GraphExtractor,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_store import (
    GraphStore,
)

from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
)


TEMP_MEMORY = Path(
    "data/memory/long_term/"
    "test_conflict_memories.json"
)

TEMP_GRAPH = Path(
    "data/knowledge_graph/"
    "test_conflict_graph.json"
)


def divider():

    print(
        "\n"
        + "=" * 70
    )


def main():

    real_memory_path = (
        memory_manager_module
        .long_term_memory
        .storage_path
    )

    real_memory_before = {
        "total": len(
            memory_manager.get_all()
        ),
        "active": len(
            memory_manager.get_active()
        ),
    }

    real_graph_before = (
        graph_manager.counts()
    )

    TEMP_MEMORY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_GRAPH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_MEMORY.unlink(
        missing_ok=True
    )

    TEMP_GRAPH.unlink(
        missing_ok=True
    )

    TEMP_MEMORY.write_text(
        "[]",
        encoding="utf-8",
    )

    try:

        memory_manager_module.long_term_memory.storage_path = (
            TEMP_MEMORY
        )

        store = GraphStore(
            TEMP_GRAPH
        )

        manager = GraphManager(
            store
        )

        extractor = GraphExtractor(
            manager
        )

        sync = (
            PersonalKnowledgeSynchronizer(
                graph_manager_instance=(
                    manager
                ),
                graph_extractor_instance=(
                    extractor
                ),
            )
        )

        # ========================================================
        # EMPLOYMENT — INITIAL
        # ========================================================

        divider()

        print(
            "TEST 1: Initial employment"
        )

        first = sync.process(
            "I work at Company A."
        )

        print(
            "MEMORY:",
            first["memory"]["action"],
        )

        print(
            "GRAPH:",
            first["graph"]["action"],
        )

        # ========================================================
        # EMPLOYMENT — CHANGE
        # ========================================================

        divider()

        print(
            "TEST 2: Employment change"
        )

        second = sync.process(
            "I now work at Company B."
        )

        print(
            "MEMORY:",
            second["memory"]["action"],
        )

        print(
            "GRAPH:",
            second["graph"]["action"],
        )

        print(
            "SUPERSEDED MEMORIES:",
            len(
                second[
                    "memory"
                ][
                    "superseded_memories"
                ]
            ),
        )

        company_a = (
            manager.get_entity(
                "Company A",
                "organization",
            )
        )

        company_b = (
            manager.get_entity(
                "Company B",
                "organization",
            )
        )

        user = manager.get_entity(
            "User",
            "person",
        )

        old_work = (
            store.find_relationships(
                source_node_id=(
                    user.node_id
                ),
                relation_type=(
                    "works_at"
                ),
                target_node_id=(
                    company_a.node_id
                ),
                status=None,
            )
        )

        new_work = (
            store.find_relationships(
                source_node_id=(
                    user.node_id
                ),
                relation_type=(
                    "works_at"
                ),
                target_node_id=(
                    company_b.node_id
                ),
                status=None,
            )
        )

        print(
            "COMPANY A RELATION:",
            [
                (
                    x.status,
                    x.superseded_by,
                )
                for x in old_work
            ],
        )

        print(
            "COMPANY B RELATION:",
            [
                (
                    x.status,
                    x.superseded_by,
                )
                for x in new_work
            ],
        )

        # ========================================================
        # MULTI-VALUE RELATION — LEARNING
        # ========================================================

        divider()

        print(
            "TEST 3: Multi-value learning"
        )

        learning_1 = sync.process(
            "I am learning Python."
        )

        learning_2 = sync.process(
            "I am learning Docker."
        )

        print(
            "PYTHON MEMORY:",
            learning_1[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "DOCKER MEMORY:",
            learning_2[
                "memory"
            ][
                "action"
            ],
        )

        learning_connections = [
            (
                x[
                    "target_name"
                ],
                x[
                    "relation_type"
                ],
            )
            for x in (
                manager.get_connections(
                    "User",
                    "person",
                    direction="outgoing",
                )
            )
            if x[
                "relation_type"
            ] == "learning"
        ]

        print(
            "ACTIVE LEARNING:",
            learning_connections,
        )

        # ========================================================
        # STRATEGY — INITIAL
        # ========================================================

        divider()

        print(
            "TEST 4: Initial strategy"
        )

        strategy_1 = sync.process(
            "My trading strategy is "
            "Strategy A."
        )

        print(
            "MEMORY:",
            strategy_1[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH:",
            strategy_1[
                "graph"
            ][
                "action"
            ],
        )

        # ========================================================
        # STRATEGY — CHANGE
        # ========================================================

        divider()

        print(
            "TEST 5: Strategy change"
        )

        strategy_2 = sync.process(
            "My trading strategy is now "
            "Strategy B."
        )

        print(
            "MEMORY:",
            strategy_2[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH:",
            strategy_2[
                "graph"
            ][
                "action"
            ],
        )

        # ========================================================
        # QUESTION SAFETY
        # ========================================================

        divider()

        print(
            "TEST 6: Question safety"
        )

        memory_before = len(
            memory_manager.get_all()
        )

        graph_before = manager.counts()

        question = sync.process(
            "What is Company B?"
        )

        memory_after = len(
            memory_manager.get_all()
        )

        graph_after = manager.counts()

        print(
            "MEMORY:",
            question[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH:",
            question[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "UNCHANGED:",
            (
                memory_before
                == memory_after
                and graph_before
                == graph_after
            ),
        )

        # ========================================================
        # FINAL MEMORY STATE
        # ========================================================

        divider()

        print(
            "FINAL TEMP MEMORY:",
            {
                "total": len(
                    memory_manager.get_all()
                ),
                "active": len(
                    memory_manager.get_active()
                ),
            },
        )

        print(
            "MEMORY CONTENTS:"
        )

        for memory in (
            memory_manager.get_all()
        ):

            print(
                "-",
                memory.status,
                "|",
                memory.content,
                "| superseded_by:",
                memory.superseded_by,
            )

        # ========================================================
        # FINAL GRAPH STATE
        # ========================================================

        divider()

        print(
            "FINAL TEMP GRAPH:",
            manager.counts(),
        )

        print(
            "ALL RELATIONSHIPS:"
        )

        for relationship in (
            store.get_all_relationships()
        ):

            source = store.get_node(
                relationship
                .source_node_id
            )

            target = store.get_node(
                relationship
                .target_node_id
            )

            print(
                "-",
                source.name,
                "--"
                + relationship
                .relation_type
                + "-->",
                target.name,
                "|",
                relationship.status,
                "| superseded_by:",
                relationship
                .superseded_by,
            )

    finally:

        memory_manager_module.long_term_memory.storage_path = (
            real_memory_path
        )

        TEMP_MEMORY.unlink(
            missing_ok=True
        )

        TEMP_GRAPH.unlink(
            missing_ok=True
        )

    divider()

    real_memory_after = {
        "total": len(
            memory_manager.get_all()
        ),
        "active": len(
            memory_manager.get_active()
        ),
    }

    real_graph_after = (
        graph_manager.counts()
    )

    print(
        "REAL MEMORY BEFORE:",
        real_memory_before,
    )

    print(
        "REAL MEMORY AFTER:",
        real_memory_after,
    )

    print(
        "REAL GRAPH BEFORE:",
        real_graph_before,
    )

    print(
        "REAL GRAPH AFTER:",
        real_graph_after,
    )

    print(
        "REAL MEMORY UNCHANGED:",
        (
            real_memory_before
            == real_memory_after
        ),
    )

    print(
        "REAL GRAPH UNCHANGED:",
        (
            real_graph_before
            == real_graph_after
        ),
    )

    print(
        "TEMP MEMORY DELETED:",
        not TEMP_MEMORY.exists(),
    )

    print(
        "TEMP GRAPH DELETED:",
        not TEMP_GRAPH.exists(),
    )


if __name__ == "__main__":

    main()