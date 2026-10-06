from __future__ import annotations

import re

from threading import Event

from app.core.config import (
    WAKE_LISTEN_SECONDS,
    WAKE_PHRASE,
)
from app.services.speech_service import (
    SpeechService,
    speech_service,
)


class NayaListener:

    def __init__(
        self,
        speech_service_instance: SpeechService | None = None,
    ) -> None:

        self.speech_service = (
            speech_service_instance
            if speech_service_instance is not None
            else speech_service
        )
        self.wake_duration = WAKE_LISTEN_SECONDS

    @staticmethod
    def _normalize(value: str) -> str:

        return " ".join(
            re.findall(
                r"[a-z0-9]+",
                value.casefold(),
            )
        )

    def matches_wake_phrase(self, text: str) -> bool:

        phrase = self._normalize(WAKE_PHRASE)
        heard = self._normalize(text)

        if not phrase or not heard:
            return False

        return bool(
            re.search(
                rf"(?:^|\s){re.escape(phrase)}(?:$|\s)",
                heard,
            )
        )

    def listen_for_wake_phrase(
        self,
        stop_event: Event | None = None,
    ) -> bool:

        while (
            stop_event is None
            or not stop_event.is_set()
        ):

            audio = self.speech_service.record_audio(
                duration=self.wake_duration,
            )
            text = self.speech_service.transcribe(audio)

            if self.matches_wake_phrase(text):
                return True

        return False


naya_listener = NayaListener()
