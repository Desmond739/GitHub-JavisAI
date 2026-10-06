"""Offline security and behavior checks for RC2 early access."""

import base64
import os
from unittest.mock import patch

os.environ["VOICE_ENABLED"] = "false"
os.environ["AUTOMATION_ENABLED"] = "false"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"

import app.product.manual_payments as manual_module
import app.product.r2_storage as r2_module
from app.product.manual_payments import ManualPaymentService
from app.product.r2_storage import R2Storage


def run() -> None:
    encryption_key = base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
    captured: dict[str, bytes] = {}
    store = R2Storage()

    def fake_request(method: str, object_key: str, payload: bytes = b"") -> bytes:
        if method == "PUT":
            captured[object_key] = payload
            return b""
        return captured[object_key]

    with patch.multiple(r2_module, R2_ACCOUNT_ID="account", R2_ACCESS_KEY_ID="access",
                        R2_SECRET_ACCESS_KEY="secret", R2_BUCKET_NAME="bucket",
                        R2_ENCRYPTION_KEY=encryption_key), patch.object(store, "_request", side_effect=fake_request):
        result = store.put("tests/private.txt", b"owner data")
        assert result["encrypted"] is True
        assert b"owner data" not in captured[result["object_key"]]
        assert store.get("tests/private.txt") == b"owner data"

    service = ManualPaymentService()
    with patch.multiple(manual_module, MOMO_MANUAL_PAYMENT_NUMBER="237600000000",
                        MOMO_MANUAL_ACCOUNT_NAME="Test Owner", PAYMENT_ADMIN_TOKEN="admin-secret"):
        payment = service.create("plus", "237611111111", "test-user")
        assert payment["status"] == "awaiting_payment"
        submitted = service.submit_reference(payment["payment_id"], "TX-TEST-123", "test-user")
        assert submitted["status"] == "pending_verification"
        try:
            service.verify(payment["payment_id"], True, "wrong")
        except PermissionError:
            pass
        else:
            raise AssertionError("Wrong payment administrator token was accepted.")
        reviewed = service.verify(payment["payment_id"], False, "admin-secret")
        assert reviewed["status"] == "rejected"

    print("NAYA EARLY ACCESS RC2 VALIDATION: PASSED")
    print("R2 NETWORK USED: NO")
    print("MOMO TRANSACTION USED: NO")
    print("ANDROID HARDWARE USED: NO")


if __name__ == "__main__":
    run()
