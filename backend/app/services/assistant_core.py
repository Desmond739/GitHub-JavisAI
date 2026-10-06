from __future__ import annotations

from threading import RLock
from time import monotonic

from app.agents.agent_coordinator import agent_coordinator
from app.core.logging_config import log_event
from app.services.ollama_client import voice_inference_mode


class AssistantCore:
    """One serialized entry point shared by API and voice requests."""

    def __init__(self) -> None:

        self._lock = RLock()
        self._last_response_seconds: float | None = None
        self._last_error_type: str | None = None
        self._last_response_mode: str | None = None

    def respond(self, request: str) -> str:

        return self._respond(
            request,
            response_mode="standard",
        )

    def respond_voice(self, request: str) -> str:
        """Answer through the bounded fast-model route used by speech."""

        with voice_inference_mode():
            return self._respond(
                request,
                response_mode="voice_fast",
            )

    def _respond(
        self,
        request: str,
        *,
        response_mode: str,
    ) -> str:

        message = str(request).strip()

        if not message:
            return "Please provide a request."

        with self._lock:

            started_at = monotonic()
            self._last_response_mode = response_mode

            try:
                response = agent_coordinator.handle(message)
                self._last_error_type = None

            except Exception as error:
                self._last_error_type = type(error).__name__
                log_event(
                    "assistant_response_failed",
                    level=40,
                    component="assistant_core",
                    error_type=self._last_error_type,
                )
                response = (
                    "I could not complete that response within "
                    "five seconds. Please try again."
                )

            self._last_response_seconds = round(
                monotonic() - started_at,
                3,
            )

            log_event(
                "assistant_response_completed",
                component="assistant_core",
                duration_ms=round(
                    self._last_response_seconds * 1000,
                    1,
                ),
                status=(
                    "failed"
                    if self._last_error_type
                    else "completed"
                ),
                response_mode=response_mode,
            )

            return response

    def status(self) -> dict[str, object]:

        return {
            "last_response_seconds": (
                self._last_response_seconds
            ),
            "last_error_type": self._last_error_type,
            "last_response_mode": self._last_response_mode,
        }


assistant_core = AssistantCore()
