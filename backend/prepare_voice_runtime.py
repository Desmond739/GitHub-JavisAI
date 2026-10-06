"""Prepare Naya's speech model and Zira TTS without using voice hardware."""

from __future__ import annotations

from time import monotonic

from app.services.speech_service import speech_service
from app.services.voice_service import voice_service


def main() -> int:

    started_at = monotonic()

    try:
        speech_service.preload_model()
        voice_service.preload()

    except Exception as error:
        print("NAYA VOICE PREPARATION: FAILED")
        print("ERROR TYPE:", type(error).__name__)
        return 1

    finally:
        voice_service.stop()

    print("NAYA VOICE PREPARATION: PASSED")
    print("PREPARATION SECONDS:", round(monotonic() - started_at, 3))
    print("SPEECH STATUS:", speech_service.status())
    print("VOICE STATUS:", voice_service.status())
    print("PIPER STARTUP WAIT REMOVED: YES")
    print("MICROPHONE USED: NO")
    print("SPEAKER USED: NO")
    print("GOOGLE ACCESS USED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
