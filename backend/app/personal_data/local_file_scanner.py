from __future__ import annotations

import os
import stat

from datetime import datetime
from pathlib import Path
from typing import Any

from app.personal_data.safe_folder_registry import (
    SafeFolderRegistry,
    safe_folder_registry,
)


DEFAULT_ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
    ".doc",
    ".docx",
    ".rtf",
    ".csv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
}


class LocalFileScanner:

    def __init__(
        self,
        registry:
        SafeFolderRegistry | None = None,
        *,
        allowed_extensions:
        set[str] | None = None,
        max_files: int = 10000,
        max_file_size_bytes:
        int = 100 * 1024 * 1024,
        include_hidden: bool = False,
    ) -> None:

        self.registry = (
            registry
            if registry is not None
            else safe_folder_registry
        )

        if max_files <= 0:

            raise ValueError(
                "max_files must be greater "
                "than zero."
            )

        if max_file_size_bytes <= 0:

            raise ValueError(
                "max_file_size_bytes must be "
                "greater than zero."
            )

        extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else DEFAULT_ALLOWED_EXTENSIONS
        )

        self.allowed_extensions = {
            (
                extension
                if str(extension).startswith(".")
                else "." + str(extension)
            ).casefold()
            for extension in extensions
        }

        self.max_files = max_files

        self.max_file_size_bytes = (
            max_file_size_bytes
        )

        self.include_hidden = bool(
            include_hidden
        )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _timestamp(
        value: float,
    ) -> str:

        return (
            datetime
            .fromtimestamp(
                value
            )
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        )

    @staticmethod
    def _is_hidden_name(
        name: str,
    ) -> bool:

        return bool(
            name
            and name.startswith(".")
        )

    # ============================================================
    # LINK / REPARSE PROTECTION
    # ============================================================

    @staticmethod
    def _is_link_or_reparse(
        path: Path,
    ) -> bool:

        try:

            if path.is_symlink():

                return True

            is_junction = getattr(
                path,
                "is_junction",
                None,
            )

            if (
                callable(
                    is_junction
                )
                and is_junction()
            ):

                return True

            info = os.lstat(
                path
            )

            attributes = getattr(
                info,
                "st_file_attributes",
                0,
            )

            reparse_flag = getattr(
                stat,
                "FILE_ATTRIBUTE_REPARSE_POINT",
                0,
            )

            if (
                reparse_flag
                and attributes
                & reparse_flag
            ):

                return True

        except OSError:

            # If link safety cannot be
            # determined, fail closed.
            return True

        return False

    # ============================================================
    # FILE TYPE
    # ============================================================

    def _extension_allowed(
        self,
        path: Path,
    ) -> bool:

        return (
            path.suffix.casefold()
            in self.allowed_extensions
        )

    # ============================================================
    # FILE METADATA
    # ============================================================

    def _file_metadata(
        self,
        path: Path,
        *,
        root: Path,
        folder:
        dict[str, Any],
    ) -> dict[str, Any] | None:

        if not self.registry.is_path_allowed(
            path
        ):

            return None

        if self.registry.is_protected_path(
            path
        ):

            return None

        if self._is_link_or_reparse(
            path
        ):

            return None

        try:

            info = path.stat(
                follow_symlinks=False
            )

        except OSError:

            return None

        if not stat.S_ISREG(
            info.st_mode
        ):

            return None

        if (
            info.st_size
            > self.max_file_size_bytes
        ):

            return None

        try:

            resolved = path.resolve(
                strict=True
            )

        except OSError:

            return None

        if not self.registry.is_path_allowed(
            resolved
        ):

            return None

        try:

            relative_path = (
                resolved
                .relative_to(
                    root
                )
            )

        except ValueError:

            # A redirection escaped the
            # approved root.
            return None

        return {
            "folder_id": (
                folder[
                    "folder_id"
                ]
            ),
            "folder_label": (
                folder.get(
                    "label",
                    "",
                )
            ),
            "root_path": str(
                root
            ),
            "path": str(
                resolved
            ),
            "relative_path": str(
                relative_path
            ),
            "name": (
                resolved.name
            ),
            "stem": (
                resolved.stem
            ),
            "extension": (
                resolved.suffix
                .casefold()
            ),
            "size_bytes": (
                info.st_size
            ),
            "created_at_file": (
                self._timestamp(
                    info.st_ctime
                )
            ),
            "modified_at": (
                self._timestamp(
                    info.st_mtime
                )
            ),
        }

    # ============================================================
    # SCAN ONE FOLDER
    # ============================================================

    def scan_folder(
        self,
        folder_id: str,
    ) -> dict[str, Any]:

        folder = (
            self.registry
            .get_folder(
                folder_id
            )
        )

        if folder is None:

            raise KeyError(
                "Approved folder not found: "
                f"{folder_id}"
            )

        if (
            folder.get(
                "status"
            )
            != "active"
        ):

            raise PermissionError(
                "Approved folder is disabled."
            )

        root = Path(
            folder[
                "path"
            ]
        ).resolve(
            strict=True
        )

        if not root.is_dir():

            raise NotADirectoryError(
                f"Approved path is not "
                f"a directory: {root}"
            )

        if not self.registry.is_path_allowed(
            root
        ):

            raise PermissionError(
                "Approved folder failed "
                "registry validation."
            )

        recursive = bool(
            folder.get(
                "recursive",
                True,
            )
        )

        files = []

        skipped = {
            "hidden": 0,
            "protected": 0,
            "unsupported": 0,
            "oversized": 0,
            "links": 0,
            "errors": 0,
        }

        truncated = False

        stack = [
            root
        ]

        visited = set()

        while stack:

            current = stack.pop()

            try:

                current_resolved = (
                    current.resolve(
                        strict=True
                    )
                )

            except OSError:

                skipped[
                    "errors"
                ] += 1

                continue

            current_key = (
                os.path.normcase(
                    os.path.abspath(
                        str(
                            current_resolved
                        )
                    )
                )
            )

            if current_key in visited:

                continue

            visited.add(
                current_key
            )

            if not self.registry.is_path_allowed(
                current_resolved
            ):

                skipped[
                    "protected"
                ] += 1

                continue

            if (
                current_resolved
                != root
                and self._is_link_or_reparse(
                    current_resolved
                )
            ):

                skipped[
                    "links"
                ] += 1

                continue

            try:

                entries = list(
                    os.scandir(
                        current_resolved
                    )
                )

            except OSError:

                skipped[
                    "errors"
                ] += 1

                continue

            entries.sort(
                key=lambda item:
                item.name.casefold()
            )

            for entry in entries:

                if (
                    not self.include_hidden
                    and self._is_hidden_name(
                        entry.name
                    )
                ):

                    skipped[
                        "hidden"
                    ] += 1

                    continue

                path = Path(
                    entry.path
                )

                if self._is_link_or_reparse(
                    path
                ):

                    skipped[
                        "links"
                    ] += 1

                    continue

                if self.registry.is_protected_path(
                    path
                ):

                    skipped[
                        "protected"
                    ] += 1

                    continue

                try:

                    is_directory = (
                        entry.is_dir(
                            follow_symlinks=False
                        )
                    )

                    is_file = (
                        entry.is_file(
                            follow_symlinks=False
                        )
                    )

                except OSError:

                    skipped[
                        "errors"
                    ] += 1

                    continue

                if is_directory:

                    if (
                        recursive
                        and self.registry
                        .is_path_allowed(
                            path
                        )
                    ):

                        stack.append(
                            path
                        )

                    continue

                if not is_file:

                    continue

                if not self._extension_allowed(
                    path
                ):

                    skipped[
                        "unsupported"
                    ] += 1

                    continue

                try:

                    size = entry.stat(
                        follow_symlinks=False
                    ).st_size

                except OSError:

                    skipped[
                        "errors"
                    ] += 1

                    continue

                if (
                    size
                    > self.max_file_size_bytes
                ):

                    skipped[
                        "oversized"
                    ] += 1

                    continue

                metadata = (
                    self._file_metadata(
                        path,
                        root=root,
                        folder=folder,
                    )
                )

                if metadata is None:

                    skipped[
                        "protected"
                    ] += 1

                    continue

                files.append(
                    metadata
                )

                if (
                    len(
                        files
                    )
                    >= self.max_files
                ):

                    truncated = True

                    break

            if truncated:

                break

        files.sort(
            key=lambda item:
            item[
                "path"
            ].casefold()
        )

        return {
            "folder_id": (
                folder[
                    "folder_id"
                ]
            ),
            "label": (
                folder.get(
                    "label",
                    ""
                )
            ),
            "root_path": (
                str(
                    root
                )
            ),
            "recursive": (
                recursive
            ),
            "files_found": (
                len(
                    files
                )
            ),
            "files": files,
            "skipped": skipped,
            "truncated": (
                truncated
            ),
        }

    # ============================================================
    # SCAN ALL APPROVED FOLDERS
    # ============================================================

    def scan_all(
        self,
    ) -> dict[str, Any]:

        folders = (
            self.registry
            .list_folders(
                active_only=True
            )
        )

        all_files = []

        seen_paths = set()

        skipped = {
            "hidden": 0,
            "protected": 0,
            "unsupported": 0,
            "oversized": 0,
            "links": 0,
            "errors": 0,
        }

        truncated = False

        for folder in folders:

            result = self.scan_folder(
                folder[
                    "folder_id"
                ]
            )

            for key in skipped:

                skipped[
                    key
                ] += result[
                    "skipped"
                ].get(
                    key,
                    0,
                )

            for file_info in result[
                "files"
            ]:

                key = os.path.normcase(
                    os.path.abspath(
                        file_info[
                            "path"
                        ]
                    )
                )

                if key in seen_paths:

                    continue

                seen_paths.add(
                    key
                )

                all_files.append(
                    file_info
                )

            if result[
                "truncated"
            ]:

                truncated = True

        all_files.sort(
            key=lambda item:
            item[
                "path"
            ].casefold()
        )

        return {
            "folders_scanned": (
                len(
                    folders
                )
            ),
            "files_found": (
                len(
                    all_files
                )
            ),
            "files": (
                all_files
            ),
            "skipped": (
                skipped
            ),
            "truncated": (
                truncated
            ),
        }


local_file_scanner = (
    LocalFileScanner()
)