from __future__ import annotations

import shutil

from pathlib import Path

from app.personal_data.file_fingerprint_service import (
    FileFingerprintService,
)

from app.personal_data.local_file_scanner import (
    LocalFileScanner,
)

from app.personal_data.safe_folder_registry import (
    SafeFolderRegistry,
)


BASE = Path(
    "data/personal_data/"
    "test_file_fingerprint_service"
).resolve()


REGISTRY_PATH = (
    BASE
    / "registry.json"
)


def main() -> None:

    if BASE.exists():

        shutil.rmtree(
            BASE
        )

    approved = (
        BASE
        / "approved"
    )

    outside = (
        BASE
        / "outside"
    )

    approved.mkdir(
        parents=True,
        exist_ok=True,
    )

    outside.mkdir(
        parents=True,
        exist_ok=True,
    )

    alpha = (
        approved
        / "alpha.txt"
    )

    rename_source = (
        approved
        / "rename_me.txt"
    )

    duplicate_one = (
        approved
        / "duplicate_one.txt"
    )

    removed_file = (
        approved
        / "removed.txt"
    )

    alpha.write_text(
        "version one",
        encoding="utf-8",
    )

    rename_source.write_text(
        "rename content",
        encoding="utf-8",
    )

    duplicate_one.write_text(
        "duplicate content",
        encoding="utf-8",
    )

    removed_file.write_text(
        "remove me",
        encoding="utf-8",
    )

    registry = SafeFolderRegistry(
        REGISTRY_PATH
    )

    folder = (
        registry.approve_folder(
            approved,
            label="Fingerprint Test",
            recursive=True,
        )
    )

    scanner = LocalFileScanner(
        registry
    )

    fingerprint = (
        FileFingerprintService(
            registry
        )
    )

    try:

        print("=" * 70)
        print("FIRST SNAPSHOT")
        print("=" * 70)

        first_scan = (
            scanner.scan_folder(
                folder[
                    "folder_id"
                ]
            )
        )

        first = (
            fingerprint
            .fingerprint_scan(
                first_scan
            )
        )

        print(
            "FILES FINGERPRINTED:",
            first[
                "files_fingerprinted"
            ]
        )

        print(
            "NO ERRORS:",
            first[
                "fingerprint_errors"
            ]
            == 0
        )

        print(
            "SHA256 LENGTH:",
            all(
                len(
                    item[
                        "sha256"
                    ]
                )
                == 64
                for item in first[
                    "files"
                ]
            )
        )

        print(
            "PATH FINGERPRINT:",
            all(
                len(
                    item[
                        "path_fingerprint"
                    ]
                )
                == 64
                for item in first[
                    "files"
                ]
            )
        )

        alpha_before = next(
            item
            for item in first[
                "files"
            ]
            if item[
                "name"
            ]
            == "alpha.txt"
        )

        # ========================================================
        # MODIFY FILE
        # ========================================================

        alpha.write_text(
            "version two",
            encoding="utf-8",
        )

        # ========================================================
        # RENAME FILE WITHOUT CHANGING CONTENT
        # ========================================================

        renamed = (
            approved
            / "renamed.txt"
        )

        rename_source.rename(
            renamed
        )

        # ========================================================
        # CREATE DUPLICATE
        # ========================================================

        duplicate_two = (
            approved
            / "duplicate_two.txt"
        )

        duplicate_two.write_text(
            "duplicate content",
            encoding="utf-8",
        )

        # ========================================================
        # REMOVE FILE
        # ========================================================

        removed_file.unlink()

        # ========================================================
        # CREATE NEW FILE
        # ========================================================

        (
            approved
            / "new.txt"
        ).write_text(
            "brand new",
            encoding="utf-8",
        )

        print()
        print("=" * 70)
        print("SECOND SNAPSHOT")
        print("=" * 70)

        second_scan = (
            scanner.scan_folder(
                folder[
                    "folder_id"
                ]
            )
        )

        second = (
            fingerprint
            .fingerprint_scan(
                second_scan
            )
        )

        alpha_after = next(
            item
            for item in second[
                "files"
            ]
            if item[
                "name"
            ]
            == "alpha.txt"
        )

        print(
            "CHANGED HASH:",
            alpha_before[
                "sha256"
            ]
            != alpha_after[
                "sha256"
            ]
        )

        comparison = (
            fingerprint
            .compare_snapshots(
                first[
                    "files"
                ],
                second[
                    "files"
                ],
            )
        )

        counts = (
            comparison[
                "counts"
            ]
        )

        print()
        print("=" * 70)
        print("COMPARISON")
        print("=" * 70)

        print(
            "CHANGED:",
            counts[
                "changed"
            ]
        )

        print(
            "RENAMED:",
            counts[
                "renamed"
            ]
        )

        print(
            "REMOVED:",
            counts[
                "removed"
            ]
        )

        print(
            "NEW:",
            counts[
                "new"
            ]
        )

        print(
            "DUPLICATE GROUPS:",
            counts[
                "duplicates"
            ]
        )

        print(
            "CHANGE DETECTED:",
            any(
                Path(
                    item[
                        "path"
                    ]
                ).name
                == "alpha.txt"
                for item in comparison[
                    "changed"
                ]
            )
        )

        print(
            "RENAME DETECTED:",
            any(
                Path(
                    item[
                        "from"
                    ]
                ).name
                == "rename_me.txt"
                and
                Path(
                    item[
                        "to"
                    ]
                ).name
                == "renamed.txt"
                for item in comparison[
                    "renamed"
                ]
            )
        )

        print(
            "REMOVAL DETECTED:",
            any(
                Path(
                    item[
                        "path"
                    ]
                ).name
                == "removed.txt"
                for item in comparison[
                    "removed"
                ]
            )
        )

        print(
            "NEW FILE DETECTED:",
            any(
                Path(
                    item[
                        "path"
                    ]
                ).name
                == "new.txt"
                for item in comparison[
                    "new"
                ]
            )
        )

        print(
            "DUPLICATE DETECTED:",
            any(
                {
                    Path(
                        path
                    ).name
                    for path
                    in group[
                        "paths"
                    ]
                }
                == {
                    "duplicate_one.txt",
                    "duplicate_two.txt",
                }
                for group
                in comparison[
                    "duplicates"
                ]
            )
        )

        # ========================================================
        # SECURITY TESTS
        # ========================================================

        print()
        print("=" * 70)
        print("SECURITY")
        print("=" * 70)

        outside_file = (
            outside
            / "outside.txt"
        )

        outside_file.write_text(
            "private",
            encoding="utf-8",
        )

        try:

            fingerprint.fingerprint_file(
                outside_file
            )

            print(
                "OUTSIDE BLOCKED:",
                False
            )

        except PermissionError:

            print(
                "OUTSIDE BLOCKED:",
                True
            )

        protected = (
            approved
            / ".env"
        )

        protected.write_text(
            "SECRET=value",
            encoding="utf-8",
        )

        try:

            fingerprint.fingerprint_file(
                protected
            )

            print(
                "PROTECTED BLOCKED:",
                False
            )

        except PermissionError:

            print(
                "PROTECTED BLOCKED:",
                True
            )

    finally:

        if BASE.exists():

            shutil.rmtree(
                BASE
            )

    print()
    print("=" * 70)
    print("FINAL")
    print("=" * 70)

    print(
        "TEMP DATA DELETED:",
        not BASE.exists()
    )


if __name__ == "__main__":

    main()