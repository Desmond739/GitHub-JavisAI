from __future__ import annotations

from pathlib import Path

import app.memory.long_term.memory_manager as memory_manager_module

from app.memory.long_term.memory_manager import (
    memory_manager,
)

from app.agents.agent_coordinator import (
    AgentCoordinator,
)

from app.knowledge_graph.graph_store import (
    GraphStore,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_extractor import (
    GraphExtractor,
)

from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
)


TEMP_MEMORY = Path(
    "data/memory/long_term/"
    "test_agent_sync_memories.json"
)

TEMP_GRAPH = Path(
    "data/knowledge_graph/"
    "test_agent_sync_graph.json"
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

        coordinator = AgentCoordinator(
            knowledge_sync_instance=sync
        )

        print(
            "SYNC TYPE:",
            type(
                coordinator.knowledge_sync
            ).__name__,
        )

        result = (
            coordinator
            ._synchronize_personal_knowledge(
                "I trade Forex."
            )
        )

        print(
            "MEMORY ACTION:",
            result[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "GRAPH ACTION:",
            result[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "TEMP MEMORY:",
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
            "TEMP GRAPH:",
            manager.counts(),
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
                for item in (
                    manager.get_connections(
                        "User",
                        "person",
                        direction="outgoing",
                    )
                )
            ],
        )

        question_before_memory = len(
            memory_manager.get_all()
        )

        question_before_graph = (
            manager.counts()
        )

        question_result = (
            coordinator
            ._synchronize_personal_knowledge(
                "What is Forex?"
            )
        )

        print(
            "QUESTION MEMORY:",
            question_result[
                "memory"
            ][
                "action"
            ],
        )

        print(
            "QUESTION GRAPH:",
            question_result[
                "graph"
            ][
                "action"
            ],
        )

        print(
            "QUESTION UNCHANGED:",
            (
                question_before_memory
                == len(
                    memory_manager.get_all()
                )
                and question_before_graph
                == manager.counts()
            ),
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