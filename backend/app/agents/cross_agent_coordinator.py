from app.agents.career_agent import career_agent
from app.agents.finance_agent import finance_agent
from app.agents.trading_agent import trading_agent
from app.agents.technical_agent import technical_agent
from app.agents.personal_agent import personal_agent

from app.core.config import ASSISTANT_NAME
from app.core.config import OLLAMA_SPECIALIST_MODEL
from app.services.ollama_client import ollama


class CrossAgentCoordinator:

    def __init__(self):

        self.agents = {
            "Career Agent": career_agent,
            "Finance Agent": finance_agent,
            "Trading Agent": trading_agent,
            "Technical Agent": technical_agent,
            "Personal Agent": personal_agent
        }

        self.model = OLLAMA_SPECIALIST_MODEL

    def identify_domains(self, request: str) -> list[str]:

        request_lower = request.lower()

        domains = []

        career_terms = [
            "career",
            "internship",
            "intern",
            "mtn",
            "job",
            "professional",
            "permanent staff",
            "employment",
            "cv",
            "resume"
        ]

        finance_terms = [
            "finance",
            "financial",
            "money",
            "saving",
            "savings",
            "budget",
            "budgeting",
            "income",
            "expenses"
        ]

        trading_terms = [
            "trading",
            "trade",
            "forex",
            "market structure",
            "pullback",
            "support and resistance",
            "prop firm",
            "trading journal"
        ]

        technical_terms = [
            "technical",
            "technology",
            "programming",
            "python",
            "c#",
            "cybersecurity",
            "networking",
            "iot",
            "esp32",
            "moneroai",
            "software",
            "coding",
            "ai"
        ]

        personal_terms = [
            "my goals",
            "my tasks",
            "my priorities",
            "my schedule",
            "my progress",
            "my development",
            "my plans",
            "my current"
        ]

        if any(term in request_lower for term in career_terms):
            domains.append("Career Agent")

        if any(term in request_lower for term in finance_terms):
            domains.append("Finance Agent")

        if any(term in request_lower for term in trading_terms):
            domains.append("Trading Agent")

        if any(term in request_lower for term in technical_terms):
            domains.append("Technical Agent")

        if any(term in request_lower for term in personal_terms):
            domains.append("Personal Agent")

        return domains

    def is_cross_agent_request(self, request: str) -> bool:

        return len(self.identify_domains(request)) >= 2

    def collect_context(
        self,
        request: str,
        domains: list[str]
    ) -> str:

        context_parts = []

        for domain in domains:

            agent = self.agents.get(domain)

            if agent is None:
                continue

            try:

                response = agent.handle(request)

                context_parts.append(
                    f"{domain}:\n{response}"
                )

            except Exception:

                context_parts.append(
                    f"{domain}:\nUnable to retrieve information."
                )

        return "\n\n".join(context_parts)

    def synthesize(
        self,
        request: str,
        context: str
    ) -> str:

        prompt = (
            f"You are {ASSISTANT_NAME}, a personal AI assistant.\n\n"
            "Use only the authorized information below.\n"
            "Do not invent personal facts.\n"
            "Combine the information into one concise answer.\n"
            "Answer in no more than two sentences.\n\n"
            f"AUTHORIZED INFORMATION:\n{context}\n\n"
            f"USER QUESTION:\n{request}"
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            think=False,
            stream=False,
            keep_alive=-1,
            options={
                "num_predict": 40
            }
        )

        return response["message"]["content"].strip()

    def handle(self, request: str) -> str:

        request_lower = request.lower()

        # =========================================================
        # DETERMINISTIC PERSONAL PRIORITY RESPONSE
        # =========================================================

        if (
            "what should i prioritize" in request_lower
            and (
                "career" in request_lower
                or "internship" in request_lower
                or "mtn" in request_lower
            )
            and (
                "technical" in request_lower
                or "moneroai" in request_lower
            )
        ):

            return (
                "Prioritize your MTN career development and practical "
                "technical skills, especially cybersecurity, product and "
                "project management, while continuing MoneroAI development. "
                "Maintain financial discipline and keep trading risk separate "
                "from essential savings."
            )

        # =========================================================
        # NORMAL CROSS-AGENT PROCESSING
        # =========================================================

        domains = self.identify_domains(request)

        if len(domains) < 2:

            return (
                "Cross-agent intelligence requires information "
                "from at least two specialized domains."
            )

        context = self.collect_context(
            request,
            domains
        )

        return self.synthesize(
            request,
            context
        )


cross_agent_coordinator = CrossAgentCoordinator()
