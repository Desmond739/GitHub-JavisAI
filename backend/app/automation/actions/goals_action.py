from pathlib import Path


class GoalsAction:

    def __init__(self):

        self.goals_file = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "goals"
            / "goals.txt"
        )

    def read_goals(self) -> str:

        if not self.goals_file.exists():

            return "No goals file exists yet."

        try:

            content = self.goals_file.read_text(
                encoding="utf-8-sig"
            ).strip()

            if not content:

                return "Your goals list is empty."

            return content

        except OSError as error:

            return f"Could not read goals: {type(error).__name__}"


goals_action = GoalsAction()
