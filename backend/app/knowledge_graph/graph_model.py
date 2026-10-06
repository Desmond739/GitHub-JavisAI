from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeNode:

    node_id: str
    node_type: str
    name: str

    attributes: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = ""
    updated_at: str = ""

    status: str = "active"

    def to_dict(self) -> dict:

        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status
        }


@dataclass
class KnowledgeRelationship:

    relationship_id: str

    source_node_id: str
    relation_type: str
    target_node_id: str

    attributes: dict[str, Any] = field(
        default_factory=dict
    )

    confidence: float = 1.0

    created_at: str = ""
    updated_at: str = ""

    status: str = "active"

    superseded_by: str | None = None

    def to_dict(self) -> dict:

        return {
            "relationship_id": self.relationship_id,
            "source_node_id": self.source_node_id,
            "relation_type": self.relation_type,
            "target_node_id": self.target_node_id,
            "attributes": self.attributes,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "superseded_by": self.superseded_by
        }