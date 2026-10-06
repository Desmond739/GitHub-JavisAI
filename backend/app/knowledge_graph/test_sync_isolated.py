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


TEMP_MEMORY_PATH = Path(
    "data/memory/long_term/test_sync_memories.json"
)

TEMP_GRAPH_PATH = Path(
    "data/knowledge_graph/test_sync_graph.json"
)


def print_separator() -> None:

    print(
        "\n"
        + "=" * 70
    )


def main() -> None:

    # ============================================================
    # RECORD REAL SYSTEM STATE
    # ============================================================

    real_memory_path = (
        memory_manager_module
        .long_term_memory
        .storage_path
    )

    real_memory_total_before = len(
        memory_manager.get_all()
    )

    real_memory_active_before = len(
        memory_manager.get_active()
    )

    real_graph_before = (
        graph_manager.counts()
    )

    print(
        "REAL MEMORY PATH:",
        real_memory_path,
    )

    print(
        "REAL MEMORY BEFORE:",
        {
            "total": (
                real_memory_total_before
            ),
            "active": (
                real_memory_active_before
            ),
        },
    )

    print(
        "REAL GRAPH BEFORE:",
        real_graph_before,
    )

    # ============================================================
    # PREPARE TEMPORARY STORAGE
    # ============================================================

    TEMP_MEMORY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_GRAPH_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_MEMORY_PATH.unlink(
        missing_ok=True
    )

    TEMP_GRAPH_PATH.unlink(
        missing_ok=True
    )

    # LongTermMemoryStore expects JSON list storage.
    TEMP_MEMORY_PATH.write_text(
        "[]",
        encoding="utf-8",
    )

    try:

        # ========================================================
        # REDIRECT MEMORY STORE FOR THIS PROCESS ONLY
        # ========================================================

        memory_manager_module.long_term_memory.storage_path = (
            TEMP_MEMORY_PATH
        )

        # ========================================================
        # CREATE ISOLATED GRAPH
        # ========================================================

        temp_store = GraphStore(
            TEMP_GRAPH_PATH
        )

        temp_graph_manager = GraphManager(
            temp_store
        )

        temp_graph_extractor = GraphExtractor(
            temp_graph_manager
        )

        synchronizer = (
            PersonalKnowledgeSynchronizer(
                graph_manager_instance=(
                    temp_graph_manager
                ),
                graph_extractor_instance=(
                    temp_graph_extractor
                ),
            )
        )

        print_separator()

        print(
            "TEMP MEMORY PATH:",
            memory_manager_module
            .long_term_memory
            .storage_path,
        )

        print(
            "TEMP GRAPH PATH:",
            TEMP_GRAPH_PATH,
        )

        # ========================================================
        # TEST 1 — NEW SYNCHRONIZED KNOWLEDGE
        # ========================================================

        statement = (
            "I am learning Docker."
        )

        print_separator()

        print(
            "TEST 1:",
            statement,
        )

        result_1 = (
            synchronizer.process(
                statement
            )
        )

        print(
            "MEMORY ACTION:",
            result_1[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result_1[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "TEMP MEMORY:",
            {
                "total": len(
                    memory_manager
                    .get_all()
                ),
                "active": len(
                    memory_manager
                    .get_active()
                ),
            },
        )

        print(
            "TEMP GRAPH:",
            temp_graph_manager
            .counts(),
        )

        docker_connections = (
            temp_graph_manager
            .get_connections(
                "User",
                "person",
                direction="outgoing",
            )
        )

        print(
            "CONNECTIONS:",
            [
                (
                    item[
                        "relation_type"
                    ],
                    item[
                        "target_name"
                    ],
                )
                for item
                in docker_connections
            ],
        )

        # ========================================================
        # TEST 2 — DUPLICATE / REINFORCEMENT
        # ========================================================

        print_separator()

        print(
            "TEST 2: Repeat same statement"
        )

        before_memory = len(
            memory_manager.get_all()
        )

        before_graph = (
            temp_graph_manager.counts()
        )

        result_2 = (
            synchronizer.process(
                statement
            )
        )

        after_memory = len(
            memory_manager.get_all()
        )

        after_graph = (
            temp_graph_manager.counts()
        )

        print(
            "MEMORY ACTION:",
            result_2[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result_2[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "MEMORY COUNT UNCHANGED:",
            (
                before_memory
                == after_memory
            ),
        )

        print(
            "GRAPH COUNT UNCHANGED:",
            (
                before_graph
                == after_graph
            ),
        )

        # ========================================================
        # TEST 3 — QUESTION REJECTION
        # ========================================================

        print_separator()

        question = (
            "What is Docker?"
        )

        print(
            "TEST 3:",
            question,
        )

        before_memory = len(
            memory_manager.get_all()
        )

        before_graph = (
            temp_graph_manager.counts()
        )

        result_3 = (
            synchronizer.process(
                question
            )
        )

        after_memory = len(
            memory_manager.get_all()
        )

        after_graph = (
            temp_graph_manager.counts()
        )

        print(
            "MEMORY ACTION:",
            result_3[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result_3[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "UNCHANGED:",
            (
                before_memory
                == after_memory
                and before_graph
                == after_graph
            ),
        )

        # ========================================================
        # TEST 4 — SECOND KNOWLEDGE ITEM
        # ========================================================

        print_separator()

        statement_2 = (
            "I am building a "
            "Network Monitoring Platform."
        )

        print(
            "TEST 4:",
            statement_2,
        )

        result_4 = (
            synchronizer.process(
                statement_2
            )
        )

        print(
            "MEMORY ACTION:",
            result_4[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result_4[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "TEMP MEMORY:",
            {
                "total": len(
                    memory_manager
                    .get_all()
                ),
                "active": len(
                    memory_manager
                    .get_active()
                ),
            },
        )

        print(
            "TEMP GRAPH:",
            temp_graph_manager
            .counts(),
        )

        # ========================================================
        # TEST 5 — GRAPH-ONLY KNOWLEDGE CURRENTLY
        # ========================================================

        print_separator()

        trading_statement = (
            "I trade Forex."
        )

        print(
            "TEST 5:",
            trading_statement,
        )

        result_5 = (
            synchronizer.process(
                trading_statement
            )
        )

        print(
            "MEMORY ACTION:",
            result_5[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result_5[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "EXPECTED CURRENT BEHAVIOR:",
            "memory=ignored, graph=created",
        )

        # ========================================================
        # FINAL TEMPORARY STATE
        # ========================================================

        print_separator()

        print(
            "FINAL TEMP MEMORY:",
            {
                "total": len(
                    memory_manager
                    .get_all()
                ),
                "active": len(
                    memory_manager
                    .get_active()
                ),
            },
        )

        print(
            "FINAL TEMP GRAPH:",
            temp_graph_manager
            .counts(),
        )

        print(
            "\nTEMP MEMORY CONTENTS:"
        )

        for memory in (
            memory_manager.get_all()
        ):

            print(
                "-",
                memory.status,
                "|",
                memory.memory_type,
                "|",
                memory.category,
                "|",
                memory.content,
            )

        print(
            "\nTEMP GRAPH CONNECTIONS:"
        )

        connections = (
            temp_graph_manager
            .get_connections(
                "User",
                "person",
                direction="outgoing",
            )
        )

        for connection in connections:

            print(
                "- User --{}--> {}".format(
                    connection[
                        "relation_type"
                    ],
                    connection[
                        "target_name"
                    ],
                )
            )

    finally:

        # ========================================================
        # ALWAYS RESTORE REAL MEMORY STORAGE
        # ========================================================

        memory_manager_module.long_term_memory.storage_path = (
            real_memory_path
        )

        # ========================================================
        # DELETE TEST FILES
        # ========================================================

        TEMP_MEMORY_PATH.unlink(
            missing_ok=True
        )

        TEMP_GRAPH_PATH.unlink(
            missing_ok=True
        )

    # ============================================================
    # VERIFY REAL SYSTEM AFTER TEST
    # ============================================================

    print_separator()

    real_memory_total_after = len(
        memory_manager.get_all()
    )

    real_memory_active_after = len(
        memory_manager.get_active()
    )

    real_graph_after = (
        graph_manager.counts()
    )

    print(
        "REAL MEMORY AFTER:",
        {
            "total": (
                real_memory_total_after
            ),
            "active": (
                real_memory_active_after
            ),
        },
    )

    print(
        "REAL GRAPH AFTER:",
        real_graph_after,
    )

    print(
        "REAL MEMORY UNCHANGED:",
        (
            real_memory_total_before
            == real_memory_total_after
            and real_memory_active_before
            == real_memory_active_after
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
        not TEMP_MEMORY_PATH.exists(),
    )

    print(
        "TEMP GRAPH DELETED:",
        not TEMP_GRAPH_PATH.exists(),
    )


if __name__ == "__main__":

    main()