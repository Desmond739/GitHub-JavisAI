from __future__ import annotations

from pathlib import Path
from typing import Any

import app.memory.long_term.memory_manager as memory_manager_module

from app.memory.long_term.long_term_memory import (
    LongTermMemoryStore,
)

from app.memory.long_term.memory_manager import (
    memory_manager,
)

from app.agents.agent_coordinator import (
    AgentCoordinator,
    agent_coordinator,
)

from app.knowledge_graph.entity_resolver import (
    entity_resolver,
)

from app.knowledge_graph.graph_context import (
    graph_context,
)

from app.knowledge_graph.graph_extractor import (
    GraphExtractor,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_reasoner import (
    GraphReasoner,
    graph_reasoner,
)

from app.knowledge_graph.graph_store import (
    GraphStore,
)

from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
)


TEMP_MEMORY = Path(
    "data/memory/long_term/"
    "phase22_final_test_memories.json"
)

TEMP_GRAPH = Path(
    "data/knowledge_graph/"
    "phase22_final_test_graph.json"
)


passes = 0
failures: list[str] = []


def divider(
    title: str,
) -> None:

    print(
        "\n"
        + "=" * 72
    )

    print(
        title
    )

    print(
        "=" * 72
    )


def check(
    name: str,
    condition: bool,
    details: Any = None,
) -> None:

    global passes

    if condition:

        passes += 1

        print(
            f"[PASS] {name}"
        )

        return

    failures.append(
        name
    )

    print(
        f"[FAIL] {name}"
    )

    if details is not None:

        print(
            "       DETAILS:",
            details,
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

    # ============================================================
    # 1. REAL PERSISTENT STATE
    # ============================================================

    divider(
        "1. REAL PERSISTENT STATE"
    )

    check(
        "Real memory baseline is 24 total / 24 active",
        (
            real_memory_before["total"] == 24
            and real_memory_before["active"] == 24
        ),
        real_memory_before,
    )

    check(
        "Real graph baseline is 24 nodes / 29 relationships",
        (
            real_graph_before[
                "nodes"
            ] == 24
            and real_graph_before[
                "active_nodes"
            ] == 24
            and real_graph_before[
                "relationships"
            ] == 29
            and real_graph_before[
                "active_relationships"
            ] == 29
        ),
        real_graph_before,
    )

    # ============================================================
    # 2. ENTITY RESOLUTION
    # ============================================================

    divider(
        "2. ENTITY RESOLUTION"
    )

    jarvis = entity_resolver.resolve(
        "JARVIS"
    )

    mtnc = entity_resolver.resolve(
        "MTNC"
    )

    qwen = entity_resolver.resolve(
        "Qwen 3"
    )

    check(
        "JARVIS resolves to MoneroAI",
        (
            jarvis is not None
            and jarvis[
                "canonical_name"
            ] == "MoneroAI"
        ),
        jarvis,
    )

    check(
        "MTNC resolves to MTN Cameroon",
        (
            mtnc is not None
            and mtnc[
                "canonical_name"
            ] == "MTN Cameroon"
        ),
        mtnc,
    )

    check(
        "Qwen 3 resolves to Qwen3",
        (
            qwen is not None
            and qwen[
                "canonical_name"
            ] == "Qwen3"
        ),
        qwen,
    )

    # ============================================================
    # 3. MULTI-HOP GRAPH REASONING
    # ============================================================

    divider(
        "3. MULTI-HOP GRAPH REASONING"
    )

    python_answer = (
        graph_reasoner.reason(
            "How is Python connected to me?"
        )
    )

    cybersecurity_answer = (
        graph_reasoner.reason(
            "How is Cybersecurity "
            "connected to my education?"
        )
    )

    forex_answer = (
        graph_reasoner.reason(
            "How is Forex connected "
            "to my trading strategy?"
        )
    )

    check(
        "User → MoneroAI → Python reasoning",
        (
            python_answer is not None
            and "MoneroAI"
            in python_answer
            and "Python"
            in python_answer
        ),
        python_answer,
    )

    check(
        "Education → Cybersecurity reasoning",
        (
            cybersecurity_answer is not None
            and "Network and Security"
            in cybersecurity_answer
            and "Cybersecurity"
            in cybersecurity_answer
        ),
        cybersecurity_answer,
    )

    check(
        "Support and Resistance → Forex reasoning",
        (
            forex_answer is not None
            and "Support and Resistance"
            in forex_answer
            and "Forex"
            in forex_answer
        ),
        forex_answer,
    )

    # ============================================================
    # 4. DIRECT PERSONAL REASONING
    # ============================================================

    divider(
        "4. DIRECT PERSONAL REASONING"
    )

    projects = graph_reasoner.reason(
        "What projects am I building?"
    )

    strategy = graph_reasoner.reason(
        "What is my trading strategy?"
    )

    workplace = graph_reasoner.reason(
        "Where do I work?"
    )

    role = graph_reasoner.reason(
        "What is my role?"
    )

    check(
        "Project reasoning returns both projects",
        (
            projects is not None
            and "MoneroAI"
            in projects
            and "Smart Home IoT System"
            in projects
        ),
        projects,
    )

    check(
        "Trading strategy reasoning returns Support and Resistance",
        (
            strategy is not None
            and "Support and Resistance"
            in strategy
        ),
        strategy,
    )

    check(
        "Workplace reasoning returns MTN Cameroon",
        (
            workplace is not None
            and "MTN Cameroon"
            in workplace
        ),
        workplace,
    )

    check(
        "Role reasoning returns Product & Service Intern",
        (
            role is not None
            and "Product & Service Intern"
            in role
        ),
        role,
    )

    # ============================================================
    # 5. GRAPH CONTEXT
    # ============================================================

    divider(
        "5. GRAPH CONTEXT"
    )

    python_context = graph_context.build(
        "How is Python connected to me?"
    )

    check(
        "Relevant graph context is generated",
        (
            bool(
                python_context
            )
            and "MoneroAI"
            in python_context
            and "Python"
            in python_context
        ),
        python_context,
    )

    general_context = graph_context.build(
        "What is the capital of France?"
    )

    check(
        "General question gets no personal graph context",
        general_context == "",
        repr(
            general_context
        ),
    )

    # ============================================================
    # 6. AGENT ROUTING
    # ============================================================

    divider(
        "6. AGENT ROUTING"
    )

    check(
        "General knowledge routes to GENERAL_AGENT",
        (
            agent_coordinator.route(
                "What is the capital of France?"
            )
            == "GENERAL_AGENT"
        ),
    )

    check(
        "Trading routes to Trading Agent",
        (
            agent_coordinator.route(
                "What is my trading strategy?"
            )
            == "Trading Agent"
        ),
    )

    check(
        "Career routes to Career Agent",
        (
            agent_coordinator.route(
                "What should I focus on "
                "in my career?"
            )
            == "Career Agent"
        ),
    )

    check(
        "Finance routes to Finance Agent",
        (
            agent_coordinator.route(
                "How should I manage "
                "my finances?"
            )
            == "Finance Agent"
        ),
    )

    check(
        "Technical routes to Technical Agent",
        (
            agent_coordinator.route(
                "Help me with my "
                "MoneroAI project."
            )
            == "Technical Agent"
        ),
    )

    check(
        "Cross-domain request routes to Cross-Agent",
        (
            agent_coordinator.route(
                "Considering my career, "
                "finances and trading, "
                "what should I prioritize?"
            )
            == "Cross-Agent Coordinator"
        ),
    )

    # ============================================================
    # 7. GENERAL KNOWLEDGE ISOLATION
    # ============================================================

    divider(
        "7. GENERAL KNOWLEDGE ISOLATION"
    )

    general_graph_answer = (
        agent_coordinator
        ._reason_from_personal_graph(
            "What is the capital of France?"
        )
    )

    check(
        "Graph Reasoner does not hijack general knowledge",
        general_graph_answer is None,
        general_graph_answer,
    )

    coordinator_graph_answer = (
        agent_coordinator.handle(
            "How is Python connected to me?"
        )
    )

    check(
        "Coordinator answers personal graph question",
        (
            "MoneroAI"
            in coordinator_graph_answer
            and "Python"
            in coordinator_graph_answer
        ),
        coordinator_graph_answer,
    )

    # ============================================================
    # 8. ISOLATED LIVE WRITE TEST
    # ============================================================

    divider(
        "8. ISOLATED MEMORY ↔ GRAPH LIFECYCLE"
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

    isolated_exception = None

    try:

        # --------------------------------------------------------
        # Redirect memory for this process only.
        # --------------------------------------------------------

        memory_manager_module.long_term_memory.storage_path = (
            TEMP_MEMORY
        )

        temp_store = GraphStore(
            TEMP_GRAPH
        )

        temp_manager = GraphManager(
            temp_store
        )

        temp_extractor = GraphExtractor(
            temp_manager
        )

        temp_sync = (
            PersonalKnowledgeSynchronizer(
                graph_manager_instance=(
                    temp_manager
                ),
                graph_extractor_instance=(
                    temp_extractor
                ),
            )
        )

        temp_reasoner = GraphReasoner(
            manager=temp_manager
        )

        temp_coordinator = AgentCoordinator(
            knowledge_sync_instance=(
                temp_sync
            ),
            graph_reasoner_instance=(
                temp_reasoner
            ),
        )

        # --------------------------------------------------------
        # CREATE
        # --------------------------------------------------------

        first_work = temp_sync.process(
            "I work at Company A."
        )

        check(
            "New employment memory is created",
            (
                first_work[
                    "memory"
                ][
                    "action"
                ]
                == "created"
            ),
            first_work[
                "memory"
            ],
        )

        check(
            "New employment graph relation is created",
            (
                first_work[
                    "graph"
                ][
                    "action"
                ]
                == "created"
            ),
            first_work[
                "graph"
            ],
        )

        # --------------------------------------------------------
        # SUPERSESSION
        # --------------------------------------------------------

        changed_work = temp_sync.process(
            "I now work at Company B."
        )

        check(
            "Old employment memory is superseded",
            (
                changed_work[
                    "memory"
                ][
                    "action"
                ]
                == "superseded"
            ),
            changed_work[
                "memory"
            ],
        )

        check(
            "Old employment graph relation is superseded",
            (
                changed_work[
                    "graph"
                ][
                    "action"
                ]
                == "superseded"
            ),
            changed_work[
                "graph"
            ],
        )

        active_work = (
            temp_manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type="works_at",
            )
        )

        active_work_names = [
            item[
                "target_name"
            ]
            for item in active_work
        ]

        check(
            "Only Company B remains active",
            (
                active_work_names
                == ["Company B"]
            ),
            active_work_names,
        )

        # --------------------------------------------------------
        # MULTI-VALUE KNOWLEDGE
        # --------------------------------------------------------

        python_learning = (
            temp_sync.process(
                "I am learning Python."
            )
        )

        docker_learning = (
            temp_sync.process(
                "I am learning Docker."
            )
        )

        learning = (
            temp_manager.get_connections(
                "User",
                "person",
                direction="outgoing",
                relation_type="learning",
            )
        )

        learning_names = {
            item[
                "target_name"
            ]
            for item in learning
        }

        check(
            "Multi-value learning preserves Python and Docker",
            learning_names
            == {
                "Python",
                "Docker",
            },
            learning_names,
        )

        # --------------------------------------------------------
        # REINFORCEMENT + GRAPH REUSE
        # --------------------------------------------------------

        repeated_python = (
            temp_sync.process(
                "I am learning Python."
            )
        )

        check(
            "Duplicate memory is reinforced",
            (
                repeated_python[
                    "memory"
                ][
                    "action"
                ]
                == "reinforced"
            ),
            repeated_python[
                "memory"
            ],
        )

        check(
            "Duplicate graph relationship is reused",
            (
                repeated_python[
                    "graph"
                ][
                    "action"
                ]
                == "reused"
            ),
            repeated_python[
                "graph"
            ],
        )

        # --------------------------------------------------------
        # QUESTION REJECTION
        # --------------------------------------------------------

        question_memory_before = len(
            memory_manager.get_all()
        )

        question_graph_before = (
            temp_manager.counts()
        )

        question = temp_sync.process(
            "What is Docker?"
        )

        check(
            "Question is ignored by memory",
            (
                question[
                    "memory"
                ][
                    "action"
                ]
                == "ignored"
            ),
            question[
                "memory"
            ],
        )

        check(
            "Question is ignored by graph",
            (
                question[
                    "graph"
                ][
                    "action"
                ]
                == "ignored"
            ),
            question[
                "graph"
            ],
        )

        check(
            "Question creates no data",
            (
                question_memory_before
                == len(
                    memory_manager.get_all()
                )
                and question_graph_before
                == temp_manager.counts()
            ),
        )

        # --------------------------------------------------------
        # GRAPH-ASSISTED MEMORY
        # --------------------------------------------------------

        forex = temp_sync.process(
            "I trade Forex."
        )

        check(
            "Graph-assisted Forex memory is created",
            (
                forex[
                    "memory"
                ][
                    "action"
                ]
                == "created"
                and forex[
                    "memory"
                ][
                    "extracted"
                ][
                    "category"
                ]
                == "trading"
                and forex[
                    "memory"
                ][
                    "extracted"
                ][
                    "derived_from_graph"
                ]
                is True
            ),
            forex[
                "memory"
            ],
        )

        check(
            "Forex graph relationship is created",
            (
                forex[
                    "graph"
                ][
                    "action"
                ]
                == "created"
            ),
            forex[
                "graph"
            ],
        )

        # --------------------------------------------------------
        # TEMP COORDINATOR REASONING
        # --------------------------------------------------------

        temp_work_answer = (
            temp_coordinator
            ._reason_from_personal_graph(
                "Where do I work?"
            )
        )

        check(
            "Injected coordinator reasons from temporary graph",
            (
                temp_work_answer is not None
                and "Company B"
                in temp_work_answer
            ),
            temp_work_answer,
        )

        check(
            "Temporary reasoner isolates general knowledge",
            (
                temp_coordinator
                ._reason_from_personal_graph(
                    "What is the capital "
                    "of France?"
                )
                is None
            ),
        )

        # --------------------------------------------------------
        # PERSISTENCE / RELOAD
        # --------------------------------------------------------

        temp_memory_count = len(
            memory_manager.get_all()
        )

        temp_graph_counts = (
            temp_manager.counts()
        )

        reloaded_memory_store = (
            LongTermMemoryStore()
        )

        reloaded_memory_store.storage_path = (
            TEMP_MEMORY
        )

        reloaded_graph_manager = (
            GraphManager(
                GraphStore(
                    TEMP_GRAPH
                )
            )
        )

        check(
            "Memory survives storage reload",
            (
                len(
                    reloaded_memory_store
                    .get_all()
                )
                == temp_memory_count
            ),
            {
                "before": temp_memory_count,
                "after": len(
                    reloaded_memory_store
                    .get_all()
                ),
            },
        )

        check(
            "Graph survives storage reload",
            (
                reloaded_graph_manager
                .counts()
                == temp_graph_counts
            ),
            {
                "before": temp_graph_counts,
                "after": (
                    reloaded_graph_manager
                    .counts()
                ),
            },
        )

    except Exception as exc:

        isolated_exception = exc

        failures.append(
            "Isolated validation raised "
            "an unexpected exception"
        )

        print(
            "[FAIL] Isolated validation "
            "raised an unexpected exception"
        )

        print(
            "       EXCEPTION:",
            repr(
                exc
            ),
        )

    finally:

        # --------------------------------------------------------
        # Always restore real memory.
        # --------------------------------------------------------

        memory_manager_module.long_term_memory.storage_path = (
            real_memory_path
        )

        TEMP_MEMORY.unlink(
            missing_ok=True
        )

        TEMP_GRAPH.unlink(
            missing_ok=True
        )

    # ============================================================
    # 9. REAL DATA INTEGRITY AFTER ALL TESTS
    # ============================================================

    divider(
        "9. FINAL REAL-DATA INTEGRITY"
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

    check(
        "Real memory remained unchanged",
        (
            real_memory_before
            == real_memory_after
        ),
        {
            "before": real_memory_before,
            "after": real_memory_after,
        },
    )

    check(
        "Real graph remained unchanged",
        (
            real_graph_before
            == real_graph_after
        ),
        {
            "before": real_graph_before,
            "after": real_graph_after,
        },
    )

    check(
        "Temporary memory file was deleted",
        not TEMP_MEMORY.exists(),
        TEMP_MEMORY,
    )

    check(
        "Temporary graph file was deleted",
        not TEMP_GRAPH.exists(),
        TEMP_GRAPH,
    )

    # ============================================================
    # FINAL RESULT
    # ============================================================

    divider(
        "PHASE 22 FINAL RESULT"
    )

    print(
        "PASSED:",
        passes,
    )

    print(
        "FAILED:",
        len(
            failures
        ),
    )

    if isolated_exception is not None:

        print(
            "ISOLATED EXCEPTION:",
            repr(
                isolated_exception
            ),
        )

    if failures:

        print(
            "\nFAILED CHECKS:"
        )

        for failure in failures:

            print(
                "-",
                failure,
            )

        print(
            "\nPHASE 22 STATUS: FAILED"
        )

        raise SystemExit(
            1
        )

    print(
        "\nPHASE 22 STATUS: PASS"
    )

    print(
        "PERSONAL KNOWLEDGE GRAPH: "
        "DDOOONNEEEE"
    )


if __name__ == "__main__":

    main()
