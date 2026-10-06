from app.services.naya_listener import naya_listener


def main() -> None:

    print("MONEROAI NAYA WAKE-PHRASE TEST")
    print("Say: Hey Naya")
    naya_listener.listen_for_wake_phrase()
    print("Wake phrase detected.")


if __name__ == "__main__":
    main()
