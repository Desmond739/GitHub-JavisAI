"""Legacy filename retained; it now tests Naya's wake phrase."""

from app.services.naya_listener import naya_listener


def main() -> None:

    print("NAYA WAKE-PHRASE TEST")
    print("Say: Hey Naya")
    naya_listener.listen_for_wake_phrase()
    print("Hey Naya detected.")


if __name__ == "__main__":
    main()
