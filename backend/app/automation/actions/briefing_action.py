from app.automation.actions.notes_action import notes_action
from app.automation.actions.tasks_action import tasks_action
from app.automation.actions.goals_action import goals_action
from app.automation.actions.calendar_action import calendar_action
from app.services.ai_service import generate_response
from app.services.voice_service import voice_service
from app.core.logging_config import log_event


class BriefingAction:

    def collect_briefing_data(self) -> str:

        notes = notes_action.read_notes()
        calendar = calendar_action.read_today()
        tasks = tasks_action.read_tasks()
        goals = goals_action.read_goals()

        return (
            f"CALENDAR:\n{calendar}\n\n"
            f"NOTES:\n{notes}\n\n"
            f"TASKS:\n{tasks}\n\n"
            f"GOALS:\n{goals}"
        )

    def generate_briefing(self) -> str:

        data = self.collect_briefing_data()

        prompt = (
            "Create a spoken briefing in ONE short sentence.\n\n"
            f"{data}\n\n"
            "Mention only the top priorities. "
            "Maximum 20 words. "
            "No markdown. "
            "No explanations. "
            "Do not invent information."
        )

        try:
            return generate_response(
                prompt,
                max_tokens=20
            )

        except Exception as error:
            log_event(
                "briefing_generation_failed",
                level=40,
                component="automation",
                error_type=type(error).__name__,
            )
            return (
                "Your local AI model is unavailable, so the morning "
                "briefing could not be summarized."
            )

    def speak_briefing(self) -> str:

        briefing = self.generate_briefing()

        voice_service.speak(briefing)

        return briefing


briefing_action = BriefingAction()
