"""Fast local Ollama client with proxy isolation and model warm-up."""

from __future__ import annotations

import os
import json
import urllib.request

from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from time import monotonic
from typing import Iterator

from app.core.config import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_REQUEST_TIMEOUT_SECONDS,
    OLLAMA_SPECIALIST_MODEL,
    VOICE_OLLAMA_MODEL,
    VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS,
    VOICE_RESPONSE_MAX_TOKENS,
    AI_PROVIDER, AI_COMPATIBLE_BASE_URL, AI_COMPATIBLE_API_KEY,
    AI_COMPATIBLE_MODEL, AI_COMPATIBLE_TIMEOUT_SECONDS,
)


_PROXY_VARIABLES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)

_saved_proxy_values = {
    name: os.environ.pop(name)
    for name in _PROXY_VARIABLES
    if name in os.environ
}

try:
    import ollama as _ollama

    _default_client = _ollama.Client(
        host=OLLAMA_HOST,
        timeout=OLLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    _voice_client = _ollama.Client(
        host=OLLAMA_HOST,
        timeout=VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    _warmup_client = _ollama.Client(
        host=OLLAMA_HOST,
        timeout=180.0,
    )

finally:
    os.environ.update(_saved_proxy_values)


_voice_inference_enabled: ContextVar[bool] = ContextVar(
    "voice_inference_enabled",
    default=False,
)
_request_status_lock = RLock()
_last_model: str | None = None
_last_route: str | None = None
_last_request_seconds: float | None = None
_last_request_error_type: str | None = None


class RoutedOllamaClient:
    """Route voice calls to the fast model without changing agent code."""

    def chat(self, *args, **kwargs):

        global _last_model
        global _last_request_error_type
        global _last_request_seconds
        global _last_route

        voice_route = _voice_inference_enabled.get()
        client = _voice_client if voice_route else _default_client

        if voice_route:
            kwargs["model"] = VOICE_OLLAMA_MODEL
            options = dict(kwargs.get("options") or {})

            try:
                requested_tokens = int(
                    options.get(
                        "num_predict",
                        VOICE_RESPONSE_MAX_TOKENS,
                    )
                )
            except (TypeError, ValueError):
                requested_tokens = VOICE_RESPONSE_MAX_TOKENS

            options["num_predict"] = min(
                requested_tokens,
                VOICE_RESPONSE_MAX_TOKENS,
            )
            kwargs["options"] = options

        if not voice_route and AI_PROVIDER == "openai_compatible":
            if not AI_COMPATIBLE_BASE_URL or not AI_COMPATIBLE_API_KEY:
                raise RuntimeError("Cloud AI provider is selected but not configured.")
            payload = {
                "model": AI_COMPATIBLE_MODEL,
                "messages": kwargs.get("messages") or (args[1] if len(args) > 1 else []),
                "stream": False,
                "max_tokens": int((kwargs.get("options") or {}).get("num_predict", 512)),
            }
            request = urllib.request.Request(
                f"{AI_COMPATIBLE_BASE_URL}/chat/completions",
                data=json.dumps(payload).encode(), method="POST",
                headers={"Authorization": f"Bearer {AI_COMPATIBLE_API_KEY}", "Content-Type": "application/json"},
            )
            started_at = monotonic()
            try:
                with urllib.request.urlopen(request, timeout=AI_COMPATIBLE_TIMEOUT_SECONDS) as response:
                    result = json.loads(response.read())
                return {"message": {"content": result["choices"][0]["message"]["content"]}}
            finally:
                with _request_status_lock:
                    _last_model = AI_COMPATIBLE_MODEL
                    _last_route = "cloud_compatible"
                    _last_request_seconds = round(monotonic() - started_at, 3)

        selected_model = str(
            kwargs.get("model")
            or (args[0] if args else "")
        )
        started_at = monotonic()
        error_type: str | None = None

        try:
            response = client.chat(*args, **kwargs)
            return response

        except Exception as error:
            error_type = type(error).__name__
            raise

        finally:
            with _request_status_lock:
                _last_model = selected_model
                _last_route = "voice_fast" if voice_route else "standard"
                _last_request_seconds = round(
                    monotonic() - started_at,
                    3,
                )
                _last_request_error_type = error_type


ollama = RoutedOllamaClient()


@contextmanager
def voice_inference_mode() -> Iterator[None]:
    """Temporarily route all agent model calls to the fast voice model."""

    token = _voice_inference_enabled.set(True)

    try:
        yield
    finally:
        _voice_inference_enabled.reset(token)


_warmup_lock = RLock()
_warmup_complete = False
_warmup_error: str | None = None


def warm_ollama_models() -> bool:

    global _warmup_complete
    global _warmup_error

    with _warmup_lock:

        if _warmup_complete:
            return True

        try:
            for model in dict.fromkeys(
                (
                    OLLAMA_MODEL,
                    OLLAMA_SPECIALIST_MODEL,
                    VOICE_OLLAMA_MODEL,
                )
            ):
                _warmup_client.generate(
                    model=model,
                    prompt="",
                    stream=False,
                    keep_alive=-1,
                    options={"num_predict": 1},
                )

        except Exception as error:
            _warmup_error = type(error).__name__
            return False

        _warmup_complete = True
        _warmup_error = None
        return True


def ollama_status() -> dict[str, object]:

    with _request_status_lock:
        last_model = _last_model
        last_route = _last_route
        last_request_seconds = _last_request_seconds
        last_request_error_type = _last_request_error_type

    return {
        "model": OLLAMA_MODEL,
        "specialist_model": OLLAMA_SPECIALIST_MODEL,
        "voice_model": VOICE_OLLAMA_MODEL,
        "host": OLLAMA_HOST,
        "warmup_complete": _warmup_complete,
        "warmup_error_type": _warmup_error,
        "request_timeout_seconds": (
            OLLAMA_REQUEST_TIMEOUT_SECONDS
        ),
        "voice_request_timeout_seconds": (
            VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS
        ),
        "voice_max_tokens": VOICE_RESPONSE_MAX_TOKENS,
        "last_model": last_model,
        "last_route": last_route,
        "last_request_seconds": last_request_seconds,
        "last_request_error_type": last_request_error_type,
    }
