from __future__ import annotations

from typing import Optional


class MemoryExtractor:

    def __init__(self):
        self.minimum_content_length = 12

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize(self, text: str) -> str:

        return " ".join(
            text.strip().split()
        )

    # ============================================================
    # PERSONAL MEMORY DETECTION
    # ============================================================

    def _is_question(self, text: str) -> bool:

        question_starters = (
            "what ",
            "why ",
            "how ",
            "when ",
            "where ",
            "who ",
            "which ",
            "can ",
            "could ",
            "would ",
            "should ",
            "is ",
            "are ",
            "do ",
            "does ",
            "did ",
            "will ",
            "have ",
            "has "
        )

        return (
            text.lower().startswith(
                question_starters
            )
            or "?" in text
        )

    # ============================================================
    # DECISION DETECTION
    # ============================================================

    def _extract_decision(
        self,
        text: str
    ) -> Optional[dict]:

        lower = text.lower()

        decision_patterns = (

            "i have decided to ",
            "i decided to ",
            "i've decided to ",
            "i have chosen to ",
            "i chose to ",
            "i will focus on ",
            "i'm going to focus on ",
            "i am going to focus on ",
            "from now on i will ",
            "from now on, i will ",
            "i will continue to ",
            "i intend to ",
            "i plan to focus on "

        )

        if not any(
            pattern in lower
            for pattern in decision_patterns
        ):
            return None

        if (
            "support and resistance" in lower
            or "support & resistance" in lower
            or "s&r" in lower
            or "trading strategy" in lower
            or "forex" in lower
            or "trading" in lower
        ):
            category = "trading"

        elif (
            "moneroai" in lower
            or "ai assistant" in lower
        ):
            category = "technical"

        elif (
            "career" in lower
            or "mtn" in lower
            or "internship" in lower
            or "job" in lower
        ):
            category = "career"

        elif (
            "cybersecurity" in lower
            or "networking" in lower
            or "programming" in lower
            or "c#" in lower
            or "python" in lower
        ):
            category = "technical"

        else:
            category = "personal"

        content = (
            "The user has decided to "
            + lower.split(
                "decided to ",
                1
            )[-1]
            if "decided to " in lower
            else text
        )

        # Preserve the original wording when possible.
        if (
            "moneroai" in lower
            and (
                "reliable personal ai assistant"
                in lower
            )
        ):
            content = (
                "The user has decided to focus on "
                "building MoneroAI into a reliable "
                "personal AI assistant."
            )

        elif (
            "support and resistance" in lower
            or "support & resistance" in lower
            or "s&r" in lower
        ):
            content = (
                "The user's active trading strategy is Support and "
                "Resistance only, without Order Blocks."
            )

        return {
            "memory_type": "decision",
            "category": category,
            "content": content,
            "importance": 8
        }

    # ============================================================
    # PREFERENCE DETECTION
    # ============================================================

    def _extract_preference(
        self,
        text: str
    ) -> Optional[dict]:

        lower = text.lower()

        preference_patterns = (

            "i prefer ",
            "i'd prefer ",
            "i would prefer ",
            "i like ",
            "i don't like ",
            "i do not like ",
            "i want naya to ",
            "i prefer naya to ",
            "i want maya to ",
            "i prefer maya to ",
            "my preference is "

        )

        if not any(
            pattern in lower
            for pattern in preference_patterns
        ):
            return None

        return {
            "memory_type": "preference",
            "category": "personal",
            "content": text,
            "importance": 7
        }

    # ============================================================
    # GOAL DETECTION
    # ============================================================

    def _extract_goal(
        self,
        text: str
    ) -> Optional[dict]:

        lower = text.lower()

        goal_patterns = (

            "i want to ",
            "i would like to ",
            "i'd like to ",
            "my goal is ",
            "my goal is to ",
            "my objective is ",
            "my objective is to ",
            "i aim to ",
            "i hope to ",
            "i'm working toward ",
            "i am working toward ",
            "i'm working towards ",
            "i am working towards "

        )

        if not any(
            pattern in lower
            for pattern in goal_patterns
        ):
            return None

        if (
            "cybersecurity" in lower
            or "cyber security" in lower
            or "networking" in lower
            or "network security" in lower
            or "programming" in lower
            or "c#" in lower
            or "python" in lower
        ):
            category = "technical"

        elif (
            "mtn" in lower
            or "career" in lower
            or "permanent staff" in lower
            or "job" in lower
            or "professional" in lower
        ):
            category = "career"

        elif (
            "saving" in lower
            or "savings" in lower
            or "financial" in lower
            or "money" in lower
            or "budget" in lower
        ):
            category = "finance"

        elif (
            "trading" in lower
            or "forex" in lower
            or "support and resistance" in lower
            or "support & resistance" in lower
            or "s&r" in lower
            or "market structure" in lower
        ):
            category = "trading"

        elif (
            "moneroai" in lower
            or "ai assistant" in lower
            or "software" in lower
        ):
            category = "technical"

        else:
            category = "personal"

        return {
            "memory_type": "goal",
            "category": category,
            "content": text,
            "importance": 8
        }

    # ============================================================
    # FACT DETECTION
    # ============================================================

    def _extract_fact(
        self,
        text: str
    ) -> Optional[dict]:

        lower = text.lower()

        fact_patterns = (

            "i am ",
            "i'm ",
            "i currently ",
            "i currently work ",
            "i work ",
            "i study ",
            "i am studying ",
            "i have ",
            "my name is ",
            "i use ",
            "i built ",
            "i have built "

        )

        if not any(
            pattern in lower
            for pattern in fact_patterns
        ):
            return None

        # Questions are never treated as facts.
        if self._is_question(text):
            return None

        if len(text) < self.minimum_content_length:
            return None

        if (
            "mtn" in lower
            or "internship" in lower
            or "career" in lower
            or "job" in lower
        ):
            category = "career"

        elif (
            "trading" in lower
            or "forex" in lower
            or "support and resistance" in lower
            or "support & resistance" in lower
            or "s&r" in lower
            or "market structure" in lower
        ):
            category = "trading"

        elif (
            "cybersecurity" in lower
            or "networking" in lower
            or "programming" in lower
            or "python" in lower
            or "c#" in lower
            or "iot" in lower
            or "moneroai" in lower
        ):
            category = "technical"

        elif (
            "saving" in lower
            or "financial" in lower
            or "money" in lower
            or "budget" in lower
        ):
            category = "finance"

        else:
            category = "personal"

        return {
            "memory_type": "fact",
            "category": category,
            "content": text,
            "importance": 6
        }

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract(
        self,
        text: str
    ) -> Optional[dict]:

        if not text or not text.strip():
            return None

        text = self._normalize(text)

        if len(text) < self.minimum_content_length:
            return None

        # Questions should never become memories.
        if self._is_question(text):
            return None

        # Priority order matters.
        decision = self._extract_decision(text)

        if decision:
            return decision

        preference = self._extract_preference(text)

        if preference:
            return preference

        goal = self._extract_goal(text)

        if goal:
            return goal

        fact = self._extract_fact(text)

        if fact:
            return fact

        return None

    # ============================================================
    # STORE IF RELEVANT
    # ============================================================

    def remember_if_relevant(
        self,
        text: str
    ):

        extracted = self.extract(text)

        if extracted is None:
            return None

        from app.memory.long_term.memory_manager import (
            memory_manager
        )

        return memory_manager.remember(
            memory_type=extracted["memory_type"],
            category=extracted["category"],
            content=extracted["content"],
            importance=extracted["importance"]
        )


memory_extractor = MemoryExtractor()
