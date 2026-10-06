"""Legacy filename retained; it launches the unified Naya voice loop."""

import time

from app.services.voice_assistant import voice_assistant


def main() -> None:

    print("NAYA PERSONAL ASSISTANT")
    print("Say 'Hey Naya' to activate. Press Ctrl+C to stop.")
    voice_assistant.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        voice_assistant.stop()


if __name__ == "__main__":
    main()
