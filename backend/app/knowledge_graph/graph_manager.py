from __future__ import annotations

from typing import Any

from app.knowledge_graph.graph_model import (
    KnowledgeNode,
    KnowledgeRelationship,
)

from app.knowledge_graph.graph_store import (
    GraphStore,
    graph_store,
)


class GraphManager:

    def __init__(
        self,
        store: GraphStore | None = None,
    ):

        self.store = (
            store
            if store is not None
            else graph_store
        )

    # ============================================================
    # GET ENTITY
    # ============================================================

    def get_entity(
        self,
        name: str,
        node_type: str | None = None,
    ) -> KnowledgeNode | None:

        if not name or not name.strip():

            return None

        matches = self.store.find_nodes(
            name=name,
            node_type=node_type,
            status="active",
        )

        if not matches:

            return None

        if (
            node_type is None
            and len(matches) > 1
        ):

            types = sorted(
                {
                    node.node_type
                    for node in matches
                }
            )

            raise ValueError(
                f"Entity '{name}' is ambiguous. "
                f"Specify node_type. "
                f"Matching types: {types}"
            )

        return matches[0]

    # ============================================================
    # ENSURE ENTITY
    # ============================================================

    def ensure_entity(
        self,
        name: str,
        node_type: str,
        attributes: dict[str, Any] | None = None,
        node_id: str | None = None,
    ) -> KnowledgeNode:

        existing = self.get_entity(
            name=name,
            node_type=node_type,
        )

        if existing is not None:

            if attributes:

                return self.store.update_node(
                    node_id=existing.node_id,
                    attributes=attributes,
                )

            return existing

        return self.store.add_node(
            name=name,
            node_type=node_type,
            attributes=attributes,
            node_id=node_id,
        )

    # ============================================================
    # UPDATE ENTITY
    # ============================================================

    def update_entity(
        self,
        name: str,
        node_type: str,
        new_name: str | None = None,
        new_node_type: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> KnowledgeNode:

        entity = self.get_entity(
            name=name,
            node_type=node_type,
        )

        if entity is None:

            raise KeyError(
                f"Entity not found: "
                f"{name} ({node_type})"
            )

        return self.store.update_node(
            node_id=entity.node_id,
            name=new_name,
            node_type=new_node_type,
            attributes=attributes,
        )

    # ============================================================
    # ARCHIVE ENTITY
    # ============================================================

    def archive_entity(
        self,
        name: str,
        node_type: str,
    ) -> KnowledgeNode:

        entity = self.get_entity(
            name=name,
            node_type=node_type,
        )

        if entity is None:

            raise KeyError(
                f"Entity not found: "
                f"{name} ({node_type})"
            )

        return self.store.archive_node(
            entity.node_id
        )

    # ============================================================
    # CONNECT ENTITIES
    # ============================================================

    def connect(
        self,
        source_name: str,
        relation_type: str,
        target_name: str,
        source_type: str = "entity",
        target_type: str = "entity",
        source_attributes: dict[str, Any] | None = None,
        target_attributes: dict[str, Any] | None = None,
        relationship_attributes: dict[str, Any] | None = None,
        confidence: float | None = None,
        source_node_id: str | None = None,
        target_node_id: str | None = None,
    ) -> KnowledgeRelationship:

        source = self.ensure_entity(
            name=source_name,
            node_type=source_type,
            attributes=source_attributes,
            node_id=source_node_id,
        )

        target = self.ensure_entity(
            name=target_name,
            node_type=target_type,
            attributes=target_attributes,
            node_id=target_node_id,
        )

        existing = (
            self.store.find_relationships(
                source_node_id=source.node_id,
                relation_type=relation_type,
                target_node_id=target.node_id,
                status="active",
            )
        )

        if existing:

            relationship = existing[0]

            update_arguments = {}

            if relationship_attributes:

                update_arguments[
                    "attributes"
                ] = relationship_attributes

            if confidence is not None:

                update_arguments[
                    "confidence"
                ] = confidence

            if update_arguments:

                relationship = (
                    self.store.update_relationship(
                        relationship.relationship_id,
                        **update_arguments,
                    )
                )

            return relationship

        return self.store.add_relationship(
            source_node_id=source.node_id,
            relation_type=relation_type,
            target_node_id=target.node_id,
            attributes=relationship_attributes,
            confidence=(
                1.0
                if confidence is None
                else confidence
            ),
        )

    # ============================================================
    # GET CONNECTIONS
    # ============================================================

    def get_connections(
        self,
        name: str,
        node_type: str | None = None,
        direction: str = "both",
        relation_type: str | None = None,
    ) -> list[dict[str, Any]]:

        direction = direction.lower().strip()

        if direction not in {
            "outgoing",
            "incoming",
            "both",
        }:

            raise ValueError(
                "direction must be "
                "'outgoing', 'incoming', "
                "or 'both'."
            )

        entity = self.get_entity(
            name=name,
            node_type=node_type,
        )

        if entity is None:

            return []

        relationships: list[
            tuple[
                str,
                KnowledgeRelationship,
            ]
        ] = []

        if direction in {
            "outgoing",
            "both",
        }:

            outgoing = (
                self.store.find_relationships(
                    source_node_id=(
                        entity.node_id
                    ),
                    relation_type=relation_type,
                    status="active",
                )
            )

            relationships.extend(
                (
                    "outgoing",
                    relationship,
                )
                for relationship
                in outgoing
            )

        if direction in {
            "incoming",
            "both",
        }:

            incoming = (
                self.store.find_relationships(
                    target_node_id=(
                        entity.node_id
                    ),
                    relation_type=relation_type,
                    status="active",
                )
            )

            relationships.extend(
                (
                    "incoming",
                    relationship,
                )
                for relationship
                in incoming
            )

        results = []

        for (
            relationship_direction,
            relationship,
        ) in relationships:

            source = self.store.get_node(
                relationship.source_node_id
            )

            target = self.store.get_node(
                relationship.target_node_id
            )

            if (
                source is None
                or target is None
            ):

                continue

            results.append(
                {
                    "direction": (
                        relationship_direction
                    ),
                    "relationship_id": (
                        relationship
                        .relationship_id
                    ),
                    "source_id": (
                        source.node_id
                    ),
                    "source_name": (
                        source.name
                    ),
                    "source_type": (
                        source.node_type
                    ),
                    "relation_type": (
                        relationship
                        .relation_type
                    ),
                    "target_id": (
                        target.node_id
                    ),
                    "target_name": (
                        target.name
                    ),
                    "target_type": (
                        target.node_type
                    ),
                    "confidence": (
                        relationship.confidence
                    ),
                    "status": (
                        relationship.status
                    ),
                    "attributes": (
                        relationship.attributes
                    ),
                }
            )

        return results

    # ============================================================
    # GET RELATIONSHIPS BETWEEN ENTITIES
    # ============================================================

    def get_relationships_between(
        self,
        source_name: str,
        target_name: str,
        source_type: str | None = None,
        target_type: str | None = None,
        relation_type: str | None = None,
        include_history: bool = False,
    ) -> list[KnowledgeRelationship]:

        source = self.get_entity(
            name=source_name,
            node_type=source_type,
        )

        target = self.get_entity(
            name=target_name,
            node_type=target_type,
        )

        if (
            source is None
            or target is None
        ):

            return []

        return self.store.find_relationships(
            source_node_id=source.node_id,
            relation_type=relation_type,
            target_node_id=target.node_id,
            status=(
                None
                if include_history
                else "active"
            ),
        )

    # ============================================================
    # ARCHIVE CONNECTION
    # ============================================================

    def archive_connection(
        self,
        source_name: str,
        relation_type: str,
        target_name: str,
        source_type: str | None = None,
        target_type: str | None = None,
    ) -> list[KnowledgeRelationship]:

        relationships = (
            self.get_relationships_between(
                source_name=source_name,
                target_name=target_name,
                source_type=source_type,
                target_type=target_type,
                relation_type=relation_type,
                include_history=False,
            )
        )

        archived = []

        for relationship in relationships:

            archived.append(
                self.store.archive_relationship(
                    relationship
                    .relationship_id
                )
            )

        return archived

    # ============================================================
    # SUPERSEDE CONNECTION
    # ============================================================

    def supersede_connection(
        self,
        source_name: str,
        relation_type: str,
        old_target_name: str,
        new_target_name: str,
        source_type: str,
        old_target_type: str,
        new_target_type: str,
        new_target_attributes: dict[
            str,
            Any,
        ] | None = None,
        relationship_attributes: dict[
            str,
            Any,
        ] | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:

        source = self.get_entity(
            source_name,
            source_type,
        )

        old_target = self.get_entity(
            old_target_name,
            old_target_type,
        )

        if source is None:

            raise KeyError(
                f"Source entity not found: "
                f"{source_name}"
            )

        if old_target is None:

            raise KeyError(
                f"Old target not found: "
                f"{old_target_name}"
            )

        old_relationships = (
            self.store.find_relationships(
                source_node_id=(
                    source.node_id
                ),
                relation_type=(
                    relation_type
                ),
                target_node_id=(
                    old_target.node_id
                ),
                status="active",
            )
        )

        if not old_relationships:

            raise KeyError(
                "No active relationship "
                f"found: {source_name} "
                f"-[{relation_type}]-> "
                f"{old_target_name}"
            )

        new_relationship = self.connect(
            source_name=source.name,
            relation_type=relation_type,
            target_name=new_target_name,
            source_type=source.node_type,
            target_type=new_target_type,
            target_attributes=(
                new_target_attributes
            ),
            relationship_attributes=(
                relationship_attributes
            ),
            confidence=confidence,
        )

        superseded = []

        for old_relationship in (
            old_relationships
        ):

            if (
                old_relationship
                .relationship_id
                ==
                new_relationship
                .relationship_id
            ):

                continue

            superseded.append(
                self.store
                .supersede_relationship(
                    old_relationship
                    .relationship_id,
                    new_relationship
                    .relationship_id,
                )
            )

        return {
            "superseded": superseded,
            "new_relationship": (
                new_relationship
            ),
        }

    # ============================================================
    # ENTITY DESCRIPTION
    # ============================================================

    def describe_entity(
        self,
        name: str,
        node_type: str | None = None,
    ) -> dict[str, Any] | None:

        entity = self.get_entity(
            name=name,
            node_type=node_type,
        )

        if entity is None:

            return None

        return {
            "node": entity.to_dict(),
            "connections": (
                self.get_connections(
                    name=entity.name,
                    node_type=(
                        entity.node_type
                    ),
                    direction="both",
                )
            ),
        }

    # ============================================================
    # GRAPH COUNTS
    # ============================================================

    def counts(
        self,
    ) -> dict[str, int]:

        return {
            "nodes": len(
                self.store.get_all_nodes()
            ),
            "active_nodes": len(
                self.store.get_active_nodes()
            ),
            "relationships": len(
                self.store
                .get_all_relationships()
            ),
            "active_relationships": len(
                self.store
                .get_active_relationships()
            ),
        }


graph_manager = GraphManager()