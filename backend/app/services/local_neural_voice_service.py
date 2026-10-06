from __future__ import annotations

import hashlib
import json
import wave

from io import BytesIO
from pathlib import Path
from threading import Event, RLock, Thread
from time import monotonic
from typing import Any

from app.core.config import (
    LOCAL_NEURAL_CONFIG_PATH,
    LOCAL_NEURAL_LENGTH_SCALE,
    LOCAL_NEURAL_MODEL_PATH,
    LOCAL_NEURAL_NOISE_SCALE,
    LOCAL_NEURAL_NOISE_WIDTH,
    LOCAL_NEURAL_TIMEOUT_SECONDS,
    LOCAL_NEURAL_VOICE_ENABLED,
    LOCAL_NEURAL_VOICE_NAME,
    LOCAL_NEURAL_VOLUME,
)


MODEL_SIZE_BYTES = 114_199_011
MODEL_SHA256 = (
    "5d4f08ba6a2a48c44592eed3ce56bf85"
    "e9de3dd4e20df90541ae68a8310c029a"
)
CONFIG_SIZE_BYTES = 4_970
CONFIG_SHA256 = (
    "7e1f4634af596d83cca997fb7a931ba8"
    "0b70f8a316a2655ee69c55365e0ace14"
)


class LocalNeuralVoiceUnavailable(RuntimeError):
    """Raised when verified local neural speech cannot be produced."""


def _sha256(path: Path) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as source:

        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def verify_local_voice_files(
    model_path: Path = LOCAL_NEURAL_MODEL_PATH,
    config_path: Path = LOCAL_NEURAL_CONFIG_PATH,
) -> None:
    """Verify the pinned model before it is loaded into the process."""

    if (
        not model_path.is_file()
        or model_path.stat().st_size != MODEL_SIZE_BYTES
        or _sha256(model_path) != MODEL_SHA256
    ):
        raise LocalNeuralVoiceUnavailable(
            "The local neural voice model is missing or invalid."
        )

    if (
        not config_path.is_file()
        or config_path.stat().st_size != CONFIG_SIZE_BYTES
        or _sha256(config_path) != CONFIG_SHA256
    ):
        raise LocalNeuralVoiceUnavailable(
            "The local neural voice configuration is missing or invalid."
        )

    try:
        configuration = json.loads(
            config_path.read_text(encoding="utf-8")
        )

    except (OSError, UnicodeError, json.JSONDecodeError):
        raise LocalNeuralVoiceUnavailable(
            "The local neural voice configuration could not be read."
        ) from None

    if (
        configuration.get("dataset") != "ljspeech"
        or configuration.get("audio", {}).get("sample_rate") != 22_050
        or configuration.get("language", {}).get("code") != "en_US"
        or configuration.get("num_speakers") != 1
    ):
        raise LocalNeuralVoiceUnavailable(
            "The local neural voice configuration is not approved."
        )


