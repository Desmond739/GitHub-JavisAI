from collections.abc import Callable

from app.automation.actions.notes_action import notes_action
from app.automation.actions.tasks_action import tasks_action
from app.automation.actions.goals_action import goals_action
from app.automation.actions.briefing_action import briefing_action
from app.automation.actions.calendar_action import calendar_action

class ActionRegistry:

    def __init__(self):

        self.actions: dict[str, Callable] = {}

    def register(
        self,
        name: str,
        action: Callable
    ) -> None:

        self.actions[name] = action

    def get(
        self,
        name: str
    ) -> Callable | None:

        return self.actions.get(name)

    def list_actions(self) -> list[str]:

        return list(self.actions.keys())


action_registry = ActionRegistry()


action_registry.register(
    "check_calendar",
    calendar_action.read_today
)

action_registry.register(
    "read_notes",
    notes_action.read_notes
)

action_registry.register(
    "check_tasks",
    tasks_action.read_tasks
)

action_registry.register(
    "review_goals",
    goals_action.read_goals
)

action_registry.register(
    "generate_daily_briefing",
    briefing_action.generate_briefing
)

action_registry.register(
    "speak_daily_briefing",
    briefing_action.speak_briefing
)
