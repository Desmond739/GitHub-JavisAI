from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from app.core.config import (
    MOMO_API_KEY, MOMO_API_USER, MOMO_BASE_URL, MOMO_CALLBACK_URL,
    MOMO_COLLECTION_SUBSCRIPTION_KEY, MOMO_ENVIRONMENT, MOMO_TARGET_ENVIRONMENT,
)
from app.product.catalog import require_plan
from app.product.store import platform_store


class MoMoConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MoMoCredentials:
    subscription_key: str = MOMO_COLLECTION_SUBSCRIPTION_KEY
    api_user: str = MOMO_API_USER
    api_key: str = MOMO_API_KEY

    @property
    def ready(self) -> bool:
        return bool(self.subscription_key and self.api_user and self.api_key)


class MoMoClient:
    """MTN MoMo Collections client. Money movement is initiated only by the owner."""

    def __init__(self) -> None:
        self.credentials = MoMoCredentials()

    def status(self) -> dict[str, object]:
        return {
            "provider": "mtn_momo_collections", "environment": MOMO_ENVIRONMENT,
            "configured": self.credentials.ready,
            "callback_configured": bool(MOMO_CALLBACK_URL),
            "currency": "XAF", "automatic_debits": False,
        }

    def _request(self, path: str, *, method: str = "GET", headers: dict[str, str] | None = None,
                 body: dict[str, object] | None = None) -> tuple[int, dict[str, object]]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{MOMO_BASE_URL.rstrip('/')}{path}", method=method, data=data,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return response.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MoMo request failed with status {error.code}.") from error

    def access_token(self) -> str:
        if not self.credentials.ready:
            raise MoMoConfigurationError("MTN MoMo credentials are not configured.")
        basic = base64.b64encode(
            f"{self.credentials.api_user}:{self.credentials.api_key}".encode("utf-8")
        ).decode("ascii")
        _, result = self._request("/collection/token/", method="POST", headers={
            "Authorization": f"Basic {basic}",
            "Ocp-Apim-Subscription-Key": self.credentials.subscription_key,
        })
        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("MoMo did not return an access token.")
        return token

    def request_subscription_payment(self, plan_id: str, phone: str) -> dict[str, object]:
        plan = require_plan(plan_id)
        if plan.price_xaf_month <= 0:
            raise ValueError("The free plan does not require payment.")
        normalized = "".join(character for character in phone if character.isdigit())
        if len(normalized) < 9 or len(normalized) > 15:
            raise ValueError("Enter a valid MoMo phone number including country code.")
        reference = str(uuid4())
        token = self.access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self.credentials.subscription_key,
            "X-Reference-Id": reference,
            "X-Target-Environment": MOMO_TARGET_ENVIRONMENT,
        }
        if MOMO_CALLBACK_URL:
            headers["X-Callback-Url"] = MOMO_CALLBACK_URL
        self._request("/collection/v1_0/requesttopay", method="POST", headers=headers, body={
            "amount": str(plan.price_xaf_month), "currency": "XAF",
            "externalId": reference,
            "payer": {"partyIdType": "MSISDN", "partyId": normalized},
            "payerMessage": f"{plan.name} monthly subscription",
            "payeeNote": "Naya subscription",
        })
        platform_store.insert("subscriptions", {
            "plan_id": plan.id, "status": "pending", "provider": "mtn_momo",
            "external_id": reference, "expires_at": None,
        })
        return {"reference_id": reference, "status": "pending", "amount_xaf": plan.price_xaf_month}

    def payment_status(self, reference_id: str) -> dict[str, object]:
        UUID(reference_id)
        token = self.access_token()
        _, result = self._request(f"/collection/v1_0/requesttopay/{reference_id}", headers={
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self.credentials.subscription_key,
            "X-Target-Environment": MOMO_TARGET_ENVIRONMENT,
        })
        return result


momo_client = MoMoClient()
