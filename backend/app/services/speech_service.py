from __future__ import annotations

from threading import Lock
from time import monotonic
from typing import Any

from app.core.config import (
    MICROPHONE_DEVICE,
    SPEECH_BEAM_SIZE,
    SPEECH_CPU_THREADS,
    SPEECH_MODEL,
)


class SpeechService:

    def __init__(self) -> None:

        self.sample_rate = 16000
        self._model: Any = None
        self._model_lock = Lock()
        self._model_load_seconds: float | None = None
        self._model_error_type: str | None = None
        self._last_transcription_seconds: float | None = None
        self._preload_complete = False

    def _get_model(self):

        if self._model is not None:
            return self._model

        with self._model_lock:

            if self._model is None:

                from faster_whisper import WhisperModel

                started_at = monotonic()

                try:
                    self._model = WhisperModel(
                        SPEECH_MODEL,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=SPEECH_CPU_THREADS,
                        num_workers=1,
                    )
                    self._model_error_type = None

                except Exception as error:
                    self._model_error_type = type(error).__name__
                    raise

                finally:
                    self._model_load_seconds = round(
                        monotonic() - started_at,
                        3,
                    )

        return self._model

    def preload_model(self) -> bool:
        """Load and initialize Whisper before Naya starts listening."""

        model = self._get_model()

        if self._preload_complete:
            return True

        import numpy as np

        warmup_audio = np.zeros(
            int(self.sample_rate * 0.25),
            dtype=np.float32,
        )
        segments, _ = model.transcribe(
            warmup_audio,
            language="en",
            beam_size=1,
            best_of=1,
            vad_filter=False,
            without_timestamps=True,
            condition_on_previous_text=False,
        )
        list(segments)
        self._preload_complete = True
        return True

    @staticmethod
    def _microphone_device():

        if MICROPHONE_DEVICE is None:
            return None

        if MICROPHONE_DEVICE.isdigit():
            return int(MICROPHONE_DEVICE)

        return MICROPHONE_DEVICE

    def record_audio(
        self,
        duration: int = 5,
        sample_rate: int = 16000,
    ):

        if duration <= 0:
            raise ValueError("Audio duration must be positive.")

        import sounddevice as sd

        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=self._microphone_device(),
        )

        sd.wait()

        return audio.flatten()

    def record_until_silence(
        self,
        *,
        max_duration: float,
        silence_duration: float,
        speech_threshold: float,
        sample_rate: int = 16000,
    ):

        if max_duration <= 0:
            raise ValueError("Maximum audio duration must be positive.")

        import math
        import numpy as np
        import sounddevice as sd

        block_seconds = 0.1
        block_size = int(sample_rate * block_seconds)
        maximum_blocks = math.ceil(
            max_duration / block_seconds
        )
        silence_blocks_required = max(
            1,
            math.ceil(
                silence_duration / block_seconds
            ),
        )

        frames = []
        speech_started = False
        silent_blocks = 0

        with sd.InputStream(
            samplerate=sample_rate,
            blocksize=block_size,
            channels=1,
            dtype="float32",
            device=self._microphone_device(),
        ) as stream:

            for _ in range(maximum_blocks):

                chunk, _ = stream.read(block_size)
                mono = np.asarray(
                    chunk[:, 0],
                    dtype=np.float32,
                ).copy()
                frames.append(mono)

                peak = float(
                    np.max(np.abs(mono))
                )

                if peak >= speech_threshold:
                    speech_started = True
                    silent_blocks = 0

                elif speech_started:
                    silent_blocks += 1

                    if (
                        silent_blocks
                        >= silence_blocks_required
                    ):
                        break

        if not frames:
            return np.empty(0, dtype=np.float32)

        return np.concatenate(frames)

    def transcribe(
        self,
        audio,
        sample_rate: int = 16000,
    ) -> str:

        del sample_rate

        started_at = monotonic()

        try:
            segments, _ = self._get_model().transcribe(
                audio,
                language="en",
                beam_size=SPEECH_BEAM_SIZE,
                best_of=1,
                vad_filter=False,
                without_timestamps=True,
                condition_on_previous_text=False,
                hotwords="Hey Naya Naya",
            )

            return " ".join(
                segment.text.strip()
                for segment in segments
            ).strip()

        finally:
            self._last_transcription_seconds = round(
                monotonic() - started_at,
                3,
            )

    def status(self) -> dict[str, object]:

        return {
            "model": SPEECH_MODEL,
            "model_loaded": self._model is not None,
            "preload_complete": self._preload_complete,
            "model_load_seconds": self._model_load_seconds,
            "model_error_type": self._model_error_type,
            "last_transcription_seconds": (
                self._last_transcription_seconds
            ),
            "cpu_threads": SPEECH_CPU_THREADS,
            "beam_size": SPEECH_BEAM_SIZE,
            "sample_rate": self.sample_rate,
            "microphone_device_configured": (
                MICROPHONE_DEVICE is not None
            ),
        }


speech_service = SpeechService()
