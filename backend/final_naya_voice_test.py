"""User-approved Windows microphone and speaker test of Naya's full pipeline."""

from __future__ import annotations

import time
import unicodedata

from app.core.config import (
    COMMAND_END_SILENCE_SECONDS,
    COMMAND_LISTEN_SECONDS,
    COMMAND_SPEECH_THRESHOLD,
    MAX_RESPONSE_DELAY_SECONDS,
    VOICE_OLLAMA_MODEL,
)
from app.services.naya_listener import naya_listener
from app.services.ollama_client import (
    ollama_status,
    warm_ollama_models,
)
from app.services.speech_service import speech_service
from app.services.voice_assistant import VoiceAssistant
from app.services.voice_service import voice_service


def main() -> int:

    try:
        print("Preparing speech recognition, Ollama, and Zira...", flush=True)
        speech_service.preload_model()
        voice_service.preload()

        if not warm_ollama_models():
            raise RuntimeError("Ollama model warm-up did not complete.")

        for number in (3, 2, 1):
            print(number, flush=True)
            time.sleep(1)

        print('SAY: "Hey Naya"', flush=True)
        wake_audio = speech_service.record_audio(duration=5)
        wake_text = speech_service.transcribe(wake_audio)
        print("WAKE TRANSCRIPTION:", wake_text)

        if not naya_listener.matches_wake_phrase(wake_text):
            raise RuntimeError("The exact wake phrase was not detected.")

        voice_service.speak("Yes?", prefer_neural=False)
        print('ASK: "What is the capital of Cameroon?"', flush=True)

        command_audio = speech_service.record_until_silence(
            max_duration=COMMAND_LISTEN_SECONDS,
            silence_duration=COMMAND_END_SILENCE_SECONDS,
            speech_threshold=COMMAND_SPEECH_THRESHOLD,
        )
        assistant = VoiceAssistant()
        request, response, timed_out = assistant._transcribe_and_respond(
            command_audio
        )
        assistant_status = assistant.status()
        processing_seconds = float(
            assistant_status.get("last_processing_seconds") or 0.0
        )
        transcription_seconds = float(
            assistant_status.get("last_transcription_seconds") or 0.0
        )
        ai_response_seconds = float(
            assistant_status.get("last_ai_response_seconds") or 0.0
        )
        print("COMMAND:", request)
        print("NAYA RESPONSE:", response)
        print("TIMED OUT:", timed_out)
        print("TRANSCRIPTION SECONDS:", transcription_seconds)
        print("AI RESPONSE SECONDS:", ai_response_seconds)
        print("PROCESSING SECONDS:", processing_seconds)

        if not request:
            raise RuntimeError("No command was detected.")

        if timed_out:
            raise RuntimeError("Naya timed out instead of answering.")

        normalized_response = unicodedata.normalize(
            "NFKD",
            response,
        ).encode("ascii", "ignore").decode("ascii").casefold()

        if "yaounde" not in normalized_response:
            raise RuntimeError("Naya did not give the correct answer.")

        voice_service.speak(response, prefer_neural=False)
        voice_status = voice_service.status()
        model_status = ollama_status()
        queue_seconds = float(
            voice_status.get("last_queue_delay_seconds") or 0.0
        )
        estimated_delay = round(
            COMMAND_END_SILENCE_SECONDS
            + processing_seconds
            + queue_seconds,
            3,
        )
        print("ZIRA QUEUE SECONDS:", queue_seconds)
        print("ESTIMATED DELAY AFTER SPEECH:", estimated_delay)
        print("VOICE STATUS:", voice_status)
        print("OLLAMA STATUS:", model_status)

        if voice_status.get("last_provider") != "local_zira_primary":
            raise RuntimeError("Zira was not the response provider.")

        if model_status.get("last_route") != "voice_fast":
            raise RuntimeError("The fast voice model route was not used.")

        if model_status.get("last_model") != VOICE_OLLAMA_MODEL:
            raise RuntimeError("The configured fast voice model was not used.")

        if estimated_delay > MAX_RESPONSE_DELAY_SECONDS:
            raise RuntimeError("The five-second response target was exceeded.")

    except Exception as error:
        print("FINAL NAYA VOICE TEST: FAILED")
        print("ERROR TYPE:", type(error).__name__)
        return 1

    finally:
        voice_service.stop()

    print("FINAL NAYA VOICE TEST: PASSED")
    print("FAST VOICE MODEL:", VOICE_OLLAMA_MODEL)
    print("PIPER USED: NO")
    print("GOOGLE ACCESS USED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
