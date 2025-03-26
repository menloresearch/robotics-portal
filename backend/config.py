import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")


class Config:
    max_concurrent_users = os.environ.get("MAX_CONCURRENT_USERS", 1)
    openai_base_url = os.environ.get(
        "OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    llm_model = os.environ.get(
        "LLM_MODEL", "anthropic/claude-3.5-haiku-20241022")
    api_key = os.environ.get("API_KEY", "")
    timeout_seconds = float(os.environ.get("TIMEOUT_SECONDS", 300))
    enable_history = bool(os.environ.get("ENABLE_HISTORY", False))
    tts_url = os.environ.get(
        "TTS_URL", "http://localhost:8880/v1/audio/speech")
    tts_voice = os.environ.get("TTS_VOICE", "af_jessica")
    tts_response_format = os.environ.get("TTS_RESPONSE_FORMAT", "wav")
    stt_url = os.environ.get(
        "STT_URL", "http://localhost:3348/v1/audio/transcriptions")
    stt_model = os.environ.get("STT_MODEL", "tiny")
