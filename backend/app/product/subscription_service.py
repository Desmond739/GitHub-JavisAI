from __future__ import annotations

from datetime import datetime, timezone

from app.product.catalog import Plan, require_plan
from app.product.store import platform_store


class SubscriptionService:
    def current_plan(self) -> Plan:
        now = datetime.now(timezone.utc).isoformat()
        with platform_store.connection() as connection:
            row = connection.execute(
                "SELECT plan_id FROM subscriptions WHERE status='active' "
                "AND (expires_at IS NULL OR expires_at>?) ORDER BY created_at DESC LIMIT 1",
                (now,),
            ).fetchone()
        if row is None:
            platform_store.set_setting("active_plan", "core")
            return require_plan("core")
        plan = require_plan(str(row["plan_id"]))
        platform_store.set_setting("active_plan", plan.id)
        return plan


subscription_service = SubscriptionService()
