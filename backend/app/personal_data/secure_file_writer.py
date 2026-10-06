from __future__ import annotations

import os
import time

from pathlib import Path
from uuid import uuid4


def atomic_write_private_text(
    path: str | Path,
    content: str,
    *,
    error_label: str,
    encoding: str = "utf-8",
    attempts: int = 5,
) -> None:
    destination = Path(path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_name(
        f".{destination.name}.{uuid4().hex}.tmp"
    )

    last_error: OSError | None = None

    try:
        temporary.write_text(
            content,
            encoding=encoding,
        )

        try:
            temporary.chmod(0o600)
        except OSError:
            pass

        for attempt in range(1, attempts + 1):
            try:
                os.replace(
                    temporary,
                    destination,
                )

                try:
                    destination.chmod(0o600)
                except OSError:
                    pass

                return

            except PermissionError as exc:
                last_error = exc
                time.sleep(0.10 * attempt)

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
                time.sleep(0.10 * attempt)

        raise RuntimeError(
            f"Could not safely save {error_label}."
        ) from last_error

    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
