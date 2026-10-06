from app.services.speech_service import speech_service


def main() -> None:

    audio = speech_service.record_audio(duration=5)
    text = speech_service.transcribe(audio)
    print("You said:", text)


if __name__ == "__main__":
    main()
