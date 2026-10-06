from app.agents.base_agent import BaseAgent


class CareerAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Career Agent",
            description=(
                "Handles career development, education, "
                "employment, CVs, professional growth, "
                "internships, and career planning."
            ),
            expertise=(
                "Career planning, professional development, "
                "education, CV improvement, interviews, "
                "workplace development, internships, "
                "skills development, professional growth, "
                "and long-term career planning."
            ),
            memory_category="career"
        )

    def can_handle(self, request: str) -> bool:

        keywords = [
            "career",
            "job",
            "cv",
            "resume",
            "interview",
            "work",
            "employment",
            "promotion",
            "skills",
            "education",
            "professional",
            "internship",
            "intern",
            "permanent staff",
            "permanent",
            "mtn",
            "workplace",
            "professional development",
            "career development"
        ]

        request = request.lower()

        return any(
            keyword in request
            for keyword in keywords
        )


career_agent = CareerAgent()