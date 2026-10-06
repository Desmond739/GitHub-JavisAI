from datetime import time

from app.automation.scheduler import automation_scheduler
from app.automation.engine import automation_engine
from app.product.suggestion_service import suggestion_service


def setup_automation_schedule() -> None:

    automation_scheduler.add_task(
        name="monday_morning_briefing",
        action=lambda: automation_engine.execute_action(
            "speak_daily_briefing"
        ),
        run_time=time(8, 0),
        weekdays={0}
    )

    automation_scheduler.add_task(
        name="daily_personal_suggestion",
        action=suggestion_service.daily_check_in,
        run_time=time(8, 5),
    )
