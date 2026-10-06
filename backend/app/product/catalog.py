from __future__ import annotations

from dataclasses import asdict, dataclass


GIB = 1024 ** 3


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    price_xaf_month: int
    hybrid_limit_bytes: int
    included_cloud_bytes: int
    included_conversations_month: int
    features: tuple[str, ...]

    def public(self) -> dict[str, object]:
        result = asdict(self)
        result["features"] = list(self.features)
        result["hybrid_limit_gb"] = self.hybrid_limit_bytes // GIB
        result["included_cloud_gb"] = self.included_cloud_bytes // GIB
        return result


PLANS = {
    "core": Plan(
        "core", "Naya Core", 0, 512 * GIB, 1 * GIB, 100,
        ("chat_and_naya_voice", "basic_memory", "wake_phrase", "basic_suggestions"),
    ),
    "plus": Plan(
        "plus", "Naya Plus", 2500, 2 * 1024 * GIB, 10 * GIB, 500,
        ("long_term_memory", "goals_and_routines", "proactive_suggestions", "google_read_only"),
    ),
    "sovereign": Plan(
        "sovereign", "Naya Sovereign", 5000, 5 * 1024 * GIB, 25 * GIB, 1500,
        ("controlled_automation", "connector_sdk", "priority_processing", "advanced_workflows"),
    ),
}


def require_plan(plan_id: str) -> Plan:
    try:
        return PLANS[plan_id]
    except KeyError as error:
        raise ValueError("Unknown subscription plan.") from error
