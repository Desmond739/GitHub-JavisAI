from datetime import datetime, time
from threading import Event, RLock, Thread
from typing import Callable

from app.core.logging_config import log_event


class ScheduledTask:

    def __init__(
        self,
        name: str,
        action: Callable[[], object],
        run_time: time,
        weekdays: set[int] | None = None
    ):

        self.name = name
        self.action = action
        self.run_time = run_time
        self.weekdays = weekdays

        self.last_run_date = None

    def is_due(self, now: datetime) -> bool:

        if self.weekdays is not None:
            if now.weekday() not in self.weekdays:
                return False

        if now.time().hour != self.run_time.hour:
            return False

        if now.time().minute != self.run_time.minute:
            return False

        if self.last_run_date == now.date():
            return False

        return True

    def execute(self) -> object:

        try:
            return self.action()

        finally:
            self.last_run_date = datetime.now().date()


class AutomationScheduler:

    def __init__(self):

        self.tasks: list[ScheduledTask] = []

        self.stop_event = Event()

        self.thread: Thread | None = None

        self._lock = RLock()

    def add_task(
        self,
        name: str,
        action: Callable[[], object],
        run_time: time,
        weekdays: set[int] | None = None
    ) -> None:

        with self._lock:

            existing = next(
                (
                    task
                    for task in self.tasks
                    if task.name == name
                ),
                None,
            )

            if existing is not None:
                existing.action = action
                existing.run_time = run_time
                existing.weekdays = weekdays
                return

            self.tasks.append(
                ScheduledTask(
                    name=name,
                    action=action,
                    run_time=run_time,
                    weekdays=weekdays,
                )
            )

    def list_tasks(self) -> list[str]:

        with self._lock:
            return [
                task.name
                for task in self.tasks
            ]

    def check_tasks(self) -> list[str]:

        now = datetime.now()

        executed = []

        with self._lock:
            tasks = list(self.tasks)

        for task in tasks:

            if task.is_due(now):

                try:
                    task.execute()

                except Exception as error:
                    log_event(
                        "scheduled_task_failed",
                        level=40,
                        component="automation",
                        error_type=type(error).__name__,
                        status="failed",
                    )
                    continue

                else:
                    executed.append(task.name)
                    log_event(
                        "scheduled_task_completed",
                        component="automation",
                        status="completed",
                    )

        return executed

    def start(self) -> None:

        with self._lock:

            if (
                self.thread is not None
                and self.thread.is_alive()
            ):
                return

            self.stop_event.clear()

            self.thread = Thread(
                target=self._run,
                name="moneroai-automation",
                daemon=True,
            )

            self.thread.start()

    def stop(self) -> None:

        self.stop_event.set()

        with self._lock:
            thread = self.thread

        if (
            thread is not None
            and thread.is_alive()
        ):
            thread.join(timeout=1.0)

        with self._lock:

            if (
                self.thread is not None
                and not self.thread.is_alive()
            ):
                self.thread = None

    def status(self) -> dict[str, object]:

        with self._lock:
            thread = self.thread

        return {
            "running": (
                thread is not None
                and thread.is_alive()
            ),
            "tasks": self.list_tasks(),
        }

    def _run(self) -> None:

        while not self.stop_event.is_set():

            self.check_tasks()

            self.stop_event.wait(30)


automation_scheduler = AutomationScheduler()
