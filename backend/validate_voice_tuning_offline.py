"""Hardware-free checks for Naya's Zira-primary voice pipeline."""

from __future__ import annotations

import sys
import time
import types

from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent


def validate_speech_decoder() -> None:

    calls: list[dict[str, object]] = []

    class FakeWhisperModel:

        def __init__(self, *args, **kwargs) -> None:
            calls.append({"init_args": args, "init_kwargs": kwargs})

        def transcribe(self, audio, **kwargs):
            del audio
            calls.append(kwargs)

            if len(calls) == 2:
                return iter(()), object()

            return iter((SimpleNamespace(text="Hey Naya"),)), object()

    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = FakeWhisperModel
    original_module = sys.modules.get("faster_whisper")
    sys.modules["faster_whisper"] = fake_module

    try:
        from app.services.speech_service import SpeechService

        service = SpeechService()
        assert service.preload_model()
        assert service.transcribe([0.0]) == "Hey Naya"
        status = service.status()

    finally:

        if original_module is None:
            sys.modules.pop("faster_whisper", None)
        else:
            sys.modules["faster_whisper"] = original_module

    init_kwargs = calls[0]["init_kwargs"]
    decode_kwargs = calls[2]
    assert init_kwargs["compute_type"] == "int8"
    assert init_kwargs["num_workers"] == 1
    assert decode_kwargs["beam_size"] == 1
    assert decode_kwargs["best_of"] == 1
    assert decode_kwargs["vad_filter"] is False
    assert decode_kwargs["without_timestamps"] is True
    assert "Naya" in str(decode_kwargs["hotwords"])
    assert status["preload_complete"] is True


class FakeZiraEngine:

    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.completed = 0
        self.stopped = False

    def say(self, text: str) -> None:
        self.spoken.append(text)

    def runAndWait(self) -> None:
        self.completed += 1

    def stop(self) -> None:
        self.stopped = True


def validate_zira_primary_direct_path() -> None:

    from app.services.voice_service import VoiceService

    engine = FakeZiraEngine()
    service = VoiceService()
    provider = service._speak_preferred(
        engine,
        "Hello Naya.",
        prefer_neural=True,
        neural_timeout_seconds=99.0,
    )
    status = service.status()

    assert engine.spoken == ["Hello Naya."]
    assert engine.completed == 1
    assert provider == "local_zira_primary"
    assert status["primary_provider"] == "local_zira"
    assert status["last_provider"] == "local_zira_primary"
    assert status["piper_runtime_enabled"] is False
    assert status["piper_wait_seconds"] == 0.0


def validate_zira_worker_and_queue() -> None:

    from app.services.voice_service import VoiceService

    engine = FakeZiraEngine()

    class TestVoiceService(VoiceService):

        def _create_engine(self):
            self._voice_name = "Microsoft Zira Desktop"
            self._engine_name = "pyttsx3 Windows SAPI5"
            return engine

    service = TestVoiceService()

    try:
        assert service.preload()
        service.speak(
            "Queue test.",
            prefer_neural=True,
            neural_timeout_seconds=99.0,
        )
        status = service.status()

    finally:
        service.stop()

    assert engine.spoken == ["Queue test."]
    assert engine.completed == 1
    assert engine.stopped is True
    assert status["last_provider"] == "local_zira_primary"
    assert float(status["last_queue_delay_seconds"] or 0.0) < 1.0


def validate_complete_voice_loop() -> None:

    from app.services import voice_assistant as module

    original_listen = module.naya_listener.listen_for_wake_phrase
    original_record = module.speech_service.record_until_silence
    original_transcribe = module.speech_service.transcribe
    original_respond = module.assistant_core.respond_voice
    original_speak = module.voice_service.speak
    calls: list[tuple[str, dict[str, object]]] = []
    assistant = module.VoiceAssistant()

    def fake_speak(text: str, **kwargs) -> None:
        calls.append((text, kwargs))

        if len(calls) == 2:
            assistant._stop_event.set()

    try:
        module.naya_listener.listen_for_wake_phrase = lambda stop: True
        module.speech_service.record_until_silence = lambda **kwargs: [0.0]
        module.speech_service.transcribe = lambda audio: "What is your name?"
        module.assistant_core.respond_voice = lambda request: "Naya"
        module.voice_service.speak = fake_speak
        assistant._run()

    finally:
        module.naya_listener.listen_for_wake_phrase = original_listen
        module.speech_service.record_until_silence = original_record
        module.speech_service.transcribe = original_transcribe
        module.assistant_core.respond_voice = original_respond
        module.voice_service.speak = original_speak

    assert [text for text, _ in calls] == ["Yes?", "Naya"]
    assert all(kwargs.get("prefer_neural") is False for _, kwargs in calls)
    assert assistant.status()["last_processing_seconds"] < 1.0
    assert assistant.status()["last_transcription_seconds"] < 1.0
    assert assistant.status()["last_ai_response_seconds"] < 1.0
    assert assistant.status()["last_timed_out"] is False


