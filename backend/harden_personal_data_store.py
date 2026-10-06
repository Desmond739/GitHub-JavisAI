from pathlib import Path


TARGET = Path(
    "app/personal_data/"
    "personal_data_store.py"
)


def replace_once(
    text: str,
    old: str,
    new: str,
    description: str,
) -> str:

    count = text.count(old)

    if count != 1:

        raise RuntimeError(
            f"{description}: expected "
            f"1 match, found {count}."
        )

    return text.replace(
        old,
        new,
        1,
    )


def main() -> None:

    if not TARGET.exists():

        raise FileNotFoundError(
            f"File not found: {TARGET}"
        )

    text = TARGET.read_text(
        encoding="utf-8"
    )

    # ============================================================
    # IMPORT TIME
    # ============================================================

    text = replace_once(
        text,
        "import os\n",
        "import os\nimport time\n",
        "time import",
    )

    # ============================================================
    # WINDOWS-SAFE ATOMIC REPLACE
    # ============================================================

    old_replace = """                os.replace(
                    temp_path,
                    self.storage_path,
                )
"""

    new_replace = """                # Windows can temporarily lock a JSON file
                # while antivirus, indexing, backup software,
                # or another process is inspecting it.
                #
                # Keep atomic replacement, but retry short-lived
                # access/sharing violations before failing.
                max_attempts = 5

                for attempt in range(
                    1,
                    max_attempts + 1,
                ):

                    try:

                        os.replace(
                            temp_path,
                            self.storage_path,
                        )

                        break

                    except OSError as exc:

                        winerror = getattr(
                            exc,
                            "winerror",
                            None,
                        )

                        retryable = (
                            isinstance(
                                exc,
                                PermissionError,
                            )
                            or winerror in {
                                5,
                                32,
                            }
                        )

                        if (
                            not retryable
                            or attempt
                            == max_attempts
                        ):

                            raise

                        time.sleep(
                            0.10 * attempt
                        )
"""

    text = replace_once(
        text,
        old_replace,
        new_replace,
        "atomic replace retry",
    )

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "PersonalDataStore Windows "
        "retry hardening applied."
    )


if __name__ == "__main__":

    main()