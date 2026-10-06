from __future__ import annotations

import re

from pathlib import Path


TARGET = Path(
    "app/agents/agent_coordinator.py"
)


NOTES_IMPORT = """from app.personal_data.notes_query_engine import (
    notes_query_engine,
)

"""


ROUTE_BLOCK = """
        # --------------------------------------------------------
        # NOTES QUERY ROUTING
        # --------------------------------------------------------

        if notes_query_engine.can_answer(
            request
        ):

            return "NOTES_QUERY_ENGINE"

"""


HANDLE_BLOCK = """
        # --------------------------------------------------------
        # NOTES QUERY REASONING
        #
        # Read-only Notes questions are answered before
        # Memory, Graph and normal agent routing.
        #
        # Notes write commands are deliberately excluded by
        # NotesQueryEngine until controlled write permissions
        # are implemented.
        # --------------------------------------------------------

        if notes_query_engine.can_answer(
            request
        ):

            try:

                notes_answer = (
                    notes_query_engine.answer(
                        request
                    )
                )

            except Exception:

                # Notes subsystem problems must not
                # break normal MoneroAI routing.
                notes_answer = None

            if notes_answer is not None:

                return notes_answer

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
    # PRE-FLIGHT
    # ============================================================

    if (
        "NOTES_QUERY_ENGINE"
        in original
        or
        "notes_query_engine.answer("
        in original
        or
        "notes_query_engine.can_answer("
        in original
    ):

        raise RuntimeError(
            "Notes Query Engine integration "
            "already appears to exist. "
            "No changes written."
        )

    required_existing = [
        "CALENDAR_QUERY_ENGINE",
        "calendar_query_engine",
        "TASK_QUERY_ENGINE",
        "task_query_engine",
        "_synchronize_personal_knowledge",
        "_reason_from_personal_graph",
        "_is_cross_agent_request",
    ]

    missing = [
        item
        for item in required_existing
        if item not in original
    ]

    if missing:

        raise RuntimeError(
            "Coordinator is missing expected "
            f"components: {missing}. "
            "No changes written."
        )

    text = original

    # ============================================================
    # IMPORT
    # ============================================================

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
        NOTES_IMPORT
        + class_marker,
        1,
    )

    # ============================================================
    # ROUTE + HANDLE
    # ============================================================

    lines = text.splitlines(
        keepends=True
    )

    # Calendar → Tasks → Notes → Cross-Agent
    lines = insert_before_unique_line(
        lines,
        "route",
        "if self._is_cross_agent_request(",
        ROUTE_BLOCK,
    )

    # Calendar → Tasks → Notes → Personal Knowledge
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
    # VALIDATE BEFORE WRITE
    # ============================================================

    required_after = [
        (
            "from app.personal_data."
            "notes_query_engine import"
        ),
        "notes_query_engine.can_answer(",
        "notes_query_engine.answer(",
        "NOTES_QUERY_ENGINE",
        "CALENDAR_QUERY_ENGINE",
        "calendar_query_engine.answer(",
        "TASK_QUERY_ENGINE",
        "task_query_engine.answer(",
        "_synchronize_personal_knowledge",
        "_reason_from_personal_graph",
        "_is_cross_agent_request",
        "general_agent",
        "cross_agent_coordinator",
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

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Notes Query Engine integrated "
        "successfully."
    )


if __name__ == "__main__":

    main()