def validate_fast_voice_model_routing() -> None:

    from app.services import ollama_client as module

    original_default = module._default_client
    original_voice = module._voice_client
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeClient:

        def __init__(self, route: str) -> None:
            self.route = route

        def chat(self, *args, **kwargs):
            del args
            calls.append((self.route, kwargs))
            return {"message": {"content": "Test response"}}

    try:
        module._default_client = FakeClient("standard")
        module._voice_client = FakeClient("voice")
        module.ollama.chat(
            model="qwen3:8b",
            messages=[],
            options={"num_predict": 40},
        )

        with module.voice_inference_mode():
            module.ollama.chat(
                model="qwen3:8b",
                messages=[],
                options={"num_predict": 40},
            )

        status = module.ollama_status()

    finally:
        module._default_client = original_default
        module._voice_client = original_voice

    assert calls[0][0] == "standard"
    assert calls[0][1]["model"] == "qwen3:8b"
    assert calls[1][0] == "voice"
    assert calls[1][1]["model"] == "qwen3:1.7b"
    assert int(calls[1][1]["options"]["num_predict"]) <= 32
    assert status["last_route"] == "voice_fast"
    assert status["last_model"] == "qwen3:1.7b"


def validate_command_is_preserved_on_ai_timeout() -> None:

    from app.services import voice_assistant as module

    original_transcribe = module.speech_service.transcribe
    original_respond = module.assistant_core.respond_voice
    original_maximum = module.MAX_RESPONSE_DELAY_SECONDS
    original_silence = module.COMMAND_END_SILENCE_SECONDS
    original_margin = module.VOICE_RESPONSE_START_MARGIN_SECONDS

    def slow_response(request: str) -> str:
        del request
        time.sleep(1.2)
        return "Late response"

    try:
        module.speech_service.transcribe = lambda audio: (
            "What is the capital of Cameroon?"
        )
        module.assistant_core.respond_voice = slow_response
        module.MAX_RESPONSE_DELAY_SECONDS = 1.0
        module.COMMAND_END_SILENCE_SECONDS = 0.0
        module.VOICE_RESPONSE_START_MARGIN_SECONDS = 0.0
        assistant = module.VoiceAssistant()
        request, response, timed_out = assistant._transcribe_and_respond([0.0])

    finally:
        module.speech_service.transcribe = original_transcribe
        module.assistant_core.respond_voice = original_respond
        module.MAX_RESPONSE_DELAY_SECONDS = original_maximum
        module.COMMAND_END_SILENCE_SECONDS = original_silence
        module.VOICE_RESPONSE_START_MARGIN_SECONDS = original_margin

    assert request == "What is the capital of Cameroon?"
    assert "heard your request" in response.casefold()
    assert timed_out is True
    assert assistant.status()["last_request_available"] is True
    assert assistant.status()["last_ai_error_type"] == "TimeoutError"


def validate_runtime_boundaries() -> None:

    voice_source = (
        ROOT / "app" / "services" / "voice_service.py"
    ).read_text(encoding="utf-8-sig")
    assistant_source = (
        ROOT / "app" / "services" / "voice_assistant.py"
    ).read_text(encoding="utf-8-sig")
    preparation_source = (
        ROOT / "prepare_voice_runtime.py"
    ).read_text(encoding="utf-8-sig")
    requirements = (ROOT / "requirements.txt").read_text(
        encoding="utf-8-sig"
    )

    assert "local_neural_voice_service" not in voice_source
    assert "_neural_budget" not in assistant_source
    assert "ensure_local_neural_voice" not in preparation_source
    assert "piper-tts" not in requirements
    assert "respond_voice" in assistant_source
    assert (ROOT / "test_naya_voice.py").is_file()
    assert (ROOT / "final_naya_voice_test.py").is_file()
    assert (ROOT / "Test_Naya_Voice.bat").is_file()
    assert (ROOT / "Final_Naya_Voice_Test.bat").is_file()


def main() -> int:

    validate_speech_decoder()
    validate_zira_primary_direct_path()
    validate_zira_worker_and_queue()
    validate_complete_voice_loop()
    validate_fast_voice_model_routing()
    validate_command_is_preserved_on_ai_timeout()
    validate_runtime_boundaries()
    print("NAYA ZIRA-PRIMARY OFFLINE VALIDATION: PASSED")
    print("PIPER RUNTIME USED: NO")
    print("MICROPHONE USED: NO")
    print("SPEAKER USED: NO")
    print("GOOGLE ACCESS USED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
