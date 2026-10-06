from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import compare_digest

from app.core.config import (
    MOMO_MANUAL_ACCOUNT_NAME, MOMO_MANUAL_PAYMENT_NUMBER, PAYMENT_ADMIN_TOKEN,
)
from app.product.catalog import require_plan
from app.product.store import platform_store, utc_now
from app.product.billing import billing_service


class ManualPaymentService:
    """Temporary MoMo flow. Payment never activates a plan without verification."""

    def status(self) -> dict[str, object]:
        return {
            "enabled": bool(MOMO_MANUAL_PAYMENT_NUMBER and MOMO_MANUAL_ACCOUNT_NAME),
            "account_name": MOMO_MANUAL_ACCOUNT_NAME or None,
            "masked_number": self._masked_number(),
            "automatic_activation": False,
        }

    def _masked_number(self) -> str | None:
        value = "".join(c for c in MOMO_MANUAL_PAYMENT_NUMBER if c.isdigit())
        return f"***{value[-4:]}" if len(value) >= 4 else None

    def create(self, plan_id: str, payer_phone: str, user_id: str) -> dict[str, object]:
        plan = require_plan(plan_id)
        if plan.price_xaf_month <= 0:
            raise ValueError("The free plan requires no payment.")
        if not MOMO_MANUAL_PAYMENT_NUMBER or not MOMO_MANUAL_ACCOUNT_NAME:
            raise RuntimeError("Temporary manual MoMo payment is not configured.")
        payer = "".join(c for c in payer_phone if c.isdigit())
        if not 9 <= len(payer) <= 15:
            raise ValueError("Enter a valid payer number.")
        payment_id = platform_store.insert("manual_payments", {
            "plan_id": plan.id, "amount_xaf": plan.price_xaf_month,
            "payer_phone": payer, "transaction_reference": None,
            "status": "awaiting_payment", "verified_at": None, "user_id": user_id,
            "purpose": "subscription",
        })
        return {
            "payment_id": payment_id, "status": "awaiting_payment",
            "amount_xaf": plan.price_xaf_month,
            "payee_number": MOMO_MANUAL_PAYMENT_NUMBER,
            "payee_name": MOMO_MANUAL_ACCOUNT_NAME,
            "instruction": "Pay using MTN MoMo, then submit the transaction reference. Activation waits for manual verification.",
        }

    def create_wallet_top_up(self, amount_xaf: int, payer_phone: str, user_id: str) -> dict[str, object]:
        if not 100 <= amount_xaf <= 50_000:
            raise ValueError("Wallet top-up must be between 100 and 50,000 XAF.")
        if not MOMO_MANUAL_PAYMENT_NUMBER or not MOMO_MANUAL_ACCOUNT_NAME:
            raise RuntimeError("Temporary manual MoMo payment is not configured.")
        payer = "".join(c for c in payer_phone if c.isdigit())
        if not 9 <= len(payer) <= 15:
            raise ValueError("Enter a valid payer number.")
        payment_id = platform_store.insert("manual_payments", {
            "plan_id": "wallet", "amount_xaf": amount_xaf, "payer_phone": payer,
            "transaction_reference": None, "status": "awaiting_payment",
            "verified_at": None, "user_id": user_id, "purpose": "wallet_top_up",
        })
        return {"payment_id": payment_id, "status": "awaiting_payment", "amount_xaf": amount_xaf,
                "payee_number": MOMO_MANUAL_PAYMENT_NUMBER, "payee_name": MOMO_MANUAL_ACCOUNT_NAME,
                "instruction": "Pay using MTN MoMo, then submit the reference. Wallet credit waits for verification."}

    def submit_reference(self, payment_id: str, reference: str, user_id: str) -> dict[str, str]:
        reference = reference.strip()
        if len(reference) < 4 or len(reference) > 100:
            raise ValueError("Enter the MoMo transaction reference.")
        with platform_store.connection() as connection:
            changed = connection.execute(
                "UPDATE manual_payments SET transaction_reference=?, status='pending_verification' "
                "WHERE id=? AND user_id=? AND status='awaiting_payment'", (reference, payment_id, user_id),
            ).rowcount
        if changed != 1:
            raise LookupError("Payment request was not found or was already submitted.")
        return {"payment_id": payment_id, "status": "pending_verification"}

    def verify(self, payment_id: str, approved: bool, admin_token: str) -> dict[str, str]:
        if not PAYMENT_ADMIN_TOKEN or not compare_digest(admin_token, PAYMENT_ADMIN_TOKEN):
            raise PermissionError("Invalid payment administrator token.")
        status = "verified" if approved else "rejected"
        with platform_store.connection() as connection:
            row = connection.execute(
                "SELECT * FROM manual_payments WHERE id=? AND status='pending_verification'", (payment_id,),
            ).fetchone()
            if row is None:
                raise LookupError("Pending payment was not found.")
            connection.execute(
                "UPDATE manual_payments SET status=?, verified_at=? WHERE id=?",
                (status, utc_now(), payment_id),
            )
        if approved and row["purpose"] == "wallet_top_up":
            billing_service.credit(str(row["user_id"]), int(row["amount_xaf"]),
                                   f"manual:{payment_id}", "Verified MoMo wallet top-up")
        elif approved:
            expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            platform_store.insert("subscriptions", {
                "plan_id": row["plan_id"], "status": "active", "provider": "manual_momo",
                "external_id": f"manual:{payment_id}", "expires_at": expires, "user_id": row["user_id"],
            })
        platform_store.insert("audit_log", {
            "event": "manual_payment_reviewed",
            "detail": f"payment={sha256(payment_id.encode()).hexdigest()[:12]};status={status}",
        })
        return {"payment_id": payment_id, "status": status}


manual_payment_service = ManualPaymentService()
