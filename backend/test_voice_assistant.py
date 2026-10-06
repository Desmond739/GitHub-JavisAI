from app.services.assistant_core import assistant_core
from app.services.speech_service import speech_service
from app.services.voice_service import voice_service


def main() -> None:

    audio = speech_service.record_audio(duration=7)
    user_message = speech_service.transcribe(audio)

    if not user_message:
        print("No speech was detected.")
        return

    response = assistant_core.respond(user_message)
    print("Naya:", response)
    voice_service.speak(response)


if __name__ == "__main__":
    main()
