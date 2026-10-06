from pathlib import Path


TARGET = Path(
    "app/agents/agent_coordinator.py"
)


def replace_once(
    text: str,
    old: str,
    new: str,
    description: str,
) -> str:

    count = text.count(old)

    if count != 1:

        raise RuntimeError(
            f"{description}: expected exactly "
            f"1 match, found {count}."
        )

    return text.replace(
        old,
        new,
        1,
    )


def main() -> None:

    if not TARGET.exists():

        raise FileNotFoundError(
            f"File not found: {TARGET}"
        )

    text = TARGET.read_text(
        encoding="utf-8"
    )

    # ============================================================
    # IMPORT GRAPH REASONER
    # ============================================================

    old_import = """from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
    personal_knowledge_sync,
)
"""

    new_import = """from app.knowledge_graph.personal_knowledge_sync import (
    PersonalKnowledgeSynchronizer,
    personal_knowledge_sync,
)

from app.knowledge_graph.graph_reasoner import (
    GraphReasoner,
    graph_reasoner,
)
"""

    text = replace_once(
        text,
        old_import,
        new_import,
        "GraphReasoner import",
    )

    # ============================================================
    # EXTEND CONSTRUCTOR
    # ============================================================

    old_constructor = """    def __init__(
        self,
        knowledge_sync_instance:
        PersonalKnowledgeSynchronizer | None = None,
    ):
"""

    new_constructor = """    def __init__(
        self,
        knowledge_sync_instance:
        PersonalKnowledgeSynchronizer | None = None,
        graph_reasoner_instance:
        GraphReasoner | None = None,
    ):
"""

    text = replace_once(
        text,
        old_constructor,
        new_constructor,
        "AgentCoordinator constructor",
    )

    # ============================================================
    # STORE GRAPH REASONER
    # ============================================================

    old_sync_assignment = """        self.knowledge_sync = (
            knowledge_sync_instance
            if knowledge_sync_instance is not None
            else personal_knowledge_sync
        )
"""

    new_sync_assignment = """        self.knowledge_sync = (
            knowledge_sync_instance
            if knowledge_sync_instance is not None
            else personal_knowledge_sync
        )

        self.graph_reasoner = (
            graph_reasoner_instance
            if graph_reasoner_instance is not None
            else graph_reasoner
        )
"""

    text = replace_once(
        text,
        old_sync_assignment,
        new_sync_assignment,
        "GraphReasoner assignment",
    )

    # ============================================================
    # ADD SAFE GRAPH REASONING METHOD
    # ============================================================

    old_wrapper = """    # ============================================================
    # BACKWARD-COMPATIBILITY WRAPPER
    # ============================================================

    def _remember_if_relevant(
"""

    new_wrapper = """    # ============================================================
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
"""

    text = replace_once(
        text,
        old_wrapper,
        new_wrapper,
        "Graph reasoning method",
    )

    # ============================================================
    # INSERT GRAPH REASONING INTO HANDLE
    # ============================================================

    old_handle_section = """        self._synchronize_personal_knowledge(
            request
        )

        # --------------------------------------------------------
        # CROSS-AGENT INTELLIGENCE
        # --------------------------------------------------------
"""

    new_handle_section = """        self._synchronize_personal_knowledge(
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
"""

    text = replace_once(
        text,
        old_handle_section,
        new_handle_section,
        "Graph reasoning handle integration",
    )

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Graph Reasoner integration applied successfully."
    )


if __name__ == "__main__":

    main()