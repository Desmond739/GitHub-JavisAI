from __future__ import annotations

import json
import os
import time

from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from app.personal_data.personal_data_model import (
    current_timestamp,
)


DEFAULT_REGISTRY_PATH = Path(
    "data/personal_data/"
    "approved_folders.json"
)


BLOCKED_DIRECTORY_NAMES = {
    ".git",
    ".ssh",
    ".gnupg",
    ".aws",
    ".azure",
    ".kube",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "appdata",
    "windows",
    "system32",
}


BLOCKED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "credentials.json",
    "client_secret.json",
    "client_secrets.json",
}


BLOCKED_FILE_SUFFIXES = {
    "_token.json",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".kdbx",
}


class SafeFolderRegistry:

    def __init__(
        self,
        storage_path:
        str | Path = DEFAULT_REGISTRY_PATH,
    ) -> None:

        self.storage_path = Path(
            storage_path
        )

        self._lock = RLock()

        self._folders: list[dict[str, Any]] = []

        self._load()

    # ============================================================
    # PATH NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_path(
        path: str | Path,
    ) -> Path:

        raw = os.path.expandvars(
            str(path)
        )

        candidate = Path(
            raw
        ).expanduser()

        if not candidate.is_absolute():

            raise ValueError(
                "Approved folder paths "
                "must be absolute."
            )

        return candidate.resolve(
            strict=False
        )

    @staticmethod
    def _path_key(
        path: Path,
    ) -> str:

        return os.path.normcase(
            os.path.abspath(
                str(path)
            )
        )

    # ============================================================
    # DANGEROUS ROOTS
    # ============================================================

    @classmethod
    def _is_dangerous_root(
        cls,
        path: Path,
    ) -> bool:

        resolved = path.resolve(
            strict=False
        )

        # Prevent approving C:\, D:\, /, etc.
        if (
            resolved.anchor
            and cls._path_key(
                resolved
            )
            == cls._path_key(
                Path(
                    resolved.anchor
                )
            )
        ):

            return True

        home = Path.home().resolve(
            strict=False
        )

        # Do not approve the entire user profile.
        if (
            cls._path_key(
                resolved
            )
            == cls._path_key(
                home
            )
        ):

            return True

        return False

    # ============================================================
    # PROTECTED PATHS
    # ============================================================

    @staticmethod
    def _has_blocked_directory(
        path: Path,
    ) -> bool:

        parts = {
            part.casefold()
            for part in path.parts
        }

        return bool(
            parts
            & {
                value.casefold()
                for value
                in BLOCKED_DIRECTORY_NAMES
            }
        )

    @staticmethod
    def _has_blocked_filename(
        path: Path,
    ) -> bool:

        name = path.name.casefold()

        if name in {
            item.casefold()
            for item in BLOCKED_FILE_NAMES
        }:

            return True

        return any(
            name.endswith(
                suffix.casefold()
            )
            for suffix
            in BLOCKED_FILE_SUFFIXES
        )

    @classmethod
    def is_protected_path(
        cls,
        path: str | Path,
    ) -> bool:

        try:

            normalized = (
                cls._normalize_path(
                    path
                )
            )

        except ValueError:

            return True

        return (
            cls._has_blocked_directory(
                normalized
            )
            or
            cls._has_blocked_filename(
                normalized
            )
        )

    # ============================================================
    # LOAD
    # ============================================================

    def _load(
        self,
    ) -> None:

        with self._lock:

            if not self.storage_path.exists():

                self._folders = []

                return

            try:

                payload = json.loads(
                    self.storage_path.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                json.JSONDecodeError,
                OSError,
            ) as exc:

                raise RuntimeError(
                    "Safe Folder Registry "
                    "could not be loaded."
                ) from exc

            folders = payload.get(
                "folders",
                []
            )

            if not isinstance(
                folders,
                list,
            ):

                raise RuntimeError(
                    "Safe Folder Registry "
                    "has an invalid format."
                )

            self._folders = folders

    # ============================================================
    # SAVE
    # ============================================================

    def _save(
        self,
    ) -> None:

        with self._lock:

            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            payload = {
                "version": 1,
                "folders": (
                    self._folders
                ),
            }

            temporary = Path(
                str(
                    self.storage_path
                )
                + ".tmp"
            )

            temporary.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            last_error = None

            try:

                for attempt in range(
                    1,
                    6,
                ):

                    try:

                        os.replace(
                            temporary,
                            self.storage_path,
                        )

                        return

                    except PermissionError as exc:

                        last_error = exc

                        time.sleep(
                            0.10
                            * attempt
                        )

                    except OSError as exc:

                        if getattr(
                            exc,
                            "winerror",
                            None,
                        ) not in {
                            5,
                            32,
                        }:

                            raise

                        last_error = exc

                        time.sleep(
                            0.10
                            * attempt
                        )

                raise RuntimeError(
                    "Could not safely save "
                    "Safe Folder Registry."
                ) from last_error

            finally:

                if temporary.exists():

                    try:

                        temporary.unlink()

                    except OSError:

                        pass

    # ============================================================
    # GET
    # ============================================================

    def get_folder(
        self,
        folder_id: str,
    ) -> dict[str, Any] | None:

        with self._lock:

            for folder in self._folders:

                if (
                    folder.get(
                        "folder_id"
                    )
                    == folder_id
                ):

                    return dict(
                        folder
                    )

        return None

    # ============================================================
    # LIST
    # ============================================================

    def list_folders(
        self,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:

        with self._lock:

            folders = [
                dict(folder)
                for folder
                in self._folders
            ]

        if not active_only:

            return folders

        return [
            folder
            for folder in folders
            if folder.get(
                "status"
            )
            == "active"
        ]

    # ============================================================
    # APPROVE
    # ============================================================

    def approve_folder(
        self,
        path: str | Path,
        *,
        label: str | None = None,
        recursive: bool = True,
    ) -> dict[str, Any]:

        normalized = (
            self._normalize_path(
                path
            )
        )

        if not normalized.exists():

            raise FileNotFoundError(
                "Approved folder does not "
                f"exist: {normalized}"
            )

        if not normalized.is_dir():

            raise NotADirectoryError(
                "Approved path is not "
                f"a directory: {normalized}"
            )

        if self._is_dangerous_root(
            normalized
        ):

            raise PermissionError(
                "Refusing to approve a "
                "drive root or entire "
                "user profile."
            )

        if self._has_blocked_directory(
            normalized
        ):

            raise PermissionError(
                "This folder is inside "
                "a protected directory."
            )

        key = self._path_key(
            normalized
        )

        with self._lock:

            for folder in self._folders:

                existing = Path(
                    folder[
                        "path"
                    ]
                )

                if (
                    self._path_key(
                        existing
                    )
                    == key
                ):

                    folder[
                        "status"
                    ] = "active"

                    folder[
                        "recursive"
                    ] = bool(
                        recursive
                    )

                    if label is not None:

                        folder[
                            "label"
                        ] = str(
                            label
                        ).strip()

                    folder[
                        "updated_at"
                    ] = (
                        current_timestamp()
                    )

                    self._save()

                    return dict(
                        folder
                    )

            timestamp = (
                current_timestamp()
            )

            folder = {
                "folder_id": (
                    str(
                        uuid4()
                    )
                ),
                "path": str(
                    normalized
                ),
                "label": (
                    str(
                        label
                    ).strip()
                    if label is not None
                    else normalized.name
                ),
                "recursive": bool(
                    recursive
                ),
                "status": "active",
                "created_at": timestamp,
                "updated_at": timestamp,
            }

            self._folders.append(
                folder
            )

            self._save()

            return dict(
                folder
            )

    # ============================================================
    # DISABLE
    # ============================================================

    def disable_folder(
        self,
        folder_id: str,
    ) -> dict[str, Any]:

        with self._lock:

            for folder in self._folders:

                if (
                    folder.get(
                        "folder_id"
                    )
                    != folder_id
                ):

                    continue

                folder[
                    "status"
                ] = "disabled"

                folder[
                    "updated_at"
                ] = (
                    current_timestamp()
                )

                self._save()

                return dict(
                    folder
                )

        raise KeyError(
            "Approved folder not found: "
            f"{folder_id}"
        )

    # ============================================================
    # ENABLE
    # ============================================================

    def enable_folder(
        self,
        folder_id: str,
    ) -> dict[str, Any]:

        with self._lock:

            for folder in self._folders:

                if (
                    folder.get(
                        "folder_id"
                    )
                    != folder_id
                ):

                    continue

                path = Path(
                    folder[
                        "path"
                    ]
                )

                if not path.exists():

                    raise FileNotFoundError(
                        "Approved folder no "
                        "longer exists: "
                        f"{path}"
                    )

                folder[
                    "status"
                ] = "active"

                folder[
                    "updated_at"
                ] = (
                    current_timestamp()
                )

                self._save()

                return dict(
                    folder
                )

        raise KeyError(
            "Approved folder not found: "
            f"{folder_id}"
        )

    # ============================================================
    # REMOVE
    # ============================================================

    def remove_folder(
        self,
        folder_id: str,
    ) -> bool:

        with self._lock:

            original_count = len(
                self._folders
            )

            self._folders = [
                folder
                for folder
                in self._folders
                if folder.get(
                    "folder_id"
                )
                != folder_id
            ]

            changed = (
                len(
                    self._folders
                )
                != original_count
            )

            if changed:

                self._save()

            return changed

    # ============================================================
    # ACCESS CHECK
    # ============================================================

    def is_path_allowed(
        self,
        path: str | Path,
    ) -> bool:

        try:

            candidate = (
                self._normalize_path(
                    path
                )
            )

        except ValueError:

            return False

        if (
            self._has_blocked_directory(
                candidate
            )
            or
            self._has_blocked_filename(
                candidate
            )
        ):

            return False

        candidate_key = (
            self._path_key(
                candidate
            )
        )

        for folder in self.list_folders(
            active_only=True
        ):

            root = Path(
                folder[
                    "path"
                ]
            ).resolve(
                strict=False
            )

            root_key = (
                self._path_key(
                    root
                )
            )

            if (
                candidate_key
                == root_key
            ):

                return True

            try:

                relative = (
                    candidate
                    .relative_to(
                        root
                    )
                )

            except ValueError:

                continue

            if folder.get(
                "recursive",
                True,
            ):

                return True

            if len(
                relative.parts
            ) == 1:

                return True

        return False

    # ============================================================
    # ASSERT ACCESS
    # ============================================================

    def require_allowed_path(
        self,
        path: str | Path,
    ) -> Path:

        normalized = (
            self._normalize_path(
                path
            )
        )

        if not self.is_path_allowed(
            normalized
        ):

            raise PermissionError(
                "Path is not inside an "
                "approved MoneroAI folder: "
                f"{normalized}"
            )

        return normalized

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
    ) -> dict[str, int]:

        folders = self.list_folders(
            active_only=False
        )

        return {
            "folders": len(
                folders
            ),
            "active": sum(
                1
                for folder in folders
                if folder.get(
                    "status"
                )
                == "active"
            ),
            "disabled": sum(
                1
                for folder in folders
                if folder.get(
                    "status"
                )
                == "disabled"
            ),
        }


safe_folder_registry = (
    SafeFolderRegistry()
)
