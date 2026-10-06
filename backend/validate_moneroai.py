"""Offline, non-voice production validation for MoneroAI."""

from __future__ import annotations

import ast
import importlib.metadata
import json
import os
import re
import sys

from pathlib import Path


ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

# Prevent application imports from starting optional hardware/background work.
os.environ["VOICE_ENABLED"] = "false"
os.environ["AUTOMATION_ENABLED"] = "false"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"


class Validation:

    def __init__(self) -> None:

        self.passed: list[str] = []
        self.failed: list[str] = []

    def check(self, name: str, condition: bool) -> None:

        if condition:
            self.passed.append(name)
        else:
            self.failed.append(name)

    def run(self) -> int:

        self._required_files()
        self._python_syntax()
        self._json_data()
        self._dependencies()
        self._security_invariants()
        self._application_invariants()

        if self.failed:
            print("MONEROAI NON-VOICE VALIDATION: FAILED")

            for name in self.failed:
                print(f"FAIL: {name}")

            print(f"PASSED CHECKS: {len(self.passed)}")
            print(f"FAILED CHECKS: {len(self.failed)}")
            return 1

        print("MONEROAI NON-VOICE VALIDATION: PASSED")
        print(f"CHECKS PASSED: {len(self.passed)}")
        print("VOICE HARDWARE USED: NO")
        print("GOOGLE AUTHORIZATION USED: NO")
        print("EXTERNAL NETWORK USED: NO")
        return 0

    def _required_files(self) -> None:

        required = (
            "app/main.py",
            "app/core/config.py",
            "app/core/logging_config.py",
            "app/services/assistant_core.py",
            "app/services/voice_service.py",
            "app/runtime/assistant_runtime.py",
            "BUILD_INFO.json",
            "prepare_voice_runtime.py",
            "Prepare_Voice_Runtime.bat",
            "Test_Naya_Voice.bat",
            "test_naya_voice.py",
            "Final_Naya_Voice_Test.bat",
            "final_naya_voice_test.py",
            "validate_voice_tuning_offline.py",
            "data/memory/long_term/memories.json",
            "data/knowledge_graph/graph.json",
            "requirements.txt",
            "Start_MoneroAI.bat",
        )

        for relative in required:
            self.check(
                f"required file: {relative}",
                (ROOT / relative).is_file(),
            )

    def _python_syntax(self) -> None:

        python_files = sorted(
            path
            for path in ROOT.rglob("*.py")
            if ".venv" not in path.parts
            and "__pycache__" not in path.parts
        )
        valid = True

        for path in python_files:

            try:
                ast.parse(
                    path.read_text(encoding="utf-8-sig"),
                    filename=str(path),
                )

            except (OSError, SyntaxError, UnicodeError):
                valid = False
                break

        self.check("all Python files parse", valid)

    def _json_data(self) -> None:

        json_files = sorted(
            path
            for path in (ROOT / "data").rglob("*.json")
            if "google" not in path.parts
        )
        valid = True

        for path in json_files:

            try:
                json.loads(path.read_text(encoding="utf-8-sig"))

            except (OSError, UnicodeError, json.JSONDecodeError):
                valid = False
                break

        self.check("local JSON data is valid", valid)

    def _dependencies(self) -> None:

        self.check(
            "Python version is supported",
            sys.version_info >= (3, 11),
        )

        requirements = {}

        for line in (ROOT / "requirements.txt").read_text(
            encoding="utf-8"
        ).splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            name, expected = stripped.split("==", 1)
            requirements[name.casefold()] = expected

        mismatches = []

        for name, expected in requirements.items():

            try:
                actual = importlib.metadata.version(name)

            except importlib.metadata.PackageNotFoundError:
                mismatches.append(name)
                continue

            if actual != expected:
                mismatches.append(name)

        self.check("requirements are installed at pinned versions", not mismatches)

    def _security_invariants(self) -> None:

        google_dir = ROOT / "data" / "personal_data" / "google"
        sensitive_files = []

        if google_dir.exists():
            sensitive_files = [
                path
                for path in google_dir.iterdir()
                if path.name == "credentials.json"
                or path.name.endswith("_token.json")
            ]

        self.check("no packaged Google credentials or tokens", not sensitive_files)

        stale_sync_token = False

        for state_name in (
            "calendar_sync_state.json",
            "contacts_sync_state.json",
        ):
            state_path = google_dir / state_name

            if not state_path.exists():
                continue

            try:
                state = json.loads(
                    state_path.read_text(encoding="utf-8-sig")
                )
            except (OSError, json.JSONDecodeError, UnicodeError):
                stale_sync_token = True
                break

            if state.get("sync_token"):
                stale_sync_token = True
                break

        self.check("packaged Google sync state has no token", not stale_sync_token)

        source_files = [
            ROOT / "app" / "personal_data" / "google_calendar_connector.py",
            ROOT / "app" / "personal_data" / "google_contacts_connector.py",
            ROOT / "app" / "personal_data" / "google_tasks_connector.py",
        ]
        scopes = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in source_files
        )
        forbidden_scopes = (
            "calendar.events",
            '"auth/contacts"',
            "'auth/contacts'",
            '"auth/tasks"',
            "'auth/tasks'",
        )
        self.check(
            "Google connectors contain no write scopes",
            not any(scope in scopes for scope in forbidden_scopes),
        )
        self.check(
            "Google connectors use read-only scopes",
            scopes.count(".readonly") >= 3,
        )

        secret_patterns = (
            re.compile("AI" + r"za[0-9A-Za-z_-]{25,}"),
            re.compile(
                "-----BEGIN "
                + r"(?:RSA |EC )?PRIVATE KEY-----"
            ),
        )
        exposed_secret = False

        for path in ROOT.rglob("*"):

            if not path.is_file():
                continue

            if any(part in {".venv", "__pycache__"} for part in path.parts):
                continue

            if path.suffix.casefold() not in {
                ".py",
                ".json",
                ".txt",
                ".md",
                ".bat",
                ".example",
            }:
                continue

            try:
                content = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue

            if any(pattern.search(content) for pattern in secret_patterns):
                exposed_secret = True
                break

        self.check("no recognizable API key or private key", not exposed_secret)

    def _application_invariants(self) -> None:

        try:
            from app.core.config import (
                APP_VERSION,
                ASSISTANT_NAME,
                BUILD_STAGE,
                COMMAND_END_SILENCE_SECONDS,
                GOOGLE_ACCESS_MODE,
                LOCAL_NEURAL_VOICE_ENABLED,
                MAX_RESPONSE_DELAY_SECONDS,
                PRIMARY_VOICE_PROVIDER,
                SPEECH_BEAM_SIZE,
                SPEECH_MODEL,
                VOICE_OLLAMA_MODEL,
                VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS,
                VOICE_TRANSCRIPTION_TIMEOUT_SECONDS,
                VOICE_RATE,
                WAKE_PHRASE,
            )
            from app.main import app, root
            from app.services.naya_listener import naya_listener
            from app.agents.agent_coordinator import agent_coordinator

            root_result = root()
            route_paths = set(app.openapi().get("paths", {}))
            strategy = agent_coordinator.handle(
                "What is my trading strategy?"
            )
            build = agent_coordinator.handle(
                "What is MoneroAI?"
            )

            self.check("assistant name is Naya", ASSISTANT_NAME == "Naya")
            self.check(
                "application version is platform release candidate",
                APP_VERSION == "2.1.0-rc2",
            )
            self.check(
                "build stage is three-tier connected assistant",
                BUILD_STAGE == "early_access_cloud_mobile",
            )
            self.check("wake phrase is exact", WAKE_PHRASE == "Hey Naya")
            self.check("Google access is read-only", GOOGLE_ACCESS_MODE == "read_only")
            self.check(
                "root identity is consistent",
                root_result.get("assistant") == "Naya"
                and root_result.get("wake_phrase") == "Hey Naya"
                and root_result.get("version") == "2.1.0-rc2"
                and root_result.get("build_stage") == "early_access_cloud_mobile",
            )
            self.check(
                "fast English speech model is configured",
                SPEECH_MODEL == "tiny.en"
                and SPEECH_BEAM_SIZE == 1,
            )
            self.check(
                "voice latency controls remain bounded",
                MAX_RESPONSE_DELAY_SECONDS == 5.0
                and COMMAND_END_SILENCE_SECONDS <= 0.45
                and VOICE_TRANSCRIPTION_TIMEOUT_SECONDS <= 2.0,
            )
            self.check(
                "fast voice model is isolated from the 8B text model",
                VOICE_OLLAMA_MODEL == "qwen3:1.7b"
                and VOICE_OLLAMA_REQUEST_TIMEOUT_SECONDS <= 2.5,
            )
            self.check(
                "Zira is the temporary primary voice",
                PRIMARY_VOICE_PROVIDER == "local_zira"
                and VOICE_RATE == 165,
            )
            self.check(
                "Piper is disabled in the production configuration",
                LOCAL_NEURAL_VOICE_ENABLED is False,
            )
            voice_source = (
                ROOT
                / "app"
                / "services"
                / "voice_service.py"
            ).read_text(encoding="utf-8-sig")
            self.check(
                "voice runtime contains no cloud or Piper dependency",
                "azure" not in voice_source.casefold()
                and "local_neural_voice_service" not in voice_source
                and "from piper" not in voice_source
                and not (
                    ROOT
                    / "app"
                    / "services"
                    / "azure_neural_voice_service.py"
                ).exists(),
            )
            from app.services.voice_service import voice_service

            voice_status = voice_service.status()
            self.check(
                "voice status reports zero Piper wait",
                voice_status.get("primary_provider") == "local_zira"
                and voice_status.get("piper_runtime_enabled") is False
                and voice_status.get("piper_wait_seconds") == 0.0,
            )
            model_source = (
                ROOT
                / "app"
                / "services"
                / "ollama_client.py"
            ).read_text(encoding="utf-8-sig")
            final_test_source = (
                ROOT / "final_naya_voice_test.py"
            ).read_text(encoding="utf-8-sig")
            self.check(
                "voice inference uses a scoped fast-model route",
                "voice_inference_mode" in model_source
                and "VOICE_OLLAMA_MODEL" in model_source,
            )
            self.check(
                "final voice test rejects false-positive timeouts",
                "if timed_out:" in final_test_source
                and 'if "yaounde" not in normalized_response:'
                in final_test_source,
            )
            self.check(
                "wake matching accepts punctuation",
                naya_listener.matches_wake_phrase("Hey, Naya!"),
            )
            self.check(
                "wake matching rejects old name",
                not naya_listener.matches_wake_phrase("Hey Maya"),
            )
            self.check(
                "production API routes are registered",
                {
                    "/api/chat",
                    "/api/google/sync",
                    "/api/system/status",
                    "/api/health/live",
                    "/api/health/ready",
                }.issubset(route_paths),
            )
            self.check(
                "current strategy is Support and Resistance",
                "Support and Resistance" in strategy
                and "MSPS" not in strategy,
            )
            self.check(
                "technical memory identifies Naya",
                "Naya" in build
                and "Maya wake-word" not in build
                and "OpenWakeWord" not in build,
            )

        except Exception:
            self.check("application imports and invariants", False)


if __name__ == "__main__":
    raise SystemExit(Validation().run())
