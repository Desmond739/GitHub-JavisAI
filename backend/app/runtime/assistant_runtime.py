from __future__ import annotations

from threading import RLock, Thread

from app.automation.scheduler import automation_scheduler
from app.automation.scheduler_setup import setup_automation_schedule
from app.automation.workflows import morning_briefing
from app.core.config import (
    APP_VERSION,
    AUTOMATION_ENABLED,
    BUILD_STAGE,
    OLLAMA_WARMUP_ENABLED,
    VOICE_ENABLED,
)
from app.core.logging_config import (
    log_event,
    logging_status,
)
from app.personal_data.google_integration_service import (
    google_integration_service,
)
from app.services.voice_assistant import voice_assistant
from app.services.assistant_core import assistant_core
from app.services.ollama_client import (
    ollama_status,
    warm_ollama_models,
)
from app.services.voice_service import voice_service
from app.services.speech_service import speech_service
from app.product.task_worker import task_worker


class AssistantRuntime:

    def __init__(self) -> None:

        self._lock = RLock()
        self._started = False
        self._component_errors: dict[str, str] = {}
        self._warmup_thread: Thread | None = None
        self._voice_prepare_thread: Thread | None = None

    def _record_error(
        self,
        component: str,
        error: Exception,
    ) -> None:

        error_type = type(error).__name__

        with self._lock:
            self._component_errors[component] = error_type
        log_event(
            "runtime_component_failed",
            level=40,
            component=component,
            error_type=error_type,
        )

    def _warmup_models(self) -> None:

        try:
            completed = warm_ollama_models()

            if not completed:
                status = ollama_status()
                error_type = str(
                    status.get("warmup_error_type")
                    or "WarmupFailed"
                )
                with self._lock:
                    self._component_errors["ollama_warmup"] = error_type
                log_event(
                    "runtime_component_failed",
                    level=30,
                    component="ollama_warmup",
                    error_type=error_type,
                )
                return

            with self._lock:
                self._component_errors.pop("ollama_warmup", None)
            log_event(
                "runtime_component_started",
                component="ollama_warmup",
            )

        except Exception as error:
            self._record_error("ollama_warmup", error)

    def _prepare_voice(self) -> None:

        try:
            warmup_thread = self._warmup_thread

            if (
                warmup_thread is not None
                and warmup_thread.is_alive()
            ):
                warmup_thread.join(timeout=10.0)

            speech_service.preload_model()
            voice_service.preload()

            with self._lock:

                if not self._started:
                    return

            voice_assistant.start()

            with self._lock:
                self._component_errors.pop("voice", None)

            log_event(
                "runtime_component_started",
                component="voice",
            )

        except Exception as error:
            self._record_error("voice", error)

    def start(self) -> None:

        with self._lock:

            if self._started:
                return

            self._started = True
            self._component_errors.clear()

            # Importing the workflow registers it with the engine.
            _ = morning_briefing

            if OLLAMA_WARMUP_ENABLED:
                self._warmup_thread = Thread(
                    target=self._warmup_models,
                    name="moneroai-model-warmup",
                    daemon=True,
                )
                self._warmup_thread.start()

            if AUTOMATION_ENABLED:

                try:
                    setup_automation_schedule()
                    automation_scheduler.start()
                    task_worker.start()
                    log_event(
                        "runtime_component_started",
                        component="automation",
                    )

                except Exception as error:
                    self._record_error("automation", error)

            if VOICE_ENABLED:
                self._voice_prepare_thread = Thread(
                    target=self._prepare_voice,
                    name="moneroai-voice-preparation",
                    daemon=True,
                )
                self._voice_prepare_thread.start()

            # Google is deliberately not synchronized here. It is
            # available only through the explicit read-only endpoint.
            log_event(
                "runtime_started",
                component="runtime",
                status=(
                    "degraded"
                    if self._component_errors
                    else "ready"
                ),
            )

    def stop(self) -> None:

        with self._lock:

            if not self._started:
                return

            for component, stop in (
                ("voice_assistant", voice_assistant.stop),
                ("voice_service", voice_service.stop),
                ("automation", automation_scheduler.stop),
                ("task_worker", task_worker.stop),
            ):

                try:
                    stop()

                except Exception as error:
                    self._record_error(component, error)

            self._started = False

    def readiness(self) -> dict[str, object]:

        with self._lock:
            started = self._started
            errors = dict(self._component_errors)

        required_components = {
            "api": started,
            "assistant_core": True,
            "read_only_google_gateway": True,
        }
        ready = all(required_components.values())

        return {
            "status": "ready" if ready else "not_ready",
            "ready": ready,
            "required_components": required_components,
            "optional_component_errors": errors,
        }

    def status(self) -> dict[str, object]:

        with self._lock:
            component_errors = dict(self._component_errors)
            warmup_thread = self._warmup_thread
            voice_prepare_thread = self._voice_prepare_thread

        return {
            "version": APP_VERSION,
            "build_stage": BUILD_STAGE,
            "runtime_started": self._started,
            "voice_enabled": VOICE_ENABLED,
            "automation_enabled": AUTOMATION_ENABLED,
            "ollama_warmup_enabled": (
                OLLAMA_WARMUP_ENABLED
            ),
            "assistant_core": assistant_core.status(),
            "ollama": ollama_status(),
            "ollama_warmup_running": (
                warmup_thread is not None
                and warmup_thread.is_alive()
            ),
            "voice_preparation_running": (
                voice_prepare_thread is not None
                and voice_prepare_thread.is_alive()
            ),
            "voice": voice_assistant.status(),
            "automation": automation_scheduler.status(),
            "task_worker": task_worker.status(),
            "google": google_integration_service.status(),
            "logging": logging_status(),
            "component_errors": component_errors,
        }


assistant_runtime = AssistantRuntime()
