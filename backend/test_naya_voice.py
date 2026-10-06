"""Speaker-only confirmation of Naya's temporary Zira primary voice."""

from __future__ import annotations

from time import monotonic

from app.services.voice_service import voice_service


def main() -> int:

    started_at = monotonic()
    status: dict[str, object] = {}

    try:
        voice_service.preload()
        voice_service.speak(
            "Hello. I am Naya, your local personal AI assistant. "
            "Microsoft Zira is my temporary primary voice."
        )
        status = voice_service.status()

        if status.get("primary_provider") != "local_zira":
            raise RuntimeError("Zira is not the configured primary voice.")

        if status.get("last_provider") != "local_zira_primary":
            raise RuntimeError("Zira was not the voice that spoke.")

        if status.get("piper_wait_seconds") != 0.0:
            raise RuntimeError("A Piper delay remains in the voice path.")

    except Exception as error:
        print("NAYA ZIRA SPEAKER TEST: FAILED")
        print("ERROR TYPE:", type(error).__name__)
        print("VOICE STATUS:", voice_service.status())
        return 1

    finally:
        voice_service.stop()

    print("NAYA ZIRA SPEAKER TEST: PASSED")
    print("TOTAL SPEAKING SECONDS:", round(monotonic() - started_at, 3))
    print("VOICE STATUS:", status)
    print("PIPER USED: NO")
    print("MICROPHONE USED: NO")
    print("GOOGLE ACCESS USED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
