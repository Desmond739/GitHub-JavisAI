from __future__ import annotations

import json

from app.product.store import platform_store
from app.security.permission_manager import PermissionLevel, PermissionManager


class TaskService:
    def __init__(self) -> None:
        self.permissions = PermissionManager()

    def create(self, title: str, action: str, payload: dict[str, object], user_id: str) -> dict[str, object]:
        permission = self.permissions.get_permission(action)
        if permission == PermissionLevel.DENY:
            raise PermissionError("This action is not permitted.")
        confirmation = permission == PermissionLevel.CONFIRM
        status = (
            "manual_required" if permission == PermissionLevel.MANUAL
            else "awaiting_confirmation" if confirmation
            else "queued"
        )
        job_id = platform_store.insert("jobs", {
            "title": title, "action": action, "payload": payload,
            "risk": permission.value, "status": status,
            "confirmation_required": int(confirmation),
            "user_id": user_id,
        })
        platform_store.insert("audit_log", {
            "event": "task_created", "detail": json.dumps({"job_id": job_id, "action": action}),
        })
        return {"id": job_id, "status": status, "confirmation_required": confirmation}

    def confirm(self, job_id: str, approved: bool, user_id: str) -> dict[str, object]:
        status = "queued" if approved else "cancelled"
        with platform_store.connection() as connection:
            owned = connection.execute("SELECT 1 FROM jobs WHERE id=? AND user_id=?", (job_id, user_id)).fetchone()
        if owned is None:
            raise LookupError("Task not found.")
        if not platform_store.update_job(job_id, status, "Owner declined." if not approved else None):
            raise LookupError("Task not found.")
        platform_store.insert("audit_log", {
            "event": "task_confirmation", "detail": json.dumps({"job_id": job_id, "approved": approved}),
        })
        return {"id": job_id, "status": status}


task_service = TaskService()
