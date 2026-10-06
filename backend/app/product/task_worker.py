from __future__ import annotations

from threading import Event, RLock, Thread

from app.automation.engine import automation_engine
from app.automation.action_registry import action_registry
from app.product.store import platform_store


class TaskWorker:
    def __init__(self) -> None:
        self._stop = Event()
        self._lock = RLock()
        self._thread: Thread | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = Thread(target=self._run, name="naya-task-worker", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def status(self) -> dict[str, bool]:
        with self._lock:
            return {"running": bool(self._thread and self._thread.is_alive())}

    def process_once(self) -> bool:
        job = platform_store.claim_job()
        if job is None:
            return False
        if bool(job["confirmation_required"]):
            action = action_registry.get(str(job["action"]))
            try:
                result = str(action()) if action is not None else f"UNAVAILABLE: {job['action']}"
            except Exception as error:
                result = f"Action failed: {job['action']} ({type(error).__name__})"
        else:
            result = automation_engine.execute_action(str(job["action"]))
        failed = result.startswith(("DENIED:", "UNAVAILABLE:", "Action failed:"))
        status = "failed" if failed else "completed"
        platform_store.update_job(str(job["id"]), status, result)
        platform_store.insert("notifications", {
            "title": f"Task {status}",
            "body": f"{job['title']}: {result}",
            "read": 0,
            "user_id": job.get("user_id"),
        })
        return True

    def _run(self) -> None:
        while not self._stop.is_set():
            while self.process_once():
                if self._stop.is_set():
                    return
            self._stop.wait(2.0)


task_worker = TaskWorker()
