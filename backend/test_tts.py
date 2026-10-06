from app.services.voice_service import voice_service


def main() -> None:

    voice_service.speak(
        "Hello. I am Naya, your personal AI assistant."
    )


if __name__ == "__main__":
    main()
