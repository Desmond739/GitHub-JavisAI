from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.config import DATA_DIR, LISTENING_MODE
from app.personal_data.google_workspace_connector import google_workspace_connector
from app.product.catalog import PLANS, require_plan
from app.product.momo import MoMoConfigurationError, momo_client
from app.product.store import platform_store
from app.product.suggestion_service import suggestion_service
from app.product.task_service import task_service
from app.product.connectors import connector_registry
from app.product.manual_payments import manual_payment_service
from app.product.r2_storage import r2_storage
from app.product.subscription_service import subscription_service
from app.api.account import current_user
from app.product.billing import billing_service


router = APIRouter()


class PaymentRequest(BaseModel):
    plan_id: str
    phone: str = Field(min_length=9, max_length=24)


class JobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=80)
    payload: dict[str, object] = {}


class ConfirmationRequest(BaseModel):
    approved: bool


class SuggestionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=1000)
    reason: str = Field(min_length=1, max_length=500)


class ManualPaymentRequest(BaseModel):
    plan_id: str
    payer_phone: str = Field(min_length=9, max_length=24)


class WalletTopUpRequest(BaseModel):
    amount_xaf: int = Field(ge=100, le=50000)
    payer_phone: str = Field(min_length=9, max_length=24)


class PaymentReferenceRequest(BaseModel):
    reference: str = Field(min_length=4, max_length=100)


class PaymentReviewRequest(BaseModel):
    approved: bool


@router.get("/platform/status")
def platform_status(user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    plan = billing_service.plan_for(str(user["id"]))
    used = sum(path.stat().st_size for path in DATA_DIR.rglob("*") if path.is_file())
    disk = shutil.disk_usage(DATA_DIR)
    return {
        "plan": plan.public(), "listening_mode": LISTENING_MODE,
        "privacy": {"ambient_recording": False, "wake_phrase_required": True,
                    "sensitive_actions_require_confirmation": True,
                    "self_modification": False},
        "storage": {"used_bytes": used, "hybrid_limit_bytes": plan.hybrid_limit_bytes,
                    "local_free_bytes": disk.free, "cloud_included_bytes": plan.included_cloud_bytes},
        "payments": {"api": momo_client.status(), "manual": manual_payment_service.status()},
        "cloud": r2_storage.status(), "google": google_workspace_connector.status(),
        "account": billing_service.account(str(user["id"])),
    }


@router.get("/plans")
def plans() -> list[dict[str, object]]:
    return [plan.public() for plan in PLANS.values()]


@router.get("/connectors")
def connectors(user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    return connector_registry.list()


@router.post("/payments/momo/request")
def request_payment(request: PaymentRequest, user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return momo_client.request_subscription_payment(request.plan_id, request.phone)
    except (ValueError, MoMoConfigurationError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/payments/momo/{reference_id}")
def payment_status(reference_id: str, user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return momo_client.payment_status(reference_id)
    except (ValueError, MoMoConfigurationError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/payments/manual")
def create_manual_payment(request: ManualPaymentRequest,
                          user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return manual_payment_service.create(request.plan_id, request.payer_phone, str(user["id"]))
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/payments/manual/{payment_id}/reference")
def submit_manual_reference(payment_id: str, request: PaymentReferenceRequest,
                            user: dict[str, object] = Depends(current_user)) -> dict[str, str]:
    try:
        return manual_payment_service.submit_reference(payment_id, request.reference, str(user["id"]))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/payments/manual/wallet")
def create_wallet_top_up(request: WalletTopUpRequest,
                         user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return manual_payment_service.create_wallet_top_up(request.amount_xaf, request.payer_phone,
                                                           str(user["id"]))
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/payments/manual/{payment_id}/review")
def review_manual_payment(payment_id: str, request: PaymentReviewRequest,
                          x_naya_payment_admin: str = Header(default="")) -> dict[str, str]:
    try:
        return manual_payment_service.verify(payment_id, request.approved, x_naya_payment_admin)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/cloud/objects/{name:path}")
async def upload_cloud_object(name: str, request: Request,
                              user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    length = int(request.headers.get("content-length", "0") or "0")
    if length > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Upload is too large.")
    data = await request.body()
    try:
        return r2_storage.put(f"users/{user['id']}/{name}", data)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/cloud/objects/{name:path}")
def download_cloud_object(name: str, user: dict[str, object] = Depends(current_user)) -> Response:
    try:
        return Response(r2_storage.get(f"users/{user['id']}/{name}"), media_type="application/octet-stream")
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/jobs")
def jobs(user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    return platform_store.list_user_rows("jobs", str(user["id"]))


@router.post("/jobs")
def create_job(request: JobRequest, user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return task_service.create(request.title, request.action, request.payload, str(user["id"]))
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.post("/jobs/{job_id}/confirmation")
def confirm_job(job_id: str, request: ConfirmationRequest,
                user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    try:
        return task_service.confirm(job_id, request.approved, str(user["id"]))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/notifications")
def notifications(user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    return platform_store.list_user_rows("notifications", str(user["id"]))


@router.get("/suggestions")
def suggestions(user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    return platform_store.list_user_rows("suggestions", str(user["id"]))


@router.post("/suggestions")
def create_suggestion(request: SuggestionRequest,
                      user: dict[str, object] = Depends(current_user)) -> dict[str, str]:
    return suggestion_service.create(request.title, request.body, request.reason, str(user["id"]))


@router.get("/google/gmail")
def gmail_summary(limit: int = 20,
                  user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    try:
        return google_workspace_connector.gmail_summary(limit)
    except (FileNotFoundError, PermissionError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/google/drive")
def drive_files(limit: int = 50,
                user: dict[str, object] = Depends(current_user)) -> list[dict[str, object]]:
    try:
        return google_workspace_connector.drive_files(limit)
    except (FileNotFoundError, PermissionError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
