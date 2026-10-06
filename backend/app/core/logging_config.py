"""Privacy-preserving application logging for MoneroAI."""

from __future__ import annotations

import json
import logging

from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.config import (
    BACKEND_DIR,
    LOG_BACKUP_COUNT,
    LOG_LEVEL,
    LOG_MAX_BYTES,
)


LOG_DIRECTORY = BACKEND_DIR / "data" / "logs"
LOG_FILE = LOG_DIRECTORY / "moneroai.log"

_LOGGER_NAME = "moneroai"
_CONFIGURATION_LOCK = RLock()
_SAFE_FIELDS = {
    "component",
    "duration_ms",
    "error_type",
    "method",
    "path",
    "request_id",
    "status",
    "status_code",
}


def configure_logging() -> logging.Logger:
    """Configure one rotating file handler and return the app logger."""

    with _CONFIGURATION_LOCK:
        logger = logging.getLogger(_LOGGER_NAME)

        if getattr(logger, "_moneroai_configured", False):
            return logger

        LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s"
            )
        )

        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        logger.propagate = False
        logger._moneroai_configured = True
        return logger


def _safe_field(value: Any) -> str | int | float | bool | None:

    if value is None or isinstance(value, (int, float, bool)):
        return value

    cleaned = str(value).replace("\r", " ").replace("\n", " ")
    return cleaned[:160]


def log_event(
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Log metadata only; message, response, token, and credential data are rejected."""

    payload = {
        "event": _safe_field(event),
    }
    payload.update(
        {
            key: _safe_field(value)
            for key, value in fields.items()
            if key in _SAFE_FIELDS
        }
    )

    configure_logging().log(
        level,
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def logging_status() -> dict[str, object]:

    return {
        "enabled": True,
        "level": LOG_LEVEL,
        "file": str(Path("data") / "logs" / LOG_FILE.name),
        "request_bodies_logged": False,
        "response_bodies_logged": False,
    }
