from __future__ import annotations

from typing import Any

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)


USER_NAME = "User"
USER_TYPE = "person"


def seed_personal_graph(
    manager: GraphManager | None = None,
) -> dict[str, Any]:

    manager = (
        manager
        if manager is not None
        else graph_manager
    )

    before = manager.counts()

    # ============================================================
    # CORE USER ENTITY
    # ============================================================

    manager.ensure_entity(
        name=USER_NAME,
        node_type=USER_TYPE,
    )

    # ============================================================
    # CAREER
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="works_at",
        target_name="MTN Cameroon",
        source_type=USER_TYPE,
        target_type="organization",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="has_role",
        target_name="Product & Service Intern",
        source_type=USER_TYPE,
        target_type="role",
    )

    manager.connect(
        source_name="Product & Service Intern",
        relation_type="role_at",
        target_name="MTN Cameroon",
        source_type="role",
        target_type="organization",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="works_in_department",
        target_name="Marketing",
        source_type=USER_TYPE,
        target_type="department",
    )

    manager.connect(
        source_name="Marketing",
        relation_type="department_of",
        target_name="MTN Cameroon",
        source_type="department",
        target_type="organization",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="has_career_goal",
        target_name="Permanent Staff at MTN Cameroon",
        source_type=USER_TYPE,
        target_type="goal",
    )

    manager.connect(
        source_name="Permanent Staff at MTN Cameroon",
        relation_type="related_to",
        target_name="MTN Cameroon",
        source_type="goal",
        target_type="organization",
    )

    # ============================================================
    # EDUCATION
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="studied",
        target_name="Network and Security",
        source_type=USER_TYPE,
        target_type="field_of_study",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="studied",
        target_name="Computer Network and System Maintenance",
        source_type=USER_TYPE,
        target_type="field_of_study",
    )

    # ============================================================
    # CURRENT LEARNING
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="learning",
        target_name="C#",
        source_type=USER_TYPE,
        target_type="technology",
    )

    # ============================================================
    # MONEROAI
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="building",
        target_name="MoneroAI",
        source_type=USER_TYPE,
        target_type="project",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="uses",
        target_name="Python",
        source_type="project",
        target_type="technology",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="uses",
        target_name="Ollama",
        source_type="project",
        target_type="technology",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="uses",
        target_name="Qwen3",
        source_type="project",
        target_type="ai_model",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="includes",
        target_name="Long-Term Memory",
        source_type="project",
        target_type="component",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="includes",
        target_name="Specialized AI Agents",
        source_type="project",
        target_type="component",
    )

    manager.connect(
        source_name="MoneroAI",
        relation_type="includes",
        target_name="Personal Knowledge Graph",
        source_type="project",
        target_type="component",
    )

    # ============================================================
    # IOT PROJECT
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="building",
        target_name="Smart Home IoT System",
        source_type=USER_TYPE,
        target_type="project",
    )

    manager.connect(
        source_name="Smart Home IoT System",
        relation_type="uses",
        target_name="ESP32",
        source_type="project",
        target_type="technology",
    )

    manager.connect(
        source_name="Smart Home IoT System",
        relation_type="uses",
        target_name="Blynk",
        source_type="project",
        target_type="technology",
    )

    manager.connect(
        source_name="Smart Home IoT System",
        relation_type="related_to",
        target_name="Internet of Things",
        source_type="project",
        target_type="field",
    )

    # ============================================================
    # TECHNICAL INTERESTS
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="interested_in",
        target_name="Cybersecurity",
        source_type=USER_TYPE,
        target_type="field",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="interested_in",
        target_name="Artificial Intelligence",
        source_type=USER_TYPE,
        target_type="field",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="interested_in",
        target_name="Computer Networking",
        source_type=USER_TYPE,
        target_type="field",
    )

    manager.connect(
        source_name="Network and Security",
        relation_type="related_to",
        target_name="Cybersecurity",
        source_type="field_of_study",
        target_type="field",
    )

    manager.connect(
        source_name="Network and Security",
        relation_type="related_to",
        target_name="Computer Networking",
        source_type="field_of_study",
        target_type="field",
    )

    # ============================================================
    # TRADING
    # ============================================================

    manager.connect(
        source_name=USER_NAME,
        relation_type="trades",
        target_name="Forex",
        source_type=USER_TYPE,
        target_type="market",
    )

    manager.connect(
        source_name=USER_NAME,
        relation_type="uses_strategy",
        target_name="Support and Resistance",
        source_type=USER_TYPE,
        target_type="trading_strategy",
    )

    manager.connect(
        source_name="Support and Resistance",
        relation_type="strategy_for",
        target_name="Forex",
        source_type="trading_strategy",
        target_type="market",
    )

    # ============================================================
    # FINAL COUNTS
    # ============================================================

    after = manager.counts()

    return {
        "before": before,
        "after": after,
        "nodes_added": (
            after["nodes"]
            - before["nodes"]
        ),
        "relationships_added": (
            after["relationships"]
            - before["relationships"]
        ),
    }


if __name__ == "__main__":

    result = seed_personal_graph()

    print(
        "Personal Knowledge Graph seeded."
    )

    print(
        "Before:",
        result["before"],
    )

    print(
        "After:",
        result["after"],
    )

    print(
        "Nodes added:",
        result["nodes_added"],
    )

    print(
        "Relationships added:",
        result[
            "relationships_added"
        ],
    )
