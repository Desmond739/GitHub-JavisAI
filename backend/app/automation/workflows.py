from app.automation.engine import automation_engine
from app.automation.models import AutomationAction, Workflow


morning_briefing = Workflow(
    name="morning_briefing",
    description="Prepare the user's daily morning briefing.",
    actions=[
        AutomationAction(
            name="check_calendar"
        ),
        AutomationAction(
            name="check_tasks"
        ),
        AutomationAction(
            name="review_goals"
        ),
        AutomationAction(
            name="generate_daily_briefing"
        ),
    ],
)


automation_engine.register_workflow(
    morning_briefing
)
