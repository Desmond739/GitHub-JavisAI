from app.core.config import (
    ASSISTANT_NAME,
    OLLAMA_MODEL,
)
from app.services.ollama_client import ollama


class GeneralAgent:

    name = "General Agent"

    def __init__(self):

        self.model = OLLAMA_MODEL

    def can_handle(self, request: str) -> bool:

        return True

    def handle(self, request: str) -> str:

        if not request or not request.strip():

            return "Please provide a request."

        prompt = (
            f"You are {ASSISTANT_NAME}, the user's personal AI assistant.\n\n"
            "Answer the user's question directly and accurately.\n"
            "If relevant personal information is provided in the "
            "AUTHORIZED MEMORY section, use it.\n"
            "Do not invent personal facts.\n"
            "Keep the response concise unless the user asks for "
            "an explanation.\n\n"
            f"USER REQUEST:\n{request}"
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


general_agent = GeneralAgent()
