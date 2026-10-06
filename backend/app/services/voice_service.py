from __future__ import annotations

from queue import Queue
from threading import Event, RLock, Thread
from time import monotonic
from typing import Any

from app.core.config import (
    PRIMARY_VOICE_PROVIDER,
    VOICE_RATE,
)


class VoiceService:
    """Serialize speech through one persistent Windows TTS worker."""

    def __init__(self) -> None:

        self._voice_name: str | None = None
        self._engine_name: str | None = None
        self._engine: Any = None
        self._worker: Thread | None = None
        self._queue: Queue = Queue()
        self._ready = Event()
        self._startup_error: Exception | None = None
        self._lock = RLock()
        self._last_provider: str | None = None
        self._last_queue_delay_seconds: float | None = None

    def _create_engine(self):

        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []

        female_voice = next(
            (
                voice
                for voice in voices
                if "zira" in str(voice.name).casefold()
            ),
            None,
        )

        if female_voice is None:

            female_voice = next(
                (
                    voice
                    for voice in voices
                    if "female" in str(voice.name).casefold()
                ),
                None,
            )

        if female_voice is None:

            engine.stop()

            raise RuntimeError(
                "Naya requires a female system voice. "
                "Microsoft Zira is recommended."
            )

        engine.setProperty("voice", female_voice.id)
        engine.setProperty("rate", VOICE_RATE)
        engine.setProperty("volume", 1.0)

        self._voice_name = str(female_voice.name)
        self._engine_name = "pyttsx3 Windows SAPI5"

        return engine

    @staticmethod
    def _speak_local(engine, text: str) -> None:

        engine.say(text)
        engine.runAndWait()

    def _speak_preferred(
        self,
        engine,
        text: str,
        *,
        prefer_neural: bool,
        neural_timeout_seconds: float | None,
    ) -> str:

        # Retain these keyword arguments for compatibility with existing
        # callers, but never enter a neural synthesis path in this release.
        # Zira is the selected primary provider and therefore has no Piper
        # timeout, model-loading wait, or fallback transition.
        del prefer_neural, neural_timeout_seconds

        self._speak_local(engine, text)

        with self._lock:
            self._last_provider = "local_zira_primary"

        return "local_zira_primary"

    def _worker_main(self) -> None:

        try:
            engine = self._create_engine()
            self._engine = engine

        except Exception as error:
            self._startup_error = error
            self._ready.set()
            return

        self._ready.set()

        try:

            while True:

                item = self._queue.get()

                if item is None:
                    break

                (
                    text,
                    prefer_neural,
                    neural_timeout_seconds,
                    queued_at,
                    completed,
                    result,
                ) = item

                try:
                    with self._lock:
                        self._last_queue_delay_seconds = round(
                            monotonic() - queued_at,
                            3,
                        )

                    self._speak_preferred(
                        engine,
                        text,
                        prefer_neural=prefer_neural,
                        neural_timeout_seconds=neural_timeout_seconds,
                    )

                except Exception as error:
                    result["error"] = error

                finally:
                    completed.set()

        finally:
            engine.stop()
            self._engine = None

    def _ensure_worker(self) -> None:

        with self._lock:

            if (
                self._worker is None
                or not self._worker.is_alive()
            ):
                self._queue = Queue()
                self._ready = Event()
                self._startup_error = None
                self._worker = Thread(
                    target=self._worker_main,
                    name="naya-tts",
                    daemon=True,
                )
                self._worker.start()

            ready = self._ready

        if not ready.wait(timeout=10.0):
            raise RuntimeError(
                "Naya's voice engine did not initialize in time."
            )

        if self._startup_error is not None:
            raise RuntimeError(
                "Naya's female voice could not be initialized."
            ) from self._startup_error

    def preload(self) -> bool:

        self._ensure_worker()
        return True

    def speak(
        self,
        text: str,
        *,
        prefer_neural: bool = False,
        neural_timeout_seconds: float | None = None,
    ) -> None:

        spoken_text = str(text).strip()

        if not spoken_text:
            return

        self._ensure_worker()

        completed = Event()
        result: dict[str, Exception] = {}
        self._queue.put(
            (
                spoken_text,
                prefer_neural,
                neural_timeout_seconds,
                monotonic(),
                completed,
                result,
            )
        )
        completed.wait()

        if "error" in result:
            raise RuntimeError(
                "Naya could not speak the response."
            ) from result["error"]

    def stop(self) -> None:

        with self._lock:
            worker = self._worker

        if worker is None or not worker.is_alive():
            return

        self._queue.put(None)
        worker.join(timeout=5.0)

        with self._lock:

            if not worker.is_alive():
                self._worker = None

    def status(self) -> dict[str, object]:

        worker = self._worker

        with self._lock:
            last_provider = self._last_provider
            last_queue_delay_seconds = (
                self._last_queue_delay_seconds
            )

        return {
            "validated_once": self._voice_name is not None,
            "female_voice_required": True,
            "voice_name": self._voice_name,
            "engine": self._engine_name,
            "primary_provider": PRIMARY_VOICE_PROVIDER,
            "temporary_primary": True,
            "rate": VOICE_RATE,
            "last_provider": last_provider,
            "last_queue_delay_seconds": last_queue_delay_seconds,
            "piper_runtime_enabled": False,
            "piper_wait_seconds": 0.0,
            "future_voice_upgrade": "local_neural_female_voice",
            "worker_running": (
                worker is not None
                and worker.is_alive()
            ),
        }


voice_service = VoiceService()
