from __future__ import annotations

import shutil

from pathlib import Path

from app.personal_data.local_file_scanner import (
    LocalFileScanner,
)

from app.personal_data.safe_folder_registry import (
    SafeFolderRegistry,
)


BASE = Path(
    "data/personal_data/"
    "test_local_file_scanner"
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

    nested = (
        approved
        / "Projects"
    )

    direct = (
        BASE
        / "direct"
    )

    direct_nested = (
        direct
        / "nested"
    )

    approved.mkdir(
        parents=True,
        exist_ok=True,
    )

    nested.mkdir(
        parents=True,
        exist_ok=True,
    )

    direct_nested.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ============================================================
    # ALLOWED FILES
    # ============================================================

    (
        approved
        / "report.txt"
    ).write_text(
        "report",
        encoding="utf-8",
    )

    (
        approved
        / "data.csv"
    ).write_text(
        "a,b\n1,2",
        encoding="utf-8",
    )

    (
        nested
        / "project.md"
    ).write_text(
        "project",
        encoding="utf-8",
    )

    # ============================================================
    # UNSUPPORTED / PROTECTED
    # ============================================================

    (
        approved
        / "program.exe"
    ).write_bytes(
        b"test"
    )

    (
        approved
        / ".env"
    ).write_text(
        "SECRET=test",
        encoding="utf-8",
    )

    (
        approved
        / "calendar_token.json"
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    (
        approved
        / ".hidden.txt"
    ).write_text(
        "hidden",
        encoding="utf-8",
    )

    ssh = (
        approved
        / ".ssh"
    )

    ssh.mkdir(
        exist_ok=True
    )

    (
        ssh
        / "id_rsa"
    ).write_text(
        "private",
        encoding="utf-8",
    )

    # Oversized for this controlled test.
    (
        approved
        / "large.pdf"
    ).write_bytes(
        b"x" * 64
    )

    # Non-recursive folder.
    (
        direct
        / "direct.txt"
    ).write_text(
        "direct",
        encoding="utf-8",
    )

    (
        direct_nested
        / "deep.txt"
    ).write_text(
        "deep",
        encoding="utf-8",
    )

    registry = SafeFolderRegistry(
        REGISTRY_PATH
    )

    scanner = LocalFileScanner(
        registry,
        max_file_size_bytes=32,
        include_hidden=False,
    )

    try:

        recursive_folder = (
            registry.approve_folder(
                approved,
                label="Recursive",
                recursive=True,
            )
        )

        direct_folder = (
            registry.approve_folder(
                direct,
                label="Direct",
                recursive=False,
            )
        )

        print("=" * 70)
        print("RECURSIVE")
        print("=" * 70)

        result = scanner.scan_folder(
            recursive_folder[
                "folder_id"
            ]
        )

        names = {
            item[
                "name"
            ]
            for item in result[
                "files"
            ]
        }

        print(
            "FILES FOUND:",
            result[
                "files_found"
            ]
        )

        print(
            "REPORT FOUND:",
            "report.txt"
            in names
        )

        print(
            "CSV FOUND:",
            "data.csv"
            in names
        )

        print(
            "NESTED FOUND:",
            "project.md"
            in names
        )

        print(
            "EXE BLOCKED:",
            "program.exe"
            not in names
        )

        print(
            "ENV BLOCKED:",
            ".env"
            not in names
        )

        print(
            "TOKEN BLOCKED:",
            "calendar_token.json"
            not in names
        )

        print(
            "HIDDEN BLOCKED:",
            ".hidden.txt"
            not in names
        )

        print(
            "LARGE BLOCKED:",
            "large.pdf"
            not in names
        )

        print(
            "PATHS ALLOWED:",
            all(
                registry
                .is_path_allowed(
                    item[
                        "path"
                    ]
                )
                for item
                in result[
                    "files"
                ]
            )
        )

        print()
        print("=" * 70)
        print("NON RECURSIVE")
        print("=" * 70)

        direct_result = (
            scanner.scan_folder(
                direct_folder[
                    "folder_id"
                ]
            )
        )

        direct_names = {
            item[
                "name"
            ]
            for item
            in direct_result[
                "files"
            ]
        }

        print(
            "DIRECT FOUND:",
            "direct.txt"
            in direct_names
        )

        print(
            "DEEP BLOCKED:",
            "deep.txt"
            not in direct_names
        )

        print()
        print("=" * 70)
        print("DISABLED")
        print("=" * 70)

        registry.disable_folder(
            recursive_folder[
                "folder_id"
            ]
        )

        try:

            scanner.scan_folder(
                recursive_folder[
                    "folder_id"
                ]
            )

            print(
                "DISABLED BLOCKED:",
                False
            )

        except PermissionError:

            print(
                "DISABLED BLOCKED:",
                True
            )

        registry.enable_folder(
            recursive_folder[
                "folder_id"
            ]
        )

        print()
        print("=" * 70)
        print("ALL")
        print("=" * 70)

        combined = (
            scanner.scan_all()
        )

        combined_names = {
            item[
                "name"
            ]
            for item
            in combined[
                "files"
            ]
        }

        print(
            "FOLDERS SCANNED:",
            combined[
                "folders_scanned"
            ]
        )

        print(
            "TOTAL FILES:",
            combined[
                "files_found"
            ]
        )

        print(
            "EXPECTED FILES:",
            combined_names
            == {
                "report.txt",
                "data.csv",
                "project.md",
                "direct.txt",
            }
        )

        print(
            "NOT TRUNCATED:",
            not combined[
                "truncated"
            ]
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