from app.core.config import (
    ASSISTANT_NAME,
    OLLAMA_MODEL,
)
from app.services.ollama_client import ollama


MODEL = OLLAMA_MODEL


def generate_response(
    message: str,
    max_tokens: int = 40
) -> str:

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are {ASSISTANT_NAME}, a helpful personal AI assistant. "
                    "Respond directly, naturally, and concisely. "
                    "Do not provide lengthy explanations unless requested."
                )
            },
            {
                "role": "user",
                "content": message
            }
        ],
        think=False,
        stream=False,
        keep_alive=-1,
        options={
            "num_predict": max_tokens
        }
    )

    return response["message"]["content"].strip()
