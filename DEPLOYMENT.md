# Deployment and owner actions

## Private phone beta

1. Choose an HTTPS host and an OpenAI-compatible inference provider. Put keys
   only in the host secret manager.
2. Copy `backend/.env.example` to a private `.env`. Set cloud AI, private-beta
   MoMo payee, a long random payment-admin token, and optional R2/search values.
3. Deploy `backend/Dockerfile` with a persistent `/app/data` volume.
4. Verify each manual MoMo reference against the actual received transaction.
5. Open `android` in Android Studio, create an owner-held upload keystore,
   build a signed APK/AAB, and enter the HTTPS URL on first launch.
6. Replace the deleted Google OAuth client. The packaged desktop token flow is
   for the owner's local instance; public multi-user Google access needs a web
   callback and encrypted per-user token storage.

Minimum cloud settings:

```dotenv
VOICE_ENABLED=false
OLLAMA_WARMUP_ENABLED=false
AI_PROVIDER=openai_compatible
AI_COMPATIBLE_BASE_URL=https://provider.example/v1
AI_COMPATIBLE_API_KEY=set-in-host-secret-manager
AI_COMPATIBLE_MODEL=provider-model-name
MOMO_MANUAL_PAYMENT_NUMBER=set-privately
MOMO_MANUAL_ACCOUNT_NAME=set-privately
PAYMENT_ADMIN_TOKEN=generate-a-long-random-value
```

Never put those values in GitHub or Android.

After confirming a transfer in the actual MoMo account, review it from the
backend directory:

```powershell
.venv\Scripts\python.exe review_payment.py PAYMENT_ID approve
```

The script asks for the administrator token without echoing it. Use `reject`
when the transfer cannot be verified.

## Production gates

- MTN merchant agreement, verified callbacks and idempotent reconciliation.
- Managed PostgreSQL and migrations; SQLite is only for a single-instance beta.
- Per-user Google OAuth token vault.
- Rate limiting, email verification, password reset and administrator console.
- Legal review of pricing, privacy, retention, refunds and consumer law.
- Security assessment, backups, observability and load testing.
- Signed Android release and store approval.
