from pathlib import Path


TARGET = Path(
    "app/personal_data/"
    "google_calendar_incremental_sync.py"
)


def main() -> None:

    if not TARGET.exists():

        raise FileNotFoundError(
            f"File not found: {TARGET}"
        )

    text = TARGET.read_text(
        encoding="utf-8"
    )

    old = """                    singleEvents=True,
                    orderBy="startTime",
                    showDeleted=True,
"""

    new = """                    singleEvents=True,
                    showDeleted=True,
"""

    count = text.count(
        old
    )

    if count != 1:

        raise RuntimeError(
            "Expected exactly one full-sync "
            "orderBy block, found "
            f"{count}. No changes made."
        )

    text = text.replace(
        old,
        new,
        1,
    )

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Calendar sync-token fix applied."
    )


if __name__ == "__main__":

    main()