from __future__ import annotations

import hashlib
import os
import stat

from pathlib import Path
from typing import Any

from app.personal_data.personal_data_model import (
    current_timestamp,
)

from app.personal_data.safe_folder_registry import (
    SafeFolderRegistry,
    safe_folder_registry,
)


class FileFingerprintService:

    def __init__(
        self,
        registry:
        SafeFolderRegistry | None = None,
        *,
        chunk_size: int = 1024 * 1024,
        max_file_size_bytes:
        int = 100 * 1024 * 1024,
    ) -> None:

        self.registry = (
            registry
            if registry is not None
            else safe_folder_registry
        )

        if chunk_size <= 0:

            raise ValueError(
                "chunk_size must be greater "
                "than zero."
            )

        if max_file_size_bytes <= 0:

            raise ValueError(
                "max_file_size_bytes must be "
                "greater than zero."
            )

        self.chunk_size = chunk_size

        self.max_file_size_bytes = (
            max_file_size_bytes
        )

    # ============================================================
    # PATH KEY
    # ============================================================

    @staticmethod
    def _path_key(
        path: str | Path,
    ) -> str:

        normalized = os.path.normcase(
            os.path.abspath(
                str(path)
            )
        )

        return hashlib.sha256(
            normalized.encode(
                "utf-8"
            )
        ).hexdigest()

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

            return True

        return False

    # ============================================================
    # VALIDATE FILE
    # ============================================================

    def _require_safe_file(
        self,
        path: str | Path,
    ) -> tuple[
        Path,
        os.stat_result,
    ]:

        candidate = (
            self.registry
            .require_allowed_path(
                path
            )
        )

        if not candidate.exists():

            raise FileNotFoundError(
                f"File not found: {candidate}"
            )

        if self.registry.is_protected_path(
            candidate
        ):

            raise PermissionError(
                "Fingerprinting protected "
                "files is not allowed."
            )

        if self._is_link_or_reparse(
            candidate
        ):

            raise PermissionError(
                "Fingerprinting links, "
                "junctions or reparse points "
                "is not allowed."
            )

        resolved = candidate.resolve(
            strict=True
        )

        if not self.registry.is_path_allowed(
            resolved
        ):

            raise PermissionError(
                "Resolved file escaped the "
                "approved folder."
            )

        try:

            info = resolved.stat(
                follow_symlinks=False
            )

        except OSError as exc:

            raise RuntimeError(
                f"Could not inspect file: "
                f"{resolved}"
            ) from exc

        if not stat.S_ISREG(
            info.st_mode
        ):

            raise ValueError(
                "Fingerprint target is not "
                "a regular file."
            )

        if (
            info.st_size
            > self.max_file_size_bytes
        ):

            raise ValueError(
                "File exceeds the maximum "
                "fingerprint size."
            )

        return (
            resolved,
            info,
        )

    # ============================================================
    # FINGERPRINT ONE FILE
    # ============================================================

    def fingerprint_file(
        self,
        path: str | Path,
    ) -> dict[str, Any]:

        resolved, before = (
            self._require_safe_file(
                path
            )
        )

        digest = hashlib.sha256()

        try:

            with resolved.open(
                "rb"
            ) as handle:

                while True:

                    chunk = handle.read(
                        self.chunk_size
                    )

                    if not chunk:

                        break

                    digest.update(
                        chunk
                    )

        except OSError as exc:

            raise RuntimeError(
                "Could not read file for "
                f"fingerprinting: {resolved}"
            ) from exc

        try:

            after = resolved.stat(
                follow_symlinks=False
            )

        except OSError as exc:

            raise RuntimeError(
                "Could not verify file after "
                "fingerprinting."
            ) from exc

        if (
            before.st_size
            != after.st_size
            or
            before.st_mtime_ns
            != after.st_mtime_ns
        ):

            raise RuntimeError(
                "File changed while it was "
                "being fingerprinted."
            )

        return {
            "path": str(
                resolved
            ),
            "path_fingerprint": (
                self._path_key(
                    resolved
                )
            ),
            "sha256": (
                digest.hexdigest()
            ),
            "algorithm": "sha256",
            "size_bytes": (
                after.st_size
            ),
            "modified_at_ns": (
                after.st_mtime_ns
            ),
            "fingerprinted_at": (
                current_timestamp()
            ),
        }

    # ============================================================
    # ENRICH SCANNER FILE
    # ============================================================

    def fingerprint_metadata(
        self,
        file_info:
        dict[str, Any],
    ) -> dict[str, Any]:

        path = file_info.get(
            "path"
        )

        if not path:

            raise ValueError(
                "Scanner metadata does not "
                "contain a file path."
            )

        fingerprint = (
            self.fingerprint_file(
                path
            )
        )

        result = dict(
            file_info
        )

        result.update(
            {
                "sha256": (
                    fingerprint[
                        "sha256"
                    ]
                ),
                "fingerprint_algorithm": (
                    fingerprint[
                        "algorithm"
                    ]
                ),
                "path_fingerprint": (
                    fingerprint[
                        "path_fingerprint"
                    ]
                ),
                "fingerprinted_at": (
                    fingerprint[
                        "fingerprinted_at"
                    ]
                ),
            }
        )

        return result

    # ============================================================
    # FINGERPRINT SCAN
    # ============================================================

    def fingerprint_scan(
        self,
        scan_result:
        dict[str, Any],
    ) -> dict[str, Any]:

        result = dict(
            scan_result
        )

        files = []

        fingerprint_errors = 0

        for file_info in scan_result.get(
            "files",
            [],
        ):

            try:

                files.append(
                    self.fingerprint_metadata(
                        file_info
                    )
                )

            except (
                OSError,
                ValueError,
                PermissionError,
                RuntimeError,
            ):

                fingerprint_errors += 1

        result[
            "files"
        ] = files

        result[
            "files_fingerprinted"
        ] = len(
            files
        )

        result[
            "fingerprint_errors"
        ] = (
            fingerprint_errors
        )

        return result

    # ============================================================
    # SNAPSHOT COMPARISON
    # ============================================================

    @staticmethod
    def compare_snapshots(
        previous:
        list[dict[str, Any]],
        current:
        list[dict[str, Any]],
    ) -> dict[str, Any]:

        def key(
            item: dict[str, Any],
        ) -> str:

            return os.path.normcase(
                os.path.abspath(
                    str(
                        item.get(
                            "path",
                            "",
                        )
                    )
                )
            )

        previous_by_path = {
            key(item): item
            for item in previous
            if item.get(
                "path"
            )
        }

        current_by_path = {
            key(item): item
            for item in current
            if item.get(
                "path"
            )
        }

        previous_paths = set(
            previous_by_path
        )

        current_paths = set(
            current_by_path
        )

        common_paths = (
            previous_paths
            & current_paths
        )

        changed = []
        unchanged = []

        for path_key in sorted(
            common_paths
        ):

            before = (
                previous_by_path[
                    path_key
                ]
            )

            after = (
                current_by_path[
                    path_key
                ]
            )

            if (
                before.get(
                    "sha256"
                )
                != after.get(
                    "sha256"
                )
            ):

                changed.append(
                    {
                        "path": (
                            after[
                                "path"
                            ]
                        ),
                        "before_sha256": (
                            before.get(
                                "sha256"
                            )
                        ),
                        "after_sha256": (
                            after.get(
                                "sha256"
                            )
                        ),
                    }
                )

            else:

                unchanged.append(
                    after
                )

        removed_candidates = [
            previous_by_path[
                path_key
            ]
            for path_key
            in (
                previous_paths
                - current_paths
            )
        ]

        new_candidates = [
            current_by_path[
                path_key
            ]
            for path_key
            in (
                current_paths
                - previous_paths
            )
        ]

        previous_by_hash: dict[
            str,
            list[
                dict[str, Any]
            ],
        ] = {}

        current_by_hash: dict[
            str,
            list[
                dict[str, Any]
            ],
        ] = {}

        for item in removed_candidates:

            checksum = str(
                item.get(
                    "sha256",
                    "",
                )
            )

            if checksum:

                previous_by_hash.setdefault(
                    checksum,
                    [],
                ).append(
                    item
                )

        for item in new_candidates:

            checksum = str(
                item.get(
                    "sha256",
                    "",
                )
            )

            if checksum:

                current_by_hash.setdefault(
                    checksum,
                    [],
                ).append(
                    item
                )

        renamed = []

        renamed_old_paths = set()
        renamed_new_paths = set()

        shared_hashes = (
            set(
                previous_by_hash
            )
            & set(
                current_by_hash
            )
        )

        for checksum in shared_hashes:

            old_items = (
                previous_by_hash[
                    checksum
                ]
            )

            new_items = (
                current_by_hash[
                    checksum
                ]
            )

            # Only classify as a rename when
            # the relationship is unambiguous.
            if (
                len(
                    old_items
                )
                == 1
                and
                len(
                    new_items
                )
                == 1
            ):

                old_item = (
                    old_items[0]
                )

                new_item = (
                    new_items[0]
                )

                renamed.append(
                    {
                        "from": (
                            old_item[
                                "path"
                            ]
                        ),
                        "to": (
                            new_item[
                                "path"
                            ]
                        ),
                        "sha256": (
                            checksum
                        ),
                    }
                )

                renamed_old_paths.add(
                    key(
                        old_item
                    )
                )

                renamed_new_paths.add(
                    key(
                        new_item
                    )
                )

        new_files = [
            item
            for item in new_candidates
            if key(
                item
            )
            not in renamed_new_paths
        ]

        removed_files = [
            item
            for item in removed_candidates
            if key(
                item
            )
            not in renamed_old_paths
        ]

        all_current_by_hash: dict[
            str,
            list[
                dict[str, Any]
            ],
        ] = {}

        for item in current:

            checksum = str(
                item.get(
                    "sha256",
                    "",
                )
            )

            if checksum:

                all_current_by_hash.setdefault(
                    checksum,
                    [],
                ).append(
                    item
                )

        duplicates = []

        for checksum, items in (
            all_current_by_hash.items()
        ):

            if len(
                items
            ) <= 1:

                continue

            duplicates.append(
                {
                    "sha256": (
                        checksum
                    ),
                    "paths": sorted(
                        [
                            item[
                                "path"
                            ]
                            for item
                            in items
                        ],
                        key=str.casefold,
                    ),
                }
            )

        return {
            "new": (
                new_files
            ),
            "changed": (
                changed
            ),
            "renamed": (
                renamed
            ),
            "removed": (
                removed_files
            ),
            "duplicates": (
                duplicates
            ),
            "unchanged": (
                unchanged
            ),
            "counts": {
                "new": len(
                    new_files
                ),
                "changed": len(
                    changed
                ),
                "renamed": len(
                    renamed
                ),
                "removed": len(
                    removed_files
                ),
                "duplicates": len(
                    duplicates
                ),
                "unchanged": len(
                    unchanged
                ),
            },
        }


file_fingerprint_service = (
    FileFingerprintService()
)
