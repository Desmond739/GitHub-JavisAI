import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


APP_VERSION = "3.0.0-beta1"
BUILD_STAGE = "commercial_private_beta"


def _environment_flag(
    name: str,
    default: bool,
) -> bool:

    value = os.getenv(
        name,
        "true" if default else "false",
    ).strip().casefold()

    return value in {
        "1",
        "true",
        "yes",
        "on",
    }


def _environment_int(
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:

    try:
        value = int(
            os.getenv(name, str(default)).strip()
        )

    except ValueError:
        value = default

    return max(
        minimum,
        min(maximum, value),
    )


def _environment_float(
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:

    try:
        value = float(
            os.getenv(name, str(default)).strip()
        )

    except ValueError:
        value = default

    return max(
        minimum,
        min(maximum, value),
    )


def _environment_text(
    name: str,
    default: str,
) -> str:

    return os.getenv(name, default).strip() or default


DEFAULT_OLLAMA_MODEL = "qwen3:8b"

# Local inference is a security boundary, not an environment option.
OLLAMA_HOST = "http://127.0.0.1:11434"

OLLAMA_MODEL = (
    os.getenv(
        "OLLAMA_MODEL",
        DEFAULT_OLLAMA_MODEL,
    ).strip()
    or DEFAULT_OLLAMA_MODEL
)

OLLAMA_SPECIALIST_MODEL = (
    os.getenv(
        "OLLAMA_SPECIALIST_MODEL",
        OLLAMA_MODEL,
    ).strip()
    or OLLAMA_MODEL
)

# Spoken requests use the smaller already-installed model so transcription and
# inference can complete inside the five-second response-start boundary. Text
# and deeper application requests continue using qwen3:8b.
VOICE_OLLAMA_MODEL = (
    os.getenv(
        "VOICE_OLLAMA_MODEL",
        "qwen3:1.7b",
    ).strip()
    or "qwen3:1.7b"
)

VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS = _environment_float(
    "VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS",
    2.25,
    1.0,
    2.5,
)

VOICE_RESPONSE_MAX_TOKENS = _environment_int(
    "VOICE_RESPONSE_MAX_TOKENS",
    32,
    12,
    48,
)

ASSISTANT_NAME = (
    os.getenv(
        "ASSISTANT_NAME",
        "Naya",
    ).strip()
    or "Naya"
)

WAKE_PHRASE = (
    os.getenv(
        "WAKE_PHRASE",
        "Hey Naya",
    ).strip()
    or "Hey Naya"
)

VOICE_ENABLED = _environment_flag(
    "VOICE_ENABLED",
    True,
)

AUTOMATION_ENABLED = _environment_flag(
    "AUTOMATION_ENABLED",
    True,
)

OLLAMA_WARMUP_ENABLED = _environment_flag(
    "OLLAMA_WARMUP_ENABLED",
    True,
)

# This build deliberately exposes no configurable write mode.
GOOGLE_ACCESS_MODE = "read_only"

# Wake-only listening is a non-configurable privacy boundary in this release.
LISTENING_MODE = "wake_phrase_only"

DATA_DIR = BACKEND_DIR / "data"
PLATFORM_DB_PATH = DATA_DIR / "platform" / "naya.db"

MOMO_ENVIRONMENT = _environment_text("MOMO_ENVIRONMENT", "sandbox").casefold()
MOMO_BASE_URL = _environment_text(
    "MOMO_BASE_URL",
    "https://sandbox.momodeveloper.mtn.com",
)
MOMO_COLLECTION_SUBSCRIPTION_KEY = os.getenv(
    "MOMO_COLLECTION_SUBSCRIPTION_KEY", ""
).strip()
MOMO_API_USER = os.getenv("MOMO_API_USER", "").strip()
MOMO_API_KEY = os.getenv("MOMO_API_KEY", "").strip()
MOMO_CALLBACK_URL = os.getenv("MOMO_CALLBACK_URL", "").strip()
MOMO_TARGET_ENVIRONMENT = _environment_text(
    "MOMO_TARGET_ENVIRONMENT", "sandbox"
)
MOMO_MANUAL_PAYMENT_NUMBER = os.getenv("MOMO_MANUAL_PAYMENT_NUMBER", "").strip()
MOMO_MANUAL_ACCOUNT_NAME = os.getenv("MOMO_MANUAL_ACCOUNT_NAME", "").strip()
PAYMENT_ADMIN_TOKEN = os.getenv("PAYMENT_ADMIN_TOKEN", "").strip()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "").strip()
R2_ENCRYPTION_KEY = os.getenv("R2_ENCRYPTION_KEY", "").strip()

MOBILE_ACCESS_ENABLED = _environment_flag("MOBILE_ACCESS_ENABLED", False)
NAYA_DEVICE_TOKEN = os.getenv("NAYA_DEVICE_TOKEN", "").strip()

# Commercial account and billing controls. Generate a long random secret in
# production; startup refuses privileged operations when secrets are absent.
SESSION_DAYS = _environment_int("SESSION_DAYS", 30, 1, 90)
USAGE_PRICE_XAF = _environment_int("USAGE_PRICE_XAF", 10, 1, 10)
PUBLIC_REGISTRATION_ENABLED = _environment_flag("PUBLIC_REGISTRATION_ENABLED", True)

# Use local_ollama on the owner's PC. A deployed phone-independent backend may
# use any OpenAI-compatible provider without changing application code.
AI_PROVIDER = _environment_text("AI_PROVIDER", "local_ollama").casefold()
AI_COMPATIBLE_BASE_URL = os.getenv("AI_COMPATIBLE_BASE_URL", "").strip().rstrip("/")
AI_COMPATIBLE_API_KEY = os.getenv("AI_COMPATIBLE_API_KEY", "").strip()
AI_COMPATIBLE_MODEL = _environment_text("AI_COMPATIBLE_MODEL", OLLAMA_MODEL)
AI_COMPATIBLE_TIMEOUT_SECONDS = _environment_float("AI_COMPATIBLE_TIMEOUT_SECONDS", 30.0, 2.0, 120.0)
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()

SPEECH_MODEL = (
    os.getenv(
        "SPEECH_MODEL",
        "tiny.en",
    ).strip()
    or "tiny.en"
)

SPEECH_CPU_THREADS = _environment_int(
    "SPEECH_CPU_THREADS",
    min(6, max(2, os.cpu_count() or 4)),
    1,
    12,
)

SPEECH_BEAM_SIZE = _environment_int(
    "SPEECH_BEAM_SIZE",
    1,
    1,
    3,
)

WAKE_LISTEN_SECONDS = _environment_int(
    "WAKE_LISTEN_SECONDS",
    3,
    1,
    30,
)

COMMAND_LISTEN_SECONDS = _environment_int(
    "COMMAND_LISTEN_SECONDS",
    7,
    1,
    60,
)

COMMAND_END_SILENCE_SECONDS = _environment_float(
    "COMMAND_END_SILENCE_SECONDS",
    0.45,
    0.3,
    2.0,
)

COMMAND_SPEECH_THRESHOLD = _environment_float(
    "COMMAND_SPEECH_THRESHOLD",
    0.012,
    0.001,
    0.2,
)

MAX_RESPONSE_DELAY_SECONDS = _environment_float(
    "MAX_RESPONSE_DELAY_SECONDS",
    5.0,
    2.0,
    5.0,
)

VOICE_TRANSCRIPTION_TIMEOUT_SECONDS = _environment_float(
    "VOICE_TRANSCRIPTION_TIMEOUT_SECONDS",
    1.75,
    0.75,
    2.0,
)

# Reserve a small amount of the response-start budget for the Zira queue.
VOICE_RESPONSE_START_MARGIN_SECONDS = 0.15

OLLAMA_REQUEST_TIMEOUT_SECONDS = _environment_float(
    "OLLAMA_REQUEST_TIMEOUT_SECONDS",
    3.5,
    1.0,
    4.0,
)

VOICE_RATE = _environment_int(
    "VOICE_RATE",
    165,
    80,
    300,
)

# Microsoft Zira is the temporary primary voice selected after the Windows
# speaker test. This constant is deliberately not environment-configurable so
# an old .env file cannot silently put Piper back into the response path.
PRIMARY_VOICE_PROVIDER = "local_zira"

# The Piper research integration is retained for a future voice upgrade, but
# it is disabled and is not imported by the production voice service. This is
# intentionally hard-coded so an RC3 .env file cannot reactivate it.
LOCAL_NEURAL_VOICE_ENABLED = False

LOCAL_NEURAL_VOICE_NAME = "en_US-ljspeech-high"
LOCAL_NEURAL_MODEL_DIR = BACKEND_DIR / "data" / "voice_models"
LOCAL_NEURAL_MODEL_PATH = (
    LOCAL_NEURAL_MODEL_DIR
    / f"{LOCAL_NEURAL_VOICE_NAME}.onnx"
)
LOCAL_NEURAL_CONFIG_PATH = (
    LOCAL_NEURAL_MODEL_DIR
    / f"{LOCAL_NEURAL_VOICE_NAME}.onnx.json"
)

LOCAL_NEURAL_TIMEOUT_SECONDS = _environment_float(
    "LOCAL_NEURAL_TIMEOUT_SECONDS",
    1.5,
    0.35,
    2.0,
)

LOCAL_NEURAL_LENGTH_SCALE = _environment_float(
    "LOCAL_NEURAL_LENGTH_SCALE",
    1.0,
    0.85,
    1.2,
)

LOCAL_NEURAL_NOISE_SCALE = _environment_float(
    "LOCAL_NEURAL_NOISE_SCALE",
    0.667,
    0.3,
    1.0,
)

LOCAL_NEURAL_NOISE_WIDTH = _environment_float(
    "LOCAL_NEURAL_NOISE_WIDTH",
    0.333,
    0.1,
    1.0,
)

LOCAL_NEURAL_VOLUME = _environment_float(
    "LOCAL_NEURAL_VOLUME",
    0.95,
    0.5,
    1.0,
)

MICROPHONE_DEVICE = (
    os.getenv("MICROPHONE_DEVICE", "").strip()
    or None
)

LOG_LEVEL = _environment_text(
    "LOG_LEVEL",
    "INFO",
).upper()

if LOG_LEVEL not in {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}:
    LOG_LEVEL = "INFO"

LOG_MAX_BYTES = _environment_int(
    "LOG_MAX_BYTES",
    2_000_000,
    100_000,
    20_000_000,
)

LOG_BACKUP_COUNT = _environment_int(
    "LOG_BACKUP_COUNT",
    3,
    1,
    10,
)

CHAT_MESSAGE_MAX_CHARACTERS = _environment_int(
    "CHAT_MESSAGE_MAX_CHARACTERS",
    4_000,
    100,
    20_000,
)
