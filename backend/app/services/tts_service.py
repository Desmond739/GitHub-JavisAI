from app.services.voice_service import (
    VoiceService,
    voice_service,
)


# Backward-compatible names for older MoneroAI modules.
TTSService = VoiceService
tts_service = voice_service
