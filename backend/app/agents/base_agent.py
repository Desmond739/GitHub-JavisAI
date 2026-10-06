from abc import ABC, abstractmethod

from app.core.config import OLLAMA_SPECIALIST_MODEL
from app.services.ollama_client import ollama
from app.memory.memory_service import memory_service


SPECIALIST_MODEL = OLLAMA_SPECIALIST_MODEL


class BaseAgent(ABC):

    def __init__(
        self,
        name: str,
        description: str,
        expertise: str,
        memory_category: str
    ):

        self.name = name
        self.description = description
        self.expertise = expertise
        self.memory_category = memory_category

    @abstractmethod
    def can_handle(self, request: str) -> bool:
        pass

    def handle(self, request: str) -> str:

        memory = memory_service.read_memory(
            self.memory_category
        )

        prompt = (
            f"You are the {self.name}.\n\n"
            f"Expertise and important facts:\n"
            f"{self.expertise}\n\n"
            f"Authorized personal memory:\n"
            f"{memory}\n\n"
            f"User question:\n"
            f"{request}\n\n"
            "Answer using the exact personal facts above. "
            "Do not combine unrelated facts. "
            "Do not invent information. "
            "If the question asks about a specific project, "
            "identify that exact project. "
            "Answer in one short sentence."
        )

        response = ollama.chat(
            model=SPECIALIST_MODEL,
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
                "num_predict": 20
            }
        )

        return response["message"]["content"].strip()
