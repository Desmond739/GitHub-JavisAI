from __future__ import annotations

from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import monotonic

from app.core.config import (
    ASSISTANT_NAME,
    COMMAND_END_SILENCE_SECONDS,
    COMMAND_LISTEN_SECONDS,
    COMMAND_SPEECH_THRESHOLD,
    MAX_RESPONSE_DELAY_SECONDS,
    VOICE_OLLAMA_MODEL,
    VOICE_RESPONSE_START_MARGIN_SECONDS,
    VOICE_TRANSCRIPTION_TIMEOUT_SECONDS,
    WAKE_PHRASE,
)
from app.services.assistant_core import assistant_core
from app.services.naya_listener import naya_listener
from app.services.speech_service import speech_service
from app.services.voice_service import voice_service


class VoiceAssistant:

    def __init__(self) -> None:

        self._stop_event = Event()
        self._state_lock = Lock()
        self._thread: Thread | None = None
        self._last_error: str | None = None
        self._last_processing_seconds: float | None = None
        self._last_transcription_seconds: float | None = None
        self._last_ai_response_seconds: float | None = None
        self._last_transcription_error_type: str | None = None
        self._last_ai_error_type: str | None = None
        self._last_timed_out = False
        self._last_request: str | None = None

    def start(self) -> bool:

        with self._state_lock:

            if self._thread is not None and self._thread.is_alive():
                return False

            self._stop_event.clear()
            self._last_error = None
            self._thread = Thread(
                target=self._run,
                name="naya-voice-assistant",
                daemon=True,
            )
            self._thread.start()

        return True

    def stop(self) -> None:

        self._stop_event.set()

        with self._state_lock:
            thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

        with self._state_lock:

            if self._thread is not None and not self._thread.is_alive():
                self._thread = None

    def _set_error(self, error: Exception) -> None:

        self._last_error = type(error).__name__

    def _finish_processing(
        self,
        started_at: float,
        *,
        timed_out: bool,
    ) -> None:

        self._last_timed_out = timed_out
        self._last_processing_seconds = round(
            monotonic() - started_at,
            3,
        )

    def _transcribe_and_respond(
        self,
        audio,
    ) -> tuple[str, str, bool]:

        started_at = monotonic()
        processing_deadline = max(
            1.0,
            MAX_RESPONSE_DELAY_SECONDS
            - COMMAND_END_SILENCE_SECONDS
            - VOICE_RESPONSE_START_MARGIN_SECONDS,
        )
        transcription_results: Queue = Queue(maxsize=1)

        def transcribe() -> None:

            stage_started_at = monotonic()

            try:
                request_text = speech_service.transcribe(audio)
                error_type = None

            except Exception as error:
                request_text = ""
                error_type = type(error).__name__

            transcription_results.put(
                (
                    request_text,
                    error_type,
                    round(monotonic() - stage_started_at, 3),
                )
            )

        Thread(
            target=transcribe,
            name="naya-command-transcription",
            daemon=True,
        ).start()

        try:
            (
                request,
                transcription_error_type,
                transcription_seconds,
            ) = transcription_results.get(
                timeout=min(
                    VOICE_TRANSCRIPTION_TIMEOUT_SECONDS,
                    processing_deadline,
                )
            )

        except Empty:
            self._last_transcription_seconds = round(
                monotonic() - started_at,
                3,
            )
            self._last_ai_response_seconds = None
            self._last_transcription_error_type = "TimeoutError"
            self._last_ai_error_type = None
            self._last_request = None
            self._finish_processing(started_at, timed_out=True)
            return (
                "",
                "I could not understand the request quickly enough. "
                "Please try again.",
                True,
            )

        self._last_transcription_seconds = transcription_seconds
        self._last_transcription_error_type = (
            transcription_error_type
        )

        if transcription_error_type is not None:
            self._last_ai_response_seconds = None
            self._last_ai_error_type = None
            self._last_request = None
            self._finish_processing(started_at, timed_out=True)
            return (
                "",
                "I could not transcribe that request. Please try again.",
                True,
            )

        request = str(request).strip()

        if not request:
            self._last_ai_response_seconds = None
            self._last_ai_error_type = None
            self._last_request = None
            self._finish_processing(started_at, timed_out=False)
            return "", "", False

        self._last_request = request
        remaining_seconds = (
            processing_deadline
            - (monotonic() - started_at)
        )

        if remaining_seconds <= 0:
            self._last_ai_response_seconds = 0.0
            self._last_ai_error_type = "TimeoutError"
            self._finish_processing(started_at, timed_out=True)
            return (
                request,
                "I heard your request but could not answer within "
                "five seconds. Please try again.",
                True,
            )

        response_results: Queue = Queue(maxsize=1)

        def respond() -> None:

            stage_started_at = monotonic()

            try:
                response_text = assistant_core.respond_voice(request)
                error_type = assistant_core.status().get(
                    "last_error_type"
                )

            except Exception as error:
                response_text = ""
                error_type = type(error).__name__

            response_results.put(
                (
                    response_text,
                    error_type,
                    round(monotonic() - stage_started_at, 3),
                )
            )

        Thread(
            target=respond,
            name="naya-fast-voice-response",
            daemon=True,
        ).start()

        try:
            (
                response,
                ai_error_type,
                ai_response_seconds,
            ) = response_results.get(
                timeout=remaining_seconds
            )

        except Empty:
            response = (
                "I heard your request but could not answer within "
                "five seconds. Please try again."
            )
            ai_error_type = "TimeoutError"
            ai_response_seconds = round(
                max(
                    0.0,
                    monotonic()
                    - started_at
                    - transcription_seconds,
                ),
                3,
            )
            timed_out = True

        else:
            response = str(response).strip()
            timed_out = ai_error_type is not None or not response

            if not response:
                response = (
                    "I heard your request but could not produce an answer. "
                    "Please try again."
                )

        self._last_ai_response_seconds = ai_response_seconds
        self._last_ai_error_type = (
            str(ai_error_type)
            if ai_error_type is not None
            else None
        )
        self._finish_processing(started_at, timed_out=timed_out)
        return request, response, timed_out

    def _run(self) -> None:

        while not self._stop_event.is_set():

            try:
                detected = naya_listener.listen_for_wake_phrase(
                    self._stop_event
                )

                if not detected or self._stop_event.is_set():
                    continue

                voice_service.speak(
                    "Yes?",
                    prefer_neural=False,
                )
                audio = speech_service.record_until_silence(
                    max_duration=COMMAND_LISTEN_SECONDS,
                    silence_duration=COMMAND_END_SILENCE_SECONDS,
                    speech_threshold=COMMAND_SPEECH_THRESHOLD,
                )
                request, response, timed_out = (
                    self._transcribe_and_respond(audio)
                )

                if not request and not timed_out:
                    voice_service.speak(
                        "I did not hear a request.",
                        prefer_neural=False,
                    )
                    continue

                voice_service.speak(
                    response,
                    prefer_neural=False,
                )

            except Exception as error:
                self._set_error(error)
                self._stop_event.wait(2.0)

    def status(self) -> dict[str, object]:

        thread = self._thread

        return {
            "assistant_name": ASSISTANT_NAME,
            "wake_phrase": WAKE_PHRASE,
            "running": thread is not None and thread.is_alive(),
            "last_error": self._last_error,
            "last_request_available": bool(self._last_request),
            "last_processing_seconds": self._last_processing_seconds,
            "last_transcription_seconds": (
                self._last_transcription_seconds
            ),
            "last_ai_response_seconds": self._last_ai_response_seconds,
            "last_transcription_error_type": (
                self._last_transcription_error_type
            ),
            "last_ai_error_type": self._last_ai_error_type,
            "last_timed_out": self._last_timed_out,
            "voice_model": VOICE_OLLAMA_MODEL,
            "maximum_response_delay_seconds": (
                MAX_RESPONSE_DELAY_SECONDS
            ),
            "speech": speech_service.status(),
            "voice": voice_service.status(),
        }


voice_assistant = VoiceAssistant()
