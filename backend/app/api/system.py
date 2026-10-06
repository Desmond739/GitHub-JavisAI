from fastapi import APIRouter

from app.personal_data.google_integration_service import (
    google_integration_service,
)
from app.runtime.assistant_runtime import assistant_runtime


router = APIRouter()


@router.get("/system/status")
def system_status() -> dict[str, object]:

    return assistant_runtime.status()


@router.post("/google/sync")
def synchronize_google_read_only() -> dict[str, object]:

    return google_integration_service.sync_all()
