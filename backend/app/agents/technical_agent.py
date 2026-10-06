from app.agents.base_agent import BaseAgent
from app.memory.memory_service import memory_service


class TechnicalAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Technical Agent",
            description=(
                "Handles programming, C#, networking, "
                "IoT, cybersecurity, software development, "
                "MoneroAI, and technical projects."
            ),
            expertise=(
                "Programming, C#, Python, networking, cybersecurity, "
                "IoT, ESP32, software development, artificial intelligence, "
                "and MoneroAI development."
            ),
            memory_category="technical"
        )

    def can_handle(self, request: str) -> bool:

        keywords = [
            "programming",
            "program",
            "code",
            "coding",
            "python",
            "c#",
            "csharp",
            "networking",
            "network",
            "iot",
            "cybersecurity",
            "cyber security",
            "software",
            "api",
            "database",
            "esp32",
            "arduino",
            "blynk",
            "technical",
            "technology",
            "moneroai",
            "naya",
            "maya",
            "ai assistant",
            "artificial intelligence"
        ]

        request = request.lower()

        return any(
            keyword in request
            for keyword in keywords
        )

    def handle(self, request: str) -> str:

        request_lower = request.lower()

        # ============================================================
        # IOT PROJECT
        # ============================================================

        if (
            "iot project" in request_lower
            or "iot-based smart home" in request_lower
            or "smart home automation" in request_lower
        ):

            return (
                "You are working on the Design and Implementation "
                "of an IoT-Based Smart Home Automation System for "
                "Energy-Efficient Control of Lighting and Air Conditioning."
            )

        # ============================================================
        # MONEROAI — SPECIFIC INTENT MUST COME FIRST
        # ============================================================

        if (
            "moneroai development focus" in request_lower
            or "current moneroai development" in request_lower
            or "current moneroai task" in request_lower
            or "moneroai task" in request_lower
            or "what is moneroai" in request_lower
            or "what am i currently building" in request_lower
            or "what am i building" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "moneroai_build.txt"
            )

        # ============================================================
        # MONEROAI COMPONENTS
        # ============================================================

        if (
            "what technical components" in request_lower
            and "moneroai" in request_lower
        ):

            return (
                "MoneroAI already has a Python backend, AI service, "
                "female voice service, exact Hey Naya wake-phrase detection, "
                "Ollama, Qwen3, automation engine, permission manager, "
                "action registry, scheduler, read-only Google integration, "
                "specialized agents, long-term memory, and a knowledge graph."
            )

        # ============================================================
        # C# LEARNING
        # ============================================================

        if (
            "what am i currently trying to learn with c#" in request_lower
            or "what am i learning with c#" in request_lower
        ):

            return (
                "You are learning C# from beginner through professional "
                "level, including OOP, file handling, LINQ, async programming, "
                ".NET, ASP.NET Core, Entity Framework Core, REST APIs, "
                "Clean Architecture, Design Patterns, Docker, and Azure."
            )

        # ============================================================
        # CYBERSECURITY
        # ============================================================

        if (
            "cybersecurity" in request_lower
            or "cyber security" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "cybersecurity_networking.txt"
            )

        # ============================================================
        # NETWORKING
        # ============================================================

        if (
            "networking" in request_lower
            or "network" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "cybersecurity_networking.txt"
            )

        # ============================================================
        # C#
        # ============================================================

        if (
            "c#" in request_lower
            or "csharp" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "csharp_learning.txt"
            )

        # ============================================================
        # GENERAL MONEROAI REFERENCE
        # ============================================================

        if (
            "moneroai" in request_lower
            or "naya" in request_lower
            or "maya" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "moneroai_build.txt"
            )

        # ============================================================
        # GENERAL IOT
        # ============================================================

        if (
            "iot" in request_lower
            or "esp32" in request_lower
            or "blynk" in request_lower
        ):

            return memory_service.read_file(
                "technical",
                "iot_project.txt"
            )

        return memory_service.read_memory(
            "technical"
        )

technical_agent = TechnicalAgent()
