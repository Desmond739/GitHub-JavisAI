from pathlib import Path

from app.personal_data.task_query_engine import (
    task_query_engine,
)


class TasksAction:

    def __init__(self):

        self.tasks_file = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "tasks"
            / "tasks.txt"
        )

    def read_tasks(self) -> str:

        if task_query_engine.has_active_source():

            answer = task_query_engine.answer(
                "What tasks do I have?"
            )

            if answer:
                return answer

        if not self.tasks_file.exists():

            return "No task list exists yet."

        try:

            content = self.tasks_file.read_text(
                encoding="utf-8-sig"
            ).strip()

            if not content:

                return "Your task list is empty."

            return content

        except OSError as error:

            return f"Could not read tasks: {type(error).__name__}"


tasks_action = TasksAction()
