"""No-network validation of accounts, plans, allowance and wallet charging."""

import os
import secrets

os.environ.update(VOICE_ENABLED="false", AUTOMATION_ENABLED="false", OLLAMA_WARMUP_ENABLED="false")

from app.product.auth import auth_service
from app.product.billing import billing_service
from app.product.catalog import PLANS
from app.product.store import platform_store


def run() -> None:
    assert len(PLANS) == 3
    assert max(plan.price_xaf_month for plan in PLANS.values()) == 5000
    assert [PLANS[key].public()["hybrid_limit_gb"] for key in ("core", "plus", "sovereign")] == [512, 2048, 5120]
    email = f"test-{secrets.token_hex(8)}@example.test"
    created = auth_service.register(email, "StrongTest123", "Test Customer")
    user_id = created["user_id"]
    assert auth_service.authenticate(created["token"])["id"] == user_id
    assert auth_service.login(email, "StrongTest123")["user_id"] == user_id
    quote = billing_service.quote_conversation(user_id)
    assert quote["charge_xaf"] == 0 and quote["allowed"]
    billing_service.credit(user_id, 20, f"test:{user_id}", "Test credit")
    with platform_store.connection() as connection:
        for index in range(PLANS["core"].included_conversations_month):
            connection.execute(
                "INSERT INTO usage_events(id,user_id,service,units,charge_xaf,plan_id,created_at) "
                "VALUES(?,?,?,?,?,?,datetime('now'))",
                (secrets.token_hex(16), user_id, "conversation", 1, 0, "core"),
            )
    assert billing_service.quote_conversation(user_id)["charge_xaf"] == 10
    account = billing_service.record_conversation(user_id)
    assert account["wallet_balance_xaf"] == 10
    with platform_store.connection() as connection:
        connection.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        connection.execute("DELETE FROM usage_events WHERE user_id=?", (user_id,))
        connection.execute("DELETE FROM wallet_transactions WHERE user_id=?", (user_id,))
        connection.execute("DELETE FROM users WHERE id=?", (user_id,))
    print("MONEROAI COMMERCIAL BETA VALIDATION: PASSED")
    print("NETWORK USED: NO")
    print("PAYMENT USED: NO")


if __name__ == "__main__":
    run()
