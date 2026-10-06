from __future__ import annotations

import re

from pathlib import Path


TARGET = Path(
    "app/agents/agent_coordinator.py"
)


TASK_IMPORT = """from app.personal_data.task_query_engine import (
    task_query_engine,
)

"""


ROUTE_BLOCK = """
        # --------------------------------------------------------
        # TASK / REMINDER QUERY ROUTING
        # --------------------------------------------------------

        if task_query_engine.can_answer(
            request
        ):

            return "TASK_QUERY_ENGINE"

"""


HANDLE_BLOCK = """
        # --------------------------------------------------------
        # TASK / REMINDER QUERY REASONING
        #
        # Read-only task and reminder questions are answered
        # before Memory, Graph and normal agent routing.
        #
        # Write commands such as "Remind me to..." are deliberately
        # excluded by TaskQueryEngine and continue through the
        # normal routing path until write permissions are added.
        # --------------------------------------------------------

        if task_query_engine.can_answer(
            request
        ):

            try:

                task_answer = (
                    task_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # A Task subsystem problem must never
                # break the remainder of MoneroAI.
                task_answer = None

            if task_answer is not None:

                return task_answer

"""


def find_method_span(
    lines: list[str],
    method_name: str,
) -> tuple[int, int]:

    pattern = re.compile(
        rf"^    def {re.escape(method_name)}\s*\("
    )

    starts = [
        index
        for index, line in enumerate(lines)
        if pattern.match(line)
    ]

    if len(starts) != 1:

        raise RuntimeError(
            f"Expected exactly one {method_name}() "
            f"method, found {len(starts)}. "
            "No changes written."
        )

    start = starts[0]
    end = len(lines)

    for index in range(
        start + 1,
        len(lines),
    ):

        if re.match(
            r"^    def \w+\s*\(",
            lines[index],
        ):

            end = index
            break

    return start, end


def insert_before_unique_line(
    lines: list[str],
    method_name: str,
    search_text: str,
    block: str,
) -> list[str]:

    start, end = find_method_span(
        lines,
        method_name,
    )

    matches = [
        index
        for index in range(
            start,
            end,
        )
        if search_text in lines[index]
    ]

    if len(matches) != 1:

        raise RuntimeError(
            f"{method_name}(): expected exactly "
            f"one occurrence of {search_text!r}, "
            f"found {len(matches)}. "
            "No changes written."
        )

    index = matches[0]

    block_lines = (
        block.strip("\n")
        .splitlines(
            keepends=True
        )
    )

    normalized = []

    for line in block_lines:

        if line.endswith("\n"):

            normalized.append(
                line
            )

        else:

            normalized.append(
                line + "\n"
            )

    normalized.append(
        "\n"
    )

    return (
        lines[:index]
        + normalized
        + lines[index:]
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
    # PRE-FLIGHT SAFETY
    # ============================================================

    if (
        "TASK_QUERY_ENGINE"
        in original
        or
        "task_query_engine.answer("
        in original
        or
        "task_query_engine.can_answer("
        in original
    ):

        raise RuntimeError(
            "Task Query Engine integration "
            "already appears to exist. "
            "No changes written."
        )

    required_existing = [
        "calendar_query_engine",
        "CALENDAR_QUERY_ENGINE",
        "_synchronize_personal_knowledge",
        "_reason_from_personal_graph",
        "_is_cross_agent_request",
        "personal_knowledge_sync",
        "graph_reasoner",
    ]

    missing_existing = [
        item
        for item in required_existing
        if item not in original
    ]

    if missing_existing:

        raise RuntimeError(
            "Current coordinator is missing "
            "expected existing components: "
            f"{missing_existing}. "
            "No changes written."
        )

    text = original

    # ============================================================
    # IMPORT
    # ============================================================

    if (
        "from app.personal_data."
        "task_query_engine import"
        not in text
    ):

        class_marker = (
            "class AgentCoordinator:"
        )

        if text.count(
            class_marker
        ) != 1:

            raise RuntimeError(
                "Could not uniquely locate "
                "AgentCoordinator class. "
                "No changes written."
            )

        text = text.replace(
            class_marker,
            TASK_IMPORT
            + class_marker,
            1,
        )

    # ============================================================
    # METHOD PATCHING
    # ============================================================

    lines = text.splitlines(
        keepends=True
    )

    # route():
    #
    # Calendar remains first.
    # Task routing is inserted immediately before
    # cross-agent routing.
    lines = insert_before_unique_line(
        lines,
        "route",
        "if self._is_cross_agent_request(",
        ROUTE_BLOCK,
    )

    # handle():
    #
    # Calendar remains first.
    # Task reasoning is inserted immediately before
    # personal knowledge synchronization.
    lines = insert_before_unique_line(
        lines,
        "handle",
        "# PHASE 22 PERSONAL KNOWLEDGE INGESTION",
        HANDLE_BLOCK,
    )

    text = "".join(
        lines
    )

    # ============================================================
    # FINAL VALIDATION BEFORE WRITE
    # ============================================================

    required_after = [
        (
            "from app.personal_data."
            "task_query_engine import"
        ),
        "task_query_engine.can_answer(",
        "task_query_engine.answer(",
        "TASK_QUERY_ENGINE",
        "calendar_query_engine",
        "CALENDAR_QUERY_ENGINE",
        "_synchronize_personal_knowledge",
        "_reason_from_personal_graph",
        "_is_cross_agent_request",
        "personal_knowledge_sync",
        "graph_reasoner",
    ]

    missing_after = [
        item
        for item in required_after
        if item not in text
    ]

    if missing_after:

        raise RuntimeError(
            "Final validation failed. "
            f"Missing: {missing_after}. "
            "No changes written."
        )

    # Existing important functionality
    # must not disappear.
    critical = [
        "general_agent",
        "cross_agent_coordinator",
        "find_agent",
        "is_general_request",
        "calendar_query_engine",
    ]

    removed = [
        item
        for item in critical
        if (
            item in original
            and item not in text
        )
    ]

    if removed:

        raise RuntimeError(
            "Patch would remove existing "
            f"components: {removed}. "
            "No changes written."
        )

    # ============================================================
    # WRITE ONLY AFTER ALL VALIDATIONS PASS
    # ============================================================

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Task Query Engine integrated "
        "successfully."
    )


if __name__ == "__main__":

    main()