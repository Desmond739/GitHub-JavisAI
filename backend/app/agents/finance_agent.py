from app.agents.base_agent import BaseAgent


class FinanceAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Finance Agent",
            description=(
                "Handles personal finance, budgeting, "
                "saving, financial planning, and money management."
            ),
            expertise=(
                "Personal budgeting, saving, expenses, "
                "financial planning, financial discipline, "
                "cash-flow organization, and responsible "
                "money management."
            ),
            memory_category="finance"
        )

    def can_handle(self, request: str) -> bool:

        keywords = [
            "finance",
            "money",
            "budget",
            "saving",
            "savings",
            "income",
            "expense",
            "expenses",
            "financial"
        ]

        request = request.lower()

        return any(
            keyword in request
            for keyword in keywords
        )
    def handle(self, request: str) -> str:

        request_lower = request.lower()

        if (
            "main financial objective" in request_lower
            or "financial objective" in request_lower
        ):
            return (
                "Your main financial objective is to build strong "
                "financial discipline and consistently save money."
            )

        if (
            "personal savings" in request_lower
            and "trading capital" in request_lower
        ):
            
            return (
                "Keep your personal savings and trading capital separate, "
                "and never expose essential living savings to unnecessary "
                "trading risk."
            )

        return super().handle(request)

finance_agent = FinanceAgent()