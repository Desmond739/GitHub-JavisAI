from __future__ import annotations

import re

from collections import deque
from typing import Any

from app.knowledge_graph.entity_resolver import (
    EntityResolver,
)

from app.knowledge_graph.graph_manager import (
    GraphManager,
    graph_manager,
)

from app.knowledge_graph.graph_model import (
    KnowledgeNode,
)


class GraphTraverser:

    def __init__(
        self,
        manager: GraphManager | None = None,
        resolver: EntityResolver | None = None,
    ):

        self.manager = (
            manager
            if manager is not None
            else graph_manager
        )

        self.store = self.manager.store

        self.resolver = (
            resolver
            if resolver is not None
            else EntityResolver(
                self.store
            )
        )

    # ============================================================
    # BASIC HELPERS
    # ============================================================

    @staticmethod
    def _normalize_relation(
        value: str,
    ) -> str:

        value = value.strip().lower()

        value = re.sub(
            r"[\s\-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip("_")

    @staticmethod
    def _node_dict(
        node: KnowledgeNode,
    ) -> dict[str, Any]:

        return {
            "node_id": node.node_id,
            "name": node.name,
            "node_type": node.node_type,
            "status": node.status,
        }

    # ============================================================
    # RESOLVE NODE
    # ============================================================

    def resolve_node(
        self,
        name: str,
        node_type: str | None = None,
    ) -> KnowledgeNode | None:

        if not name or not name.strip():

            return None

        result = self.resolver.resolve(
            name=name,
            node_type=node_type,
        )

        node_id = result.get(
            "node_id"
        )

        if node_id:

            return self.store.get_node(
                node_id
            )

        canonical_name = result.get(
            "canonical_name"
        )

        canonical_type = result.get(
            "node_type"
        )

        if not canonical_name:

            return None

        try:

            return self.manager.get_entity(
                name=canonical_name,
                node_type=canonical_type,
            )

        except ValueError:

            return None

    # ============================================================
    # VALIDATE DIRECTION
    # ============================================================

    @staticmethod
    def _validate_direction(
        direction: str,
    ) -> str:

        direction = (
            direction.lower().strip()
        )

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

        return direction

    # ============================================================
    # GET EDGE RECORDS
    # ============================================================

    def _get_edge_records(
        self,
        node_id: str,
        direction: str = "both",
        relation_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:

        direction = (
            self._validate_direction(
                direction
            )
        )

        allowed_relations = None

        if relation_types:

            allowed_relations = {
                self._normalize_relation(
                    relation
                )
                for relation
                in relation_types
            }

        current_node = self.store.get_node(
            node_id
        )

        if current_node is None:

            return []

        results = []

        # --------------------------------------------------------
        # OUTGOING
        # --------------------------------------------------------

        if direction in {
            "outgoing",
            "both",
        }:

            for relationship in (
                self.store.get_outgoing(
                    node_id
                )
            ):

                if (
                    allowed_relations is not None
                    and relationship.relation_type
                    not in allowed_relations
                ):

                    continue

                neighbor = self.store.get_node(
                    relationship.target_node_id
                )

                if (
                    neighbor is None
                    or neighbor.status
                    != "active"
                ):

                    continue

                results.append(
                    {
                        "relationship_id": (
                            relationship
                            .relationship_id
                        ),
                        "relation_type": (
                            relationship
                            .relation_type
                        ),
                        "traversal_direction": (
                            "outgoing"
                        ),
                        "from_node_id": (
                            current_node.node_id
                        ),
                        "from_name": (
                            current_node.name
                        ),
                        "neighbor_node_id": (
                            neighbor.node_id
                        ),
                        "neighbor_name": (
                            neighbor.name
                        ),
                        "neighbor_type": (
                            neighbor.node_type
                        ),
                        "edge_source_node_id": (
                            relationship
                            .source_node_id
                        ),
                        "edge_target_node_id": (
                            relationship
                            .target_node_id
                        ),
                        "confidence": (
                            relationship
                            .confidence
                        ),
                    }
                )

        # --------------------------------------------------------
        # INCOMING
        # --------------------------------------------------------

        if direction in {
            "incoming",
            "both",
        }:

            for relationship in (
                self.store.get_incoming(
                    node_id
                )
            ):

                if (
                    allowed_relations is not None
                    and relationship.relation_type
                    not in allowed_relations
                ):

                    continue

                neighbor = self.store.get_node(
                    relationship.source_node_id
                )

                if (
                    neighbor is None
                    or neighbor.status
                    != "active"
                ):

                    continue

                results.append(
                    {
                        "relationship_id": (
                            relationship
                            .relationship_id
                        ),
                        "relation_type": (
                            relationship
                            .relation_type
                        ),
                        "traversal_direction": (
                            "incoming"
                        ),
                        "from_node_id": (
                            current_node.node_id
                        ),
                        "from_name": (
                            current_node.name
                        ),
                        "neighbor_node_id": (
                            neighbor.node_id
                        ),
                        "neighbor_name": (
                            neighbor.name
                        ),
                        "neighbor_type": (
                            neighbor.node_type
                        ),
                        "edge_source_node_id": (
                            relationship
                            .source_node_id
                        ),
                        "edge_target_node_id": (
                            relationship
                            .target_node_id
                        ),
                        "confidence": (
                            relationship
                            .confidence
                        ),
                    }
                )

        return results

    # ============================================================
    # GET NEIGHBORS
    # ============================================================

    def get_neighbors(
        self,
        name: str,
        node_type: str | None = None,
        direction: str = "both",
        relation_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:

        node = self.resolve_node(
            name=name,
            node_type=node_type,
        )

        if node is None:

            return []

        return self._get_edge_records(
            node_id=node.node_id,
            direction=direction,
            relation_types=relation_types,
        )

    # ============================================================
    # TRAVERSE GRAPH
    # ============================================================

    def traverse(
        self,
        start_name: str,
        start_type: str | None = None,
        max_depth: int = 2,
        direction: str = "both",
        relation_types: list[str] | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:

        if max_depth < 1:

            return []

        if max_results < 1:

            return []

        start = self.resolve_node(
            start_name,
            start_type,
        )

        if start is None:

            return []

        direction = (
            self._validate_direction(
                direction
            )
        )

        queue = deque(
            [
                (
                    start.node_id,
                    0,
                    [start.node_id],
                    [],
                )
            ]
        )

        visited_depth = {
            start.node_id: 0
        }

        results = []

        while queue:

            (
                current_id,
                depth,
                path_nodes,
                path_steps,
            ) = queue.popleft()

            if depth >= max_depth:

                continue

            edges = self._get_edge_records(
                node_id=current_id,
                direction=direction,
                relation_types=relation_types,
            )

            for edge in edges:

                neighbor_id = edge[
                    "neighbor_node_id"
                ]

                if neighbor_id in path_nodes:

                    continue

                new_depth = depth + 1

                previous_depth = (
                    visited_depth.get(
                        neighbor_id
                    )
                )

                if (
                    previous_depth is not None
                    and previous_depth
                    <= new_depth
                ):

                    continue

                neighbor = self.store.get_node(
                    neighbor_id
                )

                if neighbor is None:

                    continue

                new_steps = [
                    *path_steps,
                    edge,
                ]

                visited_depth[
                    neighbor_id
                ] = new_depth

                results.append(
                    {
                        "start": (
                            self._node_dict(
                                start
                            )
                        ),
                        "node": (
                            self._node_dict(
                                neighbor
                            )
                        ),
                        "depth": new_depth,
                        "steps": new_steps,
                    }
                )

                if len(results) >= max_results:

                    return results

                queue.append(
                    (
                        neighbor_id,
                        new_depth,
                        [
                            *path_nodes,
                            neighbor_id,
                        ],
                        new_steps,
                    )
                )

        return results

    # ============================================================
    # FIND SHORTEST PATHS
    # ============================================================

    def find_paths(
        self,
        start_name: str,
        target_name: str,
        start_type: str | None = None,
        target_type: str | None = None,
        max_depth: int = 4,
        direction: str = "both",
        relation_types: list[str] | None = None,
        max_paths: int = 10,
    ) -> list[dict[str, Any]]:

        if max_depth < 0:

            return []

        if max_paths < 1:

            return []

        start = self.resolve_node(
            start_name,
            start_type,
        )

        target = self.resolve_node(
            target_name,
            target_type,
        )

        if (
            start is None
            or target is None
        ):

            return []

        direction = (
            self._validate_direction(
                direction
            )
        )

        if (
            start.node_id
            == target.node_id
        ):

            return [
                {
                    "start": (
                        self._node_dict(
                            start
                        )
                    ),
                    "target": (
                        self._node_dict(
                            target
                        )
                    ),
                    "hops": 0,
                    "steps": [],
                }
            ]

        queue = deque(
            [
                (
                    start.node_id,
                    [start.node_id],
                    [],
                )
            ]
        )

        found_paths = []
        found_depth = None

        while queue:

            (
                current_id,
                path_nodes,
                path_steps,
            ) = queue.popleft()

            current_depth = len(
                path_steps
            )

            if current_depth >= max_depth:

                continue

            if (
                found_depth is not None
                and current_depth
                >= found_depth
            ):

                continue

            edges = self._get_edge_records(
                node_id=current_id,
                direction=direction,
                relation_types=relation_types,
            )

            for edge in edges:

                neighbor_id = edge[
                    "neighbor_node_id"
                ]

                # Cycle protection.
                if neighbor_id in path_nodes:

                    continue

                new_steps = [
                    *path_steps,
                    edge,
                ]

                new_depth = len(
                    new_steps
                )

                if (
                    neighbor_id
                    == target.node_id
                ):

                    if found_depth is None:

                        found_depth = (
                            new_depth
                        )

                    if (
                        new_depth
                        == found_depth
                    ):

                        found_paths.append(
                            {
                                "start": (
                                    self._node_dict(
                                        start
                                    )
                                ),
                                "target": (
                                    self._node_dict(
                                        target
                                    )
                                ),
                                "hops": (
                                    new_depth
                                ),
                                "steps": (
                                    new_steps
                                ),
                            }
                        )

                        if (
                            len(found_paths)
                            >= max_paths
                        ):

                            return found_paths

                    continue

                if (
                    found_depth is not None
                    and new_depth
                    >= found_depth
                ):

                    continue

                queue.append(
                    (
                        neighbor_id,
                        [
                            *path_nodes,
                            neighbor_id,
                        ],
                        new_steps,
                    )
                )

        return found_paths

    # ============================================================
    # SHORTEST PATH
    # ============================================================

    def shortest_path(
        self,
        start_name: str,
        target_name: str,
        start_type: str | None = None,
        target_type: str | None = None,
        max_depth: int = 4,
        direction: str = "both",
        relation_types: list[str] | None = None,
    ) -> dict[str, Any] | None:

        paths = self.find_paths(
            start_name=start_name,
            target_name=target_name,
            start_type=start_type,
            target_type=target_type,
            max_depth=max_depth,
            direction=direction,
            relation_types=relation_types,
            max_paths=1,
        )

        if not paths:

            return None

        return paths[0]

    # ============================================================
    # FORMAT PATH
    # ============================================================

    @staticmethod
    def format_path(
        path: dict[str, Any] | None,
    ) -> str:

        if path is None:

            return ""

        start = path.get(
            "start",
            {}
        )

        text = start.get(
            "name",
            ""
        )

        for step in path.get(
            "steps",
            []
        ):

            relation = step[
                "relation_type"
            ]

            neighbor = step[
                "neighbor_name"
            ]

            if (
                step[
                    "traversal_direction"
                ]
                == "outgoing"
            ):

                text += (
                    f" --{relation}--> "
                    f"{neighbor}"
                )

            else:

                text += (
                    f" <--{relation}-- "
                    f"{neighbor}"
                )

        return text

    # ============================================================
    # EXPLAIN CONNECTION
    # ============================================================

    def explain_connection(
        self,
        start_name: str,
        target_name: str,
        start_type: str | None = None,
        target_type: str | None = None,
        max_depth: int = 4,
        direction: str = "both",
    ) -> str:

        path = self.shortest_path(
            start_name=start_name,
            target_name=target_name,
            start_type=start_type,
            target_type=target_type,
            max_depth=max_depth,
            direction=direction,
        )

        if path is None:

            return (
                f"No connection found between "
                f"{start_name} and "
                f"{target_name} within "
                f"{max_depth} hops."
            )

        formatted = self.format_path(
            path
        )

        return (
            f"Connection found in "
            f"{path['hops']} hop(s): "
            f"{formatted}"
        )


graph_traverser = GraphTraverser()