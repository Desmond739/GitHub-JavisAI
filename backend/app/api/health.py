from fastapi import APIRouter, Response, status

from app.core.config import APP_VERSION
from app.runtime.assistant_runtime import assistant_runtime


router = APIRouter()


@router.get("/health/live")
def liveness() -> dict[str, str]:

    return {
        "status": "alive",
        "service": "MoneroAI",
        "version": APP_VERSION,
    }


@router.get("/health/ready")
def readiness(response: Response) -> dict[str, object]:

    result = assistant_runtime.readiness()

    if not result["ready"]:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result
