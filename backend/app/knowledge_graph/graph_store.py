from __future__ import annotations

import json
import os
import re
import threading
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .graph_model import (  # type: ignore[reportMissingImports]
    KnowledgeNode,
    KnowledgeRelationship,
)


class GraphStore:

    VALID_NODE_STATUSES = {
        "active",
        "archived",
    }

    VALID_RELATIONSHIP_STATUSES = {
        "active",
        "superseded",
        "archived",
    }

    def __init__(
        self,
        storage_path: str | Path | None = None,
    ):

        self._lock = threading.RLock()

        backend_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        if storage_path is None:

            self.storage_path = (
                backend_root
                / "data"
                / "knowledge_graph"
                / "graph.json"
            )

        else:

            self.storage_path = Path(
                storage_path
            ).resolve()

        self._ensure_storage()

    # ============================================================
    # BASIC UTILITIES
    # ============================================================

    @staticmethod
    def _now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _normalize_name(
        value: str
    ) -> str:

        return " ".join(
            value.strip().lower().split()
        )

    @staticmethod
    def _normalize_token(
        value: str
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

    # ============================================================
    # STORAGE INITIALIZATION
    # ============================================================

    def _ensure_storage(self):

        with self._lock:

            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if not self.storage_path.exists():

                self._save_raw(
                    {
                        "nodes": [],
                        "relationships": [],
                    }
                )

    # ============================================================
    # RAW LOAD
    # ============================================================

    def _load_raw(self) -> dict:

        with self._lock:

            try:

                with self.storage_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = json.load(
                        file
                    )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    f"Knowledge graph file is invalid JSON: "
                    f"{self.storage_path}"
                ) from exc

            if not isinstance(
                data,
                dict,
            ):

                raise RuntimeError(
                    "Knowledge graph storage must "
                    "contain a JSON object."
                )

            nodes = data.get(
                "nodes",
                [],
            )

            relationships = data.get(
                "relationships",
                [],
            )

            if not isinstance(
                nodes,
                list,
            ):

                raise RuntimeError(
                    "'nodes' must be a list."
                )

            if not isinstance(
                relationships,
                list,
            ):

                raise RuntimeError(
                    "'relationships' must be a list."
                )

            return {
                "nodes": nodes,
                "relationships": relationships,
            }

    # ============================================================
    # RAW SAVE
    # ============================================================

    def _save_raw(
        self,
        data: dict,
    ):

        with self._lock:

            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_path = (
                self.storage_path.with_suffix(
                    self.storage_path.suffix
                    + ".tmp"
                )
            )

            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            os.replace(
                temporary_path,
                self.storage_path,
            )

    # ============================================================
    # DICT → NODE
    # ============================================================

    @staticmethod
    def _node_from_dict(
        data: dict,
    ) -> KnowledgeNode:

        return KnowledgeNode(
            node_id=data["node_id"],
            node_type=data["node_type"],
            name=data["name"],
            attributes=data.get(
                "attributes",
                {},
            ),
            created_at=data.get(
                "created_at",
                "",
            ),
            updated_at=data.get(
                "updated_at",
                "",
            ),
            status=data.get(
                "status",
                "active",
            ),
        )

    # ============================================================
    # DICT → RELATIONSHIP
    # ============================================================

    @staticmethod
    def _relationship_from_dict(
        data: dict,
    ) -> KnowledgeRelationship:

        return KnowledgeRelationship(
            relationship_id=(
                data["relationship_id"]
            ),
            source_node_id=(
                data["source_node_id"]
            ),
            relation_type=(
                data["relation_type"]
            ),
            target_node_id=(
                data["target_node_id"]
            ),
            attributes=data.get(
                "attributes",
                {},
            ),
            confidence=float(
                data.get(
                    "confidence",
                    1.0,
                )
            ),
            created_at=data.get(
                "created_at",
                "",
            ),
            updated_at=data.get(
                "updated_at",
                "",
            ),
            status=data.get(
                "status",
                "active",
            ),
            superseded_by=data.get(
                "superseded_by"
            ),
        )

    # ============================================================
    # GET ALL NODES
    # ============================================================

    def get_all_nodes(
        self,
    ) -> list[KnowledgeNode]:

        data = self._load_raw()

        return [
            self._node_from_dict(node)
            for node in data["nodes"]
        ]

    # ============================================================
    # GET ACTIVE NODES
    # ============================================================

    def get_active_nodes(
        self,
    ) -> list[KnowledgeNode]:

        return [
            node
            for node in self.get_all_nodes()
            if node.status == "active"
        ]

    # ============================================================
    # GET NODE
    # ============================================================

    def get_node(
        self,
        node_id: str,
    ) -> KnowledgeNode | None:

        for node in self.get_all_nodes():

            if node.node_id == node_id:

                return node

        return None

    # ============================================================
    # FIND NODES
    # ============================================================

    def find_nodes(
        self,
        name: str | None = None,
        node_type: str | None = None,
        status: str | None = "active",
    ) -> list[KnowledgeNode]:

        normalized_name = None

        normalized_type = None

        if name is not None:

            normalized_name = (
                self._normalize_name(
                    name
                )
            )

        if node_type is not None:

            normalized_type = (
                self._normalize_token(
                    node_type
                )
            )

        results = []

        for node in self.get_all_nodes():

            if (
                status is not None
                and node.status != status
            ):
                continue

            if (
                normalized_name is not None
                and self._normalize_name(
                    node.name
                )
                != normalized_name
            ):
                continue

            if (
                normalized_type is not None
                and self._normalize_token(
                    node.node_type
                )
                != normalized_type
            ):
                continue

            results.append(
                node
            )

        return results

    # ============================================================
    # ADD NODE
    # ============================================================

    def add_node(
        self,
        name: str,
        node_type: str,
        attributes: dict[str, Any] | None = None,
        node_id: str | None = None,
    ) -> KnowledgeNode:

        if not name or not name.strip():

            raise ValueError(
                "Node name cannot be empty."
            )

        if not node_type or not node_type.strip():

            raise ValueError(
                "Node type cannot be empty."
            )

        normalized_type = (
            self._normalize_token(
                node_type
            )
        )

        existing = self.find_nodes(
            name=name,
            node_type=normalized_type,
            status="active",
        )

        if existing:

            return existing[0]

        with self._lock:

            data = self._load_raw()

            now = self._now()

            node = KnowledgeNode(
                node_id=(
                    node_id
                    or str(uuid.uuid4())
                ),
                node_type=normalized_type,
                name=name.strip(),
                attributes=(
                    attributes.copy()
                    if attributes
                    else {}
                ),
                created_at=now,
                updated_at=now,
                status="active",
            )

            if any(
                existing_node.get(
                    "node_id"
                )
                == node.node_id
                for existing_node
                in data["nodes"]
            ):

                raise ValueError(
                    f"Node ID already exists: "
                    f"{node.node_id}"
                )

            data["nodes"].append(
                node.to_dict()
            )

            self._save_raw(
                data
            )

            return node

    # ============================================================
    # UPDATE NODE
    # ============================================================

    def update_node(
        self,
        node_id: str,
        name: str | None = None,
        node_type: str | None = None,
        attributes: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> KnowledgeNode:

        with self._lock:

            data = self._load_raw()

            for node_data in data["nodes"]:

                if (
                    node_data.get(
                        "node_id"
                    )
                    != node_id
                ):
                    continue

                if name is not None:

                    if not name.strip():

                        raise ValueError(
                            "Node name cannot "
                            "be empty."
                        )

                    node_data["name"] = (
                        name.strip()
                    )

                if node_type is not None:

                    if not node_type.strip():

                        raise ValueError(
                            "Node type cannot "
                            "be empty."
                        )

                    node_data["node_type"] = (
                        self._normalize_token(
                            node_type
                        )
                    )

                if attributes is not None:

                    current_attributes = (
                        node_data.get(
                            "attributes",
                            {}
                        )
                    )

                    current_attributes.update(
                        attributes
                    )

                    node_data["attributes"] = (
                        current_attributes
                    )

                if status is not None:

                    if (
                        status
                        not in
                        self.VALID_NODE_STATUSES
                    ):

                        raise ValueError(
                            f"Invalid node status: "
                            f"{status}"
                        )

                    node_data["status"] = status

                node_data["updated_at"] = (
                    self._now()
                )

                self._save_raw(
                    data
                )

                return self._node_from_dict(
                    node_data
                )

            raise KeyError(
                f"Node not found: {node_id}"
            )

    # ============================================================
    # ARCHIVE NODE
    # ============================================================

    def archive_node(
        self,
        node_id: str,
    ) -> KnowledgeNode:

        return self.update_node(
            node_id=node_id,
            status="archived",
        )

    # ============================================================
    # GET ALL RELATIONSHIPS
    # ============================================================

    def get_all_relationships(
        self,
    ) -> list[KnowledgeRelationship]:

        data = self._load_raw()

        return [
            self._relationship_from_dict(
                relationship
            )
            for relationship
            in data["relationships"]
        ]

    # ============================================================
    # GET ACTIVE RELATIONSHIPS
    # ============================================================

    def get_active_relationships(
        self,
    ) -> list[KnowledgeRelationship]:

        return [
            relationship
            for relationship
            in self.get_all_relationships()
            if relationship.status == "active"
        ]

    # ============================================================
    # GET RELATIONSHIP
    # ============================================================

    def get_relationship(
        self,
        relationship_id: str,
    ) -> KnowledgeRelationship | None:

        for relationship in (
            self.get_all_relationships()
        ):

            if (
                relationship.relationship_id
                == relationship_id
            ):

                return relationship

        return None

    # ============================================================
    # FIND RELATIONSHIPS
    # ============================================================

    def find_relationships(
        self,
        source_node_id: str | None = None,
        relation_type: str | None = None,
        target_node_id: str | None = None,
        status: str | None = "active",
    ) -> list[KnowledgeRelationship]:

        normalized_relation = None

        if relation_type is not None:

            normalized_relation = (
                self._normalize_token(
                    relation_type
                )
            )

        results = []

        for relationship in (
            self.get_all_relationships()
        ):

            if (
                status is not None
                and relationship.status
                != status
            ):
                continue

            if (
                source_node_id is not None
                and relationship.source_node_id
                != source_node_id
            ):
                continue

            if (
                normalized_relation is not None
                and relationship.relation_type
                != normalized_relation
            ):
                continue

            if (
                target_node_id is not None
                and relationship.target_node_id
                != target_node_id
            ):
                continue

            results.append(
                relationship
            )

        return results

    # ============================================================
    # ADD RELATIONSHIP
    # ============================================================

    def add_relationship(
        self,
        source_node_id: str,
        relation_type: str,
        target_node_id: str,
        attributes: dict[str, Any] | None = None,
        confidence: float = 1.0,
        relationship_id: str | None = None,
    ) -> KnowledgeRelationship:

        if not relation_type or not relation_type.strip():

            raise ValueError(
                "Relationship type cannot "
                "be empty."
            )

        source = self.get_node(
            source_node_id
        )

        target = self.get_node(
            target_node_id
        )

        if source is None:

            raise KeyError(
                f"Source node not found: "
                f"{source_node_id}"
            )

        if target is None:

            raise KeyError(
                f"Target node not found: "
                f"{target_node_id}"
            )

        if source.status != "active":

            raise ValueError(
                "Source node must be active."
            )

        if target.status != "active":

            raise ValueError(
                "Target node must be active."
            )

        normalized_relation = (
            self._normalize_token(
                relation_type
            )
        )

        existing = self.find_relationships(
            source_node_id=source_node_id,
            relation_type=normalized_relation,
            target_node_id=target_node_id,
            status="active",
        )

        if existing:

            return existing[0]

        confidence = float(
            confidence
        )

        if not 0.0 <= confidence <= 1.0:

            raise ValueError(
                "Confidence must be between "
                "0.0 and 1.0."
            )

        with self._lock:

            data = self._load_raw()

            now = self._now()

            relationship = (
                KnowledgeRelationship(
                    relationship_id=(
                        relationship_id
                        or str(uuid.uuid4())
                    ),
                    source_node_id=(
                        source_node_id
                    ),
                    relation_type=(
                        normalized_relation
                    ),
                    target_node_id=(
                        target_node_id
                    ),
                    attributes=(
                        attributes.copy()
                        if attributes
                        else {}
                    ),
                    confidence=confidence,
                    created_at=now,
                    updated_at=now,
                    status="active",
                    superseded_by=None,
                )
            )

            if any(
                existing_relationship.get(
                    "relationship_id"
                )
                == relationship.relationship_id
                for existing_relationship
                in data["relationships"]
            ):

                raise ValueError(
                    "Relationship ID already "
                    f"exists: "
                    f"{relationship.relationship_id}"
                )

            data["relationships"].append(
                relationship.to_dict()
            )

            self._save_raw(
                data
            )

            return relationship

    # ============================================================
    # UPDATE RELATIONSHIP
    # ============================================================

    def update_relationship(
        self,
        relationship_id: str,
        relation_type: str | None = None,
        attributes: dict[str, Any] | None = None,
        confidence: float | None = None,
        status: str | None = None,
        superseded_by: str | None = None,
    ) -> KnowledgeRelationship:

        with self._lock:

            data = self._load_raw()

            for relationship_data in (
                data["relationships"]
            ):

                if (
                    relationship_data.get(
                        "relationship_id"
                    )
                    != relationship_id
                ):
                    continue

                if relation_type is not None:

                    if not relation_type.strip():

                        raise ValueError(
                            "Relationship type "
                            "cannot be empty."
                        )

                    relationship_data[
                        "relation_type"
                    ] = self._normalize_token(
                        relation_type
                    )

                if attributes is not None:

                    current_attributes = (
                        relationship_data.get(
                            "attributes",
                            {}
                        )
                    )

                    current_attributes.update(
                        attributes
                    )

                    relationship_data[
                        "attributes"
                    ] = current_attributes

                if confidence is not None:

                    confidence = float(
                        confidence
                    )

                    if not (
                        0.0
                        <= confidence
                        <= 1.0
                    ):

                        raise ValueError(
                            "Confidence must be "
                            "between 0.0 and 1.0."
                        )

                    relationship_data[
                        "confidence"
                    ] = confidence

                if status is not None:

                    if (
                        status
                        not in
                        self.VALID_RELATIONSHIP_STATUSES
                    ):

                        raise ValueError(
                            "Invalid relationship "
                            f"status: {status}"
                        )

                    relationship_data[
                        "status"
                    ] = status

                if superseded_by is not None:

                    relationship_data[
                        "superseded_by"
                    ] = superseded_by

                relationship_data[
                    "updated_at"
                ] = self._now()

                self._save_raw(
                    data
                )

                return (
                    self._relationship_from_dict(
                        relationship_data
                    )
                )

            raise KeyError(
                "Relationship not found: "
                f"{relationship_id}"
            )

    # ============================================================
    # SUPERSEDE RELATIONSHIP
    # ============================================================

    def supersede_relationship(
        self,
        old_relationship_id: str,
        new_relationship_id: str,
    ) -> KnowledgeRelationship:

        old_relationship = (
            self.get_relationship(
                old_relationship_id
            )
        )

        new_relationship = (
            self.get_relationship(
                new_relationship_id
            )
        )

        if old_relationship is None:

            raise KeyError(
                "Old relationship not found: "
                f"{old_relationship_id}"
            )

        if new_relationship is None:

            raise KeyError(
                "New relationship not found: "
                f"{new_relationship_id}"
            )

        return self.update_relationship(
            relationship_id=(
                old_relationship_id
            ),
            status="superseded",
            superseded_by=(
                new_relationship_id
            ),
        )

    # ============================================================
    # ARCHIVE RELATIONSHIP
    # ============================================================

    def archive_relationship(
        self,
        relationship_id: str,
    ) -> KnowledgeRelationship:

        return self.update_relationship(
            relationship_id=(
                relationship_id
            ),
            status="archived",
        )

    # ============================================================
    # OUTGOING RELATIONSHIPS
    # ============================================================

    def get_outgoing(
        self,
        node_id: str,
    ) -> list[KnowledgeRelationship]:

        return self.find_relationships(
            source_node_id=node_id,
            status="active",
        )

    # ============================================================
    # INCOMING RELATIONSHIPS
    # ============================================================

    def get_incoming(
        self,
        node_id: str,
    ) -> list[KnowledgeRelationship]:

        return self.find_relationships(
            target_node_id=node_id,
            status="active",
        )

    # ============================================================
    # NEIGHBORS
    # ============================================================

    def get_neighbors(
        self,
        node_id: str,
    ) -> list[KnowledgeNode]:

        neighbor_ids = set()

        for relationship in (
            self.get_outgoing(
                node_id
            )
        ):

            neighbor_ids.add(
                relationship.target_node_id
            )

        for relationship in (
            self.get_incoming(
                node_id
            )
        ):

            neighbor_ids.add(
                relationship.source_node_id
            )

        neighbors = []

        for neighbor_id in neighbor_ids:

            node = self.get_node(
                neighbor_id
            )

            if (
                node is not None
                and node.status == "active"
            ):

                neighbors.append(
                    node
                )

        return neighbors


graph_store = GraphStore()