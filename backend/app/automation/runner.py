import time

from app.automation.scheduler import automation_scheduler
from app.automation.scheduler_setup import (
    setup_automation_schedule,
)


def start_automation_scheduler() -> None:

    setup_automation_schedule()
    automation_scheduler.start()

    print("MoneroAI automation scheduler started.")
    print(
        "Registered tasks:",
        automation_scheduler.list_tasks()
    )

    try:

        while True:

            time.sleep(60)

    except KeyboardInterrupt:

        print("Stopping MoneroAI automation scheduler...")

        automation_scheduler.stop()

        print("Automation scheduler stopped.")


if __name__ == "__main__":

    start_automation_scheduler()
