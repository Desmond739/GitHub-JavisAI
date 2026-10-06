"""Download and verify Naya's pinned local neural female voice once."""

from __future__ import annotations

import hashlib
import os
import ssl

from pathlib import Path
from urllib.request import Request, urlopen

from app.core.config import (
    LOCAL_NEURAL_CONFIG_PATH,
    LOCAL_NEURAL_MODEL_DIR,
    LOCAL_NEURAL_MODEL_PATH,
    LOCAL_NEURAL_VOICE_NAME,
)
from app.services.local_neural_voice_service import (
    CONFIG_SHA256,
    CONFIG_SIZE_BYTES,
    MODEL_SHA256,
    MODEL_SIZE_BYTES,
    verify_local_voice_files,
)


PINNED_VOICE_REVISION = (
    "0c9c5d340496a47205a799eb046aab69334a88e9"
)
VOICE_BASE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/"
    f"{PINNED_VOICE_REVISION}/en/en_US/ljspeech/high/"
)
MODEL_URL = (
    f"{VOICE_BASE_URL}{LOCAL_NEURAL_VOICE_NAME}.onnx?download=true"
)
CONFIG_URL = (
    f"{VOICE_BASE_URL}{LOCAL_NEURAL_VOICE_NAME}.onnx.json?download=true"
)


class LocalVoiceDownloadError(RuntimeError):
    """Raised when a pinned local voice file cannot be installed safely."""


def _file_matches(
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
) -> bool:

    if not path.is_file() or path.stat().st_size != expected_size:
        return False

    digest = hashlib.sha256()

    with path.open("rb") as source:

        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest() == expected_sha256


def _download_verified(
    url: str,
    destination: Path,
    *,
    expected_size: int,
    expected_sha256: str,
) -> None:

    if _file_matches(
        destination,
        expected_size=expected_size,
        expected_sha256=expected_sha256,
    ):
        print("VERIFIED:", destination.name)
        return

    temporary_path = destination.with_suffix(
        destination.suffix + ".download"
    )
    temporary_path.unlink(missing_ok=True)
    request = Request(
        url,
        headers={"User-Agent": "MoneroAI-Naya-Local-Voice"},
    )
    digest = hashlib.sha256()
    received = 0
    next_progress = 10 * 1024 * 1024

    try:

        with urlopen(
            request,
            timeout=30.0,
            context=ssl.create_default_context(),
        ) as response:

            with temporary_path.open("wb") as target:

                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    received += len(chunk)

                    if received > expected_size:
                        raise LocalVoiceDownloadError(
                            "The local voice download exceeded its pinned size."
                        )

                    target.write(chunk)
                    digest.update(chunk)

                    if received >= next_progress:
                        print(
                            "DOWNLOADED:",
                            f"{received // (1024 * 1024)} MB",
                        )
                        next_progress += 10 * 1024 * 1024

                target.flush()
                os.fsync(target.fileno())

        if (
            received != expected_size
            or digest.hexdigest() != expected_sha256
        ):
            raise LocalVoiceDownloadError(
                "The local voice download failed integrity verification."
            )

        temporary_path.replace(destination)
        print("INSTALLED:", destination.name)

    except Exception as error:
        temporary_path.unlink(missing_ok=True)

        if isinstance(error, LocalVoiceDownloadError):
            raise

        raise LocalVoiceDownloadError(
            "The local neural voice could not be downloaded."
        ) from None


def ensure_local_neural_voice() -> None:

    LOCAL_NEURAL_MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    print("LOCAL NEURAL VOICE:", LOCAL_NEURAL_VOICE_NAME)
    print("The 114 MB model is downloaded once, then Naya runs offline.")
    _download_verified(
        MODEL_URL,
        LOCAL_NEURAL_MODEL_PATH,
        expected_size=MODEL_SIZE_BYTES,
        expected_sha256=MODEL_SHA256,
    )
    _download_verified(
        CONFIG_URL,
        LOCAL_NEURAL_CONFIG_PATH,
        expected_size=CONFIG_SIZE_BYTES,
        expected_sha256=CONFIG_SHA256,
    )
    verify_local_voice_files()
    print("LOCAL NEURAL VOICE FILES: VERIFIED")


def main() -> int:

    try:
        ensure_local_neural_voice()

    except Exception as error:
        print("LOCAL NEURAL VOICE DOWNLOAD: FAILED")
        print("ERROR TYPE:", type(error).__name__)
        return 1

    print("LOCAL NEURAL VOICE DOWNLOAD: PASSED")
    print("MICROPHONE USED: NO")
    print("SPEAKER USED: NO")
    print("GOOGLE ACCESS USED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
