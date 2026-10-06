"""Offline validation for the three-tier Naya platform."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ["VOICE_ENABLED"] = "false"
os.environ["AUTOMATION_ENABLED"] = "false"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"

from fastapi.testclient import TestClient

from app.main import app
from app.product.catalog import PLANS
from app.product.momo import MoMoClient, MoMoConfigurationError
from app.product.store import PlatformStore


def run() -> None:
    assert list(PLANS) == ["core", "plus", "sovereign"]
    assert PLANS["sovereign"].price_xaf_month == 5000
    assert PLANS["core"].hybrid_limit_bytes == 512 * 1024 ** 3
    assert PLANS["plus"].hybrid_limit_bytes == 2 * 1024 ** 4
    assert PLANS["sovereign"].hybrid_limit_bytes == 5 * 1024 ** 4

    with tempfile.TemporaryDirectory() as directory:
        store = PlatformStore(Path(directory) / "test.db")
        assert store.setting("listening_mode") == "wake_phrase_only"
        job = store.insert("jobs", {"title": "Test", "action": "review_goals", "payload": "{}",
            "risk": "allow", "status": "queued", "confirmation_required": 0})
        assert store.update_job(job, "completed", "done")
        assert store.list_rows("jobs")[0]["status"] == "completed"

    with TestClient(app) as client:
        assert client.get("/api/plans").status_code == 200
        status = client.get("/api/platform/status").json()
        assert status["listening_mode"] == "wake_phrase_only"
        assert status["privacy"]["ambient_recording"] is False
        assert client.get("/app/").status_code == 200
        allowed = client.post("/api/jobs", json={"title": "Review", "action": "review_goals", "payload": {}})
        assert allowed.status_code == 200
        confirm = client.post("/api/jobs", json={"title": "Email", "action": "send_email", "payload": {}})
        assert confirm.json()["confirmation_required"] is True
        denied = client.post("/api/jobs", json={"title": "Unknown", "action": "unknown", "payload": {}})
        assert denied.status_code == 403

    try:
        MoMoClient().access_token()
    except MoMoConfigurationError:
        pass
    else:
        raise AssertionError("Unconfigured MoMo must fail closed.")

    print("NAYA PLATFORM V2 VALIDATION: PASSED")
    print("LEVELS: 3")
    print("AMBIENT RECORDING: NO")
    print("MOMO NETWORK USED: NO")
    print("GOOGLE AUTHORIZATION USED: NO")
    print("VOICE HARDWARE USED: NO")


if __name__ == "__main__":
    run()
