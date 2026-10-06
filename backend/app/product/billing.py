"""Transparent subscription allowance and prepaid-wallet metering."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import USAGE_PRICE_XAF
from app.product.catalog import require_plan
from app.product.store import platform_store, utc_now


class BillingService:
    def plan_for(self, user_id: str):
        with platform_store.connection() as connection:
            row = connection.execute(
                "SELECT plan_id FROM subscriptions WHERE user_id=? AND status='active' "
                "AND (expires_at IS NULL OR expires_at>?) ORDER BY created_at DESC LIMIT 1",
                (user_id, datetime.now(timezone.utc).isoformat())).fetchone()
        return require_plan(str(row["plan_id"]) if row else "core")

    def wallet_balance(self, user_id: str) -> int:
        with platform_store.connection() as connection:
            row = connection.execute("SELECT COALESCE(SUM(amount_xaf),0) balance FROM wallet_transactions WHERE user_id=?",
                                     (user_id,)).fetchone()
        return int(row["balance"])

    def monthly_usage(self, user_id: str) -> int:
        start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        with platform_store.connection() as connection:
            row = connection.execute("SELECT COALESCE(SUM(units),0) used FROM usage_events WHERE user_id=? AND service='conversation' AND created_at>=?",
                                     (user_id, start)).fetchone()
        return int(row["used"])

    def quote_conversation(self, user_id: str) -> dict[str, object]:
        plan = self.plan_for(user_id)
        used = self.monthly_usage(user_id)
        charge = 0 if used < plan.included_conversations_month else USAGE_PRICE_XAF
        balance = self.wallet_balance(user_id)
        return {"plan_id": plan.id, "included": plan.included_conversations_month,
                "used": used, "charge_xaf": charge, "wallet_balance_xaf": balance,
                "allowed": charge == 0 or balance >= charge}

    def record_conversation(self, user_id: str) -> dict[str, object]:
        quote = self.quote_conversation(user_id)
        if not quote["allowed"]:
            raise PermissionError("Monthly conversations are used up. Add funds to your wallet to continue at 10 XAF per message.")
        charge = int(quote["charge_xaf"])
        with platform_store.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if charge:
                balance = connection.execute("SELECT COALESCE(SUM(amount_xaf),0) balance FROM wallet_transactions WHERE user_id=?",
                                             (user_id,)).fetchone()["balance"]
                if int(balance) < charge:
                    raise PermissionError("Wallet balance is too low.")
            connection.execute(
                "INSERT INTO usage_events(id,user_id,service,units,charge_xaf,plan_id,created_at) VALUES(?,?,?,?,?,?,?)",
                (uuid4().hex, user_id, "conversation", 1, charge, quote["plan_id"], utc_now()),
            )
            if charge:
                connection.execute(
                    "INSERT INTO wallet_transactions(id,user_id,amount_xaf,kind,description,reference,created_at) VALUES(?,?,?,?,?,?,?)",
                    (uuid4().hex, user_id, -charge, "usage", "Naya conversation", None, utc_now()),
                )
        return self.account(user_id)

    def credit(self, user_id: str, amount_xaf: int, reference: str, description: str) -> None:
        if amount_xaf <= 0:
            raise ValueError("Credit must be positive.")
        platform_store.insert("wallet_transactions", {"user_id": user_id, "amount_xaf": amount_xaf,
            "kind": "top_up", "description": description, "reference": reference})

    def account(self, user_id: str) -> dict[str, object]:
        plan = self.plan_for(user_id)
        return {"plan": plan.public(), "usage": self.monthly_usage(user_id),
                "wallet_balance_xaf": self.wallet_balance(user_id), "overage_xaf_per_conversation": USAGE_PRICE_XAF}


billing_service = BillingService()
