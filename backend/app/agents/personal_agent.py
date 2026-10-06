from app.agents.base_agent import BaseAgent
from app.memory.memory_service import memory_service


class PersonalAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Personal Agent",
            description=(
                "Handles personal tasks, goals, notes, reminders, "
                "schedules, priorities, and daily organization."
            ),
            expertise=(
                "Personal organization, tasks, goals, notes, reminders, "
                "schedules, priorities, productivity, and daily planning."
            ),
            memory_category="personal"
        )

    def can_handle(self, request: str) -> bool:

        keywords = [
            "task",
            "tasks",
            "goal",
            "goals",
            "priority",
            "priorities",
            "note",
            "notes",
            "reminder",
            "reminders",
            "schedule",
            "schedules",
            "today",
            "daily",
            "personal",
            "organize",
            "organization",
            "productivity",
            "focus",
            "priority",
            "moneroai task",
            "current task",
            "current tasks",
            "current goal",
            "current goals"
        ]

        request_lower = request.lower()

        return any(
            keyword in request_lower
            for keyword in keywords
        )

    def handle(self, request: str) -> str:

        request_lower = request.lower()

        # =========================================================
        # PRIMARY PERSONAL OBJECTIVES
        # =========================================================

        if (
            "primary personal objectives" in request_lower
            or "personal objectives" in request_lower
            or "main personal objectives" in request_lower
        ):
            return (
                "Your primary objectives are to build MoneroAI into "
                "a reliable personal AI assistant, improve your technical "
                "skills, build strong financial discipline, develop your "
                "trading consistently, and continue progressing professionally."
            )

        # =========================================================
        # CURRENT PRIORITIES
        # =========================================================

        if (
            "current priorities" in request_lower
            or "what are my priorities" in request_lower
            or "my priorities" in request_lower
        ):
            return (
                "Your current priorities are continuing MoneroAI development, "
                "completing production hardening and non-voice validation, "
                "improving your "
                "technical skills, maintaining disciplined trading development, "
                "maintaining financial discipline, and continuing professional development."
            )

        # =========================================================
        # CURRENT MONEROAI TASK
        # =========================================================

        if (
            "current moneroai task" in request_lower
            or "current moneroai tasks" in request_lower
        ):
            return (
                "Your current MoneroAI task is production hardening and "
                "non-voice validation. Voice tuning and Google authorization "
                "are deferred until you approve the final validation stage."
            )

        # =========================================================
        # CURRENT TASKS
        # =========================================================

        if (
            "current tasks" in request_lower
            or "my tasks" in request_lower
            or "what are my tasks" in request_lower
            or "tasks today" in request_lower
            or "what should i do today" in request_lower
        ):
            return (
                "Your documented tasks are: complete MoneroAI production "
                "hardening, review your trading journal, prepare weekly goals, "
                "and study C#."
            )

        # =========================================================
        # CURRENT GOALS
        # =========================================================

        if (
            "current goals" in request_lower
            or "my goals" in request_lower
            or "what are my goals" in request_lower
        ):
            return (
                "Your documented goals are to build MoneroAI into a reliable "
                "personal AI assistant, improve your technical skills, build "
                "strong financial discipline, develop your trading consistently, "
                "and continue progressing in your career."
            )

        # =========================================================
        # DAILY ORGANIZATION
        # =========================================================

        if (
            "organize my day" in request_lower
            or "organize my tasks" in request_lower
            or "daily organization" in request_lower
        ):
            return (
                "Start with your highest-priority MoneroAI task, then review "
                "your trading journal, prepare your weekly goals, and dedicate "
                "time to C# study."
            )

        # =========================================================
        # MONEROAI PROGRESS
        # =========================================================

        if (
            "moneroai progress" in request_lower
            or "where am i with moneroai" in request_lower
            or "moneroai development progress" in request_lower
        ):
            return (
                "MoneroAI's core application is integrated. The current work "
                "is production hardening and non-voice validation; voice "
                "tuning and Google authorization remain intentionally deferred."
            )

        # =========================================================
        # FALLBACK TO BASE AGENT AI REASONING
        # =========================================================

        return super().handle(request)


personal_agent = PersonalAgent()
