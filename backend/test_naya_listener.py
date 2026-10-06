from app.services.naya_listener import NayaListener


def main() -> None:

    listener = NayaListener()

    cases = {
        "Hey Naya": True,
        "hey, Naya!": True,
        "Please, hey Naya, check my calendar": True,
        "Naya": False,
        "Hey Maya": False,
        "Hey Jarvis": False,
    }

    failures = {
        phrase: expected
        for phrase, expected in cases.items()
        if listener.matches_wake_phrase(phrase) is not expected
    }

    if failures:
        raise AssertionError(f"Wake phrase failures: {failures}")

    print("Naya exact wake-phrase checks passed.")


if __name__ == "__main__":
    main()
