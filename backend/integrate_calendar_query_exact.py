from __future__ import annotations

from pathlib import Path


TARGET = Path(
    "app/agents/agent_coordinator.py"
)


CALENDAR_IMPORT = """from app.personal_data.calendar_query_engine import (
    calendar_query_engine,
)

"""


ROUTE_OLD = """        if (
            not request
            or not request.strip()
        ):

            return "GENERAL_AGENT"

        if self._is_cross_agent_request(
"""


ROUTE_NEW = """        if (
            not request
            or not request.strip()
        ):

            return "GENERAL_AGENT"

        # --------------------------------------------------------
        # CALENDAR QUERY ROUTING
        # --------------------------------------------------------

        if calendar_query_engine.can_answer(
            request
        ):

            return "CALENDAR_QUERY_ENGINE"

        if self._is_cross_agent_request(
"""


HANDLE_OLD = """        if (
            not request
            or not request.strip()
        ):

            return (
                "Please provide a request."
            )

        # --------------------------------------------------------
        # PHASE 22 PERSONAL KNOWLEDGE INGESTION
"""


HANDLE_NEW = """        if (
            not request
            or not request.strip()
        ):

            return (
                "Please provide a request."
            )

        # --------------------------------------------------------
        # CALENDAR QUERY REASONING
        #
        # Calendar requests are handled before Memory, Graph,
        # General-Agent and Specialized-Agent routing.
        #
        # This prevents the language model from inventing schedule
        # information when verified Calendar data is available.
        # --------------------------------------------------------

        if calendar_query_engine.can_answer(
            request
        ):

            try:

                calendar_answer = (
                    calendar_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # Calendar failure must never break
                # the remainder of MoneroAI routing.
                calendar_answer = None

            if calendar_answer is not None:

                return calendar_answer

        # --------------------------------------------------------
        # PHASE 22 PERSONAL KNOWLEDGE INGESTION
"""


def replace_exactly_once(
    text: str,
    old: str,
    new: str,
    description: str,
) -> str:

    count = text.count(
        old
    )

    if count != 1:

        raise RuntimeError(
            f"{description}: expected exactly "
            f"1 match, found {count}. "
            "No changes written."
        )

    return text.replace(
        old,
        new,
        1,
    )


def main() -> None:

    if not TARGET.exists():

        raise FileNotFoundError(
            f"Coordinator not found: {TARGET}"
        )

    original = TARGET.read_text(
        encoding="utf-8"
    )

    # ============================================================
    # SAFETY — PREVENT DOUBLE INTEGRATION
    # ============================================================

    already_integrated = (
        "CALENDAR_QUERY_ENGINE"
        in original
        or
        "calendar_query_engine.can_answer("
        in original
        or
        "calendar_query_engine.answer("
        in original
    )

    if already_integrated:

        raise RuntimeError(
            "Calendar integration already appears "
            "to exist. No changes written."
        )

    text = original

    # ============================================================
    # IMPORT
    # ============================================================

    if (
        "from app.personal_data."
        "calendar_query_engine import"
        not in text
    ):

        class_marker = (
            "class AgentCoordinator:"
        )

        count = text.count(
            class_marker
        )

        if count != 1:

            raise RuntimeError(
                "Expected exactly one "
                "AgentCoordinator class, "
                f"found {count}. "
                "No changes written."
            )

        text = text.replace(
            class_marker,
            CALENDAR_IMPORT
            + class_marker,
            1,
        )

    # ============================================================
    # ROUTE()
    # ============================================================

    text = replace_exactly_once(
        text,
        ROUTE_OLD,
        ROUTE_NEW,
        "route() integration",
    )

    # ============================================================
    # HANDLE()
    # ============================================================

    text = replace_exactly_once(
        text,
        HANDLE_OLD,
        HANDLE_NEW,
        "handle() integration",
    )

    # ============================================================
    # FINAL VALIDATION BEFORE WRITE
    # ============================================================

    required = [
        (
            "from app.personal_data."
            "calendar_query_engine import"
        ),
        "calendar_query_engine.can_answer(",
        "calendar_query_engine.answer(",
        "CALENDAR_QUERY_ENGINE",
        "_synchronize_personal_knowledge",
        "_reason_from_personal_graph",
        "graph_reasoner",
        "personal_knowledge_sync",
    ]

    missing = [
        item
        for item in required
        if item not in text
    ]

    if missing:

        raise RuntimeError(
            "Final validation failed. "
            f"Missing components: {missing}. "
            "No changes written."
        )

    # Existing critical functionality must survive.
    critical_existing = [
        "_is_cross_agent_request",
        "is_general_request",
        "find_agent",
        "general_agent",
        "cross_agent_coordinator",
    ]

    removed = [
        item
        for item in critical_existing
        if (
            item in original
            and item not in text
        )
    ]

    if removed:

        raise RuntimeError(
            "Patch would remove existing "
            f"functionality: {removed}. "
            "No changes written."
        )

    # ============================================================
    # WRITE ONLY AFTER EVERY CHECK PASSES
    # ============================================================

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Calendar Query Engine integrated "
        "successfully."
    )


if __name__ == "__main__":

    main()