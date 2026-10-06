from __future__ import annotations

import re

from pathlib import Path


TARGET = Path(
    "app/agents/agent_coordinator.py"
)


CALENDAR_IMPORT = """
from app.personal_data.calendar_query_engine import (
    calendar_query_engine,
)

"""


HANDLE_BLOCK = """
        # Calendar questions have priority over
        # memory, graph and normal agent routing.
        #
        # CalendarQueryEngine returns None for
        # questions that are not Calendar-related.
        try:

            calendar_answer = (
                calendar_query_engine.answer(
                    request
                )
            )

        except Exception:

            # A Calendar subsystem problem must
            # never break normal MoneroAI routing.
            calendar_answer = None

        if calendar_answer is not None:

            return calendar_answer

"""


ROUTE_BLOCK = """
        if calendar_query_engine.can_answer(
            request
        ):

            return "CALENDAR_QUERY_ENGINE"

"""


def find_method_start(
    lines: list[str],
    method_name: str,
) -> int:

    pattern = re.compile(
        rf"^    def {re.escape(method_name)}\s*\("
    )

    matches = [
        index
        for index, line
        in enumerate(lines)
        if pattern.match(line)
    ]

    if len(matches) != 1:

        raise RuntimeError(
            f"Expected exactly one "
            f"{method_name}() method, "
            f"found {len(matches)}. "
            "No changes written."
        )

    return matches[0]


def find_method_end(
    lines: list[str],
    start: int,
) -> int:

    for index in range(
        start + 1,
        len(lines),
    ):

        line = lines[index]

        if re.match(
            r"^    def \w+\s*\(",
            line,
        ):

            return index

    return len(lines)


def insert_after_empty_guard(
    lines: list[str],
    method_name: str,
    block: str,
) -> list[str]:

    start = find_method_start(
        lines,
        method_name,
    )

    end = find_method_end(
        lines,
        start,
    )

    return_indexes = []

    for index in range(
        start,
        end,
    ):

        if (
            'return "Please provide a request."'
            in lines[index]
            or
            "return 'Please provide a request.'"
            in lines[index]
            or
            'return "GENERAL_AGENT"'
            in lines[index]
            or
            "return 'GENERAL_AGENT'"
            in lines[index]
        ):

            return_indexes.append(
                index
            )

    if not return_indexes:

        raise RuntimeError(
            f"Could not find the empty-request "
            f"guard inside {method_name}(). "
            "No changes written."
        )

    insertion_index = (
        return_indexes[0]
        + 1
    )

    block_lines = (
        block.strip("\n")
        .splitlines(
            keepends=True
        )
    )

    if block_lines:

        block_lines = [
            line
            if line.endswith("\n")
            else line + "\n"
            for line in block_lines
        ]

    block_lines.insert(
        0,
        "\n",
    )

    block_lines.append(
        "\n"
    )

    return (
        lines[:insertion_index]
        + block_lines
        + lines[insertion_index:]
    )


def main() -> None:

    if not TARGET.exists():

        raise FileNotFoundError(
            f"Coordinator not found: "
            f"{TARGET}"
        )

    original = TARGET.read_text(
        encoding="utf-8"
    )

    # ============================================================
    # DO NOT PATCH TWICE
    # ============================================================

    if (
        "calendar_query_engine.answer("
        in original
        and
        "CALENDAR_QUERY_ENGINE"
        in original
    ):

        print(
            "Calendar coordinator "
            "integration already exists. "
            "No changes made."
        )

        return

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
            "\nclass AgentCoordinator:"
        )

        count = text.count(
            class_marker
        )

        if count != 1:

            raise RuntimeError(
                "Expected exactly one "
                "AgentCoordinator class. "
                f"Found {count}. "
                "No changes written."
            )

        text = text.replace(
            class_marker,
            "\n"
            + CALENDAR_IMPORT
            + "class AgentCoordinator:",
            1,
        )

    # ============================================================
    # HANDLE()
    # ============================================================

    lines = text.splitlines(
        keepends=True
    )

    lines = insert_after_empty_guard(
        lines,
        "handle",
        HANDLE_BLOCK,
    )

    text = "".join(
        lines
    )

    # ============================================================
    # ROUTE()
    # ============================================================

    lines = text.splitlines(
        keepends=True
    )

    lines = insert_after_empty_guard(
        lines,
        "route",
        ROUTE_BLOCK,
    )

    text = "".join(
        lines
    )

    # ============================================================
    # FINAL VALIDATION
    # ============================================================

    required = [
        (
            "from app.personal_data."
            "calendar_query_engine import"
        ),
        "calendar_query_engine.answer(",
        "calendar_query_engine.can_answer(",
        "CALENDAR_QUERY_ENGINE",
        "def handle",
        "def route",
    ]

    missing = [
        item
        for item in required
        if item not in text
    ]

    if missing:

        raise RuntimeError(
            "Calendar integration validation "
            f"failed. Missing: {missing}. "
            "No changes written."
        )

    # Existing Graph / Knowledge components
    # must not disappear.
    for existing_component in (
        "graph_reasoner",
        "personal_knowledge_sync",
    ):

        if (
            existing_component in original
            and existing_component not in text
        ):

            raise RuntimeError(
                f"Existing component "
                f"{existing_component!r} "
                "would be removed. "
                "No changes written."
            )

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Calendar Query Engine integrated "
        "into AgentCoordinator."
    )


if __name__ == "__main__":

    main()