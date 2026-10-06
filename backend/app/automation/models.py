from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutomationAction:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    name: str
    description: str
    actions: list[AutomationAction] = field(default_factory=list)