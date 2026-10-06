from __future__ import annotations

import shutil

from pathlib import Path

from app.personal_data.safe_folder_registry import (
    SafeFolderRegistry,
)


BASE = Path(
    "data/personal_data/"
    "test_safe_folder_registry"
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

    outside = (
        BASE
        / "outside"
    )

    direct_only = (
        BASE
        / "direct"
    )

    nested.mkdir(
        parents=True,
        exist_ok=True,
    )

    outside.mkdir(
        parents=True,
        exist_ok=True,
    )

    direct_only.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry = (
        SafeFolderRegistry(
            REGISTRY_PATH
        )
    )

    try:

        first = (
            registry.approve_folder(
                approved,
                label=(
                    "Approved Test"
                ),
                recursive=True,
            )
        )

        second = (
            registry.approve_folder(
                approved,
                label=(
                    "Approved Test"
                ),
                recursive=True,
            )
        )

        print(
            "SAME FOLDER:",
            first["folder_id"]
            == second["folder_id"]
        )

        print(
            "NO DUPLICATE:",
            len(
                registry.list_folders()
            )
            == 1
        )

        print(
            "ROOT ALLOWED:",
            registry.is_path_allowed(
                approved
            )
        )

        print(
            "CHILD ALLOWED:",
            registry.is_path_allowed(
                nested
                / "report.pdf"
            )
        )

        print(
            "OUTSIDE BLOCKED:",
            not registry.is_path_allowed(
                outside
                / "private.pdf"
            )
        )

        print(
            "ENV BLOCKED:",
            not registry.is_path_allowed(
                approved
                / ".env"
            )
        )

        print(
            "TOKEN BLOCKED:",
            not registry.is_path_allowed(
                approved
                / "calendar_token.json"
            )
        )

        print(
            "PRIVATE KEY BLOCKED:",
            not registry.is_path_allowed(
                approved
                / "private.key"
            )
        )

        print(
            "SSH BLOCKED:",
            not registry.is_path_allowed(
                approved
                / ".ssh"
                / "id_rsa"
            )
        )

        registry.disable_folder(
            first[
                "folder_id"
            ]
        )

        print(
            "DISABLED BLOCKS:",
            not registry.is_path_allowed(
                nested
                / "report.pdf"
            )
        )

        registry.enable_folder(
            first[
                "folder_id"
            ]
        )

        print(
            "REENABLED:",
            registry.is_path_allowed(
                nested
                / "report.pdf"
            )
        )

        direct = (
            registry.approve_folder(
                direct_only,
                label="Direct Only",
                recursive=False,
            )
        )

        print(
            "DIRECT FILE ALLOWED:",
            registry.is_path_allowed(
                direct_only
                / "file.txt"
            )
        )

        print(
            "NESTED BLOCKED:",
            not registry.is_path_allowed(
                direct_only
                / "nested"
                / "file.txt"
            )
        )

        summary = (
            registry.summary()
        )

        print(
            "SUMMARY FOLDERS:",
            summary[
                "folders"
            ]
        )

        print(
            "SUMMARY ACTIVE:",
            summary[
                "active"
            ]
        )

        reloaded = (
            SafeFolderRegistry(
                REGISTRY_PATH
            )
        )

        print(
            "PERSISTED:",
            reloaded.summary()
            == summary
        )

        print(
            "REMOVE WORKS:",
            registry.remove_folder(
                direct[
                    "folder_id"
                ]
            )
        )

    finally:

        if BASE.exists():

            shutil.rmtree(
                BASE
            )

    print(
        "TEMP DATA DELETED:",
        not BASE.exists()
    )


if __name__ == "__main__":

    main()