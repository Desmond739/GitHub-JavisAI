# MoneroAI 2.1 Release Candidate 2 — Naya Early Access

This build adds the three-level commercial platform and responsive PWA without
changing the validated Naya/Zira voice path. It includes hybrid quota metadata,
MTN MoMo Collections integration, granular Google Calendar/Gmail/Drive read-only
connectors, explainable suggestions, a persistent task worker, owner confirmation,
notifications, and audit events. Open `http://127.0.0.1:8001/app/` after startup.

External credentials are never packaged. MoMo, Google OAuth, cloud storage,
public HTTPS hosting and Android signing remain inactive until the owner supplies
the corresponding accounts and explicitly approves activation.

RC2 additionally provides client-side AES-256-GCM encryption for Cloudflare R2,
a fail-closed temporary manual MoMo verification flow, authenticated LAN device
pairing, and a native Android Studio shell using `cm.nexora.naya`.

MoneroAI is a local-first personal AI assistant for Windows. Its production
backend is Python and FastAPI, inference runs locally through Ollama using
`qwen3:8b`, the assistant name is **Naya**, and the exact wake phrase is
**“Hey Naya”**.

## Production architecture

- One assistant coordinator serves the HTTP API and voice pipeline.
- Specialized personal, career, finance, trading, technical, and general agents
  share long-term memory and a personal knowledge graph.
- Calendar, Contacts, Tasks, Notes, Goals, and approved-folder queries use
  verified local data before language-model routing.
- Google Calendar, Contacts, and Tasks synchronization is read-only,
  non-interactive, and available only through an explicit API request.
- Ollama is fixed to `127.0.0.1:11434` and warms in the background.
- Text and deeper requests use `qwen3:8b`; spoken requests use the separately
  bounded `qwen3:1.7b` route so transcription and inference fit the response
  deadline without lowering normal text-response quality.
- `tiny.en` speech recognition is preloaded and uses CPU int8, one worker, and
  single-beam English decoding.
- Command capture stops after about 0.45 seconds of silence. Transcription and
  AI inference are timed separately, the heard command is retained on an AI
  timeout, and processing remains inside the five-second response target.
- Microsoft Zira is the temporary primary voice through Windows SAPI5. It is
  local, requires no account, and has zero Piper loading or fallback wait.
- Piper and Azure are absent from the active startup and response paths.

## Safe Windows setup

Prerequisites are Windows 10 or newer, Python 3.11 or newer, Ollama, the
`qwen3:8b` and `qwen3:1.7b` models, a microphone, and Microsoft Zira Desktop.

1. Open the extracted `MoneroAI\backend` folder.
2. Run `Setup_MoneroAI.bat`.
3. Run `Validate_MoneroAI.bat`.
4. Run `Prepare_Voice_Runtime.bat` once.
5. Run `Start_MoneroAI.bat` after the final hardware test passes.

Setup creates `.venv`, installs pinned dependencies, confirms Ollama, performs
hardware-free validation, and prepares Whisper plus the Zira engine. Whisper
may download its `tiny.en` model once. Preparation does not record audio, play
audio, authorize Google, or use a cloud voice.

## Validation launchers

- `Validate_MoneroAI.bat`: complete offline code and simulated-pipeline checks;
  no microphone or speaker.
- `Test_Naya_Voice.bat`: Zira speaker-only check; no microphone or Google.
- `Final_Naya_Voice_Test.bat`: final wake phrase, microphone, fast-model answer,
  answer correctness, five-second timing, and Zira speaker test. A blank
  command, timeout, incorrect answer, wrong model, or wrong voice fails it.

## Local API

The launcher binds only to `127.0.0.1:8001`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Naya identity and access-mode summary |
| `GET` | `/api/health/live` | Process liveness |
| `GET` | `/api/health/ready` | Required-component readiness |
| `GET` | `/api/system/status` | Safe runtime diagnostics |
| `POST` | `/api/chat` | Text request to the shared assistant core |
| `POST` | `/api/google/sync` | Explicit, non-interactive read-only sync |

Example text request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8001/api/chat" `
  -ContentType "application/json" `
  -Body '{"message":"What is my trading strategy?"}'
```

## Security and privacy boundaries

- The API and Ollama connections are local-only.
- Google access is hard-coded to `read_only`; environment configuration cannot
  enable writes.
- Normal startup never opens a browser or initiates OAuth.
- Google credentials, tokens, synchronization state, generated personal-data
  stores, `.env`, `.venv`, diagnostics, and downloaded models are excluded from
  release packages. Project-owned seeded assistant memory remains.
- Live TTS sends no text or audio to a network service.
- Automation denies unknown actions and retains confirmation boundaries for
  sensitive actions.

## Voice decision

The attempted Piper voice was not used successfully on the target Windows
machine and the user accepted Zira temporarily. RC5 therefore removes Piper
from required dependencies, preparation, preload, normal speech, and timeout
logic. The experimental Piper source is retained only for a later voice upgrade
and cannot become the provider through an old `.env` file.

## Google read-only authorization — deferred

Do not perform this section until the user explicitly approves Google
authorization. At that time, place a Google Desktop OAuth client file at
`data/personal_data/google/credentials.json`, then run:

```powershell
.venv\Scripts\python.exe authorize_google_read_only.py --authorize-read-only
```

## Troubleshooting

- If setup reports Python is missing, install Python 3.11 or newer and enable
  the Python launcher or add Python to `PATH`.
- If Ollama is unavailable, start Ollama and run `ollama list`.
- If `qwen3:8b` is missing, run `ollama pull qwen3:8b`.
- If the fast voice model is missing, run `ollama pull qwen3:1.7b`.
- If the final test does not hear you, close other microphone applications and
  configure `MICROPHONE_DEVICE` in `.env`.
- If Zira is missing, install the English (United States) Windows speech voice.
- Health and status endpoints never authorize Google.
