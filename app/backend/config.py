import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")


class Config:
    max_concurrent_users = os.environ.get("MAX_CONCURRENT_USERS", 1)
    openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    llm_model = os.environ.get("LLM_MODEL", "anthropic/claude-3.5-haiku-20241022")
    api_key = os.environ.get("API_KEY", "")