class LocalNeuralVoiceService:
    """Run Naya's verified Piper female voice entirely on this computer."""

    _maximum_audio_bytes = 16 * 1024 * 1024

    def __init__(self) -> None:

        self._lock = RLock()
        self._load_lock = RLock()
        self._voice: Any = None
        self._synthesis_config: Any = None
        self._synthesis_busy = False
        self._model_load_seconds: float | None = None
        self._last_synthesis_seconds: float | None = None
        self._last_error_type: str | None = None
        self._successful_once = False

    @property
    def available(self) -> bool:

        return bool(
            LOCAL_NEURAL_VOICE_ENABLED
            and LOCAL_NEURAL_MODEL_PATH.is_file()
            and LOCAL_NEURAL_CONFIG_PATH.is_file()
        )

    @property
    def ready(self) -> bool:

        with self._lock:
            return self._voice is not None

    def preload(self) -> bool:

        if not LOCAL_NEURAL_VOICE_ENABLED:
            raise LocalNeuralVoiceUnavailable(
                "The local neural voice is disabled."
            )

        with self._load_lock:

            if self.ready:
                return True

            started_at = monotonic()

            try:
                verify_local_voice_files()
                from piper import PiperVoice, SynthesisConfig

                voice = PiperVoice.load(
                    LOCAL_NEURAL_MODEL_PATH,
                    config_path=LOCAL_NEURAL_CONFIG_PATH,
                    use_cuda=False,
                )
                synthesis_config = SynthesisConfig(
                    length_scale=LOCAL_NEURAL_LENGTH_SCALE,
                    noise_scale=LOCAL_NEURAL_NOISE_SCALE,
                    noise_w_scale=LOCAL_NEURAL_NOISE_WIDTH,
                    normalize_audio=True,
                    volume=LOCAL_NEURAL_VOLUME,
                )

                # Warm the model without touching the speaker. This removes
                # first-request inference overhead from the live voice path.
                self._render_wav(
                    voice,
                    synthesis_config,
                    "Naya is ready.",
                )

            except Exception as error:

                with self._lock:
                    self._last_error_type = type(error).__name__
                    self._model_load_seconds = round(
                        monotonic() - started_at,
                        3,
                    )

                if isinstance(error, LocalNeuralVoiceUnavailable):
                    raise

                raise LocalNeuralVoiceUnavailable(
                    "The local neural voice could not be loaded."
                ) from None

            with self._lock:
                self._voice = voice
                self._synthesis_config = synthesis_config
                self._last_error_type = None
                self._model_load_seconds = round(
                    monotonic() - started_at,
                    3,
                )

        return True

    @classmethod
    def _render_wav(
        cls,
        voice: Any,
        synthesis_config: Any,
        text: str,
    ) -> bytes:

        buffer = BytesIO()

        with wave.open(buffer, "wb") as wav_file:
            voice.synthesize_wav(
                text,
                wav_file,
                syn_config=synthesis_config,
            )

        audio = buffer.getvalue()

        if (
            len(audio) < 44
            or len(audio) > cls._maximum_audio_bytes
            or audio[:4] != b"RIFF"
            or audio[8:12] != b"WAVE"
        ):
            raise LocalNeuralVoiceUnavailable(
                "The local neural engine returned invalid audio."
            )

        return audio

    def synthesize(
        self,
        text: str,
        *,
        timeout_seconds: float | None = None,
    ) -> bytes:

        spoken_text = str(text).strip()

        if not spoken_text:
            raise LocalNeuralVoiceUnavailable(
                "No speech text was provided."
            )

        if len(spoken_text) > 4_000:
            raise LocalNeuralVoiceUnavailable(
                "The speech text is too long."
            )

        if not self.ready:
            raise LocalNeuralVoiceUnavailable(
                "The local neural voice is not preloaded."
            )

        allowed_timeout = LOCAL_NEURAL_TIMEOUT_SECONDS

        if timeout_seconds is not None:
            allowed_timeout = min(
                allowed_timeout,
                max(0.0, float(timeout_seconds)),
            )

        if allowed_timeout < 0.2:
            raise LocalNeuralVoiceUnavailable(
                "The local neural voice deadline was reached."
            )

        with self._lock:

            if self._synthesis_busy:
                raise LocalNeuralVoiceUnavailable(
                    "The local neural voice is still processing."
                )

            voice = self._voice
            synthesis_config = self._synthesis_config
            self._synthesis_busy = True

        completed = Event()
        result: dict[str, object] = {}
        started_at = monotonic()

        def render() -> None:

            try:
                result["audio"] = self._render_wav(
                    voice,
                    synthesis_config,
                    spoken_text,
                )

            except Exception as error:
                result["error"] = error

            finally:

                with self._lock:
                    self._synthesis_busy = False

                completed.set()

        Thread(
            target=render,
            name="naya-local-neural-synthesis",
            daemon=True,
        ).start()

        if not completed.wait(timeout=allowed_timeout):

            with self._lock:
                self._last_error_type = "TimeoutError"
                self._last_synthesis_seconds = round(
                    monotonic() - started_at,
                    3,
                )

            raise LocalNeuralVoiceUnavailable(
                "The local neural voice exceeded its deadline."
            )

        error = result.get("error")

        if isinstance(error, Exception):

            with self._lock:
                self._last_error_type = type(error).__name__
                self._last_synthesis_seconds = round(
                    monotonic() - started_at,
                    3,
                )

            if isinstance(error, LocalNeuralVoiceUnavailable):
                raise error

            raise LocalNeuralVoiceUnavailable(
                "The local neural voice could not synthesize audio."
            ) from None

        audio = result.get("audio")

        if not isinstance(audio, bytes):
            raise LocalNeuralVoiceUnavailable(
                "The local neural voice returned no audio."
            )

        with self._lock:
            self._last_error_type = None
            self._last_synthesis_seconds = round(
                monotonic() - started_at,
                3,
            )
            self._successful_once = True

        return audio

    @staticmethod
    def play_audio(audio: bytes) -> None:

        try:
            import winsound

            winsound.PlaySound(
                audio,
                winsound.SND_MEMORY | winsound.SND_NODEFAULT,
            )

        except Exception:
            raise LocalNeuralVoiceUnavailable(
                "The local neural voice audio could not be played."
            ) from None

    def status(self) -> dict[str, object]:

        with self._lock:
            model_loaded = self._voice is not None
            synthesis_busy = self._synthesis_busy
            model_load_seconds = self._model_load_seconds
            last_synthesis_seconds = self._last_synthesis_seconds
            last_error_type = self._last_error_type
            successful_once = self._successful_once

        return {
            "provider": "Piper local neural TTS",
            "enabled": LOCAL_NEURAL_VOICE_ENABLED,
            "available": self.available,
            "model_loaded": model_loaded,
            "voice_name": LOCAL_NEURAL_VOICE_NAME,
            "model_path": str(LOCAL_NEURAL_MODEL_PATH),
            "offline_after_preparation": True,
            "network_used_at_runtime": False,
            "request_timeout_seconds": LOCAL_NEURAL_TIMEOUT_SECONDS,
            "model_load_seconds": model_load_seconds,
            "last_synthesis_seconds": last_synthesis_seconds,
            "last_error_type": last_error_type,
            "successful_once": successful_once,
            "synthesis_busy": synthesis_busy,
        }


local_neural_voice_service = LocalNeuralVoiceService()
