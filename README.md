# MoneroAI 3.0 Beta — Naya

MoneroAI is a local-first personal AI platform for Windows, Android and mobile
web. The validated Windows voice remains **Naya** using **“Hey Naya”**, local
Whisper, local Ollama and Microsoft Zira.

This repository is a commercial private-beta build—not a claim of finished,
unlimited or autonomous intelligence. It supplies working source, security
boundaries, deployment files and a path to production. Hosting accounts,
merchant approval, secrets, Android signing and store publication belong to the
operator and are deliberately not included.

## Commercial model

| Plan | Monthly | Included messages | Hybrid capacity | Included cloud |
|---|---:|---:|---:|---:|
| Naya Core | Free | 100 | 512 GB | 1 GB |
| Naya Plus | 2,500 XAF | 500 | 2 TB | 10 GB |
| Naya Sovereign | 5,000 XAF | 1,500 | 5 TB | 25 GB |

After the allowance, a customer may choose prepaid wallet use at **10 XAF per
successful message**. The app displays this price and every deduction. There are
no hidden charges. Hybrid capacity is a management quota across the customer's
devices plus included cloud storage; it is not a promise to host terabytes for
5,000 XAF.

Private beta payments use manual MTN MoMo transfer plus transaction-reference
review. Production payments require an approved MTN MoMo Collections merchant
account. Never collect automated commercial payments through an unapproved
personal wallet.

## Repository

- `backend/` — FastAPI, agents, voice, accounts, subscriptions, wallet, MoMo,
  research, automation and responsive PWA.
- `android/` — Android Studio shell, application ID `cm.nexora.naya`, for
  local pairing or a deployed HTTPS URL.
- `docker-compose.yml` and `backend/Dockerfile` — deployment.
- `.github/workflows/validate.yml` — automated validation.

## Windows local mode

1. Install Python 3.11+, Ollama, `qwen3:8b` and `qwen3:1.7b`.
2. Copy `backend/.env.example` to `backend/.env`.
3. Run `Setup_MoneroAI.bat`, then `Validate_MoneroAI.bat`.
4. Run `Start_MoneroAI.bat` and open `http://127.0.0.1:8001/app/`.

## Phone-independent mode

Deploy the backend behind HTTPS, set `AI_PROVIDER=openai_compatible`, and add
the compatible provider URL, server-side API key and model in the host secret
manager. Then build `android` in Android Studio and enter the deployed URL on
first launch. The Android app cannot be independent merely by copying an APK:
it needs a running backend and inference service. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Security boundaries

- Passwords use PBKDF2-SHA256 with per-user salts; session tokens are stored as hashes.
- Subscription, usage, wallet, tasks, notifications, suggestions and cloud keys are user-scoped.
- Sensitive automation requires confirmation; ambient conversation recording is disabled.
- Google integrations are read-only. Multi-customer Google OAuth remains gated
  until a web callback and per-user token vault are configured.
- Credentials, databases, OAuth tokens, signing keys and personal memory are excluded.

## Validation

```bash
cd backend
python -m compileall -q app
python test_commercial_beta.py
```

Legal/privacy review, security testing, merchant onboarding and store approval
are required before a public paid launch.